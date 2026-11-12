"""Sistema de medallas y logros de CodeCore.

Cada medalla tiene un identificador único, un nombre, una descripción y una
función que determina si el usuario la ha ganado basándose en su progreso.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from core.models import Progress


@dataclass(frozen=True)
class Achievement:
    id: str
    name: str
    description: str
    icon: str  # emoji o símbolo
    condition: Callable[[Progress], bool]


# --------------------------------------------------------------------------
# Definición de medallas
# --------------------------------------------------------------------------

ACHIEVEMENTS: tuple[Achievement, ...] = (
    Achievement(
        id="primeros_pasos",
        name="Primeros pasos",
        description="Completa tu primera lección.",
        icon="👣",
        condition=lambda progress: any(
            item.status == "completed" for item in progress.lessons.values()
        ),
    ),
    Achievement(
        id="constante",
        name="Constante",
        description="Completa 5 lecciones.",
        icon="🔥",
        condition=lambda progress: sum(
            1 for item in progress.lessons.values() if item.status == "completed"
        )
        >= 5,
    ),
    Achievement(
        id="nivel_dominado",
        name="Nivel dominado",
        description="Completa todas las lecciones de un nivel.",
        icon="🏆",
        condition=lambda progress: any(
            all(
                progress.lessons.get(lesson_id, None)
                and progress.lessons[lesson_id].status == "completed"
                for lesson_id in lesson_ids
            )
            for lesson_ids in (
                ["beg_01_orden", "beg_02_variables", "beg_03_decisiones",
                 "beg_04_bucles", "beg_05_funciones", "beg_06_tipos_datos",
                 "beg_07_listas_basicas", "beg_08_texto", "beg_09_while"],
                ["int_01_listas", "int_02_diccionarios", "int_03_descomponer",
                 "int_04_depurar", "int_05_listas_comprension",
                 "int_06_funciones_avanzadas", "int_07_modulos",
                 "int_08_manejo_errores"],
                ["adv_01_recursion", "adv_02_complejidad", "adv_03_errores",
                 "adv_04_diseno", "adv_05_poo", "adv_06_archivos",
                 "adv_07_algoritmos_basicos", "adv_08_testing"],
            )
        ),
    ),
    Achievement(
        id="persistente",
        name="Persistente",
        description="Haz 5 intentos en una sola lección sin rendirte.",
        icon="💪",
        condition=lambda progress: any(
            item.attempts >= 5 for item in progress.lessons.values()
        ),
    ),
    Achievement(
        id="rapido",
        name="Rápido",
        description="Completa una lección en el primer intento.",
        icon="⚡",
        condition=lambda progress: any(
            item.status == "completed" and item.attempts == 1
            for item in progress.lessons.values()
        ),
    ),
    Achievement(
        id="explorador",
        name="Explorador",
        description="Prueba al menos una lección de cada nivel.",
        icon="🧭",
        condition=lambda progress: any(
            progress.lessons.get(lid, None)
            and progress.lessons[lid].status in ("in_progress", "completed")
            for lid in ["beg_01_orden", "beg_02_variables", "beg_03_decisiones"]
        )
        and any(
            progress.lessons.get(lid, None)
            and progress.lessons[lid].status in ("in_progress", "completed")
            for lid in ["int_01_listas", "int_02_diccionarios"]
        )
        and any(
            progress.lessons.get(lid, None)
            and progress.lessons[lid].status in ("in_progress", "completed")
            for lid in ["adv_01_recursion", "adv_02_complejidad"]
        ),
    ),
)


def get_achievements() -> tuple[Achievement, ...]:
    return ACHIEVEMENTS


def earned_achievements(progress: Progress) -> tuple[Achievement, ...]:
    """Devuelve las medallas que el usuario ha ganado según su progreso."""
    return tuple(a for a in ACHIEVEMENTS if a.condition(progress))
