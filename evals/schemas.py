"""Dataset and result schemas for Phase 3 evaluation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VALID_CATEGORIES = {"single_hop", "multi_hop", "comparative", "adversarial"}
VALID_BEHAVIORS = {"answer", "refuse_false_premise"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_CONFIGS = {"pipeline", "agent_no_assertions", "agent_with_assertions"}


@dataclass(frozen=True)
class SourceRef:
    project: str
    document: str
    chunk_id: str
    heading: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceRef":
        return cls(
            project=data["project"],
            document=data["document"],
            chunk_id=data["chunk_id"],
            heading=data["heading"],
        )


@dataclass(frozen=True)
class RequiredFact:
    fact: str
    keywords: list[str]
    source_refs: list[SourceRef] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RequiredFact":
        return cls(
            fact=data["fact"],
            keywords=list(data["keywords"]),
            source_refs=[SourceRef.from_dict(ref) for ref in data.get("source_refs", [])],
        )


@dataclass(frozen=True)
class EvalItem:
    id: str
    category: str
    question: str
    expected_projects: list[str]
    required_facts: list[RequiredFact]
    acceptable_variants: list[str]
    forbidden_claims: list[str]
    expected_behavior: str
    difficulty: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvalItem":
        return cls(
            id=data["id"],
            category=data["category"],
            question=data["question"],
            expected_projects=list(data.get("expected_projects", [])),
            required_facts=[
                RequiredFact.from_dict(item) for item in data.get("required_facts", [])
            ],
            acceptable_variants=list(data.get("acceptable_variants", [])),
            forbidden_claims=list(data.get("forbidden_claims", [])),
            expected_behavior=data["expected_behavior"],
            difficulty=data["difficulty"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "question": self.question,
            "expected_projects": self.expected_projects,
            "required_facts": [
                {
                    "fact": fact.fact,
                    "keywords": fact.keywords,
                    "source_refs": [ref.__dict__ for ref in fact.source_refs],
                }
                for fact in self.required_facts
            ],
            "acceptable_variants": self.acceptable_variants,
            "forbidden_claims": self.forbidden_claims,
            "expected_behavior": self.expected_behavior,
            "difficulty": self.difficulty,
        }


def load_dataset(path: Path) -> list[EvalItem]:
    items = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            items.append(EvalItem.from_dict(json.loads(line)))
        except Exception as exc:
            raise ValueError(f"Invalid JSONL item at {path}:{line_no}: {exc}") from exc
    return items


def validate_dataset(
    items: list[EvalItem], project_registry: list[str] | None = None
) -> list[str]:
    errors: list[str] = []
    project_registry = project_registry or []
    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    for item in items:
        if item.id in seen_ids:
            errors.append(f"duplicate id: {item.id}")
        seen_ids.add(item.id)
        if item.question.lower() in seen_questions:
            errors.append(f"duplicate question: {item.question}")
        seen_questions.add(item.question.lower())
        if item.category not in VALID_CATEGORIES:
            errors.append(f"{item.id}: invalid category {item.category}")
        if item.expected_behavior not in VALID_BEHAVIORS:
            errors.append(f"{item.id}: invalid expected_behavior {item.expected_behavior}")
        if item.difficulty not in VALID_DIFFICULTIES:
            errors.append(f"{item.id}: invalid difficulty {item.difficulty}")
        if item.expected_behavior == "answer" and not item.required_facts:
            errors.append(f"{item.id}: answer item must include required_facts")
        if item.expected_behavior == "refuse_false_premise" and item.required_facts:
            errors.append(f"{item.id}: adversarial refusal should not require facts")
        for project in item.expected_projects:
            if project_registry and project not in project_registry:
                errors.append(f"{item.id}: unsupported project {project}")
        for fact in item.required_facts:
            if not fact.keywords:
                errors.append(f"{item.id}: required fact has no keywords")
            for ref in fact.source_refs:
                if project_registry and ref.project not in project_registry:
                    errors.append(f"{item.id}: source ref unsupported project {ref.project}")
        for fact in item.required_facts:
            for forbidden in item.forbidden_claims:
                if forbidden.lower() in fact.fact.lower():
                    errors.append(f"{item.id}: required/forbidden contradiction")
    return errors
