"""Panel de progreso global y por nivel."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from ui import theme, widgets


class ProgressView(tk.Frame):
    def __init__(self, parent: tk.Misc, app) -> None:
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.scroll = widgets.ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True)
        content = tk.Frame(self.scroll.inner, bg=theme.BG)
        content.pack(fill="both", expand=True, padx=6, pady=6)

        header = tk.Frame(content, bg=theme.BG)
        header.pack(fill="x")
        widgets.mk_label(header, "PROGRESO", size=9, bold=True, color=theme.ACCENT).pack(anchor="w")
        widgets.mk_label(header, "Tu recorrido, en datos", size=24, bold=True).pack(anchor="w")
        widgets.mk_label(
            header,
            "El progreso se guarda automáticamente en tu equipo. Completar una lección "
            "no borra los intentos anteriores.",
            size=10,
            color=theme.MUTED,
            wrap=860,
        ).pack(anchor="w", pady=(2, 14))

        summary = app.summary()
        self._build_overall(content, summary)
        self._build_levels(content, summary)
        self._build_detail(content)
        self._build_maintenance(content)

        self.scroll.bind_mousewheel()
        self.scroll.scroll_to_top()

    # ------------------------------------------------------------------

    def _build_overall(self, parent, summary: dict) -> None:
        overall = summary["overall"]
        card = widgets.Card(parent, padding=22)
        card.pack(fill="x")
        body = card.body

        top = tk.Frame(body, bg=theme.SURFACE)
        top.pack(fill="x")
        widgets.mk_label(
            top, f"{overall['percent']}%", size=34, bold=True, color=theme.ACCENT
        ).pack(side="left")
        stats = tk.Frame(top, bg=theme.SURFACE)
        stats.pack(side="left", padx=(18, 0), pady=(6, 0))
        widgets.mk_label(
            stats, f"{overall['completed']} de {overall['total']} lecciones completadas",
            size=11, bold=True,
        ).pack(anchor="w")
        remaining = overall["total"] - overall["completed"]
        widgets.mk_label(
            stats,
            f"Te quedan {remaining} lecciones para completar el recorrido.",
            size=9,
            color=theme.MUTED,
        ).pack(anchor="w", pady=(2, 0))

        bar = widgets.progress_bar(body)
        bar["value"] = overall["percent"]
        bar.pack(fill="x", pady=(14, 0))

    def _build_levels(self, parent, summary: dict) -> None:
        widgets.mk_label(
            parent, "POR NIVEL", size=9, bold=True, color=theme.MUTED
        ).pack(anchor="w", pady=(18, 8))

        row = tk.Frame(parent, bg=theme.BG)
        row.pack(fill="x")
        for index, level in enumerate(self.app.repo.levels):
            data = next((item for item in summary["levels"] if item["id"] == level.id), None)
            if data is None:
                continue
            card = widgets.Card(row, padding=16)
            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(0 if index == 0 else 8, 0),
            )
            body = card.body
            soft, strong = widgets.level_color(level.id)
            widgets.Badge(body, level.name, bg=soft, fg=strong).pack(anchor="w")
            widgets.mk_label(
                body, f"{data['percent']}%", size=22, bold=True, color=strong
            ).pack(anchor="w", pady=(8, 2))
            bar = widgets.progress_bar(body)
            bar["value"] = data["percent"]
            bar.pack(fill="x", pady=(2, 6))
            widgets.mk_label(
                body,
                f"{data['completed']} de {data['total']} lecciones",
                size=9,
                color=theme.MUTED,
            ).pack(anchor="w")
            widgets.mk_button(
                body,
                "Abrir ruta",
                lambda level_id=level.id: self.app.open_path(level_id),
                kind="secondary",
                size=9,
                padx=10,
                pady=5,
            ).pack(anchor="w", pady=(10, 0))

    def _build_detail(self, parent) -> None:
        widgets.mk_label(
            parent, "DETALLE DE LECCIONES", size=9, bold=True, color=theme.MUTED
        ).pack(anchor="w", pady=(18, 8))

        for level in self.app.repo.levels:
            lessons = self.app.repo.lessons_for_level(level.id)
            completed = sum(1 for lesson in lessons if self.app.progress.is_completed(lesson.id))
            section = tk.Frame(parent, bg=theme.BG)
            section.pack(fill="x", pady=(0, 10))
            head = tk.Frame(section, bg=theme.BG)
            head.pack(fill="x")
            soft, strong = widgets.level_color(level.id)
            widgets.Badge(head, level.name, bg=soft, fg=strong).pack(side="left")
            widgets.mk_label(
                head, f"{completed} de {len(lessons)}", size=9, color=theme.MUTED
            ).pack(side="left", padx=(10, 0))

            card = widgets.Card(section, padding=8)
            card.pack(fill="x", pady=(6, 0))
            for lesson in lessons:
                item = self.app.progress.lessons.get(lesson.id)
                status = item.status if item else "not_started"
                best = item.best_score if item else 0
                attempts = item.attempts if item else 0
                row = tk.Frame(card.body, bg=theme.SURFACE)
                row.pack(fill="x", padx=6, pady=4)

                icon = "✓" if status == "completed" else ("●" if status == "in_progress" else "○")
                color = (
                    theme.SUCCESS
                    if status == "completed"
                    else theme.WARNING if status == "in_progress" else theme.MUTED
                )
                widgets.mk_label(row, icon, size=11, bold=True, color=color).pack(side="left")
                widgets.mk_label(row, lesson.title, size=10).pack(side="left", padx=(8, 0))
                widgets.mk_label(
                    row,
                    f"{attempts} intento{'s' if attempts != 1 else ''} · mejor {best}%",
                    size=9,
                    color=theme.MUTED,
                ).pack(side="left", padx=(12, 0))
                widgets.mk_button(
                    row,
                    "Abrir",
                    lambda lesson_id=lesson.id: self.app.open_lesson(lesson_id),
                    kind="ghost",
                    size=9,
                    padx=6,
                    pady=2,
                ).pack(side="right")

    def _build_maintenance(self, parent) -> None:
        widgets.mk_label(
            parent, "MANTENIMIENTO", size=9, bold=True, color=theme.MUTED
        ).pack(anchor="w", pady=(10, 8))

        card = widgets.Card(parent, padding=18)
        card.pack(fill="x")
        body = card.body
        widgets.mk_label(
            body, "Reiniciar progreso", size=12, bold=True
        ).pack(anchor="w")
        widgets.mk_label(
            body,
            "Reiniciar un nivel conserva los demás. Borrar todo devuelve la app al inicio "
            "y no se puede deshacer.",
            size=9,
            color=theme.MUTED,
            wrap=760,
        ).pack(anchor="w", pady=(2, 10))

        buttons = tk.Frame(body, bg=theme.SURFACE)
        buttons.pack(anchor="w")
        current = self.app.repo.get_level(self.app.progress.level or "")
        if current:
            widgets.mk_button(
                buttons,
                f"Reiniciar {current.name}",
                lambda level=current: self._reset_level(level),
                kind="secondary",
                size=9,
            ).pack(side="left")
        widgets.mk_button(
            buttons,
            "Borrar todo el progreso",
            self._reset_all,
            kind="danger",
            size=9,
        ).pack(side="left", padx=(8, 0))

    # ------------------------------------------------------------------

    def _reset_level(self, level) -> None:
        confirmed = messagebox.askyesno(
            "Reiniciar nivel",
            f"¿Reiniciar todo el progreso de «{level.name}»?\n\n"
            "Las lecciones de otros niveles se conservan.",
            parent=self,
        )
        if not confirmed:
            return
        self.app.store.reset_level(
            self.app.progress, self.app.repo.lessons_for_level(level.id)
        )
        self.app.save_progress()
        self.app.refresh_shell()
        self.app.open_progress()

    def _reset_all(self) -> None:
        confirmed = messagebox.askyesno(
            "Borrar todo el progreso",
            "¿Borrar todo el progreso y volver a elegir nivel?\n\nEsta acción no se puede deshacer.",
            parent=self,
        )
        if not confirmed:
            return
        self.app.store.reset_all(self.app.progress)
        self.app.save_progress()
        self.app.refresh_shell()
        self.app.open_welcome()
