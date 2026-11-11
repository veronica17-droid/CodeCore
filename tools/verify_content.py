"""Valida el contenido local y la biblioteca sin abrir la interfaz.

Uso:
    python tools/verify_content.py
    python tools/verify_content.py --check-urls
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.content import ContentError, ContentRepository  # noqa: E402


def check_urls(repository: ContentRepository) -> int:
    """Comprueba que las URLs responden. Requiere conexión a internet."""
    import urllib.error
    import urllib.request

    failures = 0
    for resource in repository.resources:
        request = urllib.request.Request(
            resource.url,
            method="HEAD",
            headers={"User-Agent": "Mozilla/5.0 (CodeCore content check)"},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status = getattr(response, "status", 200)
            if status >= 400:
                print(f"[URL {status}] {resource.id}: {resource.url}")
                failures += 1
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            print(f"[URL ERROR] {resource.id}: {resource.url} -> {exc}")
            failures += 1
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida el contenido de CodeCore.")
    parser.add_argument(
        "--check-urls",
        action="store_true",
        help="Además del esquema, comprueba que las URLs responden.",
    )
    args = parser.parse_args()

    try:
        repository = ContentRepository()
    except ContentError as exc:
        print(f"ERROR DE CONTENIDO: {exc}")
        return 1

    print(f"Niveles:    {len(repository.levels)}")
    print(f"Lecciones:  {len(repository.lessons)}")
    print(f"Recursos:   {len(repository.resources)}")

    for level in repository.levels:
        lessons = repository.lessons_for_level(level.id)
        print(f"  - {level.name}: {len(lessons)} lecciones")

    missing = repository.missing_resource_ids()
    if missing:
        if not repository.resources:
            print("AVISO: la biblioteca todavía no está creada (Fase 4); "
                  f"{len(missing)} recursos referenciados quedan pendientes.")
        else:
            print(f"ERROR: recursos referenciados que no existen: {', '.join(sorted(missing))}")
            return 1

    if args.check_urls:
        if not repository.resources:
            print("No hay biblioteca que comprobar.")
        else:
            failures = check_urls(repository)
            if failures:
                print(f"ERROR: {failures} URL(s) no responden.")
                return 1
            print(f"URLs comprobadas: {len(repository.resources)}")

    print("Contenido OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
