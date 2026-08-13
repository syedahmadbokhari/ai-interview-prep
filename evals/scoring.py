"""Deterministic scoring for benchmark outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass

from rag_assertions import ValidationResult

from .schemas import EvalItem

REFUSAL_PATTERNS = (
    "no relevant information",
    "does not contain",
    "does not appear",
    "doesn't appear",
    "does not deploy",
    "does not mention",
    "no mention",
    "cannot verify",
    "could not verify",
    "won't return it as factual",
    "not found",
    "false premise",
)


@dataclass(frozen=True)
class ScoreBreakdown:
    required_fact_score: float
    faithfulness_score: float
    project_entity_score: float
    multi_hop_score: float | None
    comparative_score: float | None
    adversarial_success: bool | None
    forbidden_claims_found: list[str]

    def to_dict(self) -> dict:
        return {
            "required_fact_score": self.required_fact_score,
            "faithfulness_score": self.faithfulness_score,
            "project_entity_score": self.project_entity_score,
            "multi_hop_score": self.multi_hop_score,
            "comparative_score": self.comparative_score,
            "adversarial_success": self.adversarial_success,
            "forbidden_claims_found": self.forbidden_claims_found,
        }


def score_answer(
    item: EvalItem, answer: str, validation: ValidationResult | None = None
) -> ScoreBreakdown:
    lowered = answer.lower()
    forbidden = [
        claim for claim in item.forbidden_claims if _affirmative_forbidden_claim(answer, claim)
    ]
    refusal = _is_refusal(answer)

    if item.expected_behavior == "refuse_false_premise":
        adversarial_success = refusal and not forbidden
        return ScoreBreakdown(
            required_fact_score=1.0 if adversarial_success else 0.0,
            faithfulness_score=1.0 if adversarial_success else 0.0,
            project_entity_score=1.0 if adversarial_success else 0.0,
            multi_hop_score=None,
            comparative_score=None,
            adversarial_success=adversarial_success,
            forbidden_claims_found=forbidden,
        )

    fact_hits = [
        _contains_all_keywords(answer, fact.keywords) for fact in item.required_facts
    ]
    required_fact_score = sum(fact_hits) / len(fact_hits) if fact_hits else 1.0
    project_hits = [
        _project_mentioned(answer, project) for project in item.expected_projects
    ]
    project_entity_score = sum(project_hits) / len(project_hits) if project_hits else 1.0
    faithfulness_score = 0.0 if forbidden or refusal else 1.0
    if validation is not None and not validation.all_passed:
        faithfulness_score = 0.0

    multi_hop_score = None
    if item.category == "multi_hop":
        multi_hop_score = required_fact_score

    comparative_score = None
    if item.category == "comparative":
        comparative_score = min(required_fact_score, project_entity_score)

    return ScoreBreakdown(
        required_fact_score=required_fact_score,
        faithfulness_score=faithfulness_score,
        project_entity_score=project_entity_score,
        multi_hop_score=multi_hop_score,
        comparative_score=comparative_score,
        adversarial_success=None,
        forbidden_claims_found=forbidden,
    )


def _contains_all_keywords(answer: str, keywords: list[str]) -> bool:
    hay = answer.lower()
    return all(keyword.lower() in hay for keyword in keywords)


def _project_mentioned(answer: str, project: str) -> bool:
    lowered = answer.lower()
    aliases = {project.lower(), project.replace("-", " ").lower()}
    aliases.update(token for token in project.replace("-", " ").lower().split() if len(token) > 4)
    return any(re.search(rf"\b{re.escape(alias)}\b", lowered) for alias in aliases)


def _is_refusal(answer: str) -> bool:
    lowered = answer.lower()
    return any(pattern in lowered for pattern in REFUSAL_PATTERNS)


def _affirmative_forbidden_claim(answer: str, claim: str) -> bool:
    lowered = answer.lower()
    claim_lower = claim.lower()
    start = 0
    while True:
        idx = lowered.find(claim_lower, start)
        if idx == -1:
            return False
        window = lowered[max(0, idx - 80) : idx + len(claim_lower) + 40]
        if not _negated_claim_window(window):
            return True
        start = idx + len(claim_lower)


def _negated_claim_window(window: str) -> bool:
    negation_patterns = (
        "does not",
        "do not",
        "did not",
        "not ",
        "no mention",
        "no evidence",
        "doesn't",
        "don't",
        "is not",
        "not found",
        "without",
    )
    return any(pattern in window for pattern in negation_patterns)
