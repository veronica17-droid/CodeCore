"""Búsqueda local de recursos: insensible a mayúsculas y acentos."""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from core.models import Resource


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", plain.lower()).strip()


def filter_resources(
    resources: Iterable[Resource],
    query: str = "",
    resource_type: str | None = None,
    language: str | None = None,
    level: str | None = None,
) -> list[Resource]:
    """Filtra por texto y metadatos.

    - La consulta se divide en tokens; todos deben aparecer en el recurso.
    - ``level`` incluye los recursos marcados como «todos».
    - Los resultados cuyo título contiene la consulta completa van primero.
    """
    tokens = normalize(query).split()
    results: list[Resource] = []

    for resource in resources:
        if resource_type and resource.type != resource_type:
            continue
        if language and resource.language != language:
            continue
        if level and level != "todos" and resource.level not in (level, "todos"):
            continue
        haystack = normalize(
            " ".join(
                [
                    resource.title,
                    resource.description,
                    resource.source,
                    resource.type,
                    resource.language,
                    resource.level,
                ]
            )
        )
        if tokens and not all(token in haystack for token in tokens):
            continue
        results.append(resource)

    full_query = normalize(query)

    def sort_key(resource: Resource) -> tuple[int, str]:
        title = normalize(resource.title)
        if not full_query:
            return (0, title)
        title_match = 0 if full_query in title else 1
        all_tokens_in_title = 0 if all(token in title for token in tokens) else 1
        return (min(title_match, all_tokens_in_title), title)

    return sorted(results, key=sort_key)


def unique_values(resources: Iterable[Resource], attribute: str) -> list[str]:
    values = {
        str(getattr(resource, attribute))
        for resource in resources
        if getattr(resource, attribute, None)
    }
    return sorted(values)
