from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401

from core.models import Resource
from core.search import filter_resources, normalize, unique_values


def resource(**overrides) -> Resource:
    base = {
        "id": "res_x",
        "title": "Título",
        "type": "doc",
        "url": "https://example.com",
        "level": "todos",
        "language": "python",
        "source": "Fuente",
        "description": "Descripción",
        "free": True,
    }
    base.update(overrides)
    return Resource(**base)


class SearchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.resources = [
            resource(id="r1", title="Documentación oficial de Python", language="python"),
            resource(
                id="r2",
                title="Depuración en Python",
                type="video",
                language="python",
                level="principiante",
            ),
            resource(
                id="r3",
                title="Eloquent JavaScript",
                type="libro",
                language="javascript",
                level="intermedio",
            ),
            resource(id="r4", title="Guía de Git", language="git", description="Control de versiones"),
        ]

    def test_normalize_removes_accents_and_case(self) -> None:
        self.assertEqual(normalize("  Depuración  ÚTIL "), "depuracion util")

    def test_search_without_accents_finds_accented_title(self) -> None:
        results = filter_resources(self.resources, query="depuracion")
        self.assertEqual([item.id for item in results], ["r2"])

    def test_filter_by_type(self) -> None:
        results = filter_resources(self.resources, resource_type="video")
        self.assertEqual([item.id for item in results], ["r2"])

    def test_filter_by_language(self) -> None:
        results = filter_resources(self.resources, language="javascript")
        self.assertEqual([item.id for item in results], ["r3"])

    def test_filter_by_level_includes_general_resources(self) -> None:
        results = filter_resources(self.resources, level="principiante")
        self.assertEqual({item.id for item in results}, {"r1", "r2", "r4"})

    def test_query_and_filter_combine(self) -> None:
        results = filter_resources(self.resources, query="python", language="javascript")
        self.assertEqual(results, [])

    def test_title_matches_sort_first(self) -> None:
        results = filter_resources(self.resources, query="python")
        self.assertEqual([item.id for item in results], ["r2", "r1"])

    def test_unknown_query_returns_empty(self) -> None:
        self.assertEqual(filter_resources(self.resources, query="cobol"), [])

    def test_unique_values(self) -> None:
        self.assertEqual(unique_values(self.resources, "language"), ["git", "javascript", "python"])


if __name__ == "__main__":
    unittest.main()
