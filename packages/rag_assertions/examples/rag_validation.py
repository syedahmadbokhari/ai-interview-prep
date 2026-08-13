from rag_assertions import (
    AssertionRunner,
    EvidenceItem,
    MetricsGroundedAssertion,
    TechnologyGroundedAssertion,
    ValidationContext,
)

retrieved_evidence = [
    EvidenceItem(
        text="The analytics service uses PostgreSQL and reduced query latency by 37%.",
        source="service.md#performance",
        entity="Analytics Service",
        chunk_id="svc_001",
        score=0.82,
    )
]

runner = AssertionRunner(
    assertions=[
        TechnologyGroundedAssertion(),
        MetricsGroundedAssertion(),
    ]
)

validation = runner.validate(
    answer="The analytics service uses PostgreSQL and reduced query latency by 37%.",
    evidence=retrieved_evidence,
    context=ValidationContext(known_entities=("Analytics Service",)),
)

if validation.passed:
    print("answer accepted")
else:
    print("answer needs review")
