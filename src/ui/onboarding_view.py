"""Pantalla de encuesta de onboarding.

Se muestra tras crear una cuenta para asignar el nivel inicial del usuario.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from core.onboarding import (
    SURVEY_QUESTIONS,
    calcular_nivel,
    nivel_a_nombre,
)
from core.profile_store import ProfileStore
from ui import theme, widgets


class OnboardingView(tk.Frame):
    """Encuesta inicial: una pregunta a la vez con opciones de selección."""

    def __init__(self, parent: tk.Misc, app, username: str) -> None:
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.username = username
        self.profile_store = ProfileStore()
        self.current_index = 0
        self.answers: dict[str, str] = {}
        self.selected_var: tk.StringVar | None = None

        self._build_ui()
        self._mostrar_pregunta()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        # Contenedor centrado
        center = tk.Frame(self, bg=theme.BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        card = widgets.Card(center, padding=40)
        card.pack()
        body = card.body

        # Título
        self.title_label = widgets.mk_label(
            body,
            "CONOCÉMOS UN POCO MÁS",
            size=10,
            bold=True,
            color=theme.ACCENT,
        )
        self.title_label.pack(anchor="w")

        self.question_label = widgets.mk_label(
            body,
            "",
            size=16,
            bold=True,
            wrap=520,
        )
        self.question_label.pack(anchor="w", pady=(4, 20))

        # Opciones (se reconstruyen en cada pregunta)
        self.options_frame = tk.Frame(body, bg=theme.SURFACE)
        self.options_frame.pack(fill="x")

        tk.Frame(body, bg=theme.SURFACE, height=20).pack()

        # Progreso
        self.progress_label = widgets.mk_label(
            body,
            "",
            size=9,
            color=theme.MUTED,
        )
        self.progress_label.pack(anchor="w")

        # Botón siguiente (inicialmente deshabilitado hasta elegir)
        self.btn_next = widgets.mk_button(
            body,
            "Siguiente →",
            self._siguiente,
            kind="primary",
            width=20,
        )
        self.btn_next.pack(anchor="e")

    def _mostrar_pregunta(self) -> None:
        for child in self.options_frame.winfo_children():
            child.destroy()

        if self.current_index >= len(SURVEY_QUESTIONS):
            self._finalizar_encuesta()
            return

        pregunta = SURVEY_QUESTIONS[self.current_index]
        self.question_label.configure(text=pregunta.text)

        # Progreso
        self.progress_label.configure(
            text=f"Pregunta {self.current_index + 1} de {len(SURVEY_QUESTIONS)}"
        )

        self.selected_var = tk.StringVar(value="")

        for opcion in pregunta.options:
            rb = tk.Radiobutton(
                self.options_frame,
                text=opcion.text,
                variable=self.selected_var,
                value=opcion.id,
                font=theme.font(11),
                bg=theme.SURFACE,
                fg=theme.TEXT,
                selectcolor=theme.SURFACE_ALT,
                activebackground=theme.SURFACE_ALT,
                cursor="hand2",
                anchor="w",
            )
            rb.pack(anchor="w", pady=4, fill="x")

        self.btn_next.configure(state="disabled")

    def _siguiente(self) -> None:
        if not self.selected_var or not self.selected_var.get():
            messagebox.showwarning(
                "Selecciona una opción",
                "Por favor elige una respuesta antes de continuar.",
                parent=self,
            )
            return

        pregunta = SURVEY_QUESTIONS[self.current_index]
        self.answers[pregunta.id] = self.selected_var.get()
        self.current_index += 1
        self._mostrar_pregunta()

    def _finalizar_encuesta(self) -> None:
        perfil = self.profile_store.create_from_survey(self.username, self.answers)
        nivel_nombre = nivel_a_nombre(perfil.level)

        messagebox.showinfo(
            "Encuesta completada",
            f"Gracias, {self.username}.\n\n"
            f"Tu nivel inicial es: {nivel_nombre}\n"
            f"Puntuación: {perfil.survey_score}\n\n"
            "Ahora puedes comenzar a aprender.",
            parent=self,
        )

        # Ir a la pantalla de bienvenida con el nivel asignado
        self.app.on_onboarding_complete(perfil)
