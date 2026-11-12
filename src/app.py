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
from core.auth import AuthStore
from core.content import ContentRepository
from core.onboarding import nivel_a_nombre
from core.paths import resource_path, user_progress_file
from core.profile_store import ProfileStore
from core.progress import ProgressStore
from ui import theme, widgets
from ui.about_view import AboutView
from ui.achievements_view import AchievementsView
from ui.auth_view import AuthView
from ui.library_view import LibraryView
from ui.lesson_view import LessonView
from ui.onboarding_view import OnboardingView
from ui.path_view import PathView
from ui.progress_view import ProgressView
from ui.welcome_view import WelcomeView

NAV_ITEMS = (
    ("welcome", "Inicio"),
    ("path", "Mi ruta"),
    ("library", "Biblioteca"),
    ("progress", "Progreso"),
    ("achievements", "Medallas"),
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
        skip_auth: bool = False,
    ) -> None:
        super().__init__()
        self.repo = repository or ContentRepository()
        self.store = store
        self.skip_auth = skip_auth
        self.progress = None
        self.current_username = None
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

        if skip_auth:
            self._start_skip_auth_session()
        else:
            self._start_auth_flow()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Autenticación
    # ------------------------------------------------------------------

    def _start_auth_flow(self) -> None:
        """Muestra la pantalla de login/registro, o restaura la sesión guardada."""
        auth_store = AuthStore()
        saved_user = auth_store.current_user()
        if saved_user:
            # Sesión activa: carga el perfil del usuario y entra directamente.
            self._restore_user_session(saved_user)
        else:
            # Pantalla de login: sin barra lateral.
            self.hide_sidebar()
            self.navigate(AuthView, on_auth_success=self._on_auth_success)

    def _restore_user_session(self, username: str) -> None:
        """Carga el perfil y progreso de un usuario que ya tiene sesión guardada."""
        profile_store = ProfileStore()
        profile = profile_store.load(username)
        if profile and profile.survey_completed:
            self.current_username = username
            self.store = ProgressStore(path=user_progress_file(username))
            self.progress = self.store.load()
            # Aplica el nivel del perfil si el progreso no tiene uno.
            if self.progress.level is None and profile.level:
                self.store.set_level(self.progress, profile.level)
                self.save_progress()
            self.show_sidebar()
            self.navigate(WelcomeView)
            self._set_active("welcome")
            self.refresh_shell()
        else:
            # No hay perfil o no hizo encuesta: ir al login para crear uno.
            self.hide_sidebar()
            self.navigate(AuthView, on_auth_success=self._on_auth_success)

    def _on_auth_success(self, username: str, is_register: bool = False) -> None:
        """Tras login/registro exitoso.

        Si es registro nuevo (is_register=True), siempre muestra la encuesta.
        Si es login existente, solo muestra la encuesta si aún no la ha hecho.
        """
        self.auth_store = AuthStore()
        self.store = ProgressStore(path=user_progress_file(username))
        self.current_username = username

        profile_store = ProfileStore()
        profile = profile_store.load(username)

        if is_register:
            # Registro nuevo: siempre mostrar encuesta de onboarding.
            self.hide_sidebar()
            self.navigate(OnboardingView, username=username)
        elif profile and profile.survey_completed:
            # Login existente con encuesta ya hecha: entra directo a la app.
            self.progress = self.store.load()
            if self.progress.level is None and profile.level:
                self.store.set_level(self.progress, profile.level)
                self.save_progress()
            self.show_sidebar()
            self.navigate(WelcomeView)
            self._set_active("welcome")
            self.refresh_shell()
        else:
            # Login sin encuesta: mostrar encuesta de onboarding.
            self.hide_sidebar()
            self.navigate(OnboardingView, username=username)

    def on_onboarding_complete(self, username: str) -> None:
        """Tras completar la encuesta: carga progreso y abre Inicio."""
        profile_store = ProfileStore()
        profile = profile_store.load(username)
        if profile:
            self.current_username = username
            self.store = ProgressStore(path=user_progress_file(username))
            self.progress = self.store.load()
            # Aplica el nivel asignado por la encuesta al progreso.
            if self.progress.level is None and profile.level:
                self.store.set_level(self.progress, profile.level)
                self.save_progress()
            self.show_sidebar()
            self.navigate(WelcomeView)
            self._set_active("welcome")
            self.refresh_shell()

    def _start_skip_auth_session(self) -> None:
        """Modo sin auth (tests / smoke test): crea progreso temporal."""
        from core.paths import progress_file

        self.store = ProgressStore(path=progress_file())
        self.progress = self.store.load()
        self.current_username = "usuario"
        self.navigate(WelcomeView)
        self._set_active("welcome")
        self.refresh_shell()

    def logout(self) -> None:
        """Cierra la sesión y vuelve a la pantalla de auth."""
        if hasattr(self, "auth_store"):
            self.auth_store.logout()
        self.progress = None
        self.store = None
        self.current_username = None
        self.hide_sidebar()
        self._start_auth_flow()

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
        self.sidebar = tk.Frame(self, bg=theme.SIDEBAR, width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo = tk.Frame(self.sidebar, bg=theme.SIDEBAR)
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

        tk.Frame(self.sidebar, bg="#1E293B", height=1).pack(fill="x", padx=18)

        nav = tk.Frame(self.sidebar, bg=theme.SIDEBAR)
        nav.pack(fill="x", pady=(12, 0))
        for index, (key, label) in enumerate(NAV_ITEMS):
            item = NavItem(nav, label, lambda key=key: self._open_nav(key))
            item.pack(fill="x", pady=1)
            self.nav_items[key] = item
            self.bind(f"<Control-Key-{index + 1}>", lambda _event, key=key: self._open_nav(key))

        # Separador antes del footer
        tk.Frame(self.sidebar, bg="#1E293B", height=1).pack(fill="x", padx=18, pady=(22, 0))

        footer = tk.Frame(self.sidebar, bg=theme.SIDEBAR)
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

        # Usuario actual y cerrar sesión
        self.user_label = widgets.mk_label(
            footer, "Sin sesión", size=8, color="#94A3B8", bg=theme.SIDEBAR
        )
        self.user_label.pack(anchor="w", pady=(16, 2))
        widgets.mk_button(
            footer,
            "Cerrar sesión",
            self.logout,
            kind="ghost",
            size=9,
            padx=10,
            pady=6,
            width=16,
        ).pack(anchor="e")

        self.content = tk.Frame(self, bg=theme.BG)
        self.content.pack(side="left", fill="both", expand=True)

    def hide_sidebar(self) -> None:
        """Oculta la barra lateral y expande el contenido a todo el ancho."""
        self.sidebar.pack_forget()
        self.content.pack(side="left", fill="both", expand=True)

    def show_sidebar(self) -> None:
        """Restaura la barra lateral y el ancho normal del contenido."""
        self.content.pack_forget()
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
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
        elif key == "achievements":
            self.open_achievements()
        elif key == "about":
            self.open_about()

    def open_welcome(self) -> None:
        self.navigate(WelcomeView)
        self._set_active("welcome")

    def open_path(self, level_id: str | None = None) -> None:
        if self.progress is None:
            self.open_welcome()
            return
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

    def open_achievements(self) -> None:
        self.navigate(AchievementsView)
        self._set_active("achievements")

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
        if self.progress is None:
            return {"overall": {"completed": 0, "total": 0, "percent": 0}, "levels": []}
        return self.store.summary(self.progress, self.repo.levels)

    def refresh_shell(self) -> None:
        summary = self.summary()
        overall = summary["overall"]
        self.overall_percent.configure(text=f"{overall['percent']}%")
        self.overall_bar["value"] = overall["percent"]
        self.overall_detail.configure(
            text=f"{overall['completed']} de {overall['total']} lecciones"
        )
        if self.progress and self.progress.level:
            level = self.repo.get_level(self.progress.level)
            self.level_detail.configure(text=level.name if level else "Sin nivel elegido")
        else:
            self.level_detail.configure(text="Sin nivel elegido")

        if self.progress is not None:
            self.user_label.configure(text=self.current_username or "Usuario")
        else:
            self.user_label.configure(text="Sin sesión")

    def save_progress(self) -> None:
        if self.store is None or self.progress is None:
            return
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
