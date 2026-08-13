"""Date and year grounding assertion."""

from __future__ import annotations

import re
from collections.abc import Sequence

from rag_assertions.base import BaseAssertion
from rag_assertions.models import AssertionResult, EvidenceItem, ValidationContext

YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
VERSION_CONTEXT = re.compile(
    r"\b(python|airflow|fastapi|dbt|postgresql|postgres|kafka|claude|llama|"
    r"gpt|yolo|model|api|version|v)\b",
    re.IGNORECASE,
)


class DateGroundedAssertion(BaseAssertion):
    """Validate that factual year claims appear in supplied evidence."""

    name = "dates_grounded"

    def validate(
        self,
        answer: str,
        evidence: Sequence[EvidenceItem],
        context: ValidationContext,
    ) -> AssertionResult:
        years = _factual_years(answer)
        if not years:
            return self.pass_result(
                "no date claim detected",
                "No factual date/year was detected.",
                skipped=True,
            )

        evidence_text = "\n".join(item.text for item in evidence)
        unsupported = [year for year in years if year not in evidence_text]
        if unsupported:
            return self.fail_result(
                ", ".join(unsupported),
                "Date/year claim was not found in supplied evidence.",
            )

        support = [item for item in evidence if any(year in item.text for year in years)]
        return self.pass_result(
            ", ".join(years),
            "Date/year claims appear in supplied evidence.",
            support[:5],
        )


class NoFabricatedDatesAssertion(DateGroundedAssertion):
    """Compatibility name used by the Interview Prep Assistant."""

    name = "no_fabricated_dates"


def _factual_years(answer: str) -> list[str]:
    years: list[str] = []
    for match in YEAR_RE.finditer(answer):
        start = max(0, match.start() - 35)
        end = min(len(answer), match.end() + 35)
        context = answer[start:end]
        if VERSION_CONTEXT.search(context):
            continue
        year = match.group(1)
        if year not in years:
            years.append(year)
    return years
