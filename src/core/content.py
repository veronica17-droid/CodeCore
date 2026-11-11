"""Carga y validación del contenido local (niveles, lecciones y biblioteca)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from config import SCHEMA_VERSION
from core.models import (
    Check,
    Exercise,
    Guide,
    Lesson,
    Level,
    Option,
    Problem,
    Resource,
    Step,
)
from core.paths import resource_path

CHECK_TYPES = {"contains", "not_contains", "count", "regex", "ast"}
EXERCISE_TYPES = {"code", "choice", "short"}
RESOURCE_TYPES = {"doc", "libro", "video", "curso", "herramienta", "referencia"}
RESOURCE_LEVELS = {"principiante", "intermedio", "avanzado", "todos"}


class ContentError(Exception):
    """El contenido local no cumple el esquema esperado."""


# --------------------------------------------------------------------------
# Utilidades de validación
# --------------------------------------------------------------------------


def _require(data: dict[str, Any], key: str, ctx: str) -> Any:
    if key not in data:
        raise ContentError(f"{ctx}: falta el campo obligatorio «{key}».")
    return data[key]


def _as_text(value: Any, ctx: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContentError(f"{ctx}: se esperaba un texto no vacío.")
    return value.strip()


def _as_int(value: Any, ctx: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ContentError(f"{ctx}: se esperaba un entero >= {minimum}.")
    return value


def _as_bool(value: Any, ctx: str) -> bool:
    if not isinstance(value, bool):
        raise ContentError(f"{ctx}: se esperaba true o false.")
    return value


def _as_list(value: Any, ctx: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContentError(f"{ctx}: se esperaba una lista.")
    return value


def _text_list(value: Any, ctx: str) -> tuple[str, ...]:
    return tuple(_as_text(item, f"{ctx}[{i}]") for i, item in enumerate(_as_list(value, ctx)))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContentError(f"No se pudo leer {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContentError(f"JSON inválido en {path.name}, línea {exc.lineno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ContentError(f"{path.name}: la raíz debe ser un objeto JSON.")
    return data


# --------------------------------------------------------------------------
# Parseo de entidades
# --------------------------------------------------------------------------


def _parse_check(data: Any, ctx: str) -> Check:
    if not isinstance(data, dict):
        raise ContentError(f"{ctx}: cada comprobación debe ser un objeto.")
    check_type = _as_text(_require(data, "type", ctx), f"{ctx}.type")
    if check_type not in CHECK_TYPES:
        raise ContentError(f"{ctx}: tipo de comprobación desconocido «{check_type}».")
    value = str(data.get("value", ""))
    if check_type != "ast" and not value:
        raise ContentError(f"{ctx}: la comprobación «{check_type}» necesita «value».")
    message = _as_text(_require(data, "message", ctx), f"{ctx}.message")
    minimum = data.get("min")
    maximum = data.get("max")
    if minimum is not None:
        minimum = _as_int(minimum, f"{ctx}.min", 0)
    if maximum is not None:
        maximum = _as_int(maximum, f"{ctx}.max", 0)
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ContentError(f"{ctx}: min no puede ser mayor que max.")
    flags = str(data.get("flags", ""))
    return Check(
        type=check_type,
        value=value,
        message=message,
        min=minimum,
        max=maximum,
        flags=flags,
    )


def _parse_option(data: Any, ctx: str) -> Option:
    if not isinstance(data, dict):
        raise ContentError(f"{ctx}: cada opción debe ser un objeto.")
    return Option(
        id=_as_text(_require(data, "id", ctx), f"{ctx}.id"),
        text=_as_text(_require(data, "text", ctx), f"{ctx}.text"),
        correct=_as_bool(data.get("correct", False), f"{ctx}.correct"),
        feedback=_as_text(_require(data, "feedback", ctx), f"{ctx}.feedback"),
    )


def _parse_exercise(data: Any, ctx: str) -> Exercise:
    if not isinstance(data, dict):
        raise ContentError(f"{ctx}: el ejercicio debe ser un objeto.")
    exercise_type = _as_text(_require(data, "type", ctx), f"{ctx}.type")
    if exercise_type not in EXERCISE_TYPES:
        raise ContentError(f"{ctx}: tipo de ejercicio desconocido «{exercise_type}».")

    checks = tuple(
        _parse_check(item, f"{ctx}.checks[{i}]")
        for i, item in enumerate(_as_list(data.get("checks", []), f"{ctx}.checks"))
    )
    options = tuple(
        _parse_option(item, f"{ctx}.options[{i}]")
        for i, item in enumerate(_as_list(data.get("options", []), f"{ctx}.options"))
    )
    keywords = _text_list(data.get("keywords", []), f"{ctx}.keywords")
    min_words = _as_int(data.get("min_words", 0), f"{ctx}.min_words", 0)
    min_keywords = _as_int(data.get("min_keywords", 0), f"{ctx}.min_keywords", 0)

    if exercise_type == "code" and not checks:
        raise ContentError(f"{ctx}: un ejercicio de código necesita al menos una comprobación.")
    if exercise_type == "choice":
        if len(options) < 2:
            raise ContentError(f"{ctx}: un ejercicio de elección necesita al menos dos opciones.")
        if sum(1 for option in options if option.correct) != 1:
            raise ContentError(f"{ctx}: debe haber exactamente una opción correcta.")
        if len({option.id for option in options}) != len(options):
            raise ContentError(f"{ctx}: los ids de las opciones deben ser únicos.")
    if exercise_type == "short":
        if not keywords:
            raise ContentError(f"{ctx}: una respuesta corta necesita palabras clave.")
        if min_words <= 0 or min_keywords <= 0:
            raise ContentError(f"{ctx}: define min_words y min_keywords mayores que cero.")
        if min_keywords > len(keywords):
            raise ContentError(f"{ctx}: min_keywords no puede superar el número de palabras clave.")

    return Exercise(
        type=exercise_type,
        prompt=_as_text(_require(data, "prompt", ctx), f"{ctx}.prompt"),
        language=str(data.get("language", "python")),
        starter_code=str(data.get("starter_code", "")),
        checks=checks,
        options=options,
        keywords=keywords,
        min_words=min_words,
        min_keywords=min_keywords,
        hints=_text_list(data.get("hints", []), f"{ctx}.hints"),
        solution=str(data.get("solution", "")),
    )


def _parse_problem(data: Any, ctx: str) -> Problem:
    if not isinstance(data, dict):
        raise ContentError(f"{ctx}: el problema debe ser un objeto.")
    return Problem(
        scenario=_as_text(_require(data, "scenario", ctx), f"{ctx}.scenario"),
        question=_as_text(_require(data, "question", ctx), f"{ctx}.question"),
        constraints=_text_list(data.get("constraints", []), f"{ctx}.constraints"),
        reflection=str(data.get("reflection", "")),
    )


def _parse_guide(data: Any, ctx: str) -> Guide:
    if not isinstance(data, dict):
        raise ContentError(f"{ctx}: la guía debe ser un objeto.")
    steps = []
    for i, item in enumerate(_as_list(data.get("steps", []), f"{ctx}.steps")):
        if not isinstance(item, dict):
            raise ContentError(f"{ctx}.steps[{i}]: se esperaba un objeto.")
        steps.append(
            Step(
                title=_as_text(_require(item, "title", f"{ctx}.steps[{i}]"), f"{ctx}.steps[{i}].title"),
                body=_as_text(_require(item, "body", f"{ctx}.steps[{i}]"), f"{ctx}.steps[{i}].body"),
            )
        )
    return Guide(
        mental_model=_as_text(_require(data, "mental_model", ctx), f"{ctx}.mental_model"),
        steps=tuple(steps),
        questions=_text_list(data.get("questions", []), f"{ctx}.questions"),
        common_mistakes=_text_list(data.get("common_mistakes", []), f"{ctx}.common_mistakes"),
    )


def _parse_lesson(data: Any, ctx: str, expected_level: str) -> Lesson:
    if not isinstance(data, dict):
        raise ContentError(f"{ctx}: la lección debe ser un objeto.")
    lesson_id = _as_text(_require(data, "id", ctx), f"{ctx}.id")
    level_id = _as_text(_require(data, "level_id", ctx), f"{ctx}.level_id")
    if level_id != expected_level:
        raise ContentError(
            f"{ctx}: la lección {lesson_id} declara level_id «{level_id}» "
            f"pero está en el archivo del nivel «{expected_level}»."
        )
    return Lesson(
        id=lesson_id,
        level_id=level_id,
        order=_as_int(_require(data, "order", ctx), f"{ctx}.order", 1),
        title=_as_text(_require(data, "title", ctx), f"{ctx}.title"),
        concept=_as_text(_require(data, "concept", ctx), f"{ctx}.concept"),
        minutes=_as_int(data.get("minutes", 15), f"{ctx}.minutes", 1),
        problem=_parse_problem(_require(data, "problem", ctx), f"{ctx}.problem"),
        guide=_parse_guide(_require(data, "guide", ctx), f"{ctx}.guide"),
        exercise=_parse_exercise(_require(data, "exercise", ctx), f"{ctx}.exercise"),
        success_criteria=_text_list(
            _require(data, "success_criteria", ctx), f"{ctx}.success_criteria"
        ),
        resource_ids=_text_list(data.get("resource_ids", []), f"{ctx}.resource_ids"),
    )


def _parse_level(data: Any, ctx: str) -> Level:
    if not isinstance(data, dict):
        raise ContentError(f"{ctx}: el nivel debe ser un objeto.")
    return Level(
        id=_as_text(_require(data, "id", ctx), f"{ctx}.id"),
        name=_as_text(_require(data, "name", ctx), f"{ctx}.name"),
        order=_as_int(_require(data, "order", ctx), f"{ctx}.order", 1),
        tagline=_as_text(_require(data, "tagline", ctx), f"{ctx}.tagline"),
        description=_as_text(_require(data, "description", ctx), f"{ctx}.description"),
        outcomes=_text_list(_require(data, "outcomes", ctx), f"{ctx}.outcomes"),
        estimated_minutes=_as_int(data.get("estimated_minutes", 0), f"{ctx}.estimated_minutes", 0),
        lesson_ids=_text_list(_require(data, "lesson_ids", ctx), f"{ctx}.lesson_ids"),
    )


def _parse_resource(data: Any, ctx: str) -> Resource:
    if not isinstance(data, dict):
        raise ContentError(f"{ctx}: el recurso debe ser un objeto.")
    resource_type = _as_text(_require(data, "type", ctx), f"{ctx}.type")
    if resource_type not in RESOURCE_TYPES:
        raise ContentError(f"{ctx}: tipo de recurso desconocido «{resource_type}».")
    level = _as_text(_require(data, "level", ctx), f"{ctx}.level")
    if level not in RESOURCE_LEVELS:
        raise ContentError(f"{ctx}: nivel de recurso desconocido «{level}».")
    url = _as_text(_require(data, "url", ctx), f"{ctx}.url")
    if not url.startswith(("https://", "http://")):
        raise ContentError(f"{ctx}: la URL debe empezar por http:// o https://.")
    return Resource(
        id=_as_text(_require(data, "id", ctx), f"{ctx}.id"),
        title=_as_text(_require(data, "title", ctx), f"{ctx}.title"),
        type=resource_type,
        url=url,
        level=level,
        language=_as_text(_require(data, "language", ctx), f"{ctx}.language"),
        source=_as_text(_require(data, "source", ctx), f"{ctx}.source"),
        description=_as_text(_require(data, "description", ctx), f"{ctx}.description"),
        free=_as_bool(data.get("free", True), f"{ctx}.free"),
    )


# --------------------------------------------------------------------------
# Repositorio
# --------------------------------------------------------------------------


class ContentRepository:
    """Acceso de solo lectura al contenido empaquetado con la aplicación."""

    def __init__(self, content_dir: Path | None = None, library_path: Path | None = None) -> None:
        self.content_dir = Path(content_dir) if content_dir else resource_path("content")
        self.library_path = (
            Path(library_path) if library_path else resource_path("library", "resources.json")
        )
        self.levels: tuple[Level, ...] = ()
        self.lessons: dict[str, Lesson] = {}
        self.resources: tuple[Resource, ...] = ()
        self._load()

    # -- carga ------------------------------------------------------------

    def _load(self) -> None:
        levels_file = self.content_dir / "levels.json"
        data = _read_json(levels_file)
        version = data.get("schema_version", SCHEMA_VERSION)
        if version != SCHEMA_VERSION:
            raise ContentError(
                f"levels.json usa schema_version {version}; esta app espera {SCHEMA_VERSION}."
            )

        levels = [
            _parse_level(item, f"levels[{i}]")
            for i, item in enumerate(_as_list(_require(data, "levels", "levels.json"), "levels"))
        ]
        if not levels:
            raise ContentError("levels.json no contiene niveles.")
        if len({level.id for level in levels}) != len(levels):
            raise ContentError("Los ids de nivel deben ser únicos.")
        self.levels = tuple(sorted(levels, key=lambda level: level.order))

        lessons: dict[str, Lesson] = {}
        for path in sorted(self.content_dir.glob("lessons_*.json")):
            payload = _read_json(path)
            file_level = _as_text(
                _require(payload, "level_id", path.name), f"{path.name}.level_id"
            )
            for i, item in enumerate(
                _as_list(_require(payload, "lessons", path.name), f"{path.name}.lessons")
            ):
                lesson = _parse_lesson(item, f"{path.name}.lessons[{i}]", file_level)
                if lesson.id in lessons:
                    raise ContentError(f"Id de lección duplicado: {lesson.id}")
                lessons[lesson.id] = lesson
        self.lessons = lessons

        self._validate_level_links()
        self._load_library()

    def _validate_level_links(self) -> None:
        for level in self.levels:
            if len(set(level.lesson_ids)) != len(level.lesson_ids):
                raise ContentError(f"El nivel {level.id} repite lecciones en lesson_ids.")
            for lesson_id in level.lesson_ids:
                lesson = self.lessons.get(lesson_id)
                if lesson is None:
                    raise ContentError(
                        f"El nivel {level.id} referencia la lección inexistente «{lesson_id}»."
                    )
                if lesson.level_id != level.id:
                    raise ContentError(
                        f"La lección {lesson_id} pertenece a {lesson.level_id}, "
                        f"pero {level.id} la incluye en su ruta."
                    )

    def _load_library(self) -> None:
        if not self.library_path.exists():
            self.resources = ()
            return
        data = _read_json(self.library_path)
        resources = [
            _parse_resource(item, f"resources[{i}]")
            for i, item in enumerate(
                _as_list(_require(data, "resources", self.library_path.name), "resources")
            )
        ]
        if len({resource.id for resource in resources}) != len(resources):
            raise ContentError("Los ids de recurso deben ser únicos.")
        self.resources = tuple(resources)

    # -- consultas --------------------------------------------------------

    def get_level(self, level_id: str) -> Level | None:
        return next((level for level in self.levels if level.id == level_id), None)

    def get_lesson(self, lesson_id: str) -> Lesson | None:
        return self.lessons.get(lesson_id)

    def lessons_for_level(self, level_id: str) -> tuple[Lesson, ...]:
        level = self.get_level(level_id)
        if level is None:
            return ()
        return tuple(self.lessons[lesson_id] for lesson_id in level.lesson_ids)

    def get_resource(self, resource_id: str) -> Resource | None:
        return next((item for item in self.resources if item.id == resource_id), None)

    def resources_for_lesson(self, lesson: Lesson) -> tuple[Resource, ...]:
        found = (self.get_resource(resource_id) for resource_id in lesson.resource_ids)
        return tuple(item for item in found if item is not None)

    def next_lesson(self, lesson_id: str) -> Lesson | None:
        lesson = self.lessons.get(lesson_id)
        if lesson is None:
            return None
        path = self.lessons_for_level(lesson.level_id)
        for index, item in enumerate(path):
            if item.id == lesson_id and index + 1 < len(path):
                return path[index + 1]
        return None

    def previous_lesson(self, lesson_id: str) -> Lesson | None:
        lesson = self.lessons.get(lesson_id)
        if lesson is None:
            return None
        path = self.lessons_for_level(lesson.level_id)
        for index, item in enumerate(path):
            if item.id == lesson_id and index > 0:
                return path[index - 1]
        return None

    def missing_resource_ids(self) -> set[str]:
        referenced: set[str] = set()
        for lesson in self.lessons.values():
            referenced.update(lesson.resource_ids)
        available = {resource.id for resource in self.resources}
        return referenced - available

    def search_resources(
        self,
        query: str = "",
        resource_type: str | None = None,
        language: str | None = None,
        level: str | None = None,
    ) -> tuple[Resource, ...]:
        from core.search import filter_resources

        return tuple(
            filter_resources(
                self.resources,
                query=query,
                resource_type=resource_type,
                language=language,
                level=level,
            )
        )

    def filter_values(self, attribute: str) -> tuple[str, ...]:
        values = {
            str(getattr(resource, attribute))
            for resource in self.resources
            if getattr(resource, attribute, None)
        }
        return tuple(sorted(values))

    def all_lessons(self) -> Iterable[Lesson]:
        return (self.lessons[lesson_id] for level in self.levels for lesson_id in level.lesson_ids)
