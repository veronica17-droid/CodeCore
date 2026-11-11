"""Biblioteca local de recursos con búsqueda y filtros."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

from core.models import Resource
from ui import theme, widgets

TYPE_LABELS = {
    "doc": "Documentación",
    "libro": "Libro",
    "video": "Vídeo",
    "curso": "Curso",
    "herramienta": "Herramienta",
    "referencia": "Referencia",
}
LANGUAGE_LABELS = {
    "python": "Python",
    "javascript": "JavaScript",
    "web": "Web",
    "general": "General",
    "git": "Git",
}
LEVEL_LABELS = {
    "principiante": "Principiante",
    "intermedio": "Intermedio",
    "avanzado": "Avanzado",
    "todos": "Todos",
}
LEVEL_TO_ID = {
    "principiante": "beginner",
    "intermedio": "intermediate",
    "avanzado": "advanced",
}
ID_TO_LEVEL = {value: key for key, value in LEVEL_TO_ID.items()}


class LibraryView(tk.Frame):
    def __init__(self, parent: tk.Misc, app) -> None:
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.query_var = tk.StringVar()
        self.type_var = tk.StringVar(value="Todos")
        self.language_var = tk.StringVar(value="Todos")
        initial_level = ID_TO_LEVEL.get(app.progress.level or "", "todos")
        self.level_var = tk.StringVar(value=LEVEL_LABELS[initial_level])

        self._type_map = {"Todos": None}
        self._language_map = {"Todos": None}
        self._level_map = {"Todos": None}
        for key, label in TYPE_LABELS.items():
            self._type_map[label] = key
        for key, label in LANGUAGE_LABELS.items():
            self._language_map[label] = key
        for key, label in LEVEL_LABELS.items():
            self._level_map[label] = key

        header = tk.Frame(self, bg=theme.BG)
        header.pack(fill="x", padx=6, pady=(6, 0))
        widgets.mk_label(header, "BIBLIOTECA", size=9, bold=True, color=theme.ACCENT).pack(anchor="w")
        widgets.mk_label(header, "Recursos para seguir aprendiendo", size=24, bold=True).pack(anchor="w")
        widgets.mk_label(
            header,
            "Libros, vídeos y documentación oficial seleccionados. La búsqueda es local; "
            "los enlaces se abren en tu navegador y necesitan conexión.",
            size=10,
            color=theme.MUTED,
            wrap=860,
        ).pack(anchor="w", pady=(2, 14))

        self._build_filters()
        self.scroll = widgets.ScrollFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=6, pady=(8, 6))
        self.results = tk.Frame(self.scroll.inner, bg=theme.BG)
        self.results.pack(fill="both", expand=True)

        self.query_var.trace_add("write", lambda *_: self._refresh())
        self._refresh()

    # ------------------------------------------------------------------

    def _build_filters(self) -> None:
        card = widgets.Card(self, padding=14)
        card.pack(fill="x", padx=6)
        body = card.body

        grid = tk.Frame(body, bg=theme.SURFACE)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)

        search = tk.Frame(grid, bg=theme.SURFACE)
        search.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        widgets.mk_label(search, "BUSCAR", size=8, bold=True, color=theme.MUTED).pack(anchor="w")
        entry_row = tk.Frame(search, bg=theme.SURFACE)
        entry_row.pack(fill="x", pady=(3, 0))
        widgets.mk_label(entry_row, "⌕", size=13, color=theme.MUTED).pack(side="left")
        entry = tk.Entry(
            entry_row,
            textvariable=self.query_var,
            font=theme.font(10),
            bg=theme.SURFACE,
            fg=theme.TEXT,
            insertbackground=theme.TEXT,
            relief="solid",
            bd=1,
            highlightthickness=0,
        )
        entry.pack(side="left", fill="x", expand=True, padx=(4, 0), ipady=5)

        self._combo(grid, "TIPO", self.type_var, list(self._type_map), column=1)
        self._combo(grid, "LENGUAJE", self.language_var, list(self._language_map), column=2)
        self._combo(grid, "NIVEL", self.level_var, list(self._level_map), column=3)

    def _combo(self, parent, title: str, variable: tk.StringVar, values: list[str], column: int) -> None:
        frame = tk.Frame(parent, bg=theme.SURFACE)
        frame.grid(row=0, column=column, sticky="ew", padx=(0, 10))
        widgets.mk_label(frame, title, size=8, bold=True, color=theme.MUTED).pack(anchor="w")
        combo = ttk.Combobox(
            frame,
            textvariable=variable,
            values=values,
            state="readonly",
            width=15,
            font=theme.font(9),
        )
        combo.pack(fill="x", pady=(3, 0))
        combo.bind("<<ComboboxSelected>>", lambda _event: self._refresh())

    def _refresh(self) -> None:
        widgets.clear(self.results)
        results = self.app.repo.search_resources(
            query=self.query_var.get(),
            resource_type=self._type_map.get(self.type_var.get()),
            language=self._language_map.get(self.language_var.get()),
            level=self._level_map.get(self.level_var.get()),
        )

        widgets.mk_label(
            self.results,
            f"{len(results)} recurso{'s' if len(results) != 1 else ''}",
            size=9,
            bold=True,
            color=theme.MUTED,
        ).pack(anchor="w", pady=(0, 6))

        if not results:
            self._empty_state()
        else:
            for resource in results:
                self._resource_card(resource)

        self.scroll.bind_mousewheel()
        self.scroll.scroll_to_top()

    def _empty_state(self) -> None:
        card = widgets.Card(self.results, padding=28)
        card.pack(fill="x")
        widgets.mk_label(card.body, "No hay recursos con esos filtros.", size=13, bold=True).pack(anchor="w")
        widgets.mk_label(
            card.body,
            "Prueba con otra palabra o quita algún filtro. La búsqueda ignora mayúsculas y acentos.",
            size=10,
            color=theme.MUTED,
        ).pack(anchor="w", pady=(4, 12))
        widgets.mk_button(
            card.body,
            "Limpiar filtros",
            self._clear_filters,
            kind="secondary",
        ).pack(anchor="w")

    def _clear_filters(self) -> None:
        self.query_var.set("")
        self.type_var.set("Todos")
        self.language_var.set("Todos")
        self.level_var.set("Todos")
        self._refresh()

    def _resource_card(self, resource: Resource) -> None:
        card = widgets.Card(self.results, padding=16)
        card.pack(fill="x", pady=(0, 8))
        body = card.body

        columns = tk.Frame(body, bg=theme.SURFACE)
        columns.pack(fill="x")
        left = tk.Frame(columns, bg=theme.SURFACE)
        left.pack(side="left", fill="both", expand=True)

        badges = tk.Frame(left, bg=theme.SURFACE)
        badges.pack(anchor="w")
        widgets.Badge(badges, TYPE_LABELS.get(resource.type, resource.type)).pack(side="left")
        level_key = resource.level if resource.level != "todos" else "todos"
        level_bg, level_fg = widgets.level_color(LEVEL_TO_ID.get(level_key, ""))
        widgets.Badge(
            badges,
            LEVEL_LABELS.get(resource.level, resource.level),
            bg=level_bg,
            fg=level_fg,
        ).pack(side="left", padx=(5, 0))
        widgets.Badge(
            badges,
            LANGUAGE_LABELS.get(resource.language, resource.language),
            bg=theme.SURFACE_ALT,
            fg=theme.MUTED,
        ).pack(side="left", padx=(5, 0))
        if resource.free:
            widgets.Badge(badges, "Gratis", bg=theme.SUCCESS_BG, fg=theme.SUCCESS).pack(
                side="left", padx=(5, 0)
            )

        widgets.mk_label(left, resource.title, size=13, bold=True, wrap=720).pack(
            anchor="w", pady=(8, 1)
        )
        widgets.mk_label(left, resource.source, size=9, color=theme.MUTED).pack(anchor="w")
        widgets.mk_label(
            left, resource.description, size=10, color=theme.TEXT, wrap=720, justify="left"
        ).pack(anchor="w", pady=(6, 0))

        right = tk.Frame(columns, bg=theme.SURFACE)
        right.pack(side="right", padx=(18, 0))
        widgets.mk_button(
            right,
            "Abrir  ↗",
            lambda url=resource.url: self._open_url(url),
            kind="secondary",
            size=9,
            padx=14,
            pady=7,
        ).pack(anchor="e")

    def _open_url(self, url: str) -> None:
        try:
            webbrowser.open_new_tab(url)
        except Exception as exc:  # pragma: no cover - depende del navegador
            messagebox.showerror("No se pudo abrir el enlace", f"{url}\n\n{exc}")
