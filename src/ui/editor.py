"""Editor de código sencillo: números de línea, indentación y resaltado básico."""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk

from ui import theme

_TOKEN_PATTERN = re.compile(
    r"(?P<comment>#[^\n]*)"
    r"|(?P<string>\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''"
    r"|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*')"
    r"|(?P<keyword>\b(?:def|return|if|elif|else|for|while|in|range|print|import|from|as|"
    r"try|except|finally|with|class|True|False|None|and|or|not|is|lambda|pass|break|"
    r"continue|raise|yield|global|nonlocal|assert|del)\b)"
    r"|(?P<number>\b\d+(?:\.\d+)?\b)"
)


class CodeEditor(tk.Frame):
    def __init__(self, parent: tk.Misc, *, height: int = 14) -> None:
        super().__init__(parent, bg=theme.CODE_BG, highlightthickness=1, highlightbackground="#1E293B")
        self.lines = tk.Text(
            self,
            width=4,
            height=height,
            bg="#0B1220",
            fg="#64748B",
            font=theme.font(11, mono=True),
            bd=0,
            padx=8,
            pady=10,
            takefocus=0,
            state="disabled",
            cursor="arrow",
        )
        self.lines.pack(side="left", fill="y")

        self.text = tk.Text(
            self,
            height=height,
            bg=theme.CODE_BG,
            fg=theme.CODE_FG,
            insertbackground="#FFFFFF",
            selectbackground="#334155",
            selectforeground="#FFFFFF",
            font=theme.font(11, mono=True),
            bd=0,
            padx=12,
            pady=10,
            undo=True,
            wrap="none",
            tabs=("4c",),
        )
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=self._on_yscroll)
        self.text.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.text.tag_configure("keyword", foreground=theme.CODE_KEYWORD)
        self.text.tag_configure("string", foreground=theme.CODE_STRING)
        self.text.tag_configure("comment", foreground=theme.CODE_COMMENT)
        self.text.tag_configure("number", foreground=theme.CODE_NUMBER)

        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<Tab>", self._on_tab)
        self.text.bind("<Shift-Tab>", self._on_shift_tab)
        self.text.bind("<Return>", self._on_return)

        self._highlight_job: str | None = None
        self._update_line_numbers()
        self.text.edit_modified(False)

    # -- API --------------------------------------------------------------

    def get_text(self) -> str:
        return self.text.get("1.0", "end-1c")

    def set_text(self, value: str) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)
        self.text.edit_reset()
        self.text.edit_modified(False)
        self._highlight()
        self._update_line_numbers()
        self.text.mark_set("insert", "1.0")

    def focus_editor(self) -> None:
        self.text.focus_set()

    def destroy(self) -> None:
        if self._highlight_job is not None:
            try:
                self.after_cancel(self._highlight_job)
            except tk.TclError:
                pass
            self._highlight_job = None
        super().destroy()

    # -- eventos ----------------------------------------------------------

    def _on_yscroll(self, first: str, last: str) -> None:
        self.scrollbar.set(first, last)
        self.lines.yview_moveto(first)

    def _on_modified(self, _event=None) -> None:
        if not self.text.edit_modified():
            return
        self.text.edit_modified(False)
        self._update_line_numbers()
        if self._highlight_job is not None:
            self.after_cancel(self._highlight_job)
        self._highlight_job = self.after(120, self._highlight)

    def _on_tab(self, _event=None):
        self.text.insert("insert", "    ")
        return "break"

    def _on_shift_tab(self, _event=None):
        index = self.text.index("insert")
        line_start = self.text.index(f"{index} linestart")
        prefix = self.text.get(line_start, index)
        remove = min(4, len(prefix) - len(prefix.lstrip(" ")))
        if remove:
            self.text.delete(f"{index} -{remove}c", index)
        return "break"

    def _on_return(self, _event=None):
        index = self.text.index("insert")
        line = self.text.get(f"{index} linestart", index)
        indent = re.match(r"[ \t]*", line).group(0)
        if line.rstrip().endswith(":"):
            indent += "    "
        self.text.insert("insert", "\n" + indent)
        self.text.see("insert")
        return "break"

    # -- pintado ----------------------------------------------------------

    def _update_line_numbers(self) -> None:
        if not self.text.winfo_exists():
            return
        line_count = int(self.text.index("end-1c").split(".")[0])
        numbers = "\n".join(str(number) for number in range(1, line_count + 1))
        self.lines.configure(state="normal")
        self.lines.delete("1.0", "end")
        self.lines.insert("1.0", numbers)
        self.lines.configure(state="disabled")
        self.lines.yview_moveto(self.text.yview()[0])

    def _highlight(self) -> None:
        self._highlight_job = None
        if not self.text.winfo_exists():
            return
        code = self.text.get("1.0", "end-1c")
        for tag in ("keyword", "string", "comment", "number"):
            self.text.tag_remove(tag, "1.0", "end")
        for match in _TOKEN_PATTERN.finditer(code):
            tag = match.lastgroup
            if tag is None:
                continue
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add(tag, start, end)
