from __future__ import annotations

from assertions import AssertionRunner, EvidenceItem
from assertions.dates import assert_no_fabricated_dates
from assertions.metrics import assert_metrics_grounded
from assertions.project import assert_project_exists
from assertions.scope import assert_scope_bounded
from assertions.technology import assert_tech_stack_grounded


PROJECTS = ["crime", "retail"]


def ev(text: str, project: str = "crime", citation: str = "crime > Evidence"):
    return EvidenceItem(citation=citation, project=project, text=text)


def test_project_assertion_valid_project_passes():
    result = assert_project_exists(
        "The crime project uses DuckDB.", [ev("DuckDB warehouse")], PROJECTS
    )
    assert result.passed is True
    assert result.skipped is False


def test_project_assertion_fabricated_project_fails():
    result = assert_project_exists(
        "The Java Fraud Detection project used XGBoost.",
        [],
        PROJECTS,
        question="What did my Java Fraud Detection project use?",
    )
    assert result.passed is False
    assert result.assertion == "project_exists"
    assert "Java Fraud Detection project" in result.claim


def test_technology_assertion_grounded_technology_passes():
    result = assert_tech_stack_grounded(
        "The crime project used DuckDB as the warehouse.",
        [ev("The pipeline loads data into a DuckDB warehouse from S3.")],
        PROJECTS,
    )
    assert result.passed is True


def test_technology_assertion_fabricated_technology_fails():
    result = assert_tech_stack_grounded(
        "The retail project used Kafka for streaming ingestion.",
        [ev("The retail platform uses Airflow and dbt.", project="retail")],
        PROJECTS,
    )
    assert result.passed is False
    assert "Kafka" in result.claim


def test_metrics_assertion_grounded_percentage_passes():
    result = assert_metrics_grounded(
        "Partitioning reduced bytes scanned by 58.7%.",
        [ev("Reduction: 58.7%")],
        PROJECTS,
    )
    assert result.passed is True


def test_metrics_assertion_fabricated_percentage_fails():
    result = assert_metrics_grounded(
        "The model achieved 94% accuracy.",
        [ev("The model used cosine similarity.")],
        PROJECTS,
    )
    assert result.passed is False
    assert "94%" in result.claim


def test_metrics_assertion_grounded_decimal_metric_passes():
    result = assert_metrics_grounded(
        "The Mann-Whitney U test had p = 2.01e-05.",
        [ev("Mann-Whitney U test: p = 2.01e-05")],
        PROJECTS,
    )
    assert result.passed is True


def test_metrics_assertion_irrelevant_numbers_are_skipped():
    result = assert_metrics_grounded(
        "I can explain this in 3 short points.",
        [ev("DuckDB warehouse")],
        PROJECTS,
    )
    assert result.skipped is True
    assert result.passed is True


def test_date_assertion_grounded_year_passes():
    result = assert_no_fabricated_dates(
        "Traffic peaked in 2019.",
        [ev("Monthly website visits peaked in 2019.", project="retail")],
        PROJECTS,
    )
    assert result.passed is True


def test_date_assertion_fabricated_year_fails():
    result = assert_no_fabricated_dates(
        "The project was completed in 2024.",
        [ev("The project processes 2026 data.")],
        PROJECTS,
    )
    assert result.passed is False
    assert "2024" in result.claim


def test_date_assertion_software_versions_are_not_years():
    result = assert_no_fabricated_dates(
        "The API used FastAPI 0.110 and Python 3.11.",
        [ev("FastAPI 0.110")],
        PROJECTS,
    )
    assert result.skipped is True
    assert result.passed is True


def test_scope_assertion_grounded_statement_passes():
    result = assert_scope_bounded(
        "The pipeline loads data into a DuckDB warehouse.",
        [ev("The pipeline loads data into a DuckDB warehouse from S3.")],
        PROJECTS,
    )
    assert result.passed is True


def test_scope_assertion_unsupported_statement_fails():
    result = assert_scope_bounded(
        "The pipeline deployed a Kubernetes cluster.",
        [ev("The pipeline loads data into a DuckDB warehouse from S3.")],
        PROJECTS,
    )
    assert result.passed is False


def test_runner_multiple_passing_assertions_and_counts():
    validation = AssertionRunner().validate(
        answer="The crime project used DuckDB and reduced nothing by 58.7%.",
        retrieved_context=[
            ev("The crime project used DuckDB."),
            ev("Reduction: 58.7%"),
        ],
        project_registry=PROJECTS,
    )
    assert validation.all_passed is True
    assert validation.failed_count == 0
    assert validation.checks_run >= 3


def test_runner_mixed_pass_fail_counts():
    validation = AssertionRunner().validate(
        answer="The crime project used Snowflake and achieved 94% accuracy.",
        retrieved_context=[ev("The crime project used DuckDB.")],
        project_registry=PROJECTS,
    )
    assert validation.all_passed is False
    assert validation.failed_count >= 2
    assert {result.assertion for result in validation.failed} >= {
        "tech_stack_grounded",
        "metrics_grounded",
    }


def test_runner_irrelevant_assertions_can_be_skipped():
    validation = AssertionRunner().validate(
        answer="The available evidence is limited.",
        retrieved_context=[],
        project_registry=PROJECTS,
    )
    skipped = [result for result in validation.results if result.skipped]
    assert skipped
    assert validation.failed_count == 0
