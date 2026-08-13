"""Metric and numeric-result grounding assertion."""

from __future__ import annotations

import re
from collections.abc import Sequence

from rag_assertions.base import BaseAssertion
from rag_assertions.models import AssertionResult, EvidenceItem, ValidationContext

METRIC_KEYWORDS = re.compile(
    r"\b(accuracy|precision|recall|f1|roc-auc|auc|latency|reduction|reduced|"
    r"improvement|improved|tests?|rows?|events?|products?|crimes?|revenue|"
    r"cost|savings?|bytes|p-value|p\s*=|score|effect|runtime|under)\b",
    re.IGNORECASE,
)
PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?\s?(?:%|percent)\b", re.IGNORECASE)
DECIMAL_METRIC_RE = re.compile(r"\b(?:p\s*=\s*)?\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?\b", re.IGNORECASE)


class MetricsGroundedAssertion(BaseAssertion):
    """Validate that quantitative claims are present in supplied evidence."""

    name = "metrics_grounded"

    def validate(
        self,
        answer: str,
        evidence: Sequence[EvidenceItem],
        context: ValidationContext,
    ) -> AssertionResult:
        claims = _metric_claims(answer)
        if not claims:
            return self.pass_result(
                "no metric claim detected",
                "No factual metric was detected.",
                skipped=True,
            )

        failures = []
        support: list[EvidenceItem] = []
        for claim in claims:
            number = claim["number"]
            matched = _evidence_for_number(number, evidence)
            if matched:
                support.extend(matched[:2])
            else:
                failures.append(claim["text"])

        if failures:
            return self.fail_result(
                "; ".join(failures),
                "Metric value was not found in supplied evidence.",
                support[:5],
            )

        return self.pass_result(
            "; ".join(claim["text"] for claim in claims),
            "Metric values appear in supplied evidence.",
            support[:5],
        )


def _metric_claims(answer: str) -> list[dict[str, str]]:
    claims: list[dict[str, str]] = []
    for sentence in re.split(r"(?<=[.!?])\s+", answer):
        if PERCENT_RE.search(sentence):
            for match in PERCENT_RE.finditer(sentence):
                claims.append({"number": match.group(0), "text": sentence.strip()})
            continue
        if not METRIC_KEYWORDS.search(sentence):
            continue
        for match in DECIMAL_METRIC_RE.finditer(sentence):
            token = match.group(0)
            if _looks_like_year_or_version(sentence, token):
                continue
            claims.append({"number": token, "text": sentence.strip()})
    return claims


def _evidence_for_number(number: str, evidence: Sequence[EvidenceItem]) -> list[EvidenceItem]:
    normalized = _normalize_number(number)
    return [
        item
        for item in evidence
        if normalized in {_normalize_number(match) for match in _all_numbers(item.text)}
    ]


def _all_numbers(text: str) -> list[str]:
    return re.findall(r"\b\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?\s?(?:%|percent)?\b", text, re.IGNORECASE)


def _normalize_number(number: str) -> str:
    normalized = number.lower().replace(",", "").replace(" ", "").rstrip(".")
    normalized = normalized.replace("percent", "%")
    return re.sub(r"^p=", "", normalized)


def _looks_like_year_or_version(sentence: str, token: str) -> bool:
    clean = token.replace(",", "")
    if re.fullmatch(r"20\d{2}|19\d{2}", clean):
        return True
    return bool(
        re.search(
            rf"\b(?:python|airflow|fastapi|dbt|v)\s*{re.escape(token)}\b",
            sentence,
            re.IGNORECASE,
        )
    )
