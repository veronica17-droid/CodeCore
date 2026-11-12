"""Pantalla de medallas y logros del usuario."""

from __future__ import annotations

import tkinter as tk

from core.achievements import earned_achievements, get_achievements
from ui import theme, widgets


class AchievementsView(tk.Frame):
    """Muestra las medallas ganadas y las disponibles."""

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
            "TUS MEDALLAS",
            size=9,
            bold=True,
            color=theme.ACCENT,
        ).pack(anchor="w")
        widgets.mk_label(
            content,
            "Logros desbloqueados por tu progreso",
            size=22,
            bold=True,
        ).pack(anchor="w", pady=(2, 6))

        widgets.mk_label(
            content,
            "Cada medalla reconoce un hito en tu aprendizaje. Sigue completando "
            "lecciones para desbloquear más.",
            size=11,
            color=theme.MUTED,
            wrap=820,
        ).pack(anchor="w", pady=(0, 18))

        progress = self.app.progress
        earned = set(a.id for a in earned_achievements(progress)) if progress else set()
        all_achievements = get_achievements()

        for achievement in all_achievements:
            self._build_medal(content, achievement, achievement.id in earned)

        self.scroll.bind_mousewheel()
        self.scroll.scroll_to_top()

    def _build_medal(self, parent, achievement, earned: bool) -> None:
        card = widgets.Card(parent, padding=18)
        card.configure(
            highlightbackground=theme.ACCENT if earned else theme.BORDER,
            highlightthickness=2 if earned else 1,
        )
        card.pack(fill="x", pady=6)
        body = card.body

        row = tk.Frame(body, bg=theme.SURFACE)
        row.pack(fill="x")

        # Icono y nombre
        icon_label = widgets.mk_label(
            row,
            achievement.icon,
            size=24,
            color=theme.ACCENT if earned else theme.MUTED,
        )
        icon_label.pack(side="left", padx=(0, 14))

        info = tk.Frame(row, bg=theme.SURFACE)
        info.pack(side="left", fill="x", expand=True)

        name_color = theme.TEXT if earned else theme.MUTED
        desc_color = theme.MUTED if earned else "#B0B7C3"

        widgets.mk_label(
            info,
            achievement.name,
            size=14,
            bold=True,
            color=name_color,
        ).pack(anchor="w")
        widgets.mk_label(
            info,
            achievement.description,
            size=10,
            color=desc_color,
            wrap=560,
        ).pack(anchor="w", pady=(2, 0))

        # Estado
        estado = "Desbloqueada" if earned else "Bloqueada"
        estado_color = theme.SUCCESS if earned else theme.WARNING
        widgets.mk_label(
            row,
            estado,
            size=9,
            bold=True,
            color=estado_color,
        ).pack(side="right")

        tk.Frame(parent, bg=theme.BG, height=4).pack()
