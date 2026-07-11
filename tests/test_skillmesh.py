import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "skillmesh.py"
PLUGIN_VALIDATOR = ROOT / "scripts" / "validate-plugin-local.py"


class SkillMeshCliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.skills = self.workspace / "skills"
        self.skills.mkdir(parents=True)
        (self.workspace / ".codex-plugin").mkdir()
        (self.workspace / "scripts").mkdir()
        (self.workspace / "docs").mkdir()
        (self.workspace / "package.json").write_text(
            json.dumps({"dependencies": {"react": "1.0.0", "typescript": "1.0.0"}}),
            encoding="utf-8",
        )
        (self.workspace / ".codex-plugin" / "plugin.json").write_text(
            json.dumps({"name": "demo-plugin"}, ensure_ascii=False),
            encoding="utf-8",
        )
        (self.workspace / "scripts" / "build-release.ps1").write_text("Write-Host 'release'", encoding="utf-8")
        (self.workspace / "scripts" / "install-local-plugin.ps1").write_text("Write-Host 'install'", encoding="utf-8")
        (self.workspace / "docs" / "schema.sql").write_text("CREATE TABLE runs(id TEXT);", encoding="utf-8")
        self.make_skill("playwright", "自动化浏览器并测试 React 页面。")
        self.make_skill("nature-writing", "把课程报告、论文正文和学术写作内容整理成可提交版本。")
        self.make_skill("skillmesh-publisher", "校验、打包并准备发布 Codex 插件。")
        self.make_skill("skillmesh-observer", "记录推荐反馈、执行结果和统计报告。")
        self.db = self.root / "skillmesh.db"

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *arguments):
        command = [sys.executable, str(CLI), "--db", str(self.db)] + list(arguments)
        return subprocess.run(command, check=True, text=True, encoding="utf-8", stdout=subprocess.PIPE).stdout

    def make_skill(self, slug, description):
        skill = self.skills / slug
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: %s\ndescription: %s\n---\n\n# %s\n" % (slug, description, slug),
            encoding="utf-8",
        )

    def test_recommend_persists_ranked_result(self):
        output = self.run_cli(
            "recommend", "用 playwright 测试 React 前端页面", "--workspace", str(self.workspace), "--limit", "1", "--json"
        )
        result = json.loads(output)
        self.assertEqual("playwright", result["items"][0]["slug"])
        self.assertGreater(result["items"][0]["score"], 0)
        connection = sqlite3.connect(str(self.db))
        try:
            self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0])
            self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM recommendation_items").fetchone()[0])
        finally:
            connection.close()

    def test_feedback_and_run_observability(self):
        result = json.loads(self.run_cli(
            "recommend", "用 playwright 测试 React 页面", "--workspace", str(self.workspace), "--json"
        ))
        self.run_cli("feedback", result["recommendation_id"], "playwright", "helpful")
        run_id = self.run_cli("observe-start", "playwright", "--workspace", str(self.workspace)).strip()
        self.run_cli("observe-finish", run_id, "--outcome", "success", "--feedback", "helpful")
        report = json.loads(self.run_cli("report", "--workspace", str(self.workspace), "--json"))
        self.assertEqual(1, report["recommendations"]["accepted"])
        self.assertEqual(1, report["runs"]["successes"])
        self.assertEqual(1, report["runs"]["helpful"])

    def test_release_task_prefers_publisher_skill(self):
        result = json.loads(self.run_cli(
            "recommend", "帮我发布这个 Codex 插件并生成 SHA256", "--workspace", str(self.workspace), "--limit", "1", "--json"
        ))
        self.assertEqual("skillmesh-publisher", result["items"][0]["slug"])

    def test_observability_task_prefers_observer_skill(self):
        result = json.loads(self.run_cli(
            "recommend", "用 skillmesh-observer 看下这个插件最近的反馈和统计报告", "--workspace", str(self.workspace), "--limit", "1", "--json"
        ))
        self.assertEqual("skillmesh-observer", result["items"][0]["slug"])

    def test_plugin_repo_focus_filters_unrelated_nature_skills(self):
        result = json.loads(self.run_cli(
            "recommend", "帮我盘点这个 Codex 插件仓库并准备发布", "--workspace", str(self.workspace), "--limit", "5", "--json"
        ))
        self.assertTrue(result["items"])
        self.assertTrue(all(not item["slug"].startswith("nature-") for item in result["items"]))


class PluginValidatorTest(unittest.TestCase):
    def test_repo_plugin_validator_passes(self):
        command = [sys.executable, str(PLUGIN_VALIDATOR), str(ROOT), "--json"]
        output = subprocess.run(command, check=True, text=True, encoding="utf-8", stdout=subprocess.PIPE).stdout
        result = json.loads(output)
        self.assertTrue(result["ok"], result["errors"])


if __name__ == "__main__":
    unittest.main()
