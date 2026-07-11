#!/usr/bin/env python3
"""Repo-local validator for the SkillMesh plugin bundle."""

import argparse
import json
import re
import sys
from pathlib import Path


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DEFAULT_PROMPT_RE = re.compile(r'default_prompt:\s*"([^"]+)"')
ICON_RE = re.compile(r'(icon_small|icon_large):\s*"([^"]+)"')


def add_error(errors, message):
    if message not in errors:
        errors.append(message)


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not match:
        return None, text

    metadata = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip("\"'")
    return metadata, text[match.end():]


def validate_plugin_manifest(root, errors):
    manifest_path = root / ".codex-plugin" / "plugin.json"
    if not manifest_path.is_file():
        add_error(errors, "missing `.codex-plugin/plugin.json`")
        return None

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        add_error(errors, "invalid plugin.json: %s" % exc)
        return None

    for key in ("name", "version", "description", "skills", "interface"):
        if key not in manifest:
            add_error(errors, "plugin.json missing `%s`" % key)

    author_name = manifest.get("author", {}).get("name", "").strip() if isinstance(manifest.get("author"), dict) else ""
    if not author_name:
        add_error(errors, "plugin.json missing `author.name`")

    name = manifest.get("name", "")
    if not SKILL_NAME_RE.match(name):
        add_error(errors, "plugin name must be kebab-case")

    version = manifest.get("version", "")
    if not SEMVER_RE.match(version):
        add_error(errors, "plugin version must be semver")

    for key in ("homepage", "repository"):
        value = manifest.get(key, "")
        if value and not str(value).startswith("https://"):
            add_error(errors, "plugin `%s` must use https://" % key)

    skills_path = manifest.get("skills", "")
    if skills_path and not (root / skills_path.replace("./", "", 1)).is_dir():
        add_error(errors, "plugin skills path does not exist: %s" % skills_path)

    interface = manifest.get("interface", {})
    for key in ("displayName", "shortDescription", "longDescription", "developerName", "category", "defaultPrompt"):
        if key not in interface:
            add_error(errors, "plugin interface missing `%s`" % key)

    if isinstance(interface.get("defaultPrompt"), list):
        prompts = interface["defaultPrompt"]
        if not prompts or len(prompts) > 3:
            add_error(errors, "plugin interface.defaultPrompt must contain 1-3 items")
    else:
        add_error(errors, "plugin interface.defaultPrompt must be an array")

    for key in ("composerIcon", "logo", "logoDark"):
        asset = interface.get(key)
        if asset and not (root / asset.replace("./", "", 1)).is_file():
            add_error(errors, "plugin asset path does not exist: %s" % asset)

    for asset in interface.get("screenshots", []):
        if not asset.endswith(".png"):
            add_error(errors, "screenshot must be a png: %s" % asset)
        if not (root / asset.replace("./", "", 1)).is_file():
            add_error(errors, "screenshot path does not exist: %s" % asset)
    return manifest


def validate_skill_agent(skill_root, skill_name, errors):
    agent_path = skill_root / "agents" / "openai.yaml"
    if not agent_path.is_file():
        return

    text = agent_path.read_text(encoding="utf-8")
    if "interface:" not in text:
        add_error(errors, "%s agents/openai.yaml missing `interface`" % skill_name)

    if "display_name:" not in text:
        add_error(errors, "%s agents/openai.yaml missing `display_name`" % skill_name)

    if "short_description:" not in text:
        add_error(errors, "%s agents/openai.yaml missing `short_description`" % skill_name)

    prompt_match = DEFAULT_PROMPT_RE.search(text)
    if not prompt_match:
        add_error(errors, "%s agents/openai.yaml missing `default_prompt`" % skill_name)
    else:
        prompt = prompt_match.group(1)
        if "$%s" % skill_name not in prompt:
            add_error(errors, "%s default_prompt must mention $%s" % (skill_name, skill_name))

    for _, raw_path in ICON_RE.findall(text):
        asset_path = skill_root / raw_path.replace("./", "", 1)
        if not asset_path.is_file():
            add_error(errors, "%s asset path does not exist: %s" % (skill_name, raw_path))


def validate_skill(skill_root, errors):
    skill_md = skill_root / "SKILL.md"
    if not skill_md.is_file():
        add_error(errors, "missing skill manifest: %s" % skill_root)
        return

    metadata, body = parse_frontmatter(skill_md)
    if metadata is None:
        add_error(errors, "%s missing YAML frontmatter" % skill_root.name)
        return

    allowed = {"name", "description"}
    for key in metadata:
        if key not in allowed:
            add_error(errors, "%s has unexpected frontmatter key `%s`" % (skill_root.name, key))

    skill_name = metadata.get("name", "").strip()
    description = metadata.get("description", "").strip()
    if not skill_name:
        add_error(errors, "%s missing frontmatter `name`" % skill_root.name)
    elif not SKILL_NAME_RE.match(skill_name):
        add_error(errors, "%s skill name must be kebab-case" % skill_root.name)

    if skill_name and skill_root.name != skill_name:
        add_error(errors, "%s folder name must match skill name" % skill_root.name)

    if not description:
        add_error(errors, "%s missing frontmatter `description`" % skill_root.name)
    elif len(description) > 1024:
        add_error(errors, "%s description is too long" % skill_root.name)

    if "[TODO:" in body:
        add_error(errors, "%s still contains TODO placeholders" % skill_root.name)

    validate_skill_agent(skill_root, skill_name or skill_root.name, errors)


def validate_plugin(root):
    root = Path(root).resolve()
    errors = []
    manifest = validate_plugin_manifest(root, errors)
    skills_root = root / "skills"
    if manifest and not skills_root.is_dir():
        add_error(errors, "missing skills directory")

    if skills_root.is_dir():
        for skill_md in sorted(skills_root.rglob("SKILL.md")):
            validate_skill(skill_md.parent, errors)

    return errors


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Validate SkillMesh plugin locally")
    parser.add_argument("plugin_root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    errors = validate_plugin(args.plugin_root)
    result = {"ok": not errors, "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        if errors:
            print("Plugin validation failed:")
            for error in errors:
                print("- %s" % error)
        else:
            print("Plugin validation passed: %s" % Path(args.plugin_root).resolve())
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
