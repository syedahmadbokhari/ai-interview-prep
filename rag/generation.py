"""Answer generation via Groq's free-tier API.

Model: llama-3.3-70b-versatile — the strongest general model on Groq's
free tier; RAG answer synthesis benefits from a large model even when
retrieval is local, and Groq's free tier makes it zero-cost here.

Grounding rules enforced by the prompt:
- Answer ONLY from the provided sources; every source block is labeled
  with its citation ("project > section") and the model must name the
  citation(s) it used.
- If the sources don't contain the answer, say so explicitly instead of
  guessing.

The no-retrieval case never reaches the LLM at all — the pipeline
short-circuits it (see pipeline.py).
"""

from __future__ import annotations

import os
from pathlib import Path

from .vector_store import SearchResult


def _load_dotenv_key() -> str | None:
    """Minimal .env reader (repo root) so no python-dotenv dependency is needed."""
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if not env_file.exists():
        return None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("GROQ_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    return None

SYSTEM_PROMPT = """\
You are an assistant that answers questions about the user's portfolio \
projects, strictly using the source excerpts provided.

Rules:
1. Use ONLY facts stated in the sources below. Do not add outside knowledge.
2. End your answer with a line: `Sources: <citation>; <citation>` listing \
the exact citation labels of the sources you actually used.
3. If the sources do not contain the information needed, reply exactly: \
"The provided project documentation does not contain information to answer \
this." — do not attempt a partial or speculative answer.
4. Quote concrete figures (percentages, counts, p-values) exactly as they \
appear in the sources."""


def build_context(results: list[SearchResult]) -> str:
    blocks = []
    for r in results:
        blocks.append(f"[{r.chunk.citation()}]\n{r.chunk.text}")
    return "\n\n---\n\n".join(blocks)


class GroqGenerator:
    MODEL = "llama-3.3-70b-versatile"

    def __init__(self, api_key: str | None = None) -> None:
        from groq import Groq

        key = api_key or os.environ.get("GROQ_API_KEY") or _load_dotenv_key()
        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com "
                "and set it as an environment variable."
            )
        self._client = Groq(api_key=key)

    def generate(self, question: str, results: list[SearchResult]) -> str:
        context = build_context(results)
        user_message = (
            f"Source excerpts from my project READMEs:\n\n{context}\n\n"
            f"Question: {question}"
        )
        response = self._client.chat.completions.create(
            model=self.MODEL,
            temperature=0.0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content.strip()
