"""Modelo de datos para la encuesta de onboarding y perfiles de usuario.

Cada pregunta tiene opciones con un puntaje asociado. El total determina
el nivel inicial del usuario al crear su cuenta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SurveyOption:
    id: str
    text: str
    score: int  # puntos que suma a la experiencia del usuario


@dataclass(frozen=True)
class SurveyQuestion:
    id: str
    text: str
    options: tuple[SurveyOption, ...]


@dataclass
class UserProfile:
    username: str
    level: str = "beginner"  # beginner / intermediate / advanced
    survey_completed: bool = False
    survey_score: int = 0
    topics_of_interest: tuple[str, ...] = ()
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "username": self.username,
            "level": self.level,
            "survey_completed": self.survey_completed,
            "survey_score": self.survey_score,
            "topics_of_interest": list(self.topics_of_interest),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "UserProfile":
        return UserProfile(
            username=data.get("username", ""),
            level=data.get("level", "beginner"),
            survey_completed=bool(data.get("survey_completed", False)),
            survey_score=int(data.get("survey_score", 0)),
            topics_of_interest=tuple(data.get("topics_of_interest", [])),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


# ------------------------------------------------------------------
# Encuesta de onboarding (7 preguntas)
# ------------------------------------------------------------------

SURVEY_QUESTIONS: tuple[SurveyQuestion, ...] = (
    SurveyQuestion(
        id="q1_experiencia",
        text="¿Cuál es tu experiencia previa programando?",
        options=(
            SurveyOption("nunca", "Nunca he programado", 0),
            SurveyOption("poco", "He visto poco o hice algún tutorial", 1),
            SurveyOption("medio", "Sé lo básico y he escrito algún código", 2),
            SurveyOption("avanzado", "Programo con regularidad", 3),
        ),
    ),
    SurveyQuestion(
        id="q2_conocimiento_basico",
        text="¿Sabes qué son las variables y los tipos de dato?",
        options=(
            SurveyOption("no", "No lo sé", 0),
            SurveyOption("basico", "Lo he oído pero no lo uso", 1),
            SurveyOption("si", "Sí, las uso con regularidad", 2),
        ),
    ),
    SurveyQuestion(
        id="q3_estructuras_control",
        text="¿Has usado condicionales (if/else) y bucles (for/while)?",
        options=(
            SurveyOption("no", "No", 0),
            SurveyOption("basico", "He visto ejemplos", 1),
            SurveyOption("si", "Sí, los uso en mis programas", 2),
        ),
    ),
    SurveyQuestion(
        id="q4_funciones",
        text="¿Has creado tus propias funciones o procedimientos?",
        options=(
            SurveyOption("no", "No", 0),
            SurveyOption("basico", "He visto cómo se definen", 1),
            SurveyOption("si", "Sí, las escribo yo mismo", 2),
        ),
    ),
    SurveyQuestion(
        id="q5_estructuras_datos",
        text="¿Conoces listas, diccionarios o arreglos?",
        options=(
            SurveyOption("no", "No", 0),
            SurveyOption("basico", "He oído hablar de ellos", 1),
            SurveyOption("si", "Sí, los uso", 2),
        ),
    ),
    SurveyQuestion(
        id="q6_depuracion",
        text="¿Sabes qué es depurar (debuggear) un programa?",
        options=(
            SurveyOption("no", "No", 0),
            SurveyOption("basico", "He oído el término", 1),
            SurveyOption("si", "Sí, encuentro y corrijo errores", 2),
        ),
    ),
    SurveyQuestion(
        id="q7_objetivos",
        text="¿Qué te gustaría aprender primero?",
        options=(
            SurveyOption("basico", "Fundamentos de programación", 0),
            SurveyOption("web", "Desarrollo web", 1),
            SurveyOption("datos", "Análisis de datos", 1),
            SurveyOption("avanzado", "Estructuras de datos y algoritmos", 2),
        ),
    ),
)


def calcular_nivel(puntaje_total: int) -> str:
    """Devuelve el nivel inicial según el puntaje total de la encuesta."""
    if puntaje_total <= 4:
        return "beginner"
    if puntaje_total <= 9:
        return "intermediate"
    return "advanced"


def nivel_a_nombre(nivel_id: str) -> str:
    return {
        "beginner": "Principiante",
        "intermediate": "Intermedio",
        "advanced": "Avanzado",
    }.get(nivel_id, "Principiante")
