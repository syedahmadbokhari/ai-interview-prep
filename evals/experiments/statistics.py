"""Small dependency-free statistics helpers for experiment reports."""

from __future__ import annotations

from statistics import mean, median


def summarize_numbers(values: list[float]) -> dict[str, float | None]:
    clean = [float(value) for value in values if value is not None]
    return {
        "mean": mean(clean) if clean else None,
        "median": median(clean) if clean else None,
        "p95": percentile(clean, 95) if clean else None,
    }


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct / 100
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight
