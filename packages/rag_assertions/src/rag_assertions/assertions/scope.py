"""Experimental practical scope-bounding assertion."""

from __future__ import annotations

import re
from collections.abc import Sequence

from rag_assertions.base import BaseAssertion
from rag_assertions.models import AssertionResult, EvidenceItem, ValidationContext

CLAIM_VERBS = re.compile(
    r"\b(uses?|used|built|implemented|achieved|reduced|improved|processes|"
    r"loads?|stores?|tracks?|validates?|generates?|ingests?|deploys?|deployed|runs?)\b",
    re.IGNORECASE,
)
STOP_TERMS = {
    "answer",
    "data",
    "pipeline",
    "platform",
    "project",
    "sources",
    "system",
    "that",
    "the",
    "this",
}


class ScopeBoundedAssertion(BaseAssertion):
    """Experimental lexical support check for factual claims.

    This validator is useful as a cheap guardrail, but it is not a semantic
    entailment model and should be reviewed before strict production gating.
    """

    name = "scope_bounded"
    severity = "warning"

    def validate(
        self,
        answer: str,
        evidence: Sequence[EvidenceItem],
        context: ValidationContext,
    ) -> AssertionResult:
        claims = _factual_claims(answer)
        if not claims:
            return self.pass_result(
                "no scoped factual claim detected",
                "No factual claim was detected.",
                skipped=True,
            )

        unsupported = []
        support: list[EvidenceItem] = []
        for claim in claims:
            matched = _claim_support(claim, evidence)
            if matched:
                support.extend(matched[:2])
            else:
                unsupported.append(claim)

        if unsupported:
            return self.fail_result(
                "; ".join(unsupported),
                "No supplied evidence shared enough salient terms with this factual claim.",
                support[:5],
            )

        return self.pass_result(
            "; ".join(claims),
            "Factual claims are bounded by supplied evidence.",
            support[:5],
        )


def _factual_claims(answer: str) -> list[str]:
    claims = []
    for sentence in re.split(r"(?<=[.!?])\s+", answer):
        clean = sentence.strip()
        if not clean or clean.lower().startswith("sources:"):
            continue
        if CLAIM_VERBS.search(clean):
            claims.append(clean)
    return claims


def _claim_support(claim: str, evidence: Sequence[EvidenceItem]) -> list[EvidenceItem]:
    claim_terms = _salient_terms(claim)
    if not claim_terms:
        return []
    matched = []
    for item in evidence:
        evidence_terms = _salient_terms(item.text)
        shared = claim_terms & evidence_terms
        if len(shared) >= min(2, len(claim_terms)):
            matched.append(item)
    return matched


def _salient_terms(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"\b[A-Za-z][A-Za-z0-9.+#-]{2,}\b", text)
        if token.lower() not in STOP_TERMS
    }
