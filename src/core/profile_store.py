"""Almacenamiento de perfiles de usuario (nivel, encuesta, temas de interés).

Se guarda en la carpeta de datos del usuario (profiles/<username>.json).
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from core.onboarding import UserProfile, calcular_nivel
from core.paths import app_data_dir


class ProfileStore:
    def __init__(self, profiles_dir: Path | None = None) -> None:
        self.profiles_dir = Path(profiles_dir) if profiles_dir else app_data_dir() / "profiles"

    def _path_for(self, username: str) -> Path:
        return self.profiles_dir / f"{username}.json"

    def load(self, username: str) -> UserProfile | None:
        path = self._path_for(username)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return UserProfile.from_dict(data)
        except (OSError, ValueError, TypeError):
            return None

    def save(self, profile: UserProfile) -> None:
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        path = self._path_for(profile.username)
        profile.updated_at = datetime.now().isoformat()
        if not profile.created_at:
            profile.created_at = profile.updated_at
        temporary = path.with_name(path.name + ".tmp")
        payload = json.dumps(profile.to_dict(), ensure_ascii=False, indent=2)
        temporary.write_text(payload + "\n", encoding="utf-8")
        os.replace(temporary, path)

    def create_from_survey(
        self,
        username: str,
        answers: dict[str, str],
    ) -> UserProfile:
        """Crea un perfil calculando el nivel a partir de las respuestas de la encuesta."""
        from core.onboarding import SURVEY_QUESTIONS

        score = 0
        for question in SURVEY_QUESTIONS:
            option_id = answers.get(question.id)
            if not option_id:
                continue
            for option in question.options:
                if option.id == option_id:
                    score += option.score
                    break

        level = calcular_nivel(score)
        profile = UserProfile(
            username=username,
            level=level,
            survey_completed=True,
            survey_score=score,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        self.save(profile)
        return profile
