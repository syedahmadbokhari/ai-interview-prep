"""JWT authentication.

Library choices:
- PyJWT for tokens — actively maintained, the de-facto standard; no
  hand-rolled encoding/decoding anywhere.
- bcrypt (direct) for password hashing rather than passlib: passlib is
  effectively unmaintained and breaks against bcrypt >= 4.1, so the thin
  direct API is the safer dependency in 2026.

Why bcrypt-hash the password even for a single-user personal project:
the password never needs to exist in recoverable form anywhere — .env
files get leaked in backups, screen shares, and accidental commits far
more often than people expect, and a leaked *hash* doesn't reveal the
password itself (which people inevitably reuse elsewhere). Hashing also
keeps the login flow identical to what a multi-user version would need,
so growing past one user later changes data, not code.

Token expiry: 45 minutes. Long enough to cover a full interview-prep
session without re-logging in mid-conversation; short enough that a
leaked/intercepted token has a tightly bounded useful life. There is no
refresh-token flow — for a single-user local API that complexity buys
nothing; you just log in again.
"""

from __future__ import annotations

import datetime as dt

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .settings import Settings, get_settings

ALGORITHM = "HS256"

# auto_error=False so a missing header raises OUR 401 below, not FastAPI's
# default 403 — a missing credential is an authentication failure, and the
# response should say so (RFC 6750 semantics, WWW-Authenticate included).
_bearer = HTTPBearer(auto_error=False)


def verify_password(plain: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(username: str, settings: Settings) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + dt.timedelta(minutes=settings.jwt_expiry_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> str:
    if credentials is None:
        raise _unauthorized("Not authenticated: missing bearer token")
    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret_key, algorithms=[ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token expired")
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid token")
    username = payload.get("sub")
    if username != settings.api_username:
        raise _unauthorized("Invalid token subject")
    return username
