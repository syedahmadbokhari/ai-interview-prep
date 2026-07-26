"""API configuration, following the exact .env pattern Phase 1 established:
values come from real environment variables first, then from the gitignored
.env at the repo root. Nothing secret is ever hardcoded or committed.

Required keys (see .env.example):
    JWT_SECRET_KEY     — HMAC signing key for access tokens
    API_USERNAME       — the single user's login name
    API_PASSWORD_HASH  — bcrypt hash of that user's password (never plaintext)
Optional:
    JWT_EXPIRY_MINUTES — access token lifetime (default 45)
    RATE_LIMIT         — slowapi limit string for /ask (default "10/minute")
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_dotenv() -> dict[str, str]:
    env_file = _REPO_ROOT / ".env"
    values: dict[str, str] = {}
    if not env_file.exists():
        return values
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"')
    return values


def _get(name: str, default: str | None = None) -> str:
    value = os.environ.get(name) or _read_dotenv().get(name) or default
    if value is None:
        raise RuntimeError(
            f"{name} is not configured. Set it as an environment variable or "
            f"add it to {_REPO_ROOT / '.env'} (see .env.example)."
        )
    return value


@dataclass(frozen=True)
class Settings:
    jwt_secret_key: str
    jwt_expiry_minutes: int
    api_username: str
    api_password_hash: str
    rate_limit: str
    index_dir: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        jwt_secret_key=_get("JWT_SECRET_KEY"),
        jwt_expiry_minutes=int(_get("JWT_EXPIRY_MINUTES", "45")),
        api_username=_get("API_USERNAME"),
        api_password_hash=_get("API_PASSWORD_HASH"),
        rate_limit=_get("RATE_LIMIT", "10/minute"),
        index_dir=Path(_get("INDEX_DIR", str(_REPO_ROOT / "index"))),
    )
