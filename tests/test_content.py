from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from core.content import ContentError, ContentRepository


class ContentRepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = ContentRepository()

    def test_levels_are_loaded_in_order(self) -> None:
        self.assertEqual([level.id for level in self.repo.levels], ["beginner", "intermediate", "advanced"])
        self.assertEqual([level.order for level in self.repo.levels], [1, 2, 3])

    def test_all_level_lessons_exist(self) -> None:
        for level in self.repo.levels:
            lessons = self.repo.lessons_for_level(level.id)
            self.assertEqual(len(lessons), len(level.lesson_ids))
            self.assertTrue(all(lesson.level_id == level.id for lesson in lessons))

    def test_expected_lesson_count(self) -> None:
        self.assertEqual(len(self.repo.lessons), 13)

    def test_lesson_ids_are_unique_and_have_required_sections(self) -> None:
        for lesson in self.repo.lessons.values():
            self.assertTrue(lesson.problem.question)
            self.assertTrue(lesson.guide.steps)
            self.assertTrue(lesson.success_criteria)
            self.assertTrue(lesson.exercise.prompt)

    def test_every_solution_passes_its_own_checks(self) -> None:
        from core.feedback import evaluate

        for lesson in self.repo.all_lessons():
            exercise = lesson.exercise
            if exercise.type == "choice":
                answer = next(option.id for option in exercise.options if option.correct)
            else:
                answer = exercise.solution
            result = evaluate(exercise, answer, attempt=3, level_id=lesson.level_id)
            self.assertTrue(
                result.passed,
                f"{lesson.id}: la solución de ejemplo no pasa sus checks "
                f"({result.score}%): "
                + "; ".join(o.message for o in result.outcomes if not o.ok),
            )

    def test_navigation(self) -> None:
        first = self.repo.lessons_for_level("beginner")[0]
        second = self.repo.next_lesson(first.id)
        self.assertIsNotNone(second)
        self.assertEqual(second.id, "beg_02_variables")
        self.assertEqual(self.repo.previous_lesson(second.id).id, first.id)
        last = self.repo.lessons_for_level("beginner")[-1]
        self.assertIsNone(self.repo.next_lesson(last.id))

    def test_search_delegates_to_library(self) -> None:
        results = self.repo.search_resources("python")
        self.assertTrue(results)
        ids = {item.id for item in results}
        self.assertTrue(ids.issubset({resource.id for resource in self.repo.resources}))
        self.assertIn("res_python_tutorial", ids)
        self.assertNotIn("res_opensource_guide", ids)

    def test_missing_resource_ids_is_a_set(self) -> None:
        self.assertIsInstance(self.repo.missing_resource_ids(), set)

    def test_library_resolves_every_referenced_resource(self) -> None:
        self.assertEqual(self.repo.missing_resource_ids(), set())
        self.assertEqual(len(self.repo.resources), 15)
        self.assertEqual(len({resource.id for resource in self.repo.resources}), 15)

    def test_resources_for_lesson_keep_declared_order(self) -> None:
        lesson = self.repo.get_lesson("beg_01_orden")
        assert lesson is not None
        resources = self.repo.resources_for_lesson(lesson)
        self.assertEqual([item.id for item in resources], list(lesson.resource_ids))
        self.assertTrue(all(item.url.startswith("https://") for item in resources))

    def test_every_resource_has_metadata_for_filters(self) -> None:
        for resource in self.repo.resources:
            self.assertIn(resource.level, {"principiante", "intermedio", "avanzado", "todos"})
            self.assertTrue(resource.source)
            self.assertTrue(resource.description)
            self.assertGreater(len(resource.description), 30)

    def test_invalid_json_raises_content_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp)
            (content / "levels.json").write_text("{ esto no es json", encoding="utf-8")
            with self.assertRaises(ContentError):
                ContentRepository(content_dir=content, library_path=content / "none.json")

    def test_duplicate_lesson_id_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp)
            levels = {
                "schema_version": 1,
                "levels": [
                    {
                        "id": "beginner",
                        "name": "Principiante",
                        "order": 1,
                        "tagline": "x",
                        "description": "x",
                        "outcomes": ["x"],
                        "lesson_ids": ["same", "same"],
                    }
                ],
            }
            lesson = {
                "id": "same",
                "level_id": "beginner",
                "order": 1,
                "title": "T",
                "concept": "C",
                "minutes": 5,
                "problem": {"scenario": "s", "question": "q"},
                "guide": {"mental_model": "m", "steps": [{"title": "t", "body": "b"}]},
                "exercise": {
                    "type": "code",
                    "prompt": "p",
                    "checks": [{"type": "contains", "value": "x", "message": "m"}],
                    "solution": "x",
                },
                "success_criteria": ["c"],
                "resource_ids": [],
            }
            (content / "levels.json").write_text(json.dumps(levels), encoding="utf-8")
            (content / "lessons_beginner.json").write_text(
                json.dumps({"level_id": "beginner", "lessons": [lesson, lesson]}),
                encoding="utf-8",
            )
            with self.assertRaises(ContentError):
                ContentRepository(content_dir=content, library_path=content / "none.json")


if __name__ == "__main__":
    unittest.main()
