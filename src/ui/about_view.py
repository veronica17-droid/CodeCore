"""Acerca de, privacidad y mantenimiento."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox

from config import APP_NAME, APP_VERSION
from core.paths import app_data_dir, progress_file
from ui import theme, widgets


class AboutView(tk.Frame):
    def __init__(self, parent: tk.Misc, app) -> None:
        super().__init__(parent, bg=theme.BG)
        self.app = app
        scroll = widgets.ScrollFrame(self)
        scroll.pack(fill="both", expand=True)
        content = tk.Frame(scroll.inner, bg=theme.BG)
        content.pack(fill="both", expand=True, padx=6, pady=6)

        widgets.mk_label(content, "ACERCA DE", size=9, bold=True, color=theme.ACCENT).pack(anchor="w")
        widgets.mk_label(content, f"{APP_NAME} {APP_VERSION}", size=24, bold=True).pack(anchor="w")
        widgets.mk_label(
            content,
            "Un prototipo para aprender a programar pensando: problema, guía, ejercicio y "
            "retroalimentación. Sin cuentas, sin nube y sin instalar nada más.",
            size=10,
            color=theme.MUTED,
            wrap=860,
        ).pack(anchor="w", pady=(2, 14))

        self._build_about(content)
        self._build_data(content)
        self._build_shortcuts(content)
        self._build_limitations(content)

        scroll.bind_mousewheel()
        scroll.scroll_to_top()

    def _build_about(self, parent) -> None:
        card = widgets.Card(parent, padding=20)
        card.pack(fill="x", pady=(0, 10))
        body = card.body
        widgets.mk_label(body, "CÓMO ESTÁ HECHA", size=9, bold=True, color=theme.MUTED).pack(anchor="w")
        rows = [
            ("Interfaz", "Python 3.12 + tkinter/ttk (biblioteca estándar, sin dependencias externas)."),
            ("Contenido", "JSON local empaquetado con la app: 3 niveles, 13 lecciones y una biblioteca curada."),
            ("Evaluación", "Sintaxis con ast + comprobaciones declarativas. El código del usuario nunca se ejecuta."),
            ("Empaquetado", "PyInstaller --onefile --windowed: un único .exe sin consola."),
            ("Progreso", "JSON local en tu carpeta de usuario, con escritura atómica y copia de seguridad ante corrupción."),
        ]
        for title, text in rows:
            row = tk.Frame(body, bg=theme.SURFACE)
            row.pack(fill="x", pady=3)
            widgets.mk_label(row, title, size=9, bold=True, color=theme.ACCENT, width=12).pack(
                side="left", anchor="n"
            )
            widgets.mk_label(row, text, size=10, wrap=760, justify="left").pack(
                side="left", padx=(8, 0), anchor="w"
            )

    def _build_data(self, parent) -> None:
        card = widgets.Card(parent, padding=20)
        card.pack(fill="x", pady=(0, 10))
        body = card.body
        widgets.mk_label(body, "TUS DATOS", size=9, bold=True, color=theme.MUTED).pack(anchor="w")
        widgets.mk_label(
            body,
            "No se pide nombre, correo ni conexión. Todo el progreso vive en este archivo:",
            size=10,
            color=theme.TEXT,
            wrap=780,
        ).pack(anchor="w", pady=(4, 6))

        path_entry = tk.Entry(
            body,
            font=theme.font(9, mono=True),
            bg=theme.SURFACE_ALT,
            fg=theme.TEXT,
            relief="flat",
            bd=0,
        )
        path_entry.insert(0, str(progress_file()))
        path_entry.configure(state="readonly", readonlybackground=theme.SURFACE_ALT)
        path_entry.pack(fill="x", ipady=7, padx=0, pady=(0, 10))

        buttons = tk.Frame(body, bg=theme.SURFACE)
        buttons.pack(anchor="w")
        widgets.mk_button(
            buttons, "Abrir carpeta", self._open_folder, kind="secondary", size=9
        ).pack(side="left")
        widgets.mk_button(
            buttons, "Borrar progreso", self._reset_all, kind="danger", size=9
        ).pack(side="left", padx=(8, 0))

    def _build_shortcuts(self, parent) -> None:
        card = widgets.Card(parent, padding=20)
        card.pack(fill="x", pady=(0, 10))
        body = card.body
        widgets.mk_label(body, "ATAJOS Y DETALLES", size=9, bold=True, color=theme.MUTED).pack(anchor="w")
        shortcuts = [
            ("Ctrl + 1 … 5", "Cambiar entre Inicio, Mi ruta, Biblioteca, Progreso y Acerca de."),
            ("Tab", "Insertar cuatro espacios en el editor (nunca sale del editor)."),
            ("Shift + Tab", "Quitar hasta cuatro espacios al inicio de la línea."),
            ("Enter", "Mantener la indentación y añadir cuatro espacios tras «:»."),
            ("Ctrl + Z / Ctrl + Y", "Deshacer y rehacer en el editor."),
            ("Rueda del ratón", "Desplazar las pantallas largas."),
        ]
        for keys, text in shortcuts:
            row = tk.Frame(body, bg=theme.SURFACE)
            row.pack(fill="x", pady=3)
            widgets.mk_label(
                row, keys, size=9, bold=True, color=theme.ACCENT, width=16, mono=True
            ).pack(side="left", anchor="n")
            widgets.mk_label(row, text, size=10, wrap=740, justify="left").pack(
                side="left", padx=(8, 0), anchor="w"
            )

    def _build_limitations(self, parent) -> None:
        card = widgets.Card(parent, padding=20)
        card.configure(highlightbackground="#FDE68A", highlightthickness=1)
        card.pack(fill="x")
        body = card.body
        widgets.mk_label(
            body, "LIMITACIONES CONOCIDAS", size=9, bold=True, color=theme.WARNING
        ).pack(anchor="w")
        limitations = [
            "El código no se ejecuta: se valida sintaxis y estructura. No detecta errores lógicos que produzcan el resultado esperado por casualidad.",
            "La biblioteca es local y funciona sin internet; abrir un enlace sí requiere conexión y un navegador.",
            "Un .exe sin firma digital puede mostrar un aviso de SmartScreen o un falso positivo de antivirus. Es habitual en PyInstaller.",
            "El modo --onefile tarda uno o dos segundos en arrancar porque descomprime sus datos en una carpeta temporal.",
        ]
        for text in limitations:
            row = tk.Frame(body, bg=theme.SURFACE)
            row.pack(fill="x", pady=2)
            widgets.mk_label(row, "•", size=10, bold=True, color=theme.WARNING).pack(
                side="left", anchor="n"
            )
            widgets.mk_label(row, text, size=10, wrap=770, justify="left").pack(
                side="left", padx=(6, 0), anchor="w"
            )

    # ------------------------------------------------------------------

    def _open_folder(self) -> None:
        folder = app_data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(folder))  # type: ignore[attr-defined]
        except OSError as exc:
            messagebox.showerror("No se pudo abrir la carpeta", str(exc), parent=self)

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
