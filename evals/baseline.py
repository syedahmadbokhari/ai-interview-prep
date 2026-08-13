"""Approve and validate evaluation baselines.

Example:
    python -m evals.baseline approve --result evals/results/run/summary.json \
        --name mock_v1 --output-dir evals/baselines
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def approve_baseline(
    result_path: Path,
    name: str,
    output_dir: Path,
    force: bool = False,
) -> Path:
    summary = json.loads(result_path.read_text(encoding="utf-8"))
    _validate_summary_for_baseline(summary)
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"{name}.json"
    if out.exists() and not force:
        raise FileExistsError(f"Baseline already exists: {out}. Use --force to replace deliberately.")
    baseline = {
        "baseline_name": name,
        "approved": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_result": str(result_path),
        "metadata": summary["metadata"],
        "aggregates": summary["aggregates"],
    }
    out.write_text(json.dumps(baseline, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def validate_baseline(path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"invalid json: {exc}"]
    errors = []
    if not data.get("approved"):
        errors.append("baseline is not approved")
    if "metadata" not in data:
        errors.append("missing metadata")
    if "aggregates" not in data:
        errors.append("missing aggregates")
    if not data.get("metadata", {}).get("dataset_version"):
        errors.append("missing dataset_version")
    if not data.get("metadata", {}).get("scoring_version"):
        errors.append("missing scoring_version")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    approve = sub.add_parser("approve")
    approve.add_argument("--result", type=Path, required=True)
    approve.add_argument("--name", required=True)
    approve.add_argument("--output-dir", type=Path, default=Path("evals/baselines"))
    approve.add_argument("--force", action="store_true")
    validate = sub.add_parser("validate")
    validate.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "approve":
        path = approve_baseline(args.result, args.name, args.output_dir, force=args.force)
        print(f"Approved baseline written to {path}")
        return 0
    errors = validate_baseline(args.baseline)
    if errors:
        print("Baseline validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Baseline validation passed")
    return 0


def _validate_summary_for_baseline(summary: dict[str, Any]) -> None:
    if not summary.get("metadata", {}).get("dataset_version"):
        raise ValueError("summary missing metadata.dataset_version")
    if not summary.get("metadata", {}).get("scoring_version"):
        raise ValueError("summary missing metadata.scoring_version")
    if not summary.get("aggregates", {}).get("by_configuration"):
        raise ValueError("summary missing configuration aggregates")


if __name__ == "__main__":
    raise SystemExit(main())
