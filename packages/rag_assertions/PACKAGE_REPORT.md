# Package Report

Generated for Phase 6.

## Architecture

`rag_assertions` is a `src/` layout package with provider-free public models,
a deterministic runner, class-based built-in assertions, compatibility aliases,
examples, tests, and packaging metadata.

## Public API

- `EvidenceItem`
- `ValidationContext`
- `AssertionResult`
- `ValidationResult`
- `AssertionRunner`
- `AssertionProtocol`
- `BaseAssertion`
- Built-in assertion classes under `rag_assertions.assertions`

## Dependencies

Runtime dependencies: none.

Dev dependencies: `pytest`, `build`, `twine`, `ruff`.

## Stability

Stable for 0.1: models, runner, assertion protocol/base, entity/project,
technology, metrics, and dates.

Experimental: `ScopeBoundedAssertion`.

## Build And Verification

- Package tests: `15 passed`.
- Parent repository tests: `95 passed, 2 warnings`.
- Ruff: `All checks passed!`.
- Build: `Successfully built rag_assertions-0.1.0.tar.gz and rag_assertions-0.1.0-py3-none-any.whl`.
- Metadata validation: `twine check` passed for wheel and sdist.
- Clean wheel install: passed in a fresh virtual environment from a temporary run directory; public API import and validation returned `True 0 3`.
- Examples:
  - `basic_usage.py`: printed `True` and `0`.
  - `rag_validation.py`: printed `answer accepted`.
  - `custom_assertion.py`: printed `True`.
- Parent mock benchmark: `evals/results/mock_phase6_regression`.
- Quality gate: `QUALITY GATE: PASS`.
- Phase 5 ablation smoke: `evals/results/experiments/assertion_ablation_phase6_smoke`.

## Compatibility With Parent Application

The parent agent and eval scoring now import `rag_assertions` directly. The old
`assertions/` package contains compatibility wrappers only and no duplicated
assertion implementation.

## Known Limitations

- Deterministic checks do not perform semantic entailment.
- Grounded means supported by supplied evidence, not universally true.
- Evidence can be incorrect or incomplete.
- Numeric equivalence is conservative.
- `ScopeBoundedAssertion` is experimental and lexical.

## Publication Status

PyPI publication not performed. TestPyPI publication not performed. Package
name availability not verified.
