import pytest

from rag_assertions import AssertionRunner, BaseAssertion, EvidenceItem, ValidationContext


class AlwaysPassAssertion(BaseAssertion):
    name = "always_pass"

    def validate(self, answer, evidence, context):
        return self.pass_result("ok", "ok")


class BrokenAssertion(BaseAssertion):
    name = "broken"

    def validate(self, answer, evidence, context):
        raise RuntimeError("boom")


def test_runner_accepts_custom_assertion():
    validation = AssertionRunner(assertions=[AlwaysPassAssertion()]).validate(
        "answer", [EvidenceItem(text="evidence")]
    )

    assert validation.passed is True


def test_runner_rejects_duplicate_assertion_names():
    with pytest.raises(ValueError):
        AssertionRunner(assertions=[AlwaysPassAssertion(), AlwaysPassAssertion()])


def test_runner_can_disable_assertion_by_name():
    validation = AssertionRunner(
        assertions=[BrokenAssertion()],
        disabled_assertions={"broken"},
    ).validate("answer", [])

    assert validation.passed is True
    assert validation.results[0].skipped is True


def test_runner_can_raise_or_capture_assertion_errors():
    captured = AssertionRunner(assertions=[BrokenAssertion()]).validate("answer", [])
    assert captured.passed is False
    assert "RuntimeError" in captured.results[0].reason

    with pytest.raises(RuntimeError):
        AssertionRunner(assertions=[BrokenAssertion()], raise_on_error=True).validate(
            "answer", []
        )


def test_default_runner_uses_context_entities():
    validation = AssertionRunner(disabled_assertions={"scope"}).validate(
        "Product Alpha used DuckDB.",
        [EvidenceItem(text="Product Alpha used DuckDB.", entity="Product Alpha")],
        context=ValidationContext(known_entities=("Product Alpha",)),
    )

    assert validation.passed is True
