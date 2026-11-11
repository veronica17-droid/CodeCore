"""Resolución de rutas en desarrollo y dentro del .exe de PyInstaller."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from config import APP_DATA_FOLDER, PROGRESS_FILENAME


def project_root() -> Path:
    """Raíz del repositorio en modo desarrollo."""
    return Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    """Devuelve una ruta dentro de resources/.

    En desarrollo: <repo>/resources/...
    Empaquetado:   <sys._MEIPASS>/resources/... (datos extraídos por --onefile)
    """
    base = Path(getattr(sys, "_MEIPASS", project_root()))
    return base.joinpath("resources", *parts)


def app_data_dir() -> Path:
    """Carpeta de datos del usuario, escribible sin permisos de administrador."""
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / ".codecore"
    return base / APP_DATA_FOLDER


def progress_file() -> Path:
    return app_data_dir() / PROGRESS_FILENAME


def is_frozen() -> bool:
    """True cuando el programa corre desde un ejecutable de PyInstaller."""
    return bool(getattr(sys, "frozen", False))
