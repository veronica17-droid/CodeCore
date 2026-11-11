from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401

from core.content import ContentRepository
from core.feedback import evaluate, should_reveal_solution
from core.models import Check, Exercise


def code_exercise(*checks: Check, hints: tuple[str, ...] = ()) -> Exercise:
    return Exercise(
        type="code",
        prompt="Escribe el programa.",
        checks=checks,
        hints=hints,
        solution="print('ok')",
    )


class CodeEvaluationTest(unittest.TestCase):
    def test_correct_code_passes(self) -> None:
        exercise = code_exercise(
            Check(type="contains", value="print(", message="Falta print."),
            Check(type="ast", value="for", message="Falta un bucle."),
        )
        result = evaluate(exercise, "for i in range(3):\n    print(i)")
        self.assertTrue(result.passed)
        self.assertEqual(result.score, 100)
        self.assertTrue(all(outcome.ok for outcome in result.outcomes))

    def test_failed_check_keeps_explanation(self) -> None:
        exercise = code_exercise(
            Check(type="contains", value="print(", message="Falta print."),
            Check(type="ast", value="for", message="Falta un bucle."),
        )
        result = evaluate(exercise, "print('hola')")
        self.assertFalse(result.passed)
        self.assertEqual(result.score, 50)
        failed = [outcome for outcome in result.outcomes if not outcome.ok]
        self.assertEqual(len(failed), 1)
        self.assertIn("bucle", failed[0].message)

    def test_syntax_error_has_line_and_column(self) -> None:
        result = evaluate(code_exercise(Check(type="contains", value="x", message="m")), "for i in range(3)")
        self.assertEqual(result.score, 0)
        self.assertFalse(result.passed)
        self.assertIsNotNone(result.syntax_error)
        self.assertIn("línea", result.syntax_error or "")

    def test_empty_answer_is_rejected(self) -> None:
        result = evaluate(code_exercise(Check(type="contains", value="x", message="m")), "   ")
        self.assertFalse(result.passed)
        self.assertIn("vacío", result.summary)

    def test_count_bounds(self) -> None:
        exercise = code_exercise(
            Check(type="count", value="print(", min=2, max=2, message="Dos prints.")
        )
        self.assertTrue(evaluate(exercise, "print(1)\nprint(2)").passed)
        self.assertFalse(evaluate(exercise, "print(1)").passed)
        self.assertFalse(evaluate(exercise, "print(1)\nprint(2)\nprint(3)").passed)

    def test_not_contains(self) -> None:
        exercise = code_exercise(Check(type="not_contains", value="sum(", message="Sin sum."))
        self.assertTrue(evaluate(exercise, "total = 0").passed)
        self.assertFalse(evaluate(exercise, "total = sum(x)").passed)

    def test_regex_is_case_insensitive_with_flag(self) -> None:
        exercise = code_exercise(
            Check(type="regex", value="hola", flags="i", message="Saludo.")
        )
        self.assertTrue(evaluate(exercise, "print('HOLA')").passed)

    def test_ast_max_zero_rejects_loop(self) -> None:
        exercise = code_exercise(
            Check(type="ast", value="while", max=0, message="Sin while."),
            Check(type="ast", value="function", message="Función."),
        )
        self.assertTrue(evaluate(exercise, "def f():\n    return 1").passed)
        self.assertFalse(evaluate(exercise, "def f():\n    while True:\n        return 1").passed)

    def test_partial_score_can_pass(self) -> None:
        exercise = code_exercise(
            Check(type="contains", value="a", message="a"),
            Check(type="contains", value="b", message="b"),
            Check(type="contains", value="c", message="c"),
            Check(type="contains", value="d", message="d"),
        )
        result = evaluate(exercise, "a = 1\nb = 2\nc = 3")
        self.assertEqual(result.score, 75)
        self.assertTrue(result.passed)


class ChoiceAndShortTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = ContentRepository()

    def test_choice_correct_option(self) -> None:
        lesson = self.repo.get_lesson("adv_02_complejidad")
        assert lesson is not None
        result = evaluate(lesson.exercise, "a")
        self.assertTrue(result.passed)
        self.assertEqual(result.score, 100)

    def test_choice_wrong_option_explains(self) -> None:
        lesson = self.repo.get_lesson("adv_02_complejidad")
        assert lesson is not None
        result = evaluate(lesson.exercise, "b")
        self.assertFalse(result.passed)
        self.assertIn("trampa", result.outcomes[0].message.lower())

    def test_choice_without_selection(self) -> None:
        lesson = self.repo.get_lesson("adv_02_complejidad")
        assert lesson is not None
        result = evaluate(lesson.exercise, "")
        self.assertFalse(result.passed)
        self.assertIn("Selecciona", result.summary)

    def test_short_answer_with_ideas_passes(self) -> None:
        lesson = self.repo.get_lesson("adv_04_diseno")
        assert lesson is not None
        answer = (
            "Modificar la lista original crea un efecto lateral y una sorpresa: otra parte "
            "del programa comparte los datos y el resultado deja de ser predecible. Depurar "
            "se vuelve más difícil porque el cambio aparece a distancia. Propongo devolver "
            "una copia nueva para que la prueba sea clara y no haya estado oculto."
        )
        result = evaluate(lesson.exercise, answer, level_id="advanced")
        self.assertTrue(result.passed, result.outcomes)

    def test_short_answer_too_brief_fails(self) -> None:
        lesson = self.repo.get_lesson("adv_04_diseno")
        assert lesson is not None
        result = evaluate(lesson.exercise, "No lo sé.")
        self.assertFalse(result.passed)
        self.assertLess(result.score, 70)


class HintTest(unittest.TestCase):
    def setUp(self) -> None:
        self.exercise = code_exercise(
            Check(type="contains", value="x", message="m"),
            hints=("pista 1", "pista 2", "pista 3"),
        )

    def test_beginner_gets_first_hint_immediately(self) -> None:
        result = evaluate(self.exercise, "x", attempt=1, level_id="beginner")
        self.assertEqual(result.next_hint, "pista 1")

    def test_advanced_waits_for_second_attempt(self) -> None:
        first = evaluate(self.exercise, "x", attempt=1, level_id="advanced")
        second = evaluate(self.exercise, "x", attempt=2, level_id="advanced")
        self.assertIsNone(first.next_hint)
        self.assertEqual(second.next_hint, "pista 1")

    def test_hints_do_not_overflow(self) -> None:
        result = evaluate(self.exercise, "x", attempt=99, level_id="beginner")
        self.assertEqual(result.next_hint, "pista 3")

    def test_solution_revealed_after_three_attempts(self) -> None:
        self.assertFalse(should_reveal_solution(2))
        self.assertTrue(should_reveal_solution(3))


if __name__ == "__main__":
    unittest.main()
