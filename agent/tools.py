"""Tool schemas and implementations for the Anthropic tool_use agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rag.vector_store import VectorStore


DEFAULT_TOOL_TOP_K = 4


ANTHROPIC_TOOLS: list[dict[str, Any]] = [
    {
        "name": "list_projects",
        "description": "Return the project names available in the indexed corpus.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_project_summary",
        "description": "Return a high-level summary of one indexed project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Exact project name from list_projects.",
                }
            },
            "required": ["project_name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "search_technical_details",
        "description": (
            "Search technical detail chunks for one project using the existing FAISS index."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Exact project name from list_projects.",
                },
                "query": {
                    "type": "string",
                    "description": "Technical retrieval query scoped to the project.",
                },
            },
            "required": ["project_name", "query"],
            "additionalProperties": False,
        },
    },
]


@dataclass
class AgentTools:
    store: VectorStore
    top_k: int = DEFAULT_TOOL_TOP_K

    def list_projects(self) -> dict[str, list[str]]:
        return {"projects": sorted({chunk.project for chunk in self.store.chunks})}

    def get_project_summary(self, project_name: str) -> dict[str, Any]:
        chunks = self._project_chunks(project_name)
        if not chunks:
            return {"project_name": project_name, "found": False, "summary": ""}

        preferred_headings = {
            "business context",
            "executive summary",
            "what this system does",
            f"{project_name} (introduction)",
        }
        selected = [
            chunk
            for chunk in chunks
            if chunk.heading.lower() in preferred_headings
            or "introduction" in chunk.heading.lower()
        ][:3]
        if not selected:
            selected = chunks[:3]

        summary = "\n\n".join(
            f"[{chunk.citation()}]\n{chunk.text.strip()}" for chunk in selected
        )
        return {"project_name": project_name, "found": True, "summary": summary}

    def search_technical_details(self, project_name: str, query: str) -> dict[str, Any]:
        if not self._project_chunks(project_name):
            return {"project_name": project_name, "query": query, "results": []}

        # Search the existing FAISS index broadly, then scope to the target project.
        candidates = self.store.search(query, top_k=len(self.store.chunks))
        scoped = [r for r in candidates if r.chunk.project == project_name][: self.top_k]
        return {
            "project_name": project_name,
            "query": query,
            "results": [
                {
                    "citation": r.chunk.citation(),
                    "score": round(r.score, 3),
                    "text": r.chunk.text,
                }
                for r in scoped
            ],
        }

    def execute(self, name: str, input_data: dict[str, Any] | None) -> dict[str, Any]:
        data = input_data or {}
        if name == "list_projects":
            return self.list_projects()
        if name == "get_project_summary":
            return self.get_project_summary(project_name=data.get("project_name", ""))
        if name == "search_technical_details":
            return self.search_technical_details(
                project_name=data.get("project_name", ""), query=data.get("query", "")
            )
        return {"error": f"Unknown tool: {name}"}

    def _project_chunks(self, project_name: str):
        return [chunk for chunk in self.store.chunks if chunk.project == project_name]
