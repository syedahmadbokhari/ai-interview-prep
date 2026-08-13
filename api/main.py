"""FastAPI wrapper around the Phase 1 RAG pipeline.

Deliberately thin: /ask calls rag.pipeline.RAGPipeline.ask() and maps its
AnswerResult onto the response model — retrieval, the similarity-gated
refusal path, and generation all live in Phase 1 code, untouched. The
refusal gate cannot be bypassed from here because it runs inside ask().

Rate limiting: slowapi, in-memory, keyed by client IP, default 10/minute
on /ask (each call costs one Groq request; Groq's free tier allows ~30/min,
so 10/min keeps one chatty client from exhausting it). Honest limitations:
counters live in process memory, so they reset on every restart, are NOT
shared across multiple uvicorn workers or horizontally scaled instances,
and IP keying misattributes clients behind a shared NAT/proxy. A real
multi-instance deployment would back this with Redis and trust
X-Forwarded-For only from a known proxy. Fine for a single-process
personal API; stated plainly rather than hidden.

Error contract: the client never sees a stack trace —
    422 invalid request body (FastAPI/Pydantic)
    401 missing/invalid/expired token
    429 rate limit exceeded
    502 the underlying pipeline failed (e.g. Groq outage/timeout)
    503 index not built yet (run ingest.py)
"""

from __future__ import annotations

import logging
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .auth import create_access_token, get_current_user, verify_password
from .schemas import (
    AgentAnswerResponse,
    AnswerResponse,
    ErrorResponse,
    LoginRequest,
    QuestionRequest,
    SourceInfo,
    TokenResponse,
)
from .settings import Settings, get_settings

logger = logging.getLogger("api")


@lru_cache(maxsize=1)
def _default_pipeline():
    """Load the real pipeline once per process, lazily (first /ask)."""
    from rag.pipeline import load_pipeline

    settings = get_settings()
    if not (settings.index_dir / "index.faiss").exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector index not found. Build it first: python ingest.py",
        )
    return load_pipeline(settings.index_dir)


def get_pipeline():
    """Dependency seam — tests override this with a fake pipeline."""
    return _default_pipeline()


def get_agent():
    """Dependency seam — tests override this with a fake agent."""
    from agent.agent import ReActAgent

    return ReActAgent(_default_pipeline().store)


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Interview Prep Assistant API",
        description="JWT-protected RAG over my portfolio project documentation",
        version="2.0.0",
    )
    # The Limiter must be per-app, not module-global: slowapi accumulates
    # limit registrations per endpoint name, so decorating a global limiter
    # from repeated create_app() calls (tests!) multiplies the per-request
    # cost. Scoping it here keeps one registration per app instance.
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": f"Rate limit exceeded: {exc.detail}"},
        )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post(
        "/auth/login",
        response_model=TokenResponse,
        responses={401: {"model": ErrorResponse}},
    )
    def login(body: LoginRequest, settings: Settings = Depends(get_settings)):
        valid = body.username == settings.api_username and verify_password(
            body.password, settings.api_password_hash
        )
        if not valid:
            # same message for unknown user and wrong password — don't
            # confirm which half was right
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
        token = create_access_token(body.username, settings)
        return TokenResponse(
            access_token=token, expires_in_minutes=settings.jwt_expiry_minutes
        )

    @app.post(
        "/ask",
        response_model=AnswerResponse,
        responses={
            401: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            502: {"model": ErrorResponse},
        },
    )
    @limiter.limit(lambda: get_settings().rate_limit)
    def ask(
        request: Request,
        body: QuestionRequest,
        user: str = Depends(get_current_user),
        pipeline=Depends(get_pipeline),
    ):
        try:
            result = pipeline.ask(body.question, top_k=body.top_k)
        except HTTPException:
            raise
        except Exception:
            # full traceback to the server log, never to the client
            logger.exception("RAG pipeline failure for question: %r", body.question)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The answer service is temporarily unavailable. Try again shortly.",
            )
        return AnswerResponse(
            question=result.question,
            answer=result.answer,
            grounded=result.grounded,
            sources=[
                SourceInfo(citation=r.chunk.citation(), score=round(r.score, 3))
                for r in result.results
            ],
        )

    @app.post(
        "/ask-agent",
        response_model=AgentAnswerResponse,
        responses={
            401: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            502: {"model": ErrorResponse},
        },
    )
    @limiter.limit(lambda: get_settings().rate_limit)
    def ask_agent(
        request: Request,
        body: QuestionRequest,
        user: str = Depends(get_current_user),
        agent=Depends(get_agent),
    ):
        try:
            result = agent.ask(body.question)
        except HTTPException:
            raise
        except Exception:
            logger.exception("Agent failure for question: %r", body.question)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The agent service is temporarily unavailable. Try again shortly.",
            )
        return AgentAnswerResponse(
            question=result.question,
            answer=result.answer,
            trace_path=result.trace_path,
        )

    return app


app = create_app()
