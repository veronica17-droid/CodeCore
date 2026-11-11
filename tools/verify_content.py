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


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _request_status(url: str, method: str) -> int:
    import urllib.request

    request = urllib.request.Request(
        url,
        method=method,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return getattr(response, "status", 200)


def check_urls(repository: ContentRepository) -> int:
    """Comprueba que las URLs responden. Requiere conexión a internet.

    Algunos servidores rechazan HEAD con 403/405; en ese caso se reintenta con
    GET antes de dar la URL por fallida.
    """
    import urllib.error

    failures = 0
    for resource in repository.resources:
        status: int | None = None
        error: object | None = None
        for method in ("HEAD", "GET"):
            try:
                status = _request_status(resource.url, method)
                error = None
                break
            except urllib.error.HTTPError as exc:
                status = exc.code
                error = exc
                if exc.code not in (403, 405, 501):
                    break
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                status = None
                error = exc
                break
        if status is None or status >= 400:
            print(f"[URL ERROR {status}] {resource.id}: {resource.url} -> {error}")
            failures += 1
        else:
            print(f"[URL {status}] {resource.id}")
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
