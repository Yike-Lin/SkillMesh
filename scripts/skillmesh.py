#!/usr/bin/env python3
"""SkillMesh local recommendation, persistence, and observability engine."""

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "docs" / "schema.sql"
RULES_PATH = REPO_ROOT / "config" / "recommendation-rules.json"
DEFAULT_DB = Path(os.environ.get("SKILLMESH_DB", Path.home() / ".skillmesh" / "skillmesh.db"))
SKIP_DIRS = {".git", ".idea", ".next", ".skillmesh", ".venv", "dist", "node_modules", "target", "venv"}


def utc_now():
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def stable_id(prefix, value):
    return "%s:%s" % (prefix, uuid.uuid5(uuid.NAMESPACE_URL, str(value)))


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_frontmatter(path):
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?", text, re.DOTALL)
    if not match:
        return {}, text
    metadata = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator and re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", key.strip()):
            metadata[key.strip()] = value.strip().strip("\"'")
    return metadata, text[match.end():]


def plugin_manifest_for(path):
    current = Path(path).resolve().parent
    for parent in [current] + list(current.parents):
        manifest = parent / ".codex-plugin" / "plugin.json"
        if manifest.is_file():
            try:
                return read_json(manifest), parent
            except (OSError, ValueError):
                return {}, parent
    return {}, None


def discover_skill_roots(workspace, explicit_roots, include_installed):
    candidates = [Path(item).expanduser() for item in explicit_roots]
    workspace_skills = Path(workspace) / "skills"
    if workspace_skills.is_dir():
        candidates.append(workspace_skills)
    if include_installed:
        home = Path.home()
        candidates.extend([
            Path(os.environ.get("CODEX_HOME", home / ".codex")) / "skills",
            home / ".agents" / "skills",
            Path(os.environ.get("CODEX_HOME", home / ".codex")) / "plugins" / "cache",
        ])
    unique = []
    seen = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        key = os.path.normcase(str(resolved))
        if resolved.is_dir() and key not in seen:
            seen.add(key)
            unique.append(resolved)
    return unique


def find_skill_files(root):
    root = Path(root)
    if root.name == "SKILL.md" and root.is_file():
        return [root]
    return sorted(root.rglob("SKILL.md"))


def scan_workspace(root, max_files=5000):
    root = Path(root).resolve()
    files = []
    extensions = {}
    manifests = []
    for current, dirs, names in os.walk(str(root)):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        for name in names:
            relative = Path(current, name).relative_to(root).as_posix()
            files.append(relative)
            suffix = Path(name).suffix.lower()
            if suffix:
                extensions[suffix] = extensions.get(suffix, 0) + 1
            if name in {"package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml", "plugin.json", ".mcp.json", ".app.json"}:
                manifests.append(relative)
            if len(files) >= max_files:
                break
        if len(files) >= max_files:
            break

    frameworks = []
    package_json = root / "package.json"
    if package_json.is_file():
        try:
            package = read_json(package_json)
            dependencies = {}
            dependencies.update(package.get("dependencies", {}))
            dependencies.update(package.get("devDependencies", {}))
            for name in ("react", "vue", "svelte", "next", "nuxt", "vite", "typescript"):
                if name in dependencies:
                    frameworks.append(name)
        except (OSError, ValueError):
            pass
    language_map = {
        ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
        ".ts": "TypeScript", ".tsx": "TypeScript", ".rs": "Rust",
        ".go": "Go", ".java": "Java", ".cs": "C#", ".swift": "Swift",
    }
    languages = sorted({language_map[key] for key in extensions if key in language_map})
    return {
        "file_count": len(files),
        "truncated": len(files) >= max_files,
        "files": files,
        "extensions": extensions,
        "manifests": manifests,
        "languages": languages,
        "frameworks": sorted(frameworks),
    }


class Store(object):
    def __init__(self, path):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.connection.commit()

    def close(self):
        self.connection.close()

    def upsert_workspace(self, root, signals):
        root = Path(root).resolve()
        workspace_id = stable_id("workspace", os.path.normcase(str(root)))
        remote = ""
        git_config = root / ".git" / "config"
        if git_config.is_file():
            text = git_config.read_text(encoding="utf-8", errors="ignore")
            match = re.search(r"url\s*=\s*(.+)", text)
            remote = match.group(1).strip() if match else ""
        self.connection.execute(
            """INSERT INTO workspaces
               (id, name, root_path, language_stack_json, frameworks_json, repo_remote, signals_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(root_path) DO UPDATE SET name=excluded.name,
                 language_stack_json=excluded.language_stack_json,
                 frameworks_json=excluded.frameworks_json, repo_remote=excluded.repo_remote,
                 signals_json=excluded.signals_json""",
            (workspace_id, root.name, str(root), json_text(signals["languages"]),
             json_text(signals["frameworks"]), remote, json_text(signals)),
        )
        self.connection.commit()
        return workspace_id

    def index_skills(self, roots):
        indexed = []
        seen_slugs = set()
        for root in roots:
            source_id = stable_id("source", os.path.normcase(str(root)))
            self.connection.execute(
                """INSERT INTO sources (id, type, name, uri, last_synced_at)
                   VALUES (?, 'local_dir', ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET name=excluded.name, uri=excluded.uri,
                     last_synced_at=excluded.last_synced_at""",
                (source_id, Path(root).name, str(root), utc_now()),
            )
            for skill_file in find_skill_files(root):
                metadata, body = parse_frontmatter(skill_file)
                slug = metadata.get("name", skill_file.parent.name).strip().lower()
                if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
                    continue
                if slug in seen_slugs:
                    continue
                seen_slugs.add(slug)
                description = metadata.get("description", "").strip()
                heading = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
                name = heading.group(1).strip() if heading else slug
                manifest, plugin_root = plugin_manifest_for(skill_file)
                plugin_name = manifest.get("name", "") if manifest else ""
                tags = sorted(set(re.findall(r"[a-z][a-z0-9-]{2,}", (slug + " " + description).lower())))
                if plugin_name:
                    tags.append("plugin:%s" % plugin_name)
                skill_id = "skill:%s" % slug
                self.connection.execute(
                    """INSERT INTO skills
                       (id, slug, name, summary, description, status, source_id, canonical_uri,
                        author, tags_json, agent_targets_json, visibility, trust_level, updated_at)
                       VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, '[\"codex\"]', ?, ?, ?)
                       ON CONFLICT(slug) DO UPDATE SET name=excluded.name, summary=excluded.summary,
                         description=excluded.description, status='active', source_id=excluded.source_id,
                         canonical_uri=excluded.canonical_uri, author=excluded.author,
                         tags_json=excluded.tags_json, updated_at=excluded.updated_at""",
                    (skill_id, slug, name, description[:240], description, source_id, str(skill_file),
                     manifest.get("author", {}).get("name", "") if manifest else "",
                     json_text(tags), "local", "verified" if plugin_root else "unverified", utc_now()),
                )
                self.connection.execute("DELETE FROM skill_search WHERE skill_id = ?", (skill_id,))
                self.connection.execute(
                    "INSERT INTO skill_search (skill_id, name, summary, tags, source) VALUES (?, ?, ?, ?, ?)",
                    (skill_id, name, description, " ".join(tags), str(root)),
                )
                indexed.append({"slug": slug, "path": str(skill_file), "plugin": plugin_name})
        self.connection.commit()
        return indexed

    def skills(self):
        return [dict(row) for row in self.connection.execute(
            "SELECT id, slug, name, summary, description, canonical_uri, tags_json, trust_level FROM skills WHERE status='active'"
        )]

    def save_recommendation(self, workspace_id, task, context, items):
        recommendation_id = stable_id("recommendation", "%s:%s" % (utc_now(), uuid.uuid4()))
        self.connection.execute(
            "INSERT INTO recommendations (id, workspace_id, prompt_excerpt, context_json) VALUES (?, ?, ?, ?)",
            (recommendation_id, workspace_id, task[:500], json_text(context)),
        )
        for item in items:
            self.connection.execute(
                """INSERT INTO recommendation_items
                   (id, recommendation_id, skill_id, score, reason_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (stable_id("recommendation-item", recommendation_id + ":" + item["slug"]),
                 recommendation_id, item["id"], item["score"], json_text(item["reasons"])),
            )
        self.connection.commit()
        return recommendation_id


def terms(text):
    lowered = text.lower()
    result = set(re.findall(r"[a-z0-9][a-z0-9+#.-]{1,}", lowered))
    for block in re.findall(r"[\u4e00-\u9fff]{2,}", lowered):
        result.update(block[index:index + 2] for index in range(len(block) - 1))
    return result


def selector_matches(skill, selectors):
    haystack = " ".join([skill["slug"], skill["name"], skill["description"]]).lower()
    return any(selector.lower() in haystack for selector in selectors)


def rule_matches(rule, task, signals):
    lowered = task.lower()
    reasons = []
    matched_keywords = [value for value in rule.get("keywords", []) if value.lower() in lowered]
    if matched_keywords:
        reasons.append("任务关键词：%s" % "、".join(matched_keywords[:4]))
    matched_files = []
    for pattern in rule.get("file_patterns", []):
        if any(fnmatch.fnmatch(path, pattern) for path in signals["files"]):
            matched_files.append(pattern)
    if matched_files:
        reasons.append("仓库文件：%s" % "、".join(matched_files[:3]))
    matched_signals = []
    signal_values = set(signals["languages"] + signals["frameworks"] + signals["manifests"])
    for value in rule.get("repo_signals", []):
        if value in signal_values:
            matched_signals.append(value)
    if matched_signals:
        reasons.append("技术信号：%s" % "、".join(matched_signals[:3]))
    return reasons, bool(matched_keywords), len(matched_files) + len(matched_signals)


def preflight(commands):
    return [{"command": command, "available": shutil.which(command) is not None} for command in sorted(set(commands))]


def rank_skills(skills, task, signals, rules, limit):
    task_terms = terms(task)
    ranked = []
    for skill in skills:
        score = 0.0
        reasons = []
        required = []
        metadata_terms = terms(" ".join([skill["slug"], skill["name"], skill["description"], skill["tags_json"]]))
        overlap = sorted(task_terms.intersection(metadata_terms))
        if overlap:
            score += min(30.0, len(overlap) * 4.0)
            reasons.append("能力描述匹配：%s" % "、".join(overlap[:5]))
        slug_words = skill["slug"].replace("-", " ")
        if slug_words in task.lower() or skill["slug"] in task.lower():
            score += 35.0
            reasons.append("任务直接点名该能力")
        for rule in rules:
            rule_reasons, intent_matched, repo_match_count = rule_matches(rule, task, signals)
            if rule_reasons and selector_matches(skill, rule.get("skill_patterns", [])):
                weight = float(rule.get("weight", 20))
                if intent_matched:
                    score += weight + min(12, len(rule_reasons) * 4)
                else:
                    score += min(10.0, weight * 0.3) + min(3.0, repo_match_count)
                reasons.extend(rule_reasons)
                required.extend(rule.get("requires", []))
        if score > 0:
            ranked.append({
                "id": skill["id"], "slug": skill["slug"], "name": skill["name"],
                "score": round(score, 2), "reasons": list(dict.fromkeys(reasons)),
                "path": skill["canonical_uri"], "trust": skill["trust_level"],
                "preflight": preflight(required),
            })
    ranked.sort(key=lambda item: (-item["score"], item["slug"]))
    return ranked[:limit]


def ensure_skill(store, slug):
    row = store.connection.execute("SELECT id FROM skills WHERE slug = ?", (slug,)).fetchone()
    if row:
        return row["id"]
    skill_id = "skill:%s" % slug
    source_id = stable_id("source", "skillmesh-runtime")
    store.connection.execute(
        "INSERT OR IGNORE INTO sources (id, type, name, uri) VALUES (?, 'plugin_bundle', 'SkillMesh Runtime', 'skillmesh://runtime')",
        (source_id,),
    )
    store.connection.execute(
        """INSERT INTO skills
           (id, slug, name, status, source_id, visibility, trust_level)
           VALUES (?, ?, ?, 'active', ?, 'local', 'unverified')""",
        (skill_id, slug, slug, source_id),
    )
    store.connection.commit()
    return skill_id


def print_recommendation(result):
    print("推荐编号：%s" % result["recommendation_id"])
    print("工作区：%s" % result["workspace"])
    if not result["items"]:
        print("没有找到足够匹配的已安装 Skill。请先运行 index 并增加 Skill 来源。")
        return
    for index, item in enumerate(result["items"], 1):
        print("\n%d. %s  [%.1f]" % (index, item["slug"], item["score"]))
        print("   原因：%s" % "；".join(item["reasons"]))
        missing = [check["command"] for check in item["preflight"] if not check["available"]]
        print("   前置：%s" % ("缺少 " + "、".join(missing) if missing else "已通过"))
        print("   位置：%s" % item["path"])


def command_index(args, store):
    workspace = Path(args.workspace).resolve()
    signals = scan_workspace(workspace)
    workspace_id = store.upsert_workspace(workspace, signals)
    roots = discover_skill_roots(workspace, args.skill_root, args.include_installed)
    indexed = store.index_skills(roots)
    result = {"workspace_id": workspace_id, "workspace": str(workspace), "roots": [str(root) for root in roots], "skills": indexed}
    if args.json:
        print(json_text(result))
    else:
        print("已索引 %d 个 Skill，来源 %d 个。" % (len(indexed), len(roots)))
        print("数据库：%s" % store.path)


def command_recommend(args, store):
    workspace = Path(args.workspace).resolve()
    signals = scan_workspace(workspace)
    workspace_id = store.upsert_workspace(workspace, signals)
    roots = discover_skill_roots(workspace, args.skill_root, True)
    indexed = store.index_skills(roots)
    rules = read_json(RULES_PATH)["rules"]
    items = rank_skills(store.skills(), args.task, signals, rules, args.limit)
    context = {"signals": signals, "indexed_skill_count": len(indexed), "skill_roots": [str(root) for root in roots]}
    recommendation_id = store.save_recommendation(workspace_id, args.task, context, items)
    result = {"recommendation_id": recommendation_id, "workspace": str(workspace), "task": args.task, "items": items}
    if args.json:
        print(json_text(result))
    else:
        print_recommendation(result)


def command_feedback(args, store):
    value = 1 if args.feedback == "helpful" else 0
    cursor = store.connection.execute(
        """UPDATE recommendation_items SET accepted=?, rejected_reason=?
           WHERE recommendation_id=? AND skill_id=(SELECT id FROM skills WHERE slug=?)""",
        (value, "" if value else args.reason, args.recommendation_id, args.skill),
    )
    store.connection.commit()
    if cursor.rowcount != 1:
        raise SystemExit("未找到对应的推荐项。")
    print("已记录反馈：%s -> %s" % (args.skill, args.feedback))


def command_observe_start(args, store):
    workspace = Path(args.workspace).resolve()
    signals = scan_workspace(workspace)
    workspace_id = store.upsert_workspace(workspace, signals)
    skill_id = ensure_skill(store, args.skill)
    run_id = stable_id("run", "%s:%s" % (utc_now(), uuid.uuid4()))
    store.connection.execute(
        "INSERT INTO runs (id, skill_id, workspace_id, started_at, outcome, cost_json) VALUES (?, ?, ?, ?, 'abandoned', ?)",
        (run_id, skill_id, workspace_id, utc_now(), json_text({"command": args.execution_command or ""})),
    )
    store.connection.commit()
    print(run_id)


def command_observe_finish(args, store):
    cursor = store.connection.execute(
        "UPDATE runs SET ended_at=?, outcome=?, feedback=?, error_summary=? WHERE id=?",
        (utc_now(), args.outcome, args.feedback, args.error, args.run_id),
    )
    store.connection.commit()
    if cursor.rowcount != 1:
        raise SystemExit("未找到运行记录：%s" % args.run_id)
    print("已完成运行记录：%s" % args.run_id)


def command_report(args, store):
    run_filter = ""
    recommendation_filter = ""
    parameters = []
    if args.workspace:
        workspace_root = Path(args.workspace).resolve()
        workspace_id = stable_id("workspace", os.path.normcase(str(workspace_root)))
        run_filter = " WHERE r.workspace_id = ?"
        recommendation_filter = " WHERE rec.workspace_id = ?"
        parameters.append(workspace_id)
    totals = store.connection.execute(
        """SELECT COUNT(*) AS runs,
                  SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END) AS successes,
                  SUM(CASE WHEN outcome='failed' THEN 1 ELSE 0 END) AS failures,
                  SUM(CASE WHEN feedback='helpful' THEN 1 ELSE 0 END) AS helpful,
                  SUM(CASE WHEN feedback='misfire' THEN 1 ELSE 0 END) AS misfires
           FROM runs r""" + run_filter,
        parameters,
    ).fetchone()
    recs = store.connection.execute(
        """SELECT COUNT(DISTINCT rec.id) AS recommendations,
                  COUNT(ri.id) AS items,
                  SUM(ri.accepted) AS accepted,
                  SUM(CASE WHEN ri.rejected_reason <> '' THEN 1 ELSE 0 END) AS rejected
           FROM recommendations rec
           LEFT JOIN recommendation_items ri ON ri.recommendation_id=rec.id""" + recommendation_filter,
        parameters,
    ).fetchone()
    top_filter = ""
    top_parameters = []
    if args.workspace:
        top_filter = " WHERE rec.workspace_id = ?"
        top_parameters.append(workspace_id)
    top = store.connection.execute(
        """SELECT s.slug, COUNT(*) AS recommended, SUM(ri.accepted) AS accepted
           FROM recommendation_items ri
           JOIN skills s ON s.id=ri.skill_id
           JOIN recommendations rec ON rec.id=ri.recommendation_id""" + top_filter + """
           GROUP BY s.slug ORDER BY recommended DESC, s.slug LIMIT 10"""
        , top_parameters).fetchall()
    result = {
        "database": str(store.path),
        "workspace_id": workspace_id if args.workspace else None,
        "runs": {key: totals[key] or 0 for key in totals.keys()},
        "recommendations": {key: recs[key] or 0 for key in recs.keys()},
        "top_skills": [dict(row) for row in top],
    }
    if args.json:
        print(json_text(result))
    else:
        print("SkillMesh 观测报告")
        print("推荐：{recommendations} 次，候选 {items} 个，采纳 {accepted} 个，拒绝 {rejected} 个".format(**result["recommendations"]))
        print("运行：{runs} 次，成功 {successes} 次，失败 {failures} 次，有帮助 {helpful} 次，误判 {misfires} 次".format(**result["runs"]))
        if result["top_skills"]:
            print("高频推荐：" + "、".join("%s(%d)" % (row["slug"], row["recommended"]) for row in result["top_skills"]))


def build_parser():
    parser = argparse.ArgumentParser(description="SkillMesh 本地推荐与观测引擎")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite 数据库路径")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index = subparsers.add_parser("index", help="索引工作区和 Skill 来源")
    index.add_argument("--workspace", default=".")
    index.add_argument("--skill-root", action="append", default=[])
    index.add_argument("--include-installed", action="store_true")
    index.add_argument("--json", action="store_true")

    recommend = subparsers.add_parser("recommend", help="生成并保存排序推荐")
    recommend.add_argument("task")
    recommend.add_argument("--workspace", default=".")
    recommend.add_argument("--skill-root", action="append", default=[])
    recommend.add_argument("--limit", type=int, default=5)
    recommend.add_argument("--json", action="store_true")

    feedback = subparsers.add_parser("feedback", help="记录推荐反馈")
    feedback.add_argument("recommendation_id")
    feedback.add_argument("skill")
    feedback.add_argument("feedback", choices=["helpful", "misfire"])
    feedback.add_argument("--reason", default="")

    observe_start = subparsers.add_parser("observe-start", help="开始记录一次 Skill 执行")
    observe_start.add_argument("skill")
    observe_start.add_argument("--workspace", default=".")
    observe_start.add_argument("--command", dest="execution_command")

    observe_finish = subparsers.add_parser("observe-finish", help="完成一次 Skill 执行记录")
    observe_finish.add_argument("run_id")
    observe_finish.add_argument("--outcome", choices=["success", "warning", "failed", "abandoned"], required=True)
    observe_finish.add_argument("--feedback", choices=["helpful", "unrated", "misfire"], default="unrated")
    observe_finish.add_argument("--error", default="")

    report = subparsers.add_parser("report", help="输出推荐与运行统计")
    report.add_argument("--workspace")
    report.add_argument("--json", action="store_true")
    return parser


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    store = Store(args.db)
    try:
        handlers = {
            "index": command_index, "recommend": command_recommend, "feedback": command_feedback,
            "observe-start": command_observe_start, "observe-finish": command_observe_finish,
            "report": command_report,
        }
        handlers[args.command](args, store)
    finally:
        store.close()


if __name__ == "__main__":
    main()
