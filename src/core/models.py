"""Modelo de dominio de CodeCore.

Dataclasses inmutables para el contenido y mutables para el progreso.
No importan tkinter: se pueden probar sin abrir una ventana.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from config import SCHEMA_VERSION


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# Contenido
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Check:
    type: str
    value: str = ""
    message: str = ""
    min: int | None = None
    max: int | None = None
    flags: str = ""


@dataclass(frozen=True)
class Option:
    id: str
    text: str
    correct: bool = False
    feedback: str = ""


@dataclass(frozen=True)
class Exercise:
    type: str
    prompt: str
    language: str = "python"
    starter_code: str = ""
    checks: tuple[Check, ...] = ()
    options: tuple[Option, ...] = ()
    keywords: tuple[str, ...] = ()
    min_words: int = 0
    min_keywords: int = 0
    hints: tuple[str, ...] = ()
    solution: str = ""


@dataclass(frozen=True)
class Step:
    title: str
    body: str


@dataclass(frozen=True)
class Problem:
    scenario: str
    question: str
    constraints: tuple[str, ...] = ()
    reflection: str = ""


@dataclass(frozen=True)
class Guide:
    mental_model: str
    steps: tuple[Step, ...] = ()
    questions: tuple[str, ...] = ()
    common_mistakes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Lesson:
    id: str
    level_id: str
    order: int
    title: str
    concept: str
    minutes: int
    problem: Problem
    guide: Guide
    exercise: Exercise
    success_criteria: tuple[str, ...]
    resource_ids: tuple[str, ...]


@dataclass(frozen=True)
class Level:
    id: str
    name: str
    order: int
    tagline: str
    description: str
    outcomes: tuple[str, ...]
    estimated_minutes: int
    lesson_ids: tuple[str, ...]


@dataclass(frozen=True)
class Resource:
    id: str
    title: str
    type: str
    url: str
    level: str
    language: str
    source: str
    description: str
    free: bool


# --------------------------------------------------------------------------
# Progreso
# --------------------------------------------------------------------------


@dataclass
class LessonProgress:
    lesson_id: str
    status: str = "not_started"
    best_score: int = 0
    attempts: int = 0
    completed_at: str | None = None
    last_answer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "best_score": self.best_score,
            "attempts": self.attempts,
            "completed_at": self.completed_at,
            "last_answer": self.last_answer,
        }

    @classmethod
    def from_dict(cls, lesson_id: str, data: dict[str, Any]) -> "LessonProgress":
        return cls(
            lesson_id=lesson_id,
            status=str(data.get("status", "not_started")),
            best_score=int(data.get("best_score", 0)),
            attempts=int(data.get("attempts", 0)),
            completed_at=data.get("completed_at"),
            last_answer=str(data.get("last_answer", "")),
        )


@dataclass
class Progress:
    schema_version: int = SCHEMA_VERSION
    level: str | None = None
    lessons: dict[str, LessonProgress] = field(default_factory=dict)
    last_lesson_id: str | None = None
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "level": self.level,
            "lessons": {k: v.to_dict() for k, v in self.lessons.items()},
            "last_lesson_id": self.last_lesson_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Progress":
        raw_lessons = data.get("lessons") or {}
        lessons = {
            str(k): LessonProgress.from_dict(str(k), v)
            for k, v in raw_lessons.items()
            if isinstance(v, dict)
        }
        return cls(
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
            level=data.get("level"),
            lessons=lessons,
            last_lesson_id=data.get("last_lesson_id"),
            created_at=str(data.get("created_at") or now_iso()),
            updated_at=str(data.get("updated_at") or now_iso()),
            settings=dict(data.get("settings") or {}),
        )

    def lesson(self, lesson_id: str) -> LessonProgress:
        if lesson_id not in self.lessons:
            self.lessons[lesson_id] = LessonProgress(lesson_id=lesson_id)
        return self.lessons[lesson_id]

    def is_completed(self, lesson_id: str) -> bool:
        item = self.lessons.get(lesson_id)
        return bool(item and item.status == "completed")
