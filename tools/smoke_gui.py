"""Smoke test sin ventana visible para la interfaz de CodeCore.

Instancia la aplicación, recorre todas las vistas, abre las 13 lecciones y
recorre sus pasos. Se ejecuta en Windows con sesión gráfica:

    python tools/smoke_gui.py

No escribe en el progreso real: usa un archivo temporal.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.content import ContentRepository  # noqa: E402
from core.feedback import evaluate  # noqa: E402
from core.progress import ProgressStore  # noqa: E402


def check_solutions() -> int:
    """Cada solución de ejemplo debe superar sus propios checks."""
    repo = ContentRepository()
    failures = 0
    for lesson in repo.all_lessons():
        exercise = lesson.exercise
        if exercise.type == "choice":
            answer = next(option.id for option in exercise.options if option.correct)
        else:
            answer = exercise.solution
        result = evaluate(exercise, answer, attempt=3, level_id=lesson.level_id)
        if not result.passed:
            failures += 1
            print(f"[FALLO] {lesson.id}: {result.score}% — {result.summary}")
            for outcome in result.outcomes:
                if not outcome.ok:
                    print(f"         - {outcome.message}")
    print(f"Soluciones comprobadas: {len(repo.lessons)} | fallos: {failures}")
    return failures


def smoke_ui() -> int:
    import tkinter as tk

    from app import CodeCoreApp

    repo = ContentRepository()
    with tempfile.TemporaryDirectory() as tmp:
        store = ProgressStore(Path(tmp) / "progress.json")
        app = CodeCoreApp(repository=repo, store=store)
        app.withdraw()
        errors: list[str] = []

        def step(name: str, action) -> None:
            try:
                action()
                app.update_idletasks()
                app.update()
            except Exception as exc:  # noqa: BLE001 - el smoke test reporta todo
                errors.append(f"{name}: {type(exc).__name__}: {exc}")

        step("welcome", app.open_welcome)
        for level in repo.levels:
            step(f"choose_level({level.id})", lambda level_id=level.id: app.choose_level(level_id))
            step(f"path({level.id})", lambda level_id=level.id: app.open_path(level_id))

        step("library", app.open_library)
        step("progress", app.open_progress)
        step("about", app.open_about)

        # Recorrer cada lección y sus cuatro pasos.
        for lesson in repo.all_lessons():
            def visit(lesson_id=lesson.id) -> None:
                app.open_lesson(lesson_id)
                view = app.current_view
                for target in range(4):
                    view.go_to(target)
                    app.update_idletasks()
                    app.update()
                # Comprobar el flujo de evaluación con una respuesta válida.
                view.go_to(2)
                exercise = lesson.exercise
                if exercise.type == "code" and view.editor is not None:
                    view.editor.set_text(exercise.solution)
                elif exercise.type == "choice":
                    view.choice_var.set(
                        next(option.id for option in exercise.options if option.correct)
                    )
                elif exercise.type == "short" and view.answer_text is not None:
                    view.answer_text.delete("1.0", "end")
                    view.answer_text.insert("1.0", exercise.solution)
                view.evaluate()
                app.update_idletasks()
                app.update()

            step(f"lesson({lesson.id})", visit)

        step("final_welcome", app.open_welcome)
        app.destroy()

        if errors:
            print(f"Errores de interfaz: {len(errors)}")
            for error in errors:
                print(f"  [ERROR] {error}")
            return len(errors)
        print(f"Vistas y lecciones recorridas sin errores: {len(repo.lessons)} lecciones")
        return 0


def main() -> int:
    failures = check_solutions()
    try:
        ui_failures = smoke_ui()
    except Exception as exc:  # noqa: BLE001 - sin pantalla no se puede probar la GUI
        print(f"No se pudo abrir la interfaz (¿sin sesión gráfica?): {type(exc).__name__}: {exc}")
        return failures
    return failures + ui_failures


if __name__ == "__main__":
    raise SystemExit(main())
