"""Pantalla de autenticación: iniciar sesión y crear cuenta."""

from __future__ import annotations

import tkinter as tk

from core.auth import AuthStore
from ui import theme, widgets


class AuthView(tk.Frame):
    """Pantalla de login y registro. Se muestra antes de la bienvenida."""

    def __init__(self, parent: tk.Misc, app, on_auth_success) -> None:
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.on_auth_success = on_auth_success
        self.auth = AuthStore()
        self.mode = "login"  # "login" o "register"

        self._build_ui()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        # Contenedor centrado
        center = tk.Frame(self, bg=theme.BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        card = widgets.Card(center, padding=32)
        card.pack()
        body = card.body

        widgets.mk_label(
            body,
            "CODECORE",
            size=20,
            bold=True,
            color=theme.ACCENT,
        ).pack(anchor="w")
        widgets.mk_label(
            body,
            "Aprende a programar pensando",
            size=11,
            color=theme.MUTED,
        ).pack(anchor="w", pady=(0, 24))

        self.message_var = tk.StringVar(value="")
        self.message_label = widgets.mk_label(
            body,
            "",
            size=10,
            color=theme.DANGER,
            wrap=340,
        )
        self.message_label.pack(anchor="w", pady=(0, 16))

        # Selector de modo
        mode_row = tk.Frame(body, bg=theme.SURFACE)
        mode_row.pack(fill="x", pady=(0, 16))

        self.btn_login_mode = widgets.mk_button(
            mode_row,
            "Iniciar sesión",
            self._set_login_mode,
            kind="primary" if self.mode == "login" else "ghost",
            size=10,
            padx=16,
            pady=8,
        )
        self.btn_login_mode.pack(side="left")

        self.btn_register_mode = widgets.mk_button(
            mode_row,
            "Crear cuenta",
            self._set_register_mode,
            kind="primary" if self.mode == "register" else "ghost",
            size=10,
            padx=16,
            pady=8,
        )
        self.btn_register_mode.pack(side="left", padx=(10, 0))

        tk.Frame(body, bg=theme.SURFACE, height=8).pack()

        # Formulario (se reconstruye al cambiar de modo)
        self.form_frame = tk.Frame(body, bg=theme.SURFACE)
        self.form_frame.pack(fill="x")
        self._build_form()

        tk.Frame(body, bg=theme.SURFACE, height=12).pack()

        # Botón principal
        self.btn_action = widgets.mk_button(
            body,
            "Entrar" if self.mode == "login" else "Crear cuenta",
            self._on_action,
            kind="primary",
            width=22,
        )
        self.btn_action.pack(anchor="e")

        # Atajo: Enter dispara la acción
        self.bind("<Return>", lambda _event: self._on_action())

    def _build_form(self) -> None:
        for child in self.form_frame.winfo_children():
            child.destroy()

        self.entry_user = widgets.mk_entry_styled(
            self.form_frame,
            placeholder="Usuario",
        )
        self.entry_user.pack(fill="x", pady=(0, 10))

        self.entry_pass = widgets.mk_entry_styled(
            self.form_frame,
            placeholder="Contraseña",
            show="*",
        )
        self.entry_pass.pack(fill="x", pady=(0, 6))

        if self.mode == "register":
            self.entry_pass_confirm = widgets.mk_entry_styled(
                self.form_frame,
                placeholder="Repetir contraseña",
                show="*",
            )
            self.entry_pass_confirm.pack(fill="x", pady=(0, 14))

    def _set_login_mode(self) -> None:
        self.mode = "login"
        self.btn_login_mode.configure(kind="primary")
        self.btn_register_mode.configure(kind="ghost")
        self.btn_action.configure(text="Entrar")
        self._build_form()
        self._clear_message()

    def _set_register_mode(self) -> None:
        self.mode = "register"
        self.btn_login_mode.configure(kind="ghost")
        self.btn_register_mode.configure(kind="primary")
        self.btn_action.configure(text="Crear cuenta")
        self._build_form()
        self._clear_message()

    def _clear_message(self) -> None:
        self.message_var.set("")
        self.message_label.configure(text="", fg=theme.DANGER)

    def _show_message(self, text: str, error: bool = True) -> None:
        self.message_var.set(text)
        self.message_label.configure(
            text=text, fg=theme.DANGER if error else theme.SUCCESS
        )

    # ------------------------------------------------------------------ Acciones

    def _on_action(self) -> None:
        username = self.entry_user.get().strip()
        password = self.entry_pass.get()

        if not username or not password:
            self._show_message("Usuario y contraseña son requeridos.")
            return

        if self.mode == "login":
            ok, msg = self.auth.login(username, password)
            if ok:
                self._show_message(msg, error=False)
                self.after(600, lambda: self.on_auth_success(username))
            else:
                self._show_message(msg)
        else:
            confirm = self.entry_pass_confirm.get()
            if password != confirm:
                self._show_message("Las contraseñas no coinciden.")
                return
            ok, msg = self.auth.register(username, password)
            if ok:
                self._show_message(msg, error=False)
                self.after(900, lambda: self.on_auth_success(username))
            else:
                self._show_message(msg)
