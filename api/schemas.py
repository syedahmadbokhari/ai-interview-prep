"""Pydantic request/response models.

AnswerResponse mirrors what Phase 1's ask.py already surfaces — answer
text, grounded flag (False = the refusal path fired), and the retrieved
sources with their cosine similarity scores — so the API is a faithful
wrapper, not a reinterpretation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
        description="Natural-language question about the indexed projects",
    )
    top_k: int = Field(default=4, ge=1, le=10)


class SourceInfo(BaseModel):
    citation: str  # "project > section", same format ask.py prints
    score: float  # cosine similarity in [-1, 1]


class AnswerResponse(BaseModel):
    question: str
    answer: str
    grounded: bool  # False => refusal path fired, no LLM was called
    sources: list[SourceInfo]


class AgentAnswerResponse(BaseModel):
    question: str
    answer: str
    trace_path: str


class ErrorResponse(BaseModel):
    detail: str
