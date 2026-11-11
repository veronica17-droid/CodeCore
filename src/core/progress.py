"""Persistencia del progreso en %APPDATA%/CodeCore/progress.json.

Escritura atómica y recuperación ante archivos corruptos. Sin datos personales.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from config import MAX_ANSWER_LENGTH, SCHEMA_VERSION
from core.models import Level, Lesson, LessonProgress, Progress, now_iso
from core.paths import progress_file


class ProgressStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else progress_file()

    # -- lectura ----------------------------------------------------------

    def load(self) -> Progress:
        if not self.path.exists():
            return Progress()

        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, ValueError, TypeError):
            self._backup_corrupt()
            return Progress()

        if not isinstance(data, dict):
            self._backup_corrupt()
            return Progress()

        version = data.get("schema_version", SCHEMA_VERSION)
        if not isinstance(version, int) or version > SCHEMA_VERSION:
            self._backup_corrupt()
            return Progress()

        try:
            return Progress.from_dict(data)
        except (ValueError, TypeError, KeyError):
            self._backup_corrupt()
            return Progress()

    def _backup_corrupt(self) -> None:
        if not self.path.exists():
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = self.path.with_name(f"progress.corrupt-{stamp}.json")
        try:
            self.path.replace(target)
        except OSError:
            # Si no se puede mover, se intenta al menos no sobrescribir en silencio.
            pass

    # -- escritura --------------------------------------------------------

    def save(self, progress: Progress) -> None:
        progress.updated_at = now_iso()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        payload = json.dumps(progress.to_dict(), ensure_ascii=False, indent=2)
        temporary.write_text(payload + "\n", encoding="utf-8")
        os.replace(temporary, self.path)

    # -- mutaciones -------------------------------------------------------

    def set_level(self, progress: Progress, level_id: str) -> None:
        progress.level = level_id
        progress.updated_at = now_iso()

    def mark_started(self, progress: Progress, lesson_id: str) -> LessonProgress:
        item = progress.lesson(lesson_id)
        if item.status == "not_started":
            item.status = "in_progress"
        progress.last_lesson_id = lesson_id
        progress.updated_at = now_iso()
        return item

    def record_attempt(
        self,
        progress: Progress,
        lesson_id: str,
        score: int,
        passed: bool,
        answer: str,
        next_lesson_id: str | None = None,
    ) -> LessonProgress:
        item = progress.lesson(lesson_id)
        item.attempts += 1
        item.best_score = max(item.best_score, max(0, min(100, int(score))))
        item.last_answer = answer[:MAX_ANSWER_LENGTH]
        if passed:
            item.status = "completed"
            item.completed_at = item.completed_at or now_iso()
        elif item.status != "completed":
            item.status = "in_progress"

        if passed and next_lesson_id:
            progress.last_lesson_id = next_lesson_id
        else:
            progress.last_lesson_id = lesson_id
        progress.updated_at = now_iso()
        return item

    def reset_all(self, progress: Progress) -> None:
        progress.lessons.clear()
        progress.last_lesson_id = None
        progress.level = None
        progress.updated_at = now_iso()

    def reset_level(self, progress: Progress, lessons: list[Lesson] | tuple[Lesson, ...]) -> None:
        for lesson in lessons:
            progress.lessons.pop(lesson.id, None)
        if progress.last_lesson_id and progress.last_lesson_id in {l.id for l in lessons}:
            progress.last_lesson_id = None
        progress.updated_at = now_iso()

    # -- resumen ----------------------------------------------------------

    def summary(
        self,
        progress: Progress,
        levels: tuple[Level, ...],
    ) -> dict[str, Any]:
        level_rows: list[dict[str, Any]] = []
        total_completed = 0
        total_lessons = 0
        for level in levels:
            completed = sum(1 for lesson_id in level.lesson_ids if progress.is_completed(lesson_id))
            total = len(level.lesson_ids)
            percent = round(completed / total * 100) if total else 0
            level_rows.append(
                {
                    "id": level.id,
                    "name": level.name,
                    "completed": completed,
                    "total": total,
                    "percent": percent,
                }
            )
            total_completed += completed
            total_lessons += total
        overall_percent = round(total_completed / total_lessons * 100) if total_lessons else 0
        return {
            "overall": {
                "completed": total_completed,
                "total": total_lessons,
                "percent": overall_percent,
            },
            "levels": level_rows,
        }

    @staticmethod
    def level_completed(progress: Progress, level: Level) -> bool:
        return bool(level.lesson_ids) and all(
            progress.is_completed(lesson_id) for lesson_id in level.lesson_ids
        )

    @staticmethod
    def next_pending(progress: Progress, lessons: tuple[Lesson, ...]) -> Lesson | None:
        for lesson in lessons:
            if not progress.is_completed(lesson.id):
                return lesson
        return None
