"""Punto de entrada de CodeCore.

Uso:
    python src/main.py
    python src/main.py --version
    python src/main.py --selftest
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import APP_VERSION  # noqa: E402


def _selftest() -> int:
    lines = [f"CodeCore {APP_VERSION}"]
    try:
        import tkinter

        lines.append(f"tkinter: {tkinter.TkVersion}")

        from core.content import ContentRepository
        from core.progress import ProgressStore

        repo = ContentRepository()
        store = ProgressStore()
        progress = store.load()
        summary = store.summary(progress, repo.levels)
        lines.append(f"niveles: {len(repo.levels)}")
        lines.append(f"lecciones: {len(repo.lessons)}")
        lines.append(f"recursos: {len(repo.resources)}")
        lines.append(
            "progreso: "
            f"{summary['overall']['completed']}/{summary['overall']['total']} lecciones"
        )
        missing = repo.missing_resource_ids()
        if missing:
            lines.append(f"recursos pendientes: {len(missing)}")
        lines.append("SELFTEST OK")
        code = 0
    except Exception as exc:  # noqa: BLE001 - el selftest debe reportar cualquier fallo
        lines.append(f"SELFTEST ERROR: {type(exc).__name__}: {exc}")
        code = 1

    text = "\n".join(lines)
    print(text)
    if getattr(sys, "frozen", False):
        try:
            (Path.cwd() / "CodeCore-selftest.txt").write_text(text + "\n", encoding="utf-8")
        except OSError:
            pass
    return code


def _fatal(title: str, message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except Exception:  # pragma: no cover - sin pantalla disponible
        print(f"{title}: {message}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--version" in args:
        print(APP_VERSION)
        return 0
    if "--selftest" in args:
        return _selftest()

    from core.content import ContentError

    try:
        from app import CodeCoreApp

        application = CodeCoreApp()
    except ContentError as exc:
        _fatal("El contenido de CodeCore está dañado", str(exc))
        return 1
    except Exception as exc:  # noqa: BLE001 - arranque: mejor un aviso que un cierre seco
        _fatal("No se pudo iniciar CodeCore", f"{type(exc).__name__}: {exc}")
        return 1

    application.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
