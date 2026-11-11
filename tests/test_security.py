"""Pruebas de seguridad: el código del usuario nunca se ejecuta."""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from core.feedback import evaluate
from core.models import Check, Exercise

SRC = Path(__file__).resolve().parents[1] / "src"
FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__"}


class SecurityTest(unittest.TestCase):
    def test_feedback_has_no_execution_primitives(self) -> None:
        tree = ast.parse((SRC / "core" / "feedback.py").read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(
                    node.func.id,
                    FORBIDDEN_CALLS,
                    f"feedback.py no debe llamar a «{node.func.id}»: el código del usuario no se ejecuta.",
                )
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                self.assertFalse(
                    node.value.id == "os" and node.attr == "system",
                    "feedback.py no debe llamar a os.system.",
                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name, "subprocess")
            if isinstance(node, ast.ImportFrom):
                self.assertNotEqual(node.module, "subprocess")

    def test_malicious_code_is_analyzed_but_not_run(self) -> None:
        marker = Path(tempfile.gettempdir()) / "codecore-should-not-exist.txt"
        if marker.exists():
            marker.unlink()

        exercise = Exercise(
            type="code",
            prompt="Escribe una función.",
            checks=(Check(type="contains", value="def ", message="Falta def."),),
            solution="def f():\n    return 1",
        )
        answer = (
            f"__import__('pathlib').Path(r'{marker}').write_text('boom')\n"
            "valor = 1\n"
        )
        result = evaluate(exercise, answer)
        self.assertFalse(marker.exists(), "El código del usuario se ha ejecutado.")
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
