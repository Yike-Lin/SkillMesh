import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "skillmesh.py"


class SkillMeshCliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.skills = self.workspace / "skills"
        self.skills.mkdir(parents=True)
        (self.workspace / "package.json").write_text(
            json.dumps({"dependencies": {"react": "1.0.0", "typescript": "1.0.0"}}),
            encoding="utf-8",
        )
        skill = self.skills / "playwright"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: playwright\ndescription: 自动化浏览器并测试 React 页面。\n---\n\n# Playwright\n",
            encoding="utf-8",
        )
        self.db = self.root / "skillmesh.db"

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *arguments):
        command = [sys.executable, str(CLI), "--db", str(self.db)] + list(arguments)
        return subprocess.run(command, check=True, text=True, encoding="utf-8", stdout=subprocess.PIPE).stdout

    def test_recommend_persists_ranked_result(self):
        output = self.run_cli(
            "recommend", "测试 React 前端页面", "--workspace", str(self.workspace), "--limit", "1", "--json"
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
            "recommend", "测试 React 页面", "--workspace", str(self.workspace), "--json"
        ))
        self.run_cli("feedback", result["recommendation_id"], "playwright", "helpful")
        run_id = self.run_cli("observe-start", "playwright", "--workspace", str(self.workspace)).strip()
        self.run_cli("observe-finish", run_id, "--outcome", "success", "--feedback", "helpful")
        report = json.loads(self.run_cli("report", "--workspace", str(self.workspace), "--json"))
        self.assertEqual(1, report["recommendations"]["accepted"])
        self.assertEqual(1, report["runs"]["successes"])
        self.assertEqual(1, report["runs"]["helpful"])


if __name__ == "__main__":
    unittest.main()
