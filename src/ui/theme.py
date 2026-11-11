"""Paleta, tipografía y estilos ttk de CodeCore."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# Paleta
BG = "#F5F7FB"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#EEF2F8"
SIDEBAR = "#101828"
SIDEBAR_HOVER = "#1D2939"
SIDEBAR_ACTIVE = "#243B63"
ACCENT = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
ACCENT_SOFT = "#DBEAFE"
TEXT = "#101828"
MUTED = "#667085"
BORDER = "#E4E7EC"
SUCCESS = "#15803D"
SUCCESS_BG = "#DCFCE7"
WARNING = "#B45309"
WARNING_BG = "#FEF3C7"
DANGER = "#B91C1C"
DANGER_BG = "#FEE2E2"
CODE_BG = "#0F172A"
CODE_FG = "#E2E8F0"
CODE_KEYWORD = "#7DD3FC"
CODE_STRING = "#86EFAC"
CODE_COMMENT = "#94A3B8"
CODE_NUMBER = "#FCA5A5"

FONT = "Segoe UI"
MONO = "Consolas"


def font(size: int = 10, bold: bool = False, mono: bool = False) -> tuple:
    family = MONO if mono else FONT
    return (family, size, "bold") if bold else (family, size)


def apply_theme(root: tk.Misc) -> None:
    root.configure(bg=BG)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=BG, foreground=TEXT, font=font(10))
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=SURFACE)
    style.configure("Sidebar.TFrame", background=SIDEBAR)
    style.configure("TLabel", background=BG, foreground=TEXT, font=font(10))
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=font(9))
    style.configure(
        "Accent.Horizontal.TProgressbar",
        troughcolor=SURFACE_ALT,
        background=ACCENT,
        borderwidth=0,
        thickness=8,
    )
    style.configure(
        "Success.Horizontal.TProgressbar",
        troughcolor=SURFACE_ALT,
        background=SUCCESS,
        borderwidth=0,
        thickness=8,
    )
    style.configure(
        "Sidebar.Horizontal.TProgressbar",
        troughcolor="#243B63",
        background="#60A5FA",
        borderwidth=0,
        thickness=6,
    )
    style.configure(
        "TCombobox",
        fieldbackground=SURFACE,
        background=SURFACE,
        foreground=TEXT,
        bordercolor=BORDER,
        arrowcolor=MUTED,
        padding=5,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", SURFACE)],
        selectbackground=[("readonly", SURFACE)],
        selectforeground=[("readonly", TEXT)],
    )
    style.configure(
        "TEntry",
        fieldbackground=SURFACE,
        foreground=TEXT,
        bordercolor=BORDER,
        insertcolor=TEXT,
        padding=6,
    )
    style.configure(
        "TRadiobutton",
        background=SURFACE,
        foreground=TEXT,
        font=font(10),
        padding=4,
    )
    style.map(
        "TRadiobutton",
        background=[("active", SURFACE)],
        foreground=[("active", ACCENT)],
    )
    style.configure("Vertical.TScrollbar", background=SURFACE_ALT, troughcolor=BG, borderwidth=0)
