from __future__ import annotations

import datetime as dt

import bcrypt
import jwt
import pytest
from fastapi.testclient import TestClient

from api import main as api_main
from api.settings import get_settings
from rag.chunking import Chunk
from rag.pipeline import NO_RESULT_ANSWER, AnswerResult
from rag.vector_store import SearchResult

TEST_PASSWORD = "correct-horse-battery"
TEST_HASH = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt()).decode()
TEST_SECRET = "test-secret-key-not-for-production"


class FakePipeline:
    """Stands in for RAGPipeline — no embeddings, FAISS, or Groq involved."""

    def __init__(self, grounded: bool = True, error: Exception | None = None) -> None:
        self.grounded = grounded
        self.error = error
        self.calls: list[str] = []

    def ask(self, question: str, top_k: int = 4) -> AnswerResult:
        self.calls.append(question)
        if self.error:
            raise self.error
        if not self.grounded:
            return AnswerResult(
                question=question, answer=NO_RESULT_ANSWER, grounded=False, results=[]
            )
        chunk = Chunk(
            text="DuckDB reads S3 via httpfs.",
            project="uk-crime-data-pipeline",
            source_file="uk-crime-data-pipeline.md",
            heading="Architecture",
        )
        return AnswerResult(
            question=question,
            answer="The pipeline uses DuckDB. Sources: uk-crime-data-pipeline > Architecture",
            grounded=True,
            results=[SearchResult(chunk=chunk, score=0.671)],
        )


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
    monkeypatch.setenv("API_USERNAME", "testuser")
    monkeypatch.setenv("API_PASSWORD_HASH", TEST_HASH)
    monkeypatch.setenv("JWT_EXPIRY_MINUTES", "45")
    monkeypatch.setenv("RATE_LIMIT", "100/minute")
    get_settings.cache_clear()

    app = api_main.create_app()
    fake = FakePipeline()
    app.dependency_overrides[api_main.get_pipeline] = lambda: fake
    test_client = TestClient(app)
    test_client.fake_pipeline = fake
    yield test_client
    get_settings.cache_clear()


def login_token(client: TestClient) -> str:
    resp = client.post(
        "/auth/login", json={"username": "testuser", "password": TEST_PASSWORD}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


# --- health ------------------------------------------------------------


def test_health_needs_no_auth(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- login -------------------------------------------------------------


def test_login_returns_valid_decodable_token(client):
    resp = client.post(
        "/auth/login", json={"username": "testuser", "password": TEST_PASSWORD}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in_minutes"] == 45
    payload = jwt.decode(body["access_token"], TEST_SECRET, algorithms=["HS256"])
    assert payload["sub"] == "testuser"
    assert payload["exp"] > payload["iat"]


def test_login_wrong_password_is_401(client):
    resp = client.post(
        "/auth/login", json={"username": "testuser", "password": "wrong"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect username or password"


def test_login_unknown_user_same_error_as_wrong_password(client):
    resp = client.post(
        "/auth/login", json={"username": "intruder", "password": TEST_PASSWORD}
    )
    assert resp.status_code == 401
    # same message either way — no username enumeration
    assert resp.json()["detail"] == "Incorrect username or password"


# --- /ask auth ----------------------------------------------------------


def test_ask_without_token_is_401(client):
    resp = client.post("/ask", json={"question": "What warehouse is used?"})
    assert resp.status_code == 401
    assert resp.headers["WWW-Authenticate"] == "Bearer"
    assert client.fake_pipeline.calls == []


def test_ask_with_malformed_token_is_401(client):
    resp = client.post(
        "/ask",
        json={"question": "What warehouse is used?"},
        headers={"Authorization": "Bearer not.a.jwt"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token"


def test_ask_with_expired_token_is_401(client):
    past = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=5)
    expired = jwt.encode(
        {"sub": "testuser", "iat": past - dt.timedelta(minutes=45), "exp": past},
        TEST_SECRET,
        algorithm="HS256",
    )
    resp = client.post(
        "/ask",
        json={"question": "What warehouse is used?"},
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token expired"


def test_ask_with_wrong_signature_is_401(client):
    forged = jwt.encode(
        {
            "sub": "testuser",
            "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=45),
        },
        "attacker-secret",
        algorithm="HS256",
    )
    resp = client.post(
        "/ask",
        json={"question": "What warehouse is used?"},
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert resp.status_code == 401


# --- /ask behavior -------------------------------------------------------


def test_ask_with_valid_token_returns_grounded_answer(client):
    token = login_token(client)
    resp = client.post(
        "/ask",
        json={"question": "Which warehouse does the crime pipeline use?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["grounded"] is True
    assert "DuckDB" in body["answer"]
    assert body["sources"] == [
        {"citation": "uk-crime-data-pipeline > Architecture", "score": 0.671}
    ]
    assert client.fake_pipeline.calls == ["Which warehouse does the crime pipeline use?"]


def test_ask_refusal_passes_through_unchanged(client):
    """Phase 1's refusal behavior must survive the API wrapper untouched."""
    app = client.app
    fake = FakePipeline(grounded=False)
    app.dependency_overrides[api_main.get_pipeline] = lambda: fake
    token = login_token(client)
    resp = client.post(
        "/ask",
        json={"question": "What is the capital of France?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["grounded"] is False
    assert body["answer"] == NO_RESULT_ANSWER
    assert body["sources"] == []


def test_ask_invalid_body_is_422(client):
    token = login_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/ask", json={}, headers=headers).status_code == 422
    assert (
        client.post("/ask", json={"question": "ab"}, headers=headers).status_code == 422
    )
    assert (
        client.post(
            "/ask", json={"question": "valid question", "top_k": 99}, headers=headers
        ).status_code
        == 422
    )


def test_pipeline_failure_returns_502_not_traceback(client):
    app = client.app
    fake = FakePipeline(error=RuntimeError("groq exploded: secret internals"))
    app.dependency_overrides[api_main.get_pipeline] = lambda: fake
    token = login_token(client)
    resp = client.post(
        "/ask",
        json={"question": "Which warehouse does the crime pipeline use?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 502
    assert "secret internals" not in resp.text
    assert "Traceback" not in resp.text


# --- rate limiting --------------------------------------------------------


def test_rate_limit_triggers_after_threshold(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT", "3/minute")
    get_settings.cache_clear()
    client.app.state.limiter.reset()

    token = login_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"question": "Which warehouse does the crime pipeline use?"}

    for _ in range(3):
        assert client.post("/ask", json=payload, headers=headers).status_code == 200
    resp = client.post("/ask", json=payload, headers=headers)
    assert resp.status_code == 429
    assert "Rate limit exceeded" in resp.json()["detail"]


def test_rate_limit_does_not_apply_to_health(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT", "1/minute")
    get_settings.cache_clear()
    client.app.state.limiter.reset()
    for _ in range(5):
        assert client.get("/health").status_code == 200
