from collections.abc import Sequence

from rag_assertions import (
    AssertionResult,
    AssertionRunner,
    BaseAssertion,
    EvidenceItem,
    ValidationContext,
)


class CitationRequiredAssertion(BaseAssertion):
    name = "citation_required"

    def validate(
        self,
        answer: str,
        evidence: Sequence[EvidenceItem],
        context: ValidationContext,
    ) -> AssertionResult:
        if "Sources:" in answer:
            return self.pass_result("Sources line", "Answer includes a Sources line.")
        return self.fail_result("missing Sources line", "Answer did not cite sources.")


runner = AssertionRunner(assertions=[CitationRequiredAssertion()])
validation = runner.validate(
    answer="The system uses DuckDB. Sources: system.md",
    evidence=[EvidenceItem(text="The system uses DuckDB.", source="system.md")],
)

print(validation.passed)
