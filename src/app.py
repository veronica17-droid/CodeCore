"""Ventana principal, navegación y estado compartido."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from config import (
    APP_NAME,
    APP_VERSION,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)
from core.content import ContentRepository
from core.paths import resource_path
from core.progress import ProgressStore
from ui import theme, widgets
from ui.about_view import AboutView
from ui.library_view import LibraryView
from ui.lesson_view import LessonView
from ui.path_view import PathView
from ui.progress_view import ProgressView
from ui.welcome_view import WelcomeView

NAV_ITEMS = (
    ("welcome", "Inicio"),
    ("path", "Mi ruta"),
    ("library", "Biblioteca"),
    ("progress", "Progreso"),
    ("about", "Acerca de"),
)


class NavItem(tk.Frame):
    def __init__(self, parent: tk.Misc, text: str, command) -> None:
        super().__init__(parent, bg=theme.SIDEBAR, cursor="hand2")
        self.command = command
        self.active = False
        self.bar = tk.Frame(self, bg=theme.SIDEBAR, width=3)
        self.bar.pack(side="left", fill="y")
        self.label = tk.Label(
            self,
            text=text,
            font=theme.font(10, True),
            bg=theme.SIDEBAR,
            fg="#CBD5E1",
            anchor="w",
            padx=16,
            pady=10,
            cursor="hand2",
        )
        self.label.pack(side="left", fill="x", expand=True)
        for widget in (self, self.label, self.bar):
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _on_click(self, _event=None) -> None:
        self.command()

    def _on_enter(self, _event=None) -> None:
        if not self.active:
            self._paint(theme.SIDEBAR_HOVER, "#FFFFFF")

    def _on_leave(self, _event=None) -> None:
        if not self.active:
            self._paint(theme.SIDEBAR, "#CBD5E1")

    def _paint(self, bg: str, fg: str) -> None:
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)

    def set_active(self, active: bool) -> None:
        self.active = active
        if active:
            self._paint(theme.SIDEBAR_ACTIVE, "#FFFFFF")
            self.bar.configure(bg=theme.ACCENT)
        else:
            self._paint(theme.SIDEBAR, "#CBD5E1")
            self.bar.configure(bg=theme.SIDEBAR)


class CodeCoreApp(tk.Tk):
    def __init__(
        self,
        repository: ContentRepository | None = None,
        store: ProgressStore | None = None,
    ) -> None:
        super().__init__()
        self.repo = repository or ContentRepository()
        self.store = store or ProgressStore()
        self.progress = self.store.load()
        self.current_view: tk.Frame | None = None
        self.nav_items: dict[str, NavItem] = {}
        self._save_error_shown = False

        self.title(WINDOW_TITLE)
        theme.apply_theme(self)
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self._center_window()
        self._set_icon()
        self.report_callback_exception = self._report_exception

        self._build_shell()
        self.refresh_shell()
        self.open_welcome()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------

    def _center_window(self) -> None:
        self.update_idletasks()
        x = max(0, (self.winfo_screenwidth() - WINDOW_WIDTH) // 2)
        y = max(0, (self.winfo_screenheight() - WINDOW_HEIGHT) // 3)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    def _set_icon(self) -> None:
        try:
            self.iconbitmap(str(resource_path("assets", "codecore.ico")))
        except (tk.TclError, OSError):
            pass

    def _build_shell(self) -> None:
        sidebar = tk.Frame(self, bg=theme.SIDEBAR, width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = tk.Frame(sidebar, bg=theme.SIDEBAR)
        logo.pack(fill="x", padx=22, pady=(24, 18))
        widgets.mk_label(
            logo, APP_NAME, size=19, bold=True, color="#FFFFFF", bg=theme.SIDEBAR
        ).pack(anchor="w")
        widgets.mk_label(
            logo,
            "Aprende pensando",
            size=9,
            color="#94A3B8",
            bg=theme.SIDEBAR,
        ).pack(anchor="w", pady=(1, 0))

        tk.Frame(sidebar, bg="#1E293B", height=1).pack(fill="x", padx=18)

        nav = tk.Frame(sidebar, bg=theme.SIDEBAR)
        nav.pack(fill="x", pady=(12, 0))
        for index, (key, label) in enumerate(NAV_ITEMS):
            item = NavItem(nav, label, lambda key=key: self._open_nav(key))
            item.pack(fill="x", pady=1)
            self.nav_items[key] = item
            self.bind(f"<Control-Key-{index + 1}>", lambda _event, key=key: self._open_nav(key))

        footer = tk.Frame(sidebar, bg=theme.SIDEBAR)
        footer.pack(side="bottom", fill="x", padx=20, pady=(0, 22))
        tk.Frame(footer, bg="#1E293B", height=1).pack(fill="x", pady=(0, 14))
        widgets.mk_label(
            footer,
            "PROGRESO TOTAL",
            size=8,
            bold=True,
            color="#94A3B8",
            bg=theme.SIDEBAR,
        ).pack(anchor="w")
        self.overall_percent = widgets.mk_label(
            footer, "0%", size=22, bold=True, color="#FFFFFF", bg=theme.SIDEBAR
        )
        self.overall_percent.pack(anchor="w", pady=(2, 4))
        self.overall_bar = widgets.progress_bar(
            footer, style="Sidebar.Horizontal.TProgressbar"
        )
        self.overall_bar.pack(fill="x", pady=(0, 6))
        self.overall_detail = widgets.mk_label(
            footer, "0 de 0 lecciones", size=8, color="#94A3B8", bg=theme.SIDEBAR
        )
        self.overall_detail.pack(anchor="w")
        self.level_detail = widgets.mk_label(
            footer, "Sin nivel elegido", size=9, color="#93C5FD", bg=theme.SIDEBAR
        )
        self.level_detail.pack(anchor="w", pady=(6, 0))

        self.content = tk.Frame(self, bg=theme.BG)
        self.content.pack(side="left", fill="both", expand=True)

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------

    def navigate(self, view_class, **kwargs) -> tk.Frame:
        if self.current_view is not None:
            self.current_view.destroy()
        self.current_view = view_class(self.content, self, **kwargs)
        self.current_view.pack(fill="both", expand=True)
        return self.current_view

    def _set_active(self, key: str) -> None:
        for name, item in self.nav_items.items():
            item.set_active(name == key)

    def _open_nav(self, key: str) -> None:
        if key == "welcome":
            self.open_welcome()
        elif key == "path":
            self.open_path()
        elif key == "library":
            self.open_library()
        elif key == "progress":
            self.open_progress()
        elif key == "about":
            self.open_about()

    def open_welcome(self) -> None:
        self.navigate(WelcomeView)
        self._set_active("welcome")

    def open_path(self, level_id: str | None = None) -> None:
        target = level_id or self.progress.level
        if target is None:
            self.open_welcome()
            return
        self.navigate(PathView, level_id=target)
        self._set_active("path")

    def open_lesson(self, lesson_id: str) -> None:
        lesson = self.repo.get_lesson(lesson_id)
        if lesson is None:
            messagebox.showerror("Lección no encontrada", f"No existe la lección «{lesson_id}».")
            return
        self.store.mark_started(self.progress, lesson_id)
        self.save_progress()
        self.refresh_shell()
        self.navigate(LessonView, lesson_id=lesson_id)
        self._set_active("path")

    def open_library(self) -> None:
        self.navigate(LibraryView)
        self._set_active("library")

    def open_progress(self) -> None:
        self.navigate(ProgressView)
        self._set_active("progress")

    def open_about(self) -> None:
        self.navigate(AboutView)
        self._set_active("about")

    def choose_level(self, level_id: str) -> None:
        if self.repo.get_level(level_id) is None:
            return
        self.store.set_level(self.progress, level_id)
        self.save_progress()
        self.refresh_shell()
        self.open_path(level_id)

    # ------------------------------------------------------------------
    # Estado y persistencia
    # ------------------------------------------------------------------

    def summary(self) -> dict:
        return self.store.summary(self.progress, self.repo.levels)

    def refresh_shell(self) -> None:
        summary = self.summary()
        overall = summary["overall"]
        self.overall_percent.configure(text=f"{overall['percent']}%")
        self.overall_bar["value"] = overall["percent"]
        self.overall_detail.configure(
            text=f"{overall['completed']} de {overall['total']} lecciones"
        )
        level = self.repo.get_level(self.progress.level or "")
        self.level_detail.configure(text=level.name if level else "Sin nivel elegido")

    def save_progress(self) -> None:
        try:
            self.store.save(self.progress)
            self._save_error_shown = False
        except OSError as exc:
            if not self._save_error_shown:
                self._save_error_shown = True
                messagebox.showerror(
                    "No se pudo guardar el progreso",
                    "La aplicación sigue funcionando, pero el progreso de esta sesión "
                    f"podría no conservarse.\n\n{exc}",
                    parent=self,
                )

    def _report_exception(self, exc_type, exc_value, traceback) -> None:
        messagebox.showerror(
            "Error inesperado",
            f"{exc_type.__name__}: {exc_value}\n\n"
            "El progreso guardado no se ha borrado. Puedes volver a abrir la aplicación.",
            parent=self,
        )

    def _on_close(self) -> None:
        self.save_progress()
        self.destroy()


def create_app() -> CodeCoreApp:
    return CodeCoreApp()
