"""Gestión de usuarios local: registro, inicio de sesión y contraseñas.

Todo se guarda en la carpeta de datos del usuario (users.json y session.json).
Las contraseñas nunca se almacenan en texto plano: se usa PBKDF2-HMAC-SHA256.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any

from core.paths import session_file, users_file


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    )
    return dk.hex(), salt


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    dk, _ = _hash_password(password, salt)
    return dk == stored_hash


class AuthStore:
    def __init__(
        self,
        users_path: Path | None = None,
        session_path: Path | None = None,
    ) -> None:
        self.users_path = Path(users_path) if users_path else users_file()
        self.session_path = Path(session_path) if session_path else session_file()

    # -- usuarios -----------------------------------------------------------

    def load_users(self) -> dict[str, dict[str, Any]]:
        if not self.users_path.exists():
            return {}
        try:
            data = json.loads(self.users_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError, TypeError):
            return {}

    def save_users(self, users: dict[str, dict[str, Any]]) -> None:
        self.users_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.users_path.with_name(self.users_path.name + ".tmp")
        payload = json.dumps(users, ensure_ascii=False, indent=2)
        temporary.write_text(payload + "\n", encoding="utf-8")
        os.replace(temporary, self.users_path)

    def register(self, username: str, password: str) -> tuple[bool, str]:
        """Crea una cuenta. Devuelve (ok, mensaje)."""
        username = username.strip()
        if not username or not password:
            return False, "Usuario y contraseña son requeridos."
        if len(username) < 3:
            return False, "El usuario debe tener al menos 3 caracteres."
        if len(password) < 4:
            return False, "La contraseña debe tener al menos 4 caracteres."

        users = self.load_users()
        if username in users:
            return False, "El usuario ya existe."

        pw_hash, salt = _hash_password(password)
        users[username] = {
            "created_at": datetime.now().isoformat(),
            "password_hash": pw_hash,
            "salt": salt,
        }
        self.save_users(users)
        return True, "Cuenta creada correctamente. Ya puedes iniciar sesión."

    def login(self, username: str, password: str) -> tuple[bool, str]:
        """Valida credenciales y abre sesión. Devuelve (ok, mensaje)."""
        users = self.load_users()
        user = users.get(username)
        if not user:
            return False, "Usuario o contraseña incorrectos."
        if not _verify_password(password, user["password_hash"], user["salt"]):
            return False, "Usuario o contraseña incorrectos."
        self._save_session(username)
        return True, "Bienvenido, " + username + "."

    # -- sesión -------------------------------------------------------------

    def logout(self) -> None:
        try:
            if self.session_path.exists():
                self.session_path.unlink()
        except OSError:
            pass

    def current_user(self) -> str | None:
        if not self.session_path.exists():
            return None
        try:
            data = json.loads(self.session_path.read_text(encoding="utf-8"))
            return str(data.get("username", "")) or None
        except (OSError, ValueError, TypeError):
            return None

    def _save_session(self, username: str) -> None:
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.session_path.with_name(self.session_path.name + ".tmp")
        payload = json.dumps({"username": username}, ensure_ascii=False)
        temporary.write_text(payload + "\n", encoding="utf-8")
        os.replace(temporary, self.session_path)
