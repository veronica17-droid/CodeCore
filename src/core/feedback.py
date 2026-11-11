"""Evaluación de ejercicios sin ejecutar el código del usuario.

- Código: se valida la sintaxis con ``ast.parse`` y se aplican comprobaciones
  declarativas (presencia de texto, expresiones regulares y nodos del AST).
- Elección: se compara el id elegido con la única opción correcta.
- Respuesta corta: se mide longitud y cobertura de ideas clave.

Nunca se usa ``eval``, ``exec`` ni ``subprocess``: evaluar el ejercicio es seguro
aunque el texto venga de un archivo o de otra persona.
"""

from __future__ import annotations

import ast
import re
import unicodedata
from dataclasses import dataclass

from config import PASS_SCORE, SOLUTION_AFTER_ATTEMPTS
from core.models import Exercise

_AST_NODES: dict[str, tuple[type[ast.AST], ...]] = {
    "assign": (ast.Assign, ast.AugAssign, ast.AnnAssign),
    "for": (ast.For, ast.AsyncFor),
    "while": (ast.While,),
    "if": (ast.If,),
    "function": (ast.FunctionDef, ast.AsyncFunctionDef),
    "return": (ast.Return,),
    "try": (ast.Try,),
    "dict": (ast.Dict,),
    "list": (ast.List,),
    "call": (ast.Call,),
}


@dataclass(frozen=True)
class CheckOutcome:
    ok: bool
    message: str
    check_type: str


@dataclass(frozen=True)
class Evaluation:
    score: int
    passed: bool
    outcomes: tuple[CheckOutcome, ...]
    summary: str
    syntax_error: str | None = None
    next_hint: str | None = None


def normalize_text(value: str) -> str:
    """Minúsculas, sin acentos y con espacios colapsados."""
    decomposed = unicodedata.normalize("NFKD", value)
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", plain.lower()).strip()


def _hint_for(exercise: Exercise, attempt: int, level_id: str) -> str | None:
    if not exercise.hints:
        return None
    if level_id == "advanced":
        if attempt < 2:
            return None
        index = min(attempt - 2, len(exercise.hints) - 1)
    else:
        index = min(max(attempt - 1, 0), len(exercise.hints) - 1)
    return exercise.hints[index]


def _syntax_error(exc: SyntaxError) -> str:
    line = exc.lineno or 0
    column = exc.offset or 0
    return f"Error de sintaxis en la línea {line}, columna {column}: {exc.msg}."


def _ast_count(tree: ast.AST, value: str) -> int:
    node_types = _AST_NODES.get(value)
    if node_types is None:
        raise KeyError(value)
    return sum(1 for node in ast.walk(tree) if isinstance(node, node_types))


def _evaluate_check(check, answer: str, tree: ast.AST) -> CheckOutcome:
    if check.type == "contains":
        ok = check.value in answer
    elif check.type == "not_contains":
        ok = check.value not in answer
    elif check.type == "count":
        amount = answer.count(check.value)
        low = check.min if check.min is not None else 0
        high = check.max
        ok = amount >= low and (high is None or amount <= high)
    elif check.type == "regex":
        flags = re.IGNORECASE if "i" in check.flags else 0
        try:
            ok = re.search(check.value, answer, flags) is not None
        except re.error as exc:
            return CheckOutcome(
                ok=False,
                message=f"Comprobación mal configurada: {exc}.",
                check_type=check.type,
            )
    elif check.type == "ast":
        try:
            amount = _ast_count(tree, check.value)
        except KeyError:
            return CheckOutcome(
                ok=False,
                message=f"Comprobación AST desconocida: «{check.value}».",
                check_type=check.type,
            )
        low = check.min if check.min is not None else (0 if check.max == 0 else 1)
        high = check.max
        ok = amount >= low and (high is None or amount <= high)
    else:  # pragma: no cover - el cargador ya valida los tipos
        return CheckOutcome(
            ok=False,
            message=f"Tipo de comprobación desconocido: «{check.type}».",
            check_type=check.type,
        )
    return CheckOutcome(ok=ok, message=check.message, check_type=check.type)


def _evaluate_code(exercise: Exercise, answer: str, attempt: int, level_id: str) -> Evaluation:
    hint = _hint_for(exercise, attempt, level_id)
    if not answer.strip():
        return Evaluation(
            score=0,
            passed=False,
            outcomes=(),
            summary="El editor está vacío. Escribe tu propuesta y vuelve a comprobar.",
            syntax_error="No hay código que analizar.",
            next_hint=hint,
        )
    try:
        tree = ast.parse(answer)
    except SyntaxError as exc:
        return Evaluation(
            score=0,
            passed=False,
            outcomes=(),
            summary="Primero corrige la sintaxis: el programa todavía no se puede leer.",
            syntax_error=_syntax_error(exc),
            next_hint=hint,
        )

    outcomes = tuple(_evaluate_check(check, answer, tree) for check in exercise.checks)
    passed_count = sum(1 for outcome in outcomes if outcome.ok)
    total = len(outcomes)
    score = round(passed_count / total * 100) if total else 0
    passed = score >= PASS_SCORE

    if passed:
        if passed_count == total:
            summary = f"Aprobado: {passed_count} de {total} comprobaciones. El razonamiento se sostiene."
        else:
            summary = (
                f"Aprobado: {passed_count} de {total} comprobaciones. "
                "Revisa las que fallan para afinar el resultado."
            )
    else:
        summary = (
            f"Todavía no: {passed_count} de {total} comprobaciones. "
            "Lee cada mensaje y corrige el razonamiento, no solo el texto."
        )
    return Evaluation(
        score=score,
        passed=passed,
        outcomes=outcomes,
        summary=summary,
        next_hint=hint,
    )


def _evaluate_choice(exercise: Exercise, answer: str) -> Evaluation:
    selected = next((option for option in exercise.options if option.id == answer), None)
    if selected is None:
        return Evaluation(
            score=0,
            passed=False,
            outcomes=(),
            summary="Selecciona una opción antes de comprobar.",
        )
    outcome = CheckOutcome(
        ok=selected.correct,
        message=selected.feedback,
        check_type="choice",
    )
    if selected.correct:
        return Evaluation(
            score=100,
            passed=True,
            outcomes=(outcome,),
            summary="Correcto. Ahora intenta explicar por qué las otras opciones no encajan.",
        )
    return Evaluation(
        score=0,
        passed=False,
        outcomes=(outcome,),
        summary="Esa opción no describe el coste real. Vuelve a contar las operaciones.",
    )


def _evaluate_short(exercise: Exercise, answer: str, attempt: int, level_id: str) -> Evaluation:
    hint = _hint_for(exercise, attempt, level_id)
    normalized = normalize_text(answer)
    word_count = len(re.findall(r"\w+", normalized))
    missing = [keyword for keyword in exercise.keywords if normalize_text(keyword) not in normalized]
    matched = len(exercise.keywords) - len(missing)

    words_ok = word_count >= exercise.min_words
    keywords_ok = matched >= exercise.min_keywords
    passed = words_ok and keywords_ok
    if passed:
        score = 100
    else:
        word_ratio = min(1.0, word_count / max(exercise.min_words, 1))
        keyword_ratio = min(1.0, matched / max(exercise.min_keywords, 1))
        score = min(65, round(50 * word_ratio + 50 * keyword_ratio))

    outcomes = [
        CheckOutcome(
            ok=words_ok,
            message=(
                f"Extensión: {word_count} palabras (mínimo {exercise.min_words})."
                if words_ok
                else f"Faltan palabras: has escrito {word_count} y necesitas al menos {exercise.min_words}."
            ),
            check_type="length",
        ),
        CheckOutcome(
            ok=keywords_ok,
            message=(
                f"Ideas cubiertas: {matched} de {len(exercise.keywords)}."
                if keywords_ok
                else "Faltan ideas clave: " + ", ".join(missing[:5]) + "."
            ),
            check_type="keywords",
        ),
    ]

    if passed:
        summary = "Respuesta completa: cubre las ideas y se apoya en el problema."
    else:
        summary = "Todavía no. Amplía la explicación y conecta las ideas que faltan."
    return Evaluation(
        score=score,
        passed=passed,
        outcomes=tuple(outcomes),
        summary=summary,
        next_hint=hint,
    )


def evaluate(
    exercise: Exercise,
    answer: str,
    attempt: int = 1,
    level_id: str = "beginner",
) -> Evaluation:
    """Evalúa una respuesta y devuelve puntaje, mensajes y siguiente pista."""
    if exercise.type == "code":
        return _evaluate_code(exercise, answer, attempt, level_id)
    if exercise.type == "choice":
        return _evaluate_choice(exercise, answer)
    if exercise.type == "short":
        return _evaluate_short(exercise, answer, attempt, level_id)
    return Evaluation(
        score=0,
        passed=False,
        outcomes=(),
        summary=f"Tipo de ejercicio no soportado: «{exercise.type}».",
    )


def should_reveal_solution(attempt: int) -> bool:
    """La solución se ofrece tras varios intentos, nunca antes."""
    return attempt >= SOLUTION_AFTER_ATTEMPTS
