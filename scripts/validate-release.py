#!/usr/bin/env python3
"""Validate a local SkillMesh release directory or zip archive."""

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path


REQUIRED_PATHS = [
    ".codex-plugin/plugin.json",
    "skills",
    "assets",
    "scripts",
    "config",
    "README.md",
]


def validate_root(root):
    missing = []
    for relative in REQUIRED_PATHS:
        if not (root / relative).exists():
            missing.append(relative)

    manifest_path = root / ".codex-plugin" / "plugin.json"
    manifest = {}
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return {"ok": False, "missing": missing, "error": "plugin.json 解析失败: %s" % exc}
    else:
        return {"ok": False, "missing": missing, "error": "缺少 plugin.json"}

    expected = {"skillmesh", manifest.get("name")}
    if manifest.get("name") not in expected:
        return {"ok": False, "missing": missing, "error": "插件名异常: %s" % manifest.get("name")}

    return {"ok": not missing, "missing": missing, "error": ""}


def validate_target(target):
    target = Path(target).resolve()
    if target.is_dir():
        return validate_root(target)
    if target.is_file() and target.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(str(target), "r") as archive:
                archive.extractall(temp_dir)
            entries = list(Path(temp_dir).iterdir())
            root = entries[0] if len(entries) == 1 and entries[0].is_dir() else Path(temp_dir)
            return validate_root(root)
    return {"ok": False, "missing": [], "error": "只支持目录或 zip 文件"}


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Validate SkillMesh release artifact")
    parser.add_argument("target", help="Release directory or zip file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = validate_target(args.target)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        if result["ok"]:
            print("Release 验证通过")
        else:
            print("Release 验证失败")
            if result["missing"]:
                print("缺失：%s" % "、".join(result["missing"]))
            if result["error"]:
                print("错误：%s" % result["error"])
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
