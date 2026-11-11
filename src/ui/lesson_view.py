"""Vista de lección: problema → guía → ejercicio → retroalimentación."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from core.feedback import Evaluation, evaluate, should_reveal_solution
from ui import theme, widgets
from ui.editor import CodeEditor


class LessonView(tk.Frame):
    STEPS = ("Problema", "Guía", "Ejercicio", "Feedback")

    def __init__(self, parent: tk.Misc, app, lesson_id: str) -> None:
        super().__init__(parent, bg=theme.BG)
        lesson = app.repo.get_lesson(lesson_id)
        if lesson is None:
            raise ValueError(f"Lección desconocida: {lesson_id}")
        self.app = app
        self.lesson = lesson
        self.item = app.progress.lesson(lesson_id)
        self.step = 0
        self.evaluation: Evaluation | None = None
        self.saved_answer = self.item.last_answer
        self.selected_option = self.saved_answer if lesson.exercise.type == "choice" else ""
        self.hints_revealed = 0
        self.solution_visible = False
        self.hint_message: str | None = None

        self.editor: CodeEditor | None = None
        self.answer_text: tk.Text | None = None
        self.choice_var = tk.StringVar(value=self.selected_option)
        self.word_label: tk.Label | None = None

        self._build_header()
        self.scroll = widgets.ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True)
        self.content = tk.Frame(self.scroll.inner, bg=theme.BG)
        self.content.pack(fill="both", expand=True, padx=6, pady=6)

        self.footer = tk.Frame(self, bg=theme.BG)
        self.footer.pack(fill="x", padx=6, pady=(4, 6))

        self.render()

    # ------------------------------------------------------------------
    # Estructura
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=theme.BG)
        header.pack(fill="x", padx=6, pady=(6, 0))

        top = tk.Frame(header, bg=theme.BG)
        top.pack(fill="x")
        widgets.mk_button(
            top,
            "←  Mi ruta",
            lambda: self.app.open_path(self.lesson.level_id),
            kind="ghost",
            padx=6,
            pady=2,
            size=9,
        ).pack(side="left")

        level = self.app.repo.get_level(self.lesson.level_id)
        lessons = self.app.repo.lessons_for_level(self.lesson.level_id)
        position = next(
            (index + 1 for index, item in enumerate(lessons) if item.id == self.lesson.id), 1
        )
        meta = f"{level.name if level else ''} · Lección {position} de {len(lessons)} · {self.lesson.minutes} min"
        widgets.mk_label(top, meta, size=9, color=theme.MUTED).pack(side="right")

        widgets.mk_label(header, self.lesson.title, size=22, bold=True).pack(
            anchor="w", pady=(10, 2)
        )
        widgets.mk_label(
            header, self.lesson.concept, size=10, color=theme.MUTED
        ).pack(anchor="w")

        self.stepper = tk.Frame(header, bg=theme.BG)
        self.stepper.pack(fill="x", pady=(12, 8))
        self.step_widgets: list[tk.Label] = []
        for index, name in enumerate(self.STEPS):
            label = tk.Label(
                self.stepper,
                text=f"{index + 1}. {name}",
                font=theme.font(9, True),
                bg=theme.SURFACE_ALT,
                fg=theme.MUTED,
                padx=12,
                pady=6,
                cursor="hand2",
            )
            label.pack(side="left", padx=(0, 6))
            label.bind("<Button-1>", lambda _event, target=index: self.go_to(target))
            self.step_widgets.append(label)

    def _update_stepper(self) -> None:
        for index, label in enumerate(self.step_widgets):
            if index == self.step:
                label.configure(bg=theme.ACCENT, fg="#FFFFFF")
            elif index == 3 and self.evaluation is not None and self.evaluation.passed:
                label.configure(bg=theme.SUCCESS_BG, fg=theme.SUCCESS)
            elif index < self.step:
                label.configure(bg=theme.SURFACE_ALT, fg=theme.ACCENT)
            else:
                label.configure(bg=theme.SURFACE_ALT, fg=theme.MUTED)

    def render(self) -> None:
        widgets.clear(self.content)
        widgets.clear(self.footer)
        self.editor = None
        self.answer_text = None
        self.word_label = None

        if self.step == 0:
            self._render_problem()
        elif self.step == 1:
            self._render_guide()
        elif self.step == 2:
            self._render_exercise()
        else:
            self._render_feedback()

        self._update_stepper()
        self._render_footer()
        self.scroll.bind_mousewheel()
        self.scroll.scroll_to_top()

    # ------------------------------------------------------------------
    # Pasos
    # ------------------------------------------------------------------

    def _render_problem(self) -> None:
        problem = self.lesson.problem
        card = widgets.Card(self.content, padding=24)
        card.pack(fill="x")
        body = card.body

        widgets.mk_label(body, "EL PROBLEMA", size=9, bold=True, color=theme.ACCENT).pack(anchor="w")
        widgets.mk_label(
            body, problem.scenario, size=11, wrap=840, justify="left"
        ).pack(anchor="w", pady=(10, 16))

        question_card = tk.Frame(body, bg=theme.ACCENT_SOFT, padx=18, pady=14)
        question_card.pack(fill="x")
        widgets.mk_label(
            question_card, "LA PREGUNTA", size=8, bold=True, color=theme.ACCENT,
            bg=theme.ACCENT_SOFT,
        ).pack(anchor="w")
        widgets.mk_label(
            question_card,
            problem.question,
            size=14,
            bold=True,
            color=theme.ACCENT,
            bg=theme.ACCENT_SOFT,
            wrap=780,
        ).pack(anchor="w", pady=(4, 0))

        if problem.constraints:
            widgets.mk_label(
                body, "RESTRICCIONES", size=9, bold=True, color=theme.MUTED
            ).pack(anchor="w", pady=(18, 6))
            for constraint in problem.constraints:
                self._bullet(body, constraint)

        if problem.reflection:
            reflection = tk.Frame(body, bg=theme.SURFACE_ALT, padx=14, pady=10)
            reflection.pack(fill="x", pady=(16, 0))
            widgets.mk_label(
                reflection,
                f"Para pensar: {problem.reflection}",
                size=10,
                color=theme.MUTED,
                bg=theme.SURFACE_ALT,
                wrap=780,
            ).pack(anchor="w")

        widgets.mk_label(
            self.content,
            "Todavía no hay que escribir código. Primero entiende qué se pide y qué restricciones lo hacen interesante.",
            size=9,
            color=theme.MUTED,
            wrap=820,
        ).pack(anchor="w", pady=(12, 0))

    def _render_guide(self) -> None:
        guide = self.lesson.guide
        card = widgets.Card(self.content, padding=24)
        card.pack(fill="x")
        body = card.body

        widgets.mk_label(body, "MODELO MENTAL", size=9, bold=True, color=theme.ACCENT).pack(anchor="w")
        widgets.mk_label(
            body, guide.mental_model, size=11, wrap=840, justify="left"
        ).pack(anchor="w", pady=(8, 16))

        for index, step in enumerate(guide.steps):
            step_card = tk.Frame(body, bg=theme.SURFACE_ALT, padx=16, pady=12)
            step_card.pack(fill="x", pady=(0, 8))
            widgets.mk_label(
                step_card, step.title, size=11, bold=True, bg=theme.SURFACE_ALT
            ).pack(anchor="w")
            widgets.mk_label(
                step_card, step.body, size=10, bg=theme.SURFACE_ALT, wrap=800, justify="left"
            ).pack(anchor="w", pady=(4, 0))

        if guide.questions:
            question_card = widgets.Card(self.content, padding=20)
            question_card.configure(highlightbackground=theme.ACCENT, highlightthickness=1)
            question_card.pack(fill="x", pady=(12, 0))
            widgets.mk_label(
                question_card.body, "PREGÚNTATE", size=9, bold=True, color=theme.ACCENT
            ).pack(anchor="w")
            for question in guide.questions:
                self._bullet(question_card.body, question, color=theme.TEXT)

        if guide.common_mistakes:
            mistake_card = widgets.Card(self.content, padding=20)
            mistake_card.configure(highlightbackground="#FDE68A", highlightthickness=1)
            mistake_card.pack(fill="x", pady=(10, 0))
            widgets.mk_label(
                mistake_card.body, "ERRORES COMUNES", size=9, bold=True, color=theme.WARNING
            ).pack(anchor="w")
            for mistake in guide.common_mistakes:
                self._bullet(mistake_card.body, mistake, color=theme.TEXT, bullet="!")

    def _render_exercise(self) -> None:
        exercise = self.lesson.exercise
        card = widgets.Card(self.content, padding=24)
        card.pack(fill="x")
        body = card.body

        widgets.mk_label(body, "EL EJERCICIO", size=9, bold=True, color=theme.ACCENT).pack(anchor="w")
        widgets.mk_label(
            body, exercise.prompt, size=11, wrap=840, justify="left"
        ).pack(anchor="w", pady=(8, 14))

        if exercise.type == "code":
            self.editor = CodeEditor(body, height=14)
            self.editor.pack(fill="both", expand=True)
            self.editor.set_text(self.saved_answer or exercise.starter_code)
            self.editor.focus_editor()
        elif exercise.type == "choice":
            for option in exercise.options:
                row = tk.Frame(body, bg=theme.SURFACE, pady=4)
                row.pack(fill="x")
                radio = tk.Radiobutton(
                    row,
                    text=option.text,
                    variable=self.choice_var,
                    value=option.id,
                    bg=theme.SURFACE,
                    fg=theme.TEXT,
                    activebackground=theme.SURFACE,
                    activeforeground=theme.ACCENT,
                    selectcolor=theme.SURFACE,
                    font=theme.font(10),
                    wraplength=780,
                    justify="left",
                    anchor="w",
                    cursor="hand2",
                    padx=6,
                    pady=6,
                )
                radio.pack(fill="x")
        else:
            self.answer_text = tk.Text(
                body,
                height=8,
                wrap="word",
                font=theme.font(10),
                bg=theme.SURFACE,
                fg=theme.TEXT,
                insertbackground=theme.TEXT,
                relief="solid",
                bd=1,
                highlightthickness=0,
                padx=10,
                pady=8,
            )
            self.answer_text.pack(fill="x")
            self.answer_text.insert("1.0", self.saved_answer)
            self.answer_text.focus_set()
            self.word_label = widgets.mk_label(
                body,
                "",
                size=9,
                color=theme.MUTED,
            )
            self.word_label.pack(anchor="w", pady=(6, 0))
            self._update_word_count()
            self.answer_text.bind("<KeyRelease>", lambda _event: self._update_word_count())

        if exercise.hints:
            hint_row = tk.Frame(body, bg=theme.SURFACE)
            hint_row.pack(fill="x", pady=(14, 0))
            remaining = len(exercise.hints) - self.hints_revealed
            label = "Ver pista" if remaining > 0 else "Sin más pistas"
            widgets.mk_button(
                hint_row,
                f"{label} ({self.hints_revealed}/{len(exercise.hints)})",
                self._show_hint,
                kind="secondary",
                size=9,
                padx=12,
                pady=6,
                state="normal" if remaining > 0 else "disabled",
            ).pack(side="left")

            if self.hint_message:
                widgets.mk_label(
                    hint_row,
                    self.hint_message,
                    size=9,
                    color=theme.WARNING,
                ).pack(side="left", padx=(12, 0))

        if self.hints_revealed:
            hint_card = tk.Frame(body, bg=theme.WARNING_BG, padx=14, pady=10)
            hint_card.pack(fill="x", pady=(10, 0))
            widgets.mk_label(
                hint_card, "PISTAS", size=8, bold=True, color=theme.WARNING, bg=theme.WARNING_BG
            ).pack(anchor="w")
            for index, hint in enumerate(exercise.hints[: self.hints_revealed], start=1):
                widgets.mk_label(
                    hint_card,
                    f"{index}. {hint}",
                    size=10,
                    color=theme.TEXT,
                    bg=theme.WARNING_BG,
                    wrap=800,
                ).pack(anchor="w", pady=(2, 0))

        if exercise.solution:
            self._render_solution(body)

    def _render_solution(self, parent) -> None:
        if self.item.attempts >= 3:
            widgets.mk_button(
                parent,
                "Ocultar solución" if self.solution_visible else "Ver una solución posible",
                self._toggle_solution,
                kind="ghost",
                size=9,
                padx=6,
                pady=4,
            ).pack(anchor="w", pady=(12, 0))
            if self.solution_visible:
                self._solution_card(parent)
        else:
            widgets.mk_label(
                parent,
                "La solución se desbloquea tras 3 intentos. Antes de eso, una pista vale más.",
                size=9,
                color=theme.MUTED,
            ).pack(anchor="w", pady=(12, 0))

    def _render_feedback(self) -> None:
        evaluation = self.evaluation
        if evaluation is None:
            card = widgets.Card(self.content, padding=24)
            card.pack(fill="x")
            widgets.mk_label(
                card.body, "Todavía no has comprobado tu respuesta.", size=12, bold=True
            ).pack(anchor="w")
            widgets.mk_label(
                card.body,
                "Vuelve al ejercicio y pulsa «Comprobar respuesta» para recibir retroalimentación.",
                size=10,
                color=theme.MUTED,
            ).pack(anchor="w", pady=(4, 12))
            widgets.mk_button(
                card.body, "Ir al ejercicio", lambda: self.go_to(2)
            ).pack(anchor="w")
            return

        color = theme.SUCCESS if evaluation.passed else theme.DANGER
        soft = theme.SUCCESS_BG if evaluation.passed else theme.DANGER_BG

        summary_card = widgets.Card(self.content, padding=24)
        summary_card.configure(highlightbackground=color, highlightthickness=2)
        summary_card.pack(fill="x")
        body = summary_card.body

        top = tk.Frame(body, bg=theme.SURFACE)
        top.pack(fill="x")
        score_box = tk.Frame(top, bg=soft, padx=18, pady=10)
        score_box.pack(side="left")
        widgets.mk_label(
            score_box,
            f"{evaluation.score}%",
            size=24,
            bold=True,
            color=color,
            bg=soft,
        ).pack()
        widgets.mk_label(
            score_box, "PUNTAJE", size=7, bold=True, color=color, bg=soft
        ).pack()

        text_box = tk.Frame(top, bg=theme.SURFACE)
        text_box.pack(side="left", fill="both", expand=True, padx=(16, 0))
        widgets.mk_label(
            text_box,
            "Aprobado" if evaluation.passed else "Todavía no",
            size=16,
            bold=True,
            color=color,
        ).pack(anchor="w")
        widgets.mk_label(
            text_box, evaluation.summary, size=10, color=theme.TEXT, wrap=700
        ).pack(anchor="w", pady=(2, 0))
        widgets.mk_label(
            text_box,
            f"Intento {self.item.attempts} · mejor puntaje {self.item.best_score}%",
            size=9,
            color=theme.MUTED,
        ).pack(anchor="w", pady=(4, 0))

        if evaluation.syntax_error:
            error_card = tk.Frame(body, bg=theme.DANGER_BG, padx=14, pady=10)
            error_card.pack(fill="x", pady=(16, 0))
            widgets.mk_label(
                error_card,
                evaluation.syntax_error,
                size=10,
                color=theme.DANGER,
                bg=theme.DANGER_BG,
                wrap=800,
                mono=True,
            ).pack(anchor="w")

        widgets.mk_label(
            body, "COMPROBACIONES", size=9, bold=True, color=theme.MUTED
        ).pack(anchor="w", pady=(16, 6))
        for outcome in evaluation.outcomes:
            row = tk.Frame(body, bg=theme.SURFACE)
            row.pack(fill="x", pady=2)
            widgets.mk_label(
                row,
                "✓" if outcome.ok else "✗",
                size=11,
                bold=True,
                color=theme.SUCCESS if outcome.ok else theme.DANGER,
            ).pack(side="left", anchor="n")
            widgets.mk_label(
                row,
                outcome.message,
                size=10,
                color=theme.MUTED if outcome.ok else theme.TEXT,
                wrap=780,
            ).pack(side="left", padx=(8, 0), anchor="w")

        if evaluation.next_hint:
            hint_card = tk.Frame(body, bg=theme.WARNING_BG, padx=14, pady=10)
            hint_card.pack(fill="x", pady=(14, 0))
            widgets.mk_label(
                hint_card,
                f"Pista: {evaluation.next_hint}",
                size=10,
                color=theme.TEXT,
                bg=theme.WARNING_BG,
                wrap=800,
            ).pack(anchor="w")

        if evaluation.passed:
            next_lesson = self.app.repo.next_lesson(self.lesson.id)
            success_card = widgets.Card(self.content, padding=20)
            success_card.configure(highlightbackground=theme.SUCCESS, highlightthickness=2)
            success_card.pack(fill="x", pady=(12, 0))
            widgets.mk_label(
                success_card.body,
                "✓  Lección completada",
                size=14,
                bold=True,
                color=theme.SUCCESS,
            ).pack(anchor="w")
            widgets.mk_label(
                success_card.body,
                "El progreso se ha guardado. Puedes repasar esta lección o continuar con la siguiente.",
                size=10,
                color=theme.TEXT,
                wrap=780,
            ).pack(anchor="w", pady=(4, 12))
            buttons = tk.Frame(success_card.body, bg=theme.SURFACE)
            buttons.pack(anchor="w")
            if next_lesson:
                widgets.mk_button(
                    buttons,
                    f"Siguiente: {next_lesson.title}  →",
                    lambda lesson_id=next_lesson.id: self.app.open_lesson(lesson_id),
                    kind="success",
                ).pack(side="left")
            widgets.mk_button(
                buttons,
                "Volver a la ruta",
                lambda: self.app.open_path(self.lesson.level_id),
                kind="secondary",
            ).pack(side="left", padx=(8, 0))
        else:
            if self.item.attempts >= 3 and self.lesson.exercise.solution:
                if self.solution_visible:
                    self._solution_card(self.content)
                else:
                    widgets.mk_button(
                        self.content,
                        "Ver una solución posible",
                        self._toggle_solution,
                        kind="ghost",
                        size=9,
                        padx=6,
                        pady=4,
                    ).pack(anchor="w", pady=(12, 0))

    # ------------------------------------------------------------------
    # Navegación y acciones
    # ------------------------------------------------------------------

    def go_to(self, step: int) -> None:
        step = max(0, min(3, step))
        if step == 3 and self.evaluation is None:
            self._capture_answer()
            if not str(self.saved_answer).strip():
                # Sin respuesta no se registra un intento: solo se muestra el
                # recordatorio de que aún no se ha comprobado nada.
                self.step = 3
                self.render()
                return
            self.evaluate()
            return
        if self.step == 2 and step != 2:
            self._capture_answer()
        self.step = step
        self.render()

    def _capture_answer(self) -> None:
        exercise = self.lesson.exercise
        if exercise.type == "code" and self.editor is not None and self.editor.winfo_exists():
            self.saved_answer = self.editor.get_text()
        elif exercise.type == "choice":
            self.saved_answer = self.choice_var.get()
        elif exercise.type == "short" and self.answer_text is not None and self.answer_text.winfo_exists():
            self.saved_answer = self.answer_text.get("1.0", "end-1c")

    def evaluate(self) -> None:
        self._capture_answer()
        if not str(self.saved_answer).strip():
            messagebox.showwarning(
                "Respuesta vacía",
                {
                    "code": "Escribe tu propuesta en el editor antes de comprobar.",
                    "choice": "Selecciona una opción antes de comprobar.",
                    "short": "Escribe tu explicación antes de comprobar.",
                }.get(self.lesson.exercise.type, "Escribe una respuesta antes de comprobar."),
                parent=self,
            )
            self.step = 2
            self.render()
            return
        attempt = self.item.attempts + 1
        result = evaluate(
            self.lesson.exercise,
            self.saved_answer,
            attempt=attempt,
            level_id=self.lesson.level_id,
        )
        next_lesson = self.app.repo.next_lesson(self.lesson.id)
        self.app.store.record_attempt(
            self.app.progress,
            self.lesson.id,
            result.score,
            result.passed,
            self.saved_answer,
            next_lesson.id if next_lesson else None,
        )
        self.app.save_progress()
        self.app.refresh_shell()
        self.item = self.app.progress.lesson(self.lesson.id)
        self.evaluation = result
        self.step = 3
        self.render()

    def _show_hint(self) -> None:
        hints = self.lesson.exercise.hints
        if not hints:
            return
        if self.lesson.level_id == "advanced" and self.item.attempts < 2:
            self.hint_message = (
                "En nivel avanzado las pistas aparecen tras dos intentos. "
                "Prueba primero tu propio camino."
            )
        elif self.hints_revealed >= len(hints):
            self.hint_message = "No hay más pistas. Relee el problema y prueba otro camino."
        else:
            self.hints_revealed += 1
            self.hint_message = None
        self.render()

    def _toggle_solution(self) -> None:
        if not should_reveal_solution(self.item.attempts):
            return
        self.solution_visible = not self.solution_visible
        self.render()

    def _update_word_count(self) -> None:
        if self.answer_text is None or self.word_label is None:
            return
        words = len(self.answer_text.get("1.0", "end-1c").split())
        minimum = self.lesson.exercise.min_words
        color = theme.SUCCESS if words >= minimum else theme.MUTED
        self.word_label.configure(
            text=f"{words} palabras · mínimo {minimum} · ideas clave: {self.lesson.exercise.min_keywords}",
            fg=color,
        )

    # ------------------------------------------------------------------
    # Piezas reutilizables
    # ------------------------------------------------------------------

    def _bullet(self, parent, text: str, color: str = theme.TEXT, bullet: str = "•") -> None:
        row = tk.Frame(parent, bg=parent.cget("bg"))
        row.pack(fill="x", anchor="w", pady=2)
        widgets.mk_label(
            row, bullet, size=10, bold=True, color=theme.ACCENT, bg=parent.cget("bg")
        ).pack(side="left", anchor="n")
        widgets.mk_label(
            row,
            text,
            size=10,
            color=color,
            bg=parent.cget("bg"),
            wrap=790,
            justify="left",
        ).pack(side="left", padx=(8, 0), anchor="w")

    def _solution_card(self, parent) -> None:
        card = tk.Frame(parent, bg=theme.CODE_BG, padx=16, pady=14)
        card.pack(fill="x", pady=(8, 0))
        widgets.mk_label(
            card, "UNA SOLUCIÓN POSIBLE", size=8, bold=True, color=theme.CODE_COMMENT, bg=theme.CODE_BG
        ).pack(anchor="w")
        widgets.mk_label(
            card,
            self.lesson.exercise.solution,
            size=10,
            color=theme.CODE_FG,
            bg=theme.CODE_BG,
            wrap=800,
            justify="left",
            mono=True,
        ).pack(anchor="w", pady=(6, 0))

    def _render_footer(self) -> None:
        if self.step > 0:
            widgets.mk_button(
                self.footer,
                "←  Anterior",
                lambda: self.go_to(self.step - 1),
                kind="secondary",
                size=9,
                padx=14,
                pady=7,
            ).pack(side="left")

        if self.step == 0:
            widgets.mk_button(
                self.footer,
                "Entender el problema  →",
                lambda: self.go_to(1),
            ).pack(side="right")
        elif self.step == 1:
            widgets.mk_button(
                self.footer,
                "Ir al ejercicio  →",
                lambda: self.go_to(2),
            ).pack(side="right")
        elif self.step == 2:
            widgets.mk_button(
                self.footer,
                "Comprobar respuesta",
                self.evaluate,
            ).pack(side="right")
        else:
            if self.evaluation is not None and not self.evaluation.passed:
                widgets.mk_button(
                    self.footer,
                    "Reintentar",
                    lambda: self.go_to(2),
                ).pack(side="right")
            elif self.evaluation is not None and self.evaluation.passed:
                next_lesson = self.app.repo.next_lesson(self.lesson.id)
                if next_lesson:
                    widgets.mk_button(
                        self.footer,
                        "Siguiente lección  →",
                        lambda lesson_id=next_lesson.id: self.app.open_lesson(lesson_id),
                        kind="success",
                    ).pack(side="right")
                else:
                    widgets.mk_button(
                        self.footer,
                        "Volver a la ruta",
                        lambda: self.app.open_path(self.lesson.level_id),
                        kind="success",
                    ).pack(side="right")
            widgets.mk_button(
                self.footer,
                "Repasar lección",
                self._restart,
                kind="secondary",
                size=9,
            ).pack(side="right", padx=(0, 8))

    def _restart(self) -> None:
        self.evaluation = None
        self.hints_revealed = 0
        self.solution_visible = False
        self.hint_message = None
        self.step = 0
        self.render()
