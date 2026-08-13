from rag_assertions import AssertionResult, AssertionStatus, EvidenceItem, ValidationResult


def test_evidence_item_is_generic_and_serializable():
    item = EvidenceItem(
        text="A system achieved 94% accuracy.",
        source="system.md",
        entity="System A",
        chunk_id="a1",
        score=0.9,
        metadata={"retriever": "custom"},
    )

    data = item.to_dict()

    assert data["text"] == "A system achieved 94% accuracy."
    assert data["source"] == "system.md"
    assert data["entity"] == "System A"
    assert data["metadata"]["retriever"] == "custom"


def test_validation_result_counts_pass_fail_skip():
    validation = ValidationResult(
        [
            AssertionResult("a", True, "claim", "ok"),
            AssertionResult("b", False, "claim", "bad"),
            AssertionResult("c", True, "claim", "skip", skipped=True),
        ]
    )

    assert validation.passed is False
    assert validation.checks_run == 2
    assert validation.failed_count == 1
    assert validation.skipped_count == 1
    assert validation.results[2].status == AssertionStatus.SKIP
