#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).parents[1]
    / "skills"
    / "daily-report"
    / "scripts"
    / "daily_report.py"
)
DAY = "2026-07-15"


class DailyReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name) / "ledger"
        self.payload_counter = 0

    def tearDown(self):
        self.temp.cleanup()

    def payload(self, data):
        self.payload_counter += 1
        path = Path(self.temp.name) / f"payload-{self.payload_counter}.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def run_command(self, *args, expected=0):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--home", str(self.home), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, expected, completed.stdout + completed.stderr)
        return json.loads(completed.stdout)

    def setup_name(self):
        payload = self.payload({"name": "张三"})
        result = self.run_command(
            "setup", "--payload", str(payload), "--consume-payload"
        )
        self.assertEqual(result["profile"]["name"], "张三")
        self.assertFalse(payload.exists())

    def record_thread_one(self):
        payload = self.payload(
            {
                "date": DAY,
                "thread_id": "thread-1",
                "thread_title": "完成网关设计",
                "thread_cwd": "/tmp/project",
                "items": [
                    {
                        "title": "整理网关下一步计划",
                        "primary_url": "https://example.com/gateway",
                        "urls": ["https://example.com/gateway"],
                    },
                    {
                        "title": "完成传输层讨论",
                        "primary_url": "/tmp/local-note.md",
                        "local_artifacts": ["/tmp/local-note.md"],
                    },
                ],
            }
        )
        return self.run_command(
            "record", "--payload", str(payload), "--consume-payload"
        )

    def test_name_is_required_before_generate(self):
        self.record_thread_one()
        result = self.run_command("generate", "--date", DAY, expected=2)
        self.assertEqual(result["error"], "name_required")

    def test_cross_thread_upsert_generate_edit_and_remove(self):
        self.setup_name()
        first = self.record_thread_one()
        self.assertEqual(first["action"], "created")
        self.assertEqual(len(first["items"]), 2)
        self.assertEqual(len(first["missing_links"]), 1)
        missing_id = first["missing_links"][0]["id"]

        replacement = self.payload(
            {
                "date": DAY,
                "thread_id": "thread-1",
                "thread_title": "完成网关设计",
                "items": [
                    {
                        "title": "整理网关下一步计划",
                        "primary_url": "https://example.com/gateway",
                    },
                    {
                        "title": "完成传输层讨论",
                        "local_artifacts": ["/tmp/local-note.md"],
                    },
                ],
            }
        )
        updated = self.run_command(
            "record", "--payload", str(replacement), "--consume-payload"
        )
        self.assertEqual(updated["action"], "updated")
        self.assertEqual(len(updated["items"]), 2)
        self.assertEqual(updated["missing_links"][0]["id"], missing_id)

        second = self.payload(
            {
                "date": DAY,
                "thread_id": "thread-2",
                "thread_title": "实现注册表",
                "items": [
                    {
                        "title": "实现分层 Action Registry",
                        "primary_url": "https://example.com/registry",
                        "urls": ["https://example.com/registry"],
                    }
                ],
            }
        )
        self.run_command(
            "record", "--payload", str(second), "--consume-payload"
        )

        listed = self.run_command("list", "--date", DAY)
        self.assertEqual(listed["count"], 3)
        self.assertEqual(listed["missing_link_count"], 1)

        report = self.run_command("generate", "--date", DAY)
        self.assertTrue(report["report"].startswith("张三 7.15 日报\n今日完成："))
        self.assertIn("- 完成传输层讨论：链接待补", report["report"])
        self.assertNotIn("明日计划：", report["report"])

        minutes = self.payload(
            {
                "tomorrow_plan": [
                    "- 继续细化网关下一步计划",
                    "继续细化网关下一步计划",
                    "实现 URL Scheme",
                ]
            }
        )
        planned = self.run_command(
            "generate",
            "--date",
            DAY,
            "--payload",
            str(minutes),
            "--consume-payload",
        )
        self.assertEqual(
            planned["tomorrow_plan"],
            ["继续细化网关下一步计划", "实现 URL Scheme"],
        )
        self.assertIn("明日计划：\n- 继续细化网关下一步计划", planned["report"])

        edit = self.payload({"primary_url": "https://example.com/transport"})
        edited = self.run_command(
            "edit", missing_id, "--payload", str(edit), "--consume-payload"
        )
        self.assertFalse(edited["missing_link"])
        self.assertEqual(edited["item"]["primary_url"], "https://example.com/transport")

        complete = self.run_command("generate", "--date", DAY)
        self.assertEqual(complete["missing_links"], [])
        self.assertIn(
            "- 完成传输层讨论：https://example.com/transport", complete["report"]
        )

        removed = self.run_command("remove", missing_id)
        self.assertEqual(removed["removed"]["title"], "完成传输层讨论")
        final_list = self.run_command("list", "--date", DAY)
        self.assertEqual(final_list["count"], 2)


if __name__ == "__main__":
    unittest.main()
