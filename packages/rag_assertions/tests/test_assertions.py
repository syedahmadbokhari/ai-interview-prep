from rag_assertions import AssertionRunner, EvidenceItem, ValidationContext
from rag_assertions.assertions import (
    DateGroundedAssertion,
    EntityExistsAssertion,
    MetricsGroundedAssertion,
    ScopeBoundedAssertion,
    TechnologyGroundedAssertion,
)


def ev(text: str, entity: str = "Product Alpha"):
    return EvidenceItem(text=text, source="source.md", entity=entity)


def ctx():
    return ValidationContext(known_entities=("Product Alpha", "Product Beta"))


def test_entity_assertion_passes_known_entity():
    result = EntityExistsAssertion().validate(
        "Product Alpha uses DuckDB.",
        [ev("Product Alpha uses DuckDB.")],
        ctx(),
    )

    assert result.passed is True


def test_entity_assertion_fails_unknown_entity():
    result = EntityExistsAssertion().validate(
        "The Fraud Detection project used XGBoost.",
        [],
        ValidationContext(known_entities=("Product Alpha",), question="What did Fraud Detection project use?"),
    )

    assert result.passed is False
    assert "Fraud Detection project" in result.claim


def test_technology_assertion_pass_fail_skip():
    assertion = TechnologyGroundedAssertion()

    assert assertion.validate("It used DuckDB.", [ev("It used DuckDB.")], ctx()).passed
    assert not assertion.validate("It used Kafka.", [ev("It used DuckDB.")], ctx()).passed
    assert assertion.validate("The evidence is limited.", [], ctx()).skipped


def test_metrics_assertion_percentage_decimal_integer_and_thousands():
    assertion = MetricsGroundedAssertion()

    assert assertion.validate("Accuracy was 94%.", [ev("Accuracy was 94%.")], ctx()).passed
    assert assertion.validate("ROC-AUC was 0.79.", [ev("ROC-AUC was 0.79.")], ctx()).passed
    assert assertion.validate("It processed 1,250 rows.", [ev("It processed 1250 rows.")], ctx()).passed
    assert not assertion.validate("Accuracy was 94%.", [ev("Accuracy was 0.94.")], ctx()).passed


def test_date_assertion_handles_years_and_versions():
    assertion = DateGroundedAssertion()

    assert assertion.validate("Launched in 2024.", [ev("Launched in 2024.")], ctx()).passed
    assert not assertion.validate("Launched in 2024.", [ev("Launched in 2023.")], ctx()).passed
    assert assertion.validate("Uses Python 3.12 and GPT-4.", [], ctx()).skipped


def test_scope_assertion_is_practical_and_experimental():
    assertion = ScopeBoundedAssertion()

    assert assertion.validate("The service loads data into DuckDB.", [ev("The service loads data into DuckDB.")], ctx()).passed
    assert not assertion.validate("The service deployed Kubernetes.", [ev("The service loads data into DuckDB.")], ctx()).passed
    assert assertion.severity == "warning"


def test_default_runner_without_external_dependencies():
    validation = AssertionRunner().validate(
        "Product Alpha used DuckDB and achieved 94% accuracy in 2024.",
        [
            ev("Product Alpha used DuckDB."),
            ev("Accuracy was 94%."),
            ev("The result was reported in 2024."),
        ],
        ctx(),
    )

    assert validation.passed is True
