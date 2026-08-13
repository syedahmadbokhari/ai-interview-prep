import json
from pathlib import Path

from evals.live_validation import (
    EXPECTED_CONFIGS,
    SELECTED_QUESTION_IDS,
    _completion,
    main,
    select_items,
    token_totals,
)
from evals.schemas import load_dataset


DATASET = Path("evals/datasets/interview_prep_v1.jsonl")


def test_live_validation_subset_is_representative_and_ordered():
    items = select_items(load_dataset(DATASET), SELECTED_QUESTION_IDS)

    assert [item.id for item in items] == SELECTED_QUESTION_IDS
    counts = {}
    for item in items:
        counts[item.category] = counts.get(item.category, 0) + 1
    assert counts == {
        "single_hop": 3,
        "multi_hop": 3,
        "comparative": 2,
        "adversarial": 2,
    }


def test_live_validation_completion_requires_all_configs():
    records = [
        {"configuration": config}
        for config in EXPECTED_CONFIGS
        for _ in range(10)
    ]

    assert _completion(records, 10)["complete"] is True
    assert _completion(records[:-1], 10)["complete"] is False


def test_token_totals_aggregate_by_config():
    records = [
        {
            "configuration": "pipeline",
            "token_usage": {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12},
        },
        {
            "configuration": "agent_no_assertions",
            "token_usage": {"input_tokens": 5, "output_tokens": 1, "total_tokens": 6},
        },
    ]

    totals = token_totals(records)

    assert totals["total"]["total_tokens"] == 18
    assert totals["by_configuration"]["pipeline"]["input_tokens"] == 10


def test_live_validation_mock_smoke_writes_manifest_and_report(tmp_path: Path):
    run_dir = tmp_path / "live_validation_mock"

    exit_code = main(["--mode", "mock", "--output-dir", str(run_dir)])

    manifest = json.loads((run_dir / "live_validation_manifest.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert manifest["status"] == "complete"
    assert manifest["expected_records"] == 30
    assert manifest["records_completed"] == 30
    assert (run_dir / "LIVE_VALIDATION_REPORT.md").exists()
    assert (run_dir / "results.json").exists()
