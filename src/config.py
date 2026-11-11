"""Constantes globales de CodeCore.

Este módulo no importa nada del proyecto: puede usarse desde core, ui y tests.
"""

from __future__ import annotations

APP_NAME = "CodeCore"
APP_VERSION = "0.1.0"
SCHEMA_VERSION = 1

# Evaluación
PASS_SCORE = 70
SOLUTION_AFTER_ATTEMPTS = 3

# Ventana
WINDOW_TITLE = "CodeCore — Aprende a programar pensando"
WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 760
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 640

# Persistencia
PROGRESS_FILENAME = "progress.json"
APP_DATA_FOLDER = "CodeCore"

# Límites defensivos
MAX_ANSWER_LENGTH = 20_000
