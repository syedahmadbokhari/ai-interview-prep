# Contributing

## Setup

```bash
cd packages/rag_assertions
python -m venv .venv
.venv\Scripts\pip install -e .[dev]
python -m pytest
```

## Adding An Assertion

- Implement `BaseAssertion` or satisfy `AssertionProtocol`.
- Give the assertion a unique `name`.
- Return `AssertionResult` via `pass_result()` or `fail_result()`.
- Avoid hidden network calls in deterministic assertions.
- Add focused tests for pass, fail, and skip behavior.
- Document limitations honestly.

## Pull Requests

- Keep runtime dependencies minimal.
- Preserve public API compatibility when possible.
- Add tests for behavior changes.
- Do not claim empirical effectiveness without live evidence.
