"""Quality gate for evaluation summaries.

Example:
    python -m evals.quality_gate --summary evals/results/run/summary.json \
        --baseline evals/baselines/mock_v1.json --policy evals/policies/pr_gate.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GateCheck:
    name: str
    status: str
    reason: str
    current: Any = None
    baseline: Any = None
    delta: float | None = None
    allowed_regression: float | None = None


@dataclass
class GateResult:
    passed: bool
    policy: str
    checks: list[GateCheck] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "policy": self.policy,
            "checks": [asdict(check) for check in self.checks],
        }


def evaluate_gate(
    summary: dict[str, Any],
    baseline: dict[str, Any] | None,
    policy: dict[str, Any],
) -> GateResult:
    checks: list[GateCheck] = []
    _hard_failure_checks(summary, policy, checks)
    if baseline is not None:
        _compatibility_checks(summary, baseline, policy, checks)
    _absolute_metric_checks(summary, policy, checks)
    if baseline is not None:
        _regression_checks(summary, baseline, policy, checks)
    _cross_config_checks(summary, policy, checks)

    passed = all(check.status != "FAIL" for check in checks)
    return GateResult(passed=passed, policy=policy.get("name", "unnamed"), checks=checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        summary = _load_json(args.summary)
        policy = _load_json(args.policy)
        baseline = _load_json(args.baseline) if args.baseline else None
        result = evaluate_gate(summary, baseline, policy)
    except Exception as exc:
        result = GateResult(
            passed=False,
            policy=args.policy.stem,
            checks=[GateCheck("gate_exception", "FAIL", str(exc))],
        )

    output_dir = args.output_dir or args.summary.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "quality_gate.json").write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "QUALITY_GATE.md").write_text(_render_markdown(result), encoding="utf-8")
    print(_render_console(result))
    return 0 if result.passed else 1


def _hard_failure_checks(
    summary: dict[str, Any], policy: dict[str, Any], checks: list[GateCheck]
) -> None:
    metadata = summary.get("metadata", {})
    expected_size = policy.get("hard_failures", {}).get("expected_dataset_size")
    if expected_size is not None:
        current = metadata.get("dataset_size")
        checks.append(
            GateCheck(
                "dataset_size",
                "PASS" if current == expected_size else "FAIL",
                f"Expected dataset size {expected_size}.",
                current=current,
                baseline=expected_size,
            )
        )
    required_configs = policy.get("hard_failures", {}).get("required_configurations", [])
    actual_configs = set(metadata.get("configurations", []))
    for config in required_configs:
        checks.append(
            GateCheck(
                f"configuration_present.{config}",
                "PASS" if config in actual_configs else "FAIL",
                "Required configuration must be present.",
                current=sorted(actual_configs),
            )
        )
    if not summary.get("aggregates", {}).get("by_configuration"):
        checks.append(GateCheck("non_empty_evaluation", "FAIL", "No configuration aggregates found."))
    else:
        checks.append(GateCheck("non_empty_evaluation", "PASS", "Configuration aggregates exist."))


def _compatibility_checks(
    summary: dict[str, Any],
    baseline: dict[str, Any],
    policy: dict[str, Any],
    checks: list[GateCheck],
) -> None:
    current_meta = summary.get("metadata", {})
    base_meta = baseline.get("metadata", {})
    fields = policy.get("compatibility", {}).get(
        "required_equal", ["dataset_version", "scoring_version"]
    )
    for field in fields:
        current = current_meta.get(field)
        base = base_meta.get(field)
        checks.append(
            GateCheck(
                f"compatibility.{field}",
                "PASS" if current == base else "FAIL",
                "Current run must be compatible with approved baseline.",
                current=current,
                baseline=base,
            )
        )


def _absolute_metric_checks(
    summary: dict[str, Any], policy: dict[str, Any], checks: list[GateCheck]
) -> None:
    for rule in policy.get("absolute_minimums", []):
        metric_path = rule["metric"]
        try:
            current = _metric(summary, metric_path)
        except KeyError as exc:
            checks.append(
                GateCheck(
                    f"minimum.{metric_path}",
                    "FAIL",
                    f"Metric is missing: {exc}",
                    baseline=rule["minimum"],
                )
            )
            continue
        minimum = rule["minimum"]
        checks.append(
            GateCheck(
                f"minimum.{metric_path}",
                "PASS" if _valid_number(current) and current >= minimum else "FAIL",
                f"Metric must be >= {minimum}.",
                current=current,
                baseline=minimum,
            )
        )


def _regression_checks(
    summary: dict[str, Any],
    baseline: dict[str, Any],
    policy: dict[str, Any],
    checks: list[GateCheck],
) -> None:
    for rule in policy.get("regression_limits", []):
        metric_path = rule["metric"]
        try:
            current = _metric(summary, metric_path)
            base = _metric(baseline, metric_path)
        except KeyError as exc:
            checks.append(
                GateCheck(
                    f"regression.{metric_path}",
                    "FAIL",
                    f"Metric is missing: {exc}",
                    allowed_regression=rule["max_regression"],
                )
            )
            continue
        allowed = rule["max_regression"]
        if not _valid_number(current) or not _valid_number(base):
            checks.append(
                GateCheck(
                    f"regression.{metric_path}",
                    "FAIL",
                    "Current or baseline metric is missing/invalid.",
                    current=current,
                    baseline=base,
                    allowed_regression=allowed,
                )
            )
            continue
        delta = current - base
        checks.append(
            GateCheck(
                f"regression.{metric_path}",
                "PASS" if delta >= -allowed else "FAIL",
                f"Metric must not regress by more than {allowed}.",
                current=current,
                baseline=base,
                delta=delta,
                allowed_regression=allowed,
            )
        )


def _cross_config_checks(
    summary: dict[str, Any], policy: dict[str, Any], checks: list[GateCheck]
) -> None:
    for rule in policy.get("cross_config_rules", []):
        try:
            left = _metric(summary, rule["left"])
            right = _metric(summary, rule["right"])
        except KeyError as exc:
            checks.append(
                GateCheck(
                    f"cross_config.{rule['left']}.{rule['operator']}.{rule['right']}",
                    "FAIL",
                    f"Metric is missing: {exc}",
                )
            )
            continue
        tolerance = rule.get("tolerance", 0.0)
        operator = rule["operator"]
        passed = _compare(left, right, operator, tolerance)
        checks.append(
            GateCheck(
                f"cross_config.{rule['left']}.{operator}.{rule['right']}",
                "PASS" if passed else "FAIL",
                f"Expected {rule['left']} {operator} {rule['right']} with tolerance {tolerance}.",
                current=left,
                baseline=right,
                allowed_regression=tolerance,
            )
        )


def _metric(summary: dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    if len(parts) == 2:
        config, metric = parts
        return summary["aggregates"]["by_configuration"][config][metric]
    if len(parts) == 3 and parts[0] == "assertions":
        _, assertion_type, metric = parts
        return summary["aggregates"]["assertions"]["by_type"][assertion_type][metric]
    raise KeyError(f"Unsupported metric path: {path}")


def _compare(left: Any, right: Any, operator: str, tolerance: float) -> bool:
    if not _valid_number(left) or not _valid_number(right):
        return False
    if operator == ">=":
        return left + tolerance >= right
    if operator == "<=":
        return left <= right + tolerance
    raise ValueError(f"Unsupported operator: {operator}")


def _valid_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not math.isnan(float(value))


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _render_console(result: GateResult) -> str:
    status = "PASS" if result.passed else "FAIL"
    failed = [check for check in result.checks if check.status == "FAIL"]
    lines = [f"QUALITY GATE: {status}", f"Policy: {result.policy}"]
    for check in failed[:10]:
        lines.append(
            f"- {check.name}: {check.status} current={check.current} baseline={check.baseline} reason={check.reason}"
        )
    return "\n".join(lines)


def _render_markdown(result: GateResult) -> str:
    status = "PASS" if result.passed else "FAIL"
    lines = [
        "# Quality Gate",
        "",
        f"Policy: `{result.policy}`",
        f"Overall outcome: **{status}**",
        "",
        "| Check | Status | Current | Baseline | Delta | Allowed | Reason |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for check in result.checks:
        lines.append(
            f"| `{check.name}` | {check.status} | {check.current} | {check.baseline} | "
            f"{check.delta} | {check.allowed_regression} | {check.reason} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
