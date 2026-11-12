"""Componentes reutilizables de la interfaz."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui import theme


def mk_label(
    parent: tk.Misc,
    text: str,
    *,
    size: int = 10,
    bold: bool = False,
    color: str = theme.TEXT,
    bg: str | None = None,
    wrap: int = 0,
    justify: str = "left",
    anchor: str = "w",
    mono: bool = False,
    **kwargs,
) -> tk.Label:
    return tk.Label(
        parent,
        text=text,
        font=theme.font(size, bold, mono),
        fg=color,
        bg=bg if bg is not None else parent.cget("bg"),
        wraplength=wrap,
        justify=justify,
        anchor=anchor,
        **kwargs,
    )


_BUTTON_KINDS = {
    "primary": (theme.ACCENT, "#FFFFFF", theme.ACCENT_HOVER, theme.ACCENT),
    "success": (theme.SUCCESS, "#FFFFFF", "#166534", theme.SUCCESS),
    "danger": (theme.DANGER, "#FFFFFF", "#991B1B", theme.DANGER),
    "secondary": (theme.SURFACE, theme.TEXT, theme.SURFACE_ALT, theme.BORDER),
    "ghost": (None, theme.ACCENT, theme.ACCENT_SOFT, None),
    "sidebar": (theme.SIDEBAR, "#CBD5E1", theme.SIDEBAR_HOVER, None),
    "sidebar_active": (theme.SIDEBAR_ACTIVE, "#FFFFFF", theme.SIDEBAR_ACTIVE, None),
}


def mk_button(
    parent: tk.Misc,
    text: str,
    command,
    *,
    kind: str = "primary",
    size: int = 10,
    bold: bool = True,
    padx: int = 14,
    pady: int = 8,
    width: int | None = None,
    **kwargs,
) -> tk.Button:
    bg, fg, hover, border = _BUTTON_KINDS[kind]
    if bg is None:
        bg = parent.cget("bg")
    button = tk.Button(
        parent,
        text=text,
        command=command,
        font=theme.font(size, bold),
        bg=bg,
        fg=fg,
        activebackground=hover,
        activeforeground=fg,
        relief="flat",
        bd=0,
        highlightthickness=1 if border else 0,
        highlightbackground=border or bg,
        highlightcolor=border or bg,
        cursor="hand2",
        padx=padx,
        pady=pady,
        width=width,
        **kwargs,
    )

    def on_enter(_event) -> None:
        button.configure(bg=hover)

    def on_leave(_event) -> None:
        button.configure(bg=bg)

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    return button


class Card(tk.Frame):
    """Panel blanco con borde suave y padding interno."""

    def __init__(self, parent: tk.Misc, padding: int = 18, **kwargs) -> None:
        super().__init__(
            parent,
            bg=theme.SURFACE,
            highlightbackground=theme.BORDER,
            highlightthickness=1,
            bd=0,
            **kwargs,
        )
        self.body = tk.Frame(self, bg=theme.SURFACE)
        self.body.pack(fill="both", expand=True, padx=padding, pady=padding)


class Badge(tk.Label):
    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        *,
        bg: str = theme.ACCENT_SOFT,
        fg: str = theme.ACCENT,
        size: int = 8,
    ) -> None:
        super().__init__(
            parent,
            text=text.upper(),
            font=theme.font(size, True),
            bg=bg,
            fg=fg,
            padx=7,
            pady=2,
        )


def divider(parent: tk.Misc, color: str = theme.BORDER, pady: int = 10) -> tk.Frame:
    line = tk.Frame(parent, bg=color, height=1)
    line.pack(fill="x", pady=pady)
    return line


class ScrollFrame(tk.Frame):
    """Área desplazable vertical con canvas + scrollbar."""

    def __init__(self, parent: tk.Misc, bg: str = theme.BG) -> None:
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_inner_configure(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self.canvas.itemconfigure(self._window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def bind_mousewheel(self) -> None:
        """Propaga la rueda a todos los hijos ya construidos."""
        for widget in self._descendants(self.inner):
            widget.bind("<MouseWheel>", self._on_mousewheel, add="+")

    def _descendants(self, widget: tk.Misc):
        for child in widget.winfo_children():
            yield child
            yield from self._descendants(child)

    def scroll_to_top(self) -> None:
        self.canvas.yview_moveto(0)


def clear(widget: tk.Misc) -> None:
    for child in widget.winfo_children():
        child.destroy()


def progress_bar(parent: tk.Misc, *, style: str = "Accent.Horizontal.TProgressbar") -> ttk.Progressbar:
    return ttk.Progressbar(parent, style=style, maximum=100, mode="determinate")


def mk_entry_styled(
    parent: tk.Misc,
    *,
    placeholder: str = "",
    show: str = "",
) -> tk.Entry:
    """Entry con texto de placeholder y estilo consistente con la app."""
    entry = tk.Entry(
        parent,
        font=theme.font(11),
        bg=theme.SURFACE,
        fg=theme.MUTED,
        insertbackground=theme.TEXT,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=theme.BORDER,
        highlightcolor=theme.ACCENT,
        show=show,
    )
    entry.insert(0, placeholder)
    entry._placeholder = placeholder
    entry._has_placeholder = True

    def on_focus_in(_event) -> None:
        if entry._has_placeholder:
            entry.delete(0, "end")
            entry.configure(fg=theme.TEXT)
            entry._has_placeholder = False

    def on_focus_out(_event) -> None:
        if not entry.get():
            entry.insert(0, entry._placeholder)
            entry.configure(fg=theme.MUTED)
            entry._has_placeholder = True

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    return entry


def status_badge(parent: tk.Misc, status: str, best_score: int = 0) -> Badge:
    if status == "completed":
        return Badge(parent, f"Completada · {best_score}%", bg=theme.SUCCESS_BG, fg=theme.SUCCESS)
    if status == "in_progress":
        return Badge(parent, "En progreso", bg=theme.WARNING_BG, fg=theme.WARNING)
    return Badge(parent, "Sin empezar", bg=theme.SURFACE_ALT, fg=theme.MUTED)


def level_color(level_id: str) -> tuple[str, str]:
    return {
        "beginner": (theme.SUCCESS_BG, theme.SUCCESS),
        "intermediate": (theme.WARNING_BG, theme.WARNING),
        "advanced": (theme.ACCENT_SOFT, theme.ACCENT),
    }.get(level_id, (theme.SURFACE_ALT, theme.MUTED))
