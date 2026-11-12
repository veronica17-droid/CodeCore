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


def user_progress_file(username: str) -> Path:
    """Ruta del progreso de un usuario concreto."""
    return app_data_dir() / "users" / username / PROGRESS_FILENAME


def users_file() -> Path:
    return app_data_dir() / "users.json"


def session_file() -> Path:
    return app_data_dir() / "session.json"


def is_frozen() -> bool:
    """True cuando el programa corre desde un ejecutable de PyInstaller."""
    return bool(getattr(sys, "frozen", False))
