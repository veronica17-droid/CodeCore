from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from core.content import ContentRepository
from core.models import Progress
from core.progress import ProgressStore


class ProgressStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "progress.json"
        self.store = ProgressStore(self.path)
        self.repo = ContentRepository()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_fresh_progress_when_file_missing(self) -> None:
        progress = self.store.load()
        self.assertIsNone(progress.level)
        self.assertEqual(progress.lessons, {})
        self.assertEqual(progress.schema_version, 1)

    def test_level_and_started_lesson(self) -> None:
        progress = Progress()
        self.store.set_level(progress, "beginner")
        self.store.mark_started(progress, "beg_01_orden")
        self.assertEqual(progress.level, "beginner")
        self.assertEqual(progress.lesson("beg_01_orden").status, "in_progress")
        self.assertEqual(progress.last_lesson_id, "beg_01_orden")

    def test_attempts_keep_best_score_and_completion(self) -> None:
        progress = Progress()
        self.store.record_attempt(progress, "beg_01_orden", 40, False, "intento 1")
        item = progress.lesson("beg_01_orden")
        self.assertEqual(item.attempts, 1)
        self.assertEqual(item.best_score, 40)
        self.assertEqual(item.status, "in_progress")

        self.store.record_attempt(
            progress, "beg_01_orden", 100, True, "intento 2", next_lesson_id="beg_02_variables"
        )
        self.assertEqual(item.status, "completed")
        self.assertEqual(item.best_score, 100)
        self.assertIsNotNone(item.completed_at)
        self.assertEqual(progress.last_lesson_id, "beg_02_variables")

        self.store.record_attempt(progress, "beg_01_orden", 20, False, "intento 3")
        self.assertEqual(item.attempts, 3)
        self.assertEqual(item.best_score, 100)
        self.assertEqual(item.status, "completed")

    def test_save_and_reload_roundtrip(self) -> None:
        progress = Progress()
        self.store.set_level(progress, "intermediate")
        self.store.record_attempt(progress, "int_01_listas", 75, True, "for nota in notas: ...")
        self.store.save(progress)

        reloaded = ProgressStore(self.path).load()
        self.assertEqual(reloaded.level, "intermediate")
        self.assertTrue(reloaded.is_completed("int_01_listas"))
        self.assertEqual(reloaded.lesson("int_01_listas").last_answer, "for nota in notas: ...")
        self.assertFalse(self.path.with_name("progress.json.tmp").exists())

    def test_corrupt_file_is_backed_up_and_replaced(self) -> None:
        self.path.write_text("{ esto no es json", encoding="utf-8")
        progress = self.store.load()
        self.assertEqual(progress.lessons, {})
        backups = list(self.path.parent.glob("progress.corrupt-*.json"))
        self.assertEqual(len(backups), 1)
        self.assertFalse(self.path.exists())

    def test_unsupported_schema_is_backed_up(self) -> None:
        self.path.write_text(json.dumps({"schema_version": 999, "lessons": {}}), encoding="utf-8")
        progress = self.store.load()
        self.assertEqual(progress.lessons, {})
        self.assertEqual(len(list(self.path.parent.glob("progress.corrupt-*.json"))), 1)

    def test_summary_counts_completed_lessons(self) -> None:
        progress = Progress()
        self.store.record_attempt(progress, "beg_01_orden", 100, True, "ok")
        summary = self.store.summary(progress, self.repo.levels)
        self.assertEqual(summary["overall"]["completed"], 1)
        self.assertEqual(summary["overall"]["total"], 13)
        beginner = next(row for row in summary["levels"] if row["id"] == "beginner")
        self.assertEqual(beginner["completed"], 1)
        self.assertEqual(beginner["total"], 5)
        self.assertEqual(beginner["percent"], 20)

    def test_reset_level_keeps_other_levels(self) -> None:
        progress = Progress()
        self.store.record_attempt(progress, "beg_01_orden", 100, True, "ok")
        self.store.record_attempt(progress, "int_01_listas", 100, True, "ok")
        self.store.reset_level(progress, self.repo.lessons_for_level("beginner"))
        self.assertFalse(progress.is_completed("beg_01_orden"))
        self.assertTrue(progress.is_completed("int_01_listas"))

    def test_reset_all(self) -> None:
        progress = Progress()
        self.store.set_level(progress, "beginner")
        self.store.record_attempt(progress, "beg_01_orden", 100, True, "ok")
        self.store.reset_all(progress)
        self.assertEqual(progress.lessons, {})
        self.assertIsNone(progress.level)
        self.assertIsNone(progress.last_lesson_id)


if __name__ == "__main__":
    unittest.main()
