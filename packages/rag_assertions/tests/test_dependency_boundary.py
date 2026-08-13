from pathlib import Path

FORBIDDEN_IMPORTS = (
    "anthropic",
    "groq",
    "openai",
    "fastapi",
    "streamlit",
    "langchain",
    "langgraph",
    "llama_index",
    "agent",
    "api",
    "evals",
)


def test_core_package_has_no_provider_or_parent_imports():
    src = Path(__file__).resolve().parents[1] / "src" / "rag_assertions"
    text = "\n".join(path.read_text(encoding="utf-8") for path in src.rglob("*.py"))

    for name in FORBIDDEN_IMPORTS:
        assert f"import {name}" not in text
        assert f"from {name}" not in text
