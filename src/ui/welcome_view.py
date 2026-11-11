"""Pantalla de inicio: selección de nivel y continuación."""

from __future__ import annotations

import tkinter as tk

from core.progress import ProgressStore
from ui import theme, widgets


class WelcomeView(tk.Frame):
    def __init__(self, parent: tk.Misc, app) -> None:
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.scroll = widgets.ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True)
        body = self.scroll.inner

        content = tk.Frame(body, bg=theme.BG)
        content.pack(fill="both", expand=True, padx=6, pady=6)

        widgets.mk_label(
            content,
            "BIENVENIDO A CODECORE",
            size=9,
            bold=True,
            color=theme.ACCENT,
        ).pack(anchor="w")
        widgets.mk_label(
            content,
            "¿Desde dónde empiezas?",
            size=26,
            bold=True,
        ).pack(anchor="w", pady=(2, 6))
        widgets.mk_label(
            content,
            "Elige tu punto de partida. No es un examen: puedes cambiar de nivel cuando quieras "
            "y tu progreso se conserva.",
            size=11,
            color=theme.MUTED,
            wrap=820,
        ).pack(anchor="w", pady=(0, 18))

        summary = self.app.summary()
        current_level = self.app.repo.get_level(self.app.progress.level or "")
        next_lesson = None
        if current_level:
            next_lesson = ProgressStore.next_pending(
                self.app.progress, self.app.repo.lessons_for_level(current_level.id)
            )

        if current_level and next_lesson:
            self._build_continue_card(content, current_level, next_lesson, summary)
            tk.Frame(content, bg=theme.BG, height=10).pack()

        for level in self.app.repo.levels:
            row = next((item for item in summary["levels"] if item["id"] == level.id), None)
            self._build_level_card(content, level, row, current_level.id if current_level else None)
            tk.Frame(content, bg=theme.BG, height=10).pack()

        self._build_how_it_works(content)
        self.scroll.bind_mousewheel()
        self.scroll.scroll_to_top()

    def _build_continue_card(self, parent, level, lesson, summary: dict) -> None:
        card = widgets.Card(parent, padding=20)
        card.configure(highlightbackground=theme.ACCENT, highlightthickness=2)
        card.pack(fill="x")
        body = card.body

        top = tk.Frame(body, bg=theme.SURFACE)
        top.pack(fill="x")
        widgets.mk_label(
            top, "CONTINÚA DONDE LO DEJASTE", size=9, bold=True, color=theme.ACCENT
        ).pack(side="left")
        widgets.mk_label(
            top,
            f"{summary['overall']['completed']} de {summary['overall']['total']} lecciones completadas",
            size=9,
            color=theme.MUTED,
        ).pack(side="right")

        widgets.mk_label(body, lesson.title, size=16, bold=True).pack(anchor="w", pady=(6, 2))
        widgets.mk_label(
            body,
            f"{level.name} · {lesson.concept} · {lesson.minutes} min",
            size=10,
            color=theme.MUTED,
        ).pack(anchor="w")
        widgets.mk_button(
            body,
            "Continuar lección  →",
            lambda: self.app.open_lesson(lesson.id),
            kind="primary",
        ).pack(anchor="w", pady=(14, 0))

    def _build_level_card(self, parent, level, row: dict | None, current_id: str | None) -> None:
        selected = level.id == current_id
        card = widgets.Card(parent, padding=20)
        if selected:
            card.configure(highlightbackground=theme.ACCENT, highlightthickness=2)
        card.pack(fill="x")

        body = card.body
        columns = tk.Frame(body, bg=theme.SURFACE)
        columns.pack(fill="x")

        left = tk.Frame(columns, bg=theme.SURFACE)
        left.pack(side="left", fill="both", expand=True)

        badges = tk.Frame(left, bg=theme.SURFACE)
        badges.pack(anchor="w")
        soft_bg, strong = widgets.level_color(level.id)
        widgets.Badge(badges, f"Nivel {level.order}", bg=soft_bg, fg=strong).pack(side="left")
        if selected:
            widgets.Badge(
                badges, "Nivel actual", bg=theme.ACCENT, fg="#FFFFFF"
            ).pack(side="left", padx=(6, 0))
        if row:
            widgets.mk_label(
                badges,
                f"{row['completed']} de {row['total']} lecciones",
                size=9,
                color=theme.MUTED,
            ).pack(side="left", padx=(10, 0))

        widgets.mk_label(left, level.name, size=18, bold=True).pack(anchor="w", pady=(8, 2))
        widgets.mk_label(
            left, level.tagline, size=10, color=theme.MUTED, wrap=620
        ).pack(anchor="w", pady=(0, 8))

        for outcome in level.outcomes[:2]:
            row_frame = tk.Frame(left, bg=theme.SURFACE)
            row_frame.pack(anchor="w", fill="x", pady=1)
            widgets.mk_label(
                row_frame, "•", size=10, bold=True, color=strong
            ).pack(side="left", anchor="n")
            widgets.mk_label(
                row_frame, outcome, size=10, color=theme.TEXT, wrap=600
            ).pack(side="left", padx=(6, 0))

        right = tk.Frame(columns, bg=theme.SURFACE, width=220)
        right.pack(side="right", fill="y", padx=(20, 0))
        right.pack_propagate(False)

        percent = row["percent"] if row else 0
        widgets.mk_label(
            right, f"{percent}%", size=22, bold=True, color=strong, anchor="e"
        ).pack(anchor="e")
        bar = widgets.progress_bar(right)
        bar["value"] = percent
        bar.pack(fill="x", pady=(4, 12))
        if row and row["completed"] == row["total"] and row["total"]:
            label = "Repasar ruta"
        elif selected:
            label = "Continuar"
        else:
            label = "Elegir este nivel"
        widgets.mk_button(
            right,
            label,
            lambda level_id=level.id: self.app.choose_level(level_id),
            kind="primary" if not selected else "secondary",
        ).pack(anchor="e", fill="x")

    def _build_how_it_works(self, parent) -> None:
        tk.Frame(parent, bg=theme.BG, height=14).pack()
        widgets.mk_label(
            parent, "CÓMO FUNCIONA UNA LECCIÓN", size=9, bold=True, color=theme.MUTED
        ).pack(anchor="w", pady=(0, 6))
        row = tk.Frame(parent, bg=theme.BG)
        row.pack(fill="x")
        steps = [
            ("1", "Problema", "Una situación concreta antes de tocar sintaxis."),
            ("2", "Guía", "Preguntas y pasos para razonar, no la respuesta."),
            ("3", "Ejercicio", "Escribes código o justificas una decisión."),
            ("4", "Feedback", "Cada error explica el malentendido."),
        ]
        for index, (number, title, text) in enumerate(steps):
            card = widgets.Card(row, padding=14)
            card.pack(side="left", fill="both", expand=True, padx=(0 if index == 0 else 8, 0))
            widgets.mk_label(card.body, number, size=16, bold=True, color=theme.ACCENT).pack(anchor="w")
            widgets.mk_label(card.body, title, size=11, bold=True).pack(anchor="w", pady=(2, 2))
            widgets.mk_label(card.body, text, size=9, color=theme.MUTED, wrap=220).pack(anchor="w")
