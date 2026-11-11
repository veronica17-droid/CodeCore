"""Ruta de aprendizaje de un nivel."""

from __future__ import annotations

import tkinter as tk

from core.progress import ProgressStore
from ui import theme, widgets


class PathView(tk.Frame):
    def __init__(self, parent: tk.Misc, app, level_id: str | None = None) -> None:
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.level = (
            app.repo.get_level(level_id or app.progress.level or "") or app.repo.levels[0]
        )
        self.scroll = widgets.ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True)
        content = tk.Frame(self.scroll.inner, bg=theme.BG)
        content.pack(fill="both", expand=True, padx=6, pady=6)

        self._build_header(content)
        summary = app.summary()
        row = next((item for item in summary["levels"] if item["id"] == self.level.id), None)
        self._build_progress(content, row or {})
        self._build_lessons(content, row or {})
        self.scroll.bind_mousewheel()
        self.scroll.scroll_to_top()

    # ------------------------------------------------------------------

    def _build_header(self, parent) -> None:
        top = tk.Frame(parent, bg=theme.BG)
        top.pack(fill="x")
        widgets.mk_button(
            top, "←  Inicio", self.app.open_welcome, kind="ghost", padx=6, pady=2, size=9
        ).pack(side="left")

        tabs = tk.Frame(top, bg=theme.BG)
        tabs.pack(side="right")
        for level in self.app.repo.levels:
            active = level.id == self.level.id
            widgets.mk_button(
                tabs,
                level.name,
                lambda level_id=level.id: self.app.choose_level(level_id),
                kind="primary" if active else "secondary",
                size=9,
                padx=12,
                pady=5,
            ).pack(side="left", padx=(6, 0))

        widgets.mk_label(
            parent, "MI RUTA", size=9, bold=True, color=theme.ACCENT
        ).pack(anchor="w", pady=(16, 0))
        widgets.mk_label(parent, self.level.name, size=26, bold=True).pack(anchor="w")
        widgets.mk_label(
            parent,
            self.level.description,
            size=10,
            color=theme.MUTED,
            wrap=860,
        ).pack(anchor="w", pady=(4, 14))

    def _build_progress(self, parent, row: dict) -> None:
        card = widgets.Card(parent, padding=18)
        card.pack(fill="x")
        body = card.body

        top = tk.Frame(body, bg=theme.SURFACE)
        top.pack(fill="x")
        widgets.mk_label(
            top, f"{row.get('completed', 0)} de {row.get('total', 0)} lecciones completadas",
            size=11, bold=True,
        ).pack(side="left")
        widgets.mk_label(
            top, f"{row.get('percent', 0)}%", size=18, bold=True, color=theme.ACCENT
        ).pack(side="right")
        bar = widgets.progress_bar(body)
        bar["value"] = row.get("percent", 0)
        bar.pack(fill="x", pady=(8, 4))
        widgets.mk_label(
            body,
            "Puedes abrir cualquier lección y repetirla. El orden marcado es una recomendación, "
            "no un candado.",
            size=9,
            color=theme.MUTED,
        ).pack(anchor="w", pady=(4, 0))

    def _build_lessons(self, parent, row: dict) -> None:
        lessons = self.app.repo.lessons_for_level(self.level.id)
        next_lesson = ProgressStore.next_pending(self.app.progress, lessons)
        completed_all = bool(lessons) and row.get("completed") == row.get("total")

        if completed_all:
            self._build_completion_banner(parent)

        widgets.mk_label(
            parent, "LECCIONES", size=9, bold=True, color=theme.MUTED
        ).pack(anchor="w", pady=(18, 8))

        for lesson in lessons:
            item = self.app.progress.lessons.get(lesson.id)
            status = item.status if item else "not_started"
            best = item.best_score if item else 0
            is_next = next_lesson is not None and lesson.id == next_lesson.id
            self._build_lesson_card(parent, lesson, status, best, is_next)

    def _build_lesson_card(self, parent, lesson, status: str, best: int, is_next: bool) -> None:
        card = widgets.Card(parent, padding=16)
        if is_next:
            card.configure(highlightbackground=theme.ACCENT, highlightthickness=2)
        card.pack(fill="x", pady=(0, 8))
        body = card.body

        columns = tk.Frame(body, bg=theme.SURFACE)
        columns.pack(fill="x")
        left = tk.Frame(columns, bg=theme.SURFACE)
        left.pack(side="left", fill="both", expand=True)

        title_row = tk.Frame(left, bg=theme.SURFACE)
        title_row.pack(anchor="w", fill="x")

        number_bg, number_fg = widgets.level_color(lesson.level_id)
        number = tk.Label(
            title_row,
            text=str(lesson.order),
            font=theme.font(11, True),
            bg=number_bg,
            fg=number_fg,
            width=3,
            pady=3,
        )
        number.pack(side="left")
        widgets.mk_label(
            title_row, lesson.title, size=13, bold=True
        ).pack(side="left", padx=(10, 8))

        if is_next:
            widgets.Badge(title_row, "Siguiente", bg=theme.ACCENT, fg="#FFFFFF").pack(side="left")

        meta = f"{lesson.concept} · {lesson.minutes} min"
        widgets.mk_label(left, meta, size=9, color=theme.MUTED).pack(anchor="w", pady=(4, 0))

        right = tk.Frame(columns, bg=theme.SURFACE)
        right.pack(side="right", padx=(16, 0))
        widgets.status_badge(right, status, best).pack(anchor="e", pady=(0, 6))
        if status == "completed":
            label = "Repasar"
            kind = "secondary"
        elif status == "in_progress":
            label = "Continuar"
            kind = "primary"
        else:
            label = "Empezar"
            kind = "primary" if is_next else "secondary"
        widgets.mk_button(
            right,
            label,
            lambda lesson_id=lesson.id: self.app.open_lesson(lesson_id),
            kind=kind,
            size=9,
            padx=14,
            pady=6,
        ).pack(anchor="e")

    def _build_completion_banner(self, parent) -> None:
        card = widgets.Card(parent, padding=18)
        card.configure(highlightbackground=theme.SUCCESS, highlightthickness=2)
        card.pack(fill="x", pady=(4, 0))
        body = card.body
        widgets.mk_label(
            body, "✓  Ruta completada", size=15, bold=True, color=theme.SUCCESS
        ).pack(anchor="w")
        widgets.mk_label(
            body,
            "Has terminado todas las lecciones de este nivel. Puedes repasar cualquiera "
            "o pasar al siguiente nivel sin perder el progreso.",
            size=10,
            color=theme.TEXT,
            wrap=760,
        ).pack(anchor="w", pady=(4, 10))

        current_index = next(
            (index for index, level in enumerate(self.app.repo.levels) if level.id == self.level.id),
            0,
        )
        if current_index + 1 < len(self.app.repo.levels):
            following = self.app.repo.levels[current_index + 1]
            widgets.mk_button(
                body,
                f"Pasar a {following.name}  →",
                lambda level_id=following.id: self.app.choose_level(level_id),
                kind="success",
            ).pack(anchor="w")
