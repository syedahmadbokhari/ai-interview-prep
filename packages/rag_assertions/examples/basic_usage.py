from rag_assertions import AssertionRunner, EvidenceItem, ValidationContext

evidence = [
    EvidenceItem(
        text="Product Alpha achieved 94% accuracy using DuckDB.",
        source="alpha.md",
        entity="Product Alpha",
    )
]

runner = AssertionRunner()
validation = runner.validate(
    answer="Product Alpha achieved 94% accuracy using DuckDB.",
    evidence=evidence,
    context=ValidationContext(known_entities=("Product Alpha",)),
)

print(validation.passed)
print(validation.to_dict()["failed_count"])
