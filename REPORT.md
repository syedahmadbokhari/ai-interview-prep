# Phase 1 Report

## 1. What Was Read

- `rag/pipeline.py`: Existing RAG entry point; `RAGPipeline.ask()` retrieves, applies `RELEVANCE_THRESHOLD = 0.30`, refuses without LLM when no chunks pass, then calls the generator.
- `rag/vector_store.py`: FAISS `IndexFlatIP` store with normalized embeddings, persisted `index.faiss` plus `chunks.json`, and `SearchResult` metadata.
- `rag/chunking.py`: Markdown chunker that splits by headings and paragraph-overlaps long sections; `Chunk` stores project/source/heading/citation metadata.
- `rag/embeddings.py`: Local sentence-transformers embedder using `sentence-transformers/all-MiniLM-L6-v2`.
- `rag/generation.py`: Existing Groq-backed answer generation with source-grounded prompt rules.
- `rag/__init__.py`: Empty package initializer.
- `api/main.py`: FastAPI app with `/health`, `/auth/login`, and JWT/rate-limited `/ask` endpoint over the existing pipeline.
- `api/schemas.py`: Pydantic request/response models; `/ask` accepts `QuestionRequest(question, top_k)`.
- `api/auth.py`: JWT bearer authentication with bcrypt password verification.
- `api/settings.py`: Environment and `.env` settings loader for auth, rate limit, and index directory.
- `api/__init__.py`: Empty package initializer.
- `ingest.py`: CLI that chunks `docs/*.md`, embeds chunks, and writes the FAISS index.
- `ask.py`: CLI wrapper around the existing pipeline and retrieval-only mode.
- `tests/conftest.py`: Test path setup and deterministic fake embedder.
- `tests/test_api.py`: API auth, `/ask`, refusal, error, and rate-limit tests using fake pipeline dependency overrides.
- `tests/test_pipeline.py`: Pipeline tests for grounded answers, refusal path, threshold filtering, and generator inputs.
- `tests/test_retrieval.py`: Vector store tests over a fake corpus.
- `tests/test_chunking.py`: Chunking behavior and serialization tests.
- `docs/uk-crime-data-pipeline.md`: Indexed crime data engineering project documentation.
- `docs/uk-retail-data-platform.md`: Indexed retail data platform project documentation.
- `index/chunks.json`: Persisted chunk metadata; 70 chunks total, 23 crime and 47 retail.
- `requirements.txt`: Existing Python dependency list.

Anthropic model check: I verified Anthropic's model docs before coding. The current Sonnet API model ID is `claude-sonnet-4-6`; Anthropic documents the 4.6+ dateless format and lists Sonnet 4.6 as `claude-sonnet-4-6`. Sources: https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions and https://platform.claude.com/docs/en/about-claude/models/overview

## 2. What Was Created

- `agent/__init__.py` - exports the agent result and agent class. Line count: 5.
- `agent/agent.py` - ReAct-style Anthropic `tool_use` loop with max-iteration handling and trace logging. Line count: 168.
- `agent/tools.py` - exactly three Anthropic-schema tools over the existing `VectorStore`: `list_projects`, `get_project_summary`, and `search_technical_details`. Line count: 129.
- `agent/traces.py` - JSONL trace logger with timestamps and session IDs. Line count: 37.
- `tests/test_agent.py` - mocked Anthropic agent-loop tests for single-hop, multi-hop, and max-iteration behavior. Line count: 129.
- `output/agent_traces/486c78edf73e48608688de7361b40a16.jsonl` - live verification trace artifact.
- `REPORT.md` - this report. Line count: 165.

## 3. What Was Modified

- `api/main.py`: Added `get_agent()` dependency and a new `/ask-agent` route. The existing `/ask` route remains unchanged in behavior and still calls `pipeline.ask(body.question, top_k=body.top_k)`.
- `api/schemas.py`: Added `AgentAnswerResponse` with `question`, `answer`, and `trace_path`.
- `tests/test_api.py`: Added a fake agent dependency and one `/ask-agent` API contract test; existing `/ask` tests remain unchanged.
- `requirements.txt`: Added the Anthropic SDK dependency.

Files outside `agent/` touched intentionally: `api/main.py`, `api/schemas.py`, `tests/test_api.py`, `requirements.txt`, and `REPORT.md`.

Unrelated pre-existing worktree items observed and not reverted: `frontend/screenshots/chat.png`, `output/`, `tmp/`, and `tools/`.

## 4. Dependencies Added

- `anthropic>=0.40`: Required to use Anthropic's native Messages API and `tool_use` blocks directly. Installed locally in the venv as `anthropic 0.121.0`.

Transitive packages installed by pip into the local venv: `docstring-parser 0.18.0` and `jiter 0.16.0`. They were not added as direct requirements.

## 5. Test Results

Initial raw `python -m pytest` from the repo root using system Python was blocked by an existing unreadable temp directory:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-7.4.0, pluggy-1.6.0
rootdir: C:\Users\ahmad\Downloads\AI-Interview-prep
collected 0 items / 1 error

=================================== ERRORS ====================================
________________________ ERROR collecting test session ________________________
..\..\AppData\Local\Programs\Python\Python311\Lib\site-packages\_pytest\runner.py:341: in from_call
    result: Optional[TResult] = func()
..\..\AppData\Local\Programs\Python\Python311\Lib\site-packages\_pytest\runner.py:372: in <lambda>
    call = CallInfo.from_call(lambda: list(collector.collect()), "collect")
..\..\AppData\Local\Programs\Python\Python311\Lib\site-packages\_pytest\main.py:723: in collect
    for direntry in visit(argpath, self._recurse):
..\..\AppData\Local\Programs\Python\Python311\Lib\site-packages\_pytest\pathlib.py:707: in visit
    yield from visit(entry.path, recurse)
..\..\AppData\Local\Programs\Python\Python311\Lib\site-packages\_pytest\pathlib.py:707: in visit
    yield from visit(entry.path, recurse)
..\..\AppData\Local\Programs\Python\Python311\Lib\site-packages\_pytest\pathlib.py:703: in visit
    entries = scandir(path)
..\..\AppData\Local\Programs\Python\Python311\Lib\site-packages\_pytest\pathlib.py:679: in scandir
    with os.scandir(path) as s:
E   PermissionError: [WinError 5] Access is denied: 'C:\\Users\\ahmad\\Downloads\\AI-Interview-prep\\tmp\\soffice_convert_f__mvvcl'
=========================== short test summary info ===========================
ERROR  - PermissionError: [WinError 5] Access is denied: 'C:\\Users\\ahmad\\D...
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.50s ===============================
```

The actual suite under `tests/` passes in the project venv:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\ahmad\Downloads\AI-Interview-prep
plugins: anyio-4.14.2
collected 35 items

tests\test_agent.py ...                                                  [  8%]
tests\test_api.py ...............                                        [ 51%]
tests\test_chunking.py .......                                           [ 71%]
tests\test_pipeline.py ....                                              [ 82%]
tests\test_retrieval.py ......                                           [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\ahmad\Downloads\AI-Interview-prep\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/test_api.py::test_ask_with_wrong_signature_is_401
  C:\Users\ahmad\Downloads\AI-Interview-prep\.venv\Lib\site-packages\jwt\api_jwt.py:147: InsecureKeyLengthWarning: The HMAC key is 15 bytes long, which is below the minimum recommended length of 32 bytes for SHA256. See RFC 7518 Section 3.2.
    return self._jws.encode(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 35 passed, 2 warnings in 13.39s =======================
```

Explicit `/ask` confirmation: `tests\test_api.py ............... [ 51%]` includes the existing `/ask` behavior tests, including `test_ask_with_valid_token_returns_grounded_answer` and `test_ask_refusal_passes_through_unchanged`.

## 6. Live Verification

I started a local uvicorn server on `127.0.0.1:8765`. Anthropic was mocked via the FastAPI dependency override; the HTTP calls were real.

```text
GET /health
request: None
status: 200
response: {"status":"ok"}

POST /ask
request: {'question': 'Which warehouse does the crime pipeline use?'}
status: 200
response: {"question":"Which warehouse does the crime pipeline use?","answer":"The old pipeline returns DuckDB from the indexed docs. Sources: crime > Warehouse","grounded":true,"sources":[{"citation":"crime > Warehouse","score":0.671}]}

POST /ask-agent
request: {'question': 'Which warehouse does the crime pipeline use?'}
status: 200
response: {"question":"Which warehouse does the crime pipeline use?","answer":"The crime project uses DuckDB as the warehouse. Sources: crime > Warehouse","trace_path":"output\\agent_traces\\486c78edf73e48608688de7361b40a16.jsonl"}
```

## 7. Trace Sample

```jsonl
{"timestamp": "2026-08-12T21:44:55.646933+00:00", "session_id": "486c78edf73e48608688de7361b40a16", "event": "session_start", "question": "Which warehouse does the crime pipeline use?", "max_iterations": 5}
{"timestamp": "2026-08-12T21:44:55.646933+00:00", "session_id": "486c78edf73e48608688de7361b40a16", "event": "iteration", "iteration": 1, "thought": "Thought: I should list the available projects first.", "tool_calls": [{"id": "toolu_live_1", "name": "list_projects", "input": {}}]}
{"timestamp": "2026-08-12T21:44:55.646933+00:00", "session_id": "486c78edf73e48608688de7361b40a16", "event": "tool_result", "iteration": 1, "tool_use_id": "toolu_live_1", "tool_name": "list_projects", "result": {"projects": ["crime", "retail"]}}
{"timestamp": "2026-08-12T21:44:55.648941+00:00", "session_id": "486c78edf73e48608688de7361b40a16", "event": "iteration", "iteration": 2, "thought": "Thought: I need the relevant technical detail from the crime project.", "tool_calls": [{"id": "toolu_live_2", "name": "search_technical_details", "input": {"project_name": "crime", "query": "duckdb warehouse"}}]}
{"timestamp": "2026-08-12T21:44:55.648941+00:00", "session_id": "486c78edf73e48608688de7361b40a16", "event": "tool_result", "iteration": 2, "tool_use_id": "toolu_live_2", "tool_name": "search_technical_details", "result": {"project_name": "crime", "query": "duckdb warehouse", "results": [{"citation": "crime > Warehouse", "score": 0.802, "text": "The pipeline loads data into a DuckDB warehouse from S3."}, {"citation": "crime > Streaming", "score": 0.0, "text": "Kafka streaming with a producer and consumer in KRaft mode."}]}}
{"timestamp": "2026-08-12T21:44:55.648941+00:00", "session_id": "486c78edf73e48608688de7361b40a16", "event": "iteration", "iteration": 3, "thought": "The crime project uses DuckDB as the warehouse. Sources: crime > Warehouse", "tool_calls": []}
{"timestamp": "2026-08-12T21:44:55.648941+00:00", "session_id": "486c78edf73e48608688de7361b40a16", "event": "final_answer", "answer": "The crime project uses DuckDB as the warehouse. Sources: crime > Warehouse", "iterations": 3}
```

## 8. Known Gaps

- Real Anthropic API calls were not made. Tests and live verification used mocked `client.messages.create` responses.
- Raw `python -m pytest` from the repo root still hits a pre-existing unreadable `tmp/soffice_*` directory during discovery. The committed test suite under `tests/` passes.
- `/ask-agent` accepts the same request shape as `/ask`, including `top_k`, but Phase 1 agent execution does not currently use request-level `top_k`; tools use their own default top-k.
- `search_technical_details` searches the existing FAISS index broadly and filters to the requested project. It does not create a second index.

## 9. What's Not In Phase 1

- No assertions on output quality beyond no-error/control-flow behavior.
- No formal eval set or eval harness.
- No CI/CD changes.
- No library extraction.

# Phase 2 Report - Model Assertions & Grounded Output Validation

## 1. Phase 2 Status

Complete. Phase 2 adds a deterministic post-generation assertion layer to the
agent path only. The baseline `/ask` pipeline remains unchanged. `/ask-agent`
now produces a draft answer, validates it against evidence retrieved during
that agent run, performs at most one controlled correction attempt on failure,
and returns either a validated answer or a safe unverifiable response.

Final test result:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\ahmad\Downloads\AI-Interview-prep
plugins: anyio-4.14.2
collected 56 items

tests\test_agent.py ........                                             [ 14%]
tests\test_api.py ...............                                        [ 41%]
tests\test_assertions.py ................                                [ 69%]
tests\test_chunking.py .......                                           [ 82%]
tests\test_pipeline.py ....                                              [ 89%]
tests\test_retrieval.py ......                                           [100%]

============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\ahmad\Downloads\AI-Interview-prep\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/test_api.py::test_ask_with_wrong_signature_is_401
  C:\Users\ahmad\Downloads\AI-Interview-prep\.venv\Lib\site-packages\jwt\api_jwt.py:147: InsecureKeyLengthWarning: The HMAC key is 15 bytes long, which is below the minimum recommended length of 32 bytes for SHA256. See RFC 7518 Section 3.2.
    return self._jws.encode(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 56 passed, 2 warnings in 4.91s ========================
```

## 2. Architecture Implemented

New package:

```text
assertions/
  __init__.py
  models.py
  runner.py
  project.py
  technology.py
  metrics.py
  dates.py
  scope.py
```

Flow:

```text
question -> agent tool loop -> draft answer -> AssertionRunner
PASS -> return answer
FAIL -> one correction prompt -> AssertionRunner
PASS -> return corrected answer
FAIL -> return safe unverifiable response
```

Evidence provenance is collected from tool outputs during that specific agent
run. `search_technical_details` results become `EvidenceItem` records with
citation, project, text, score, tool name, and query. `get_project_summary`
also contributes summary evidence. The assertion package does not read or
duplicate the full corpus.

## 3. Files Created

- `assertions/__init__.py` - package exports. Line count: 11.
- `assertions/models.py` - `EvidenceItem`, `AssertionResult`, and `ValidationResult`. Line count: 71.
- `assertions/runner.py` - extensible aggregate validation runner. Line count: 62.
- `assertions/project.py` - project existence assertion. Line count: 112.
- `assertions/technology.py` - technology grounding assertion. Line count: 90.
- `assertions/metrics.py` - metric grounding assertion. Line count: 103.
- `assertions/dates.py` - date/year grounding assertion. Line count: 62.
- `assertions/scope.py` - practical scope-boundedness assertion. Line count: 101.
- `tests/test_assertions.py` - assertion and runner unit tests. Line count: 178.

## 4. Files Modified

- `agent/agent.py`: Added evidence collection, structured validation, one correction retry, safe final fallback, and validation trace events.
- `tests/test_agent.py`: Added validation expectations and integration tests for pass, correction, persistent failure, and retry limit.
- `README.md`: Updated architecture, endpoint, test-count, and project-structure documentation for `agent/` and `assertions/`.
- `REPORT.md`: Added this Phase 2 report.

Phase 1 files from the previous step remain present: `api/main.py`,
`api/schemas.py`, `tests/test_api.py`, `requirements.txt`, and `agent/`.
No changes were made to the baseline `/ask` implementation.

## 5. Assertions Implemented

- `project_exists`: Detects project-like claims and checks them against the project registry derived from the active `VectorStore`. Safe refusals for nonexistent projects pass.
- `tech_stack_grounded`: Extracts technology-like terms from technology-claim sentences and checks that each appears in retrieved evidence.
- `metrics_grounded`: Extracts factual project metrics such as percentages, p-values, decimal metrics, counts, and performance figures, then verifies normalized numeric values against retrieved evidence.
- `no_fabricated_dates`: Checks factual years in answers against retrieved evidence while ignoring likely software/model version context.
- `scope_bounded`: A practical first version that checks project-specific factual claim sentences for overlap with salient terms in retrieved evidence. This is deliberately explainable rather than a full entailment model.

Assertions return structured `AssertionResult` objects, not booleans. The
aggregate `ValidationResult` reports `all_passed`, `checks_run`,
`passed_count`, `failed_count`, and failed assertion details.

## 6. Correction / Retry Behaviour

If draft validation fails, the agent appends one controlled correction prompt
listing failed assertions, unsupported claims, and reasons. The correction
call uses the same Anthropic Messages API directly and does not create a
second tool loop. The corrected answer is validated once more.

Retry limit: exactly one assertion-driven retry maximum. If the corrected
answer still fails, the agent returns:

```text
I could not verify enough of the generated answer against the retrieved project evidence, so I won't return it as factual. Failed assertions: ...
```

The original unsupported draft is never silently returned.

## 7. Tracing Changes

JSONL traces now include:

- `draft_answer`
- `validation` with stage `draft`
- retrieved evidence attached to validation events
- `correction_retry` with failed assertions
- `corrected_answer`
- `validation` with stage `corrected`
- `validation_failed_final` when persistent failure occurs
- final answer

The trace logs operational text and validation outcomes. It does not log hidden
chain-of-thought.

## 8. Tests Added

New assertion coverage:

- valid project passes
- fabricated project fails
- grounded technology passes
- fabricated technology fails
- grounded percentage passes
- fabricated percentage fails
- grounded decimal metric passes
- irrelevant numbers are skipped
- grounded year passes
- fabricated year fails
- software/model version numbers are ignored as dates
- grounded scoped claim passes
- unsupported scoped claim fails
- runner aggregate pass/fail/skip counts

New agent integration coverage:

- draft passes assertions and returns immediately
- draft fails and correction attempt occurs
- corrected answer passes and is returned
- draft and correction both fail, producing safe unverifiable response
- retry happens at most once

API regression coverage remains green, including existing `/ask` behavior and
the `/ask-agent` endpoint contract.

## 9. Demonstration Scenarios

Scenario A - grounded response:

```text
answer=The crime project used DuckDB as the warehouse. Sources: crime > Warehouse
assertions_passed=True
retry=False
checks_run=3
failed=[]
trace_path=output\agent_traces\46e0264d10ea479f92debd42c485bce1.jsonl
```

Scenario B - hallucinated metric:

```text
draft validation=False
metrics_grounded=False
retry=True
corrected answer=The crime project used DuckDB as the warehouse. Sources: crime > Warehouse
corrected validation=True
trace_path=output\agent_traces\89f3f26678b64ccd885dc551436db2eb.jsonl
```

Draft failure details:

```text
metrics_grounded failed: The crime project achieved 94% accuracy using DuckDB.
scope_bounded failed: The crime project achieved 94% accuracy using DuckDB.
```

Scenario C - fabricated project:

```text
draft validation=False
project_exists=False
retry=True
answer=The indexed documentation does not contain a Java Fraud Detection project, so I cannot verify an answer.
assertions_passed=True
trace_path=output\agent_traces\c6a0d6abc8984457aff645dd1dd29ab8.jsonl
```

## 10. Known Limitations

- Assertions are deterministic heuristics, not complete natural-language entailment.
- `scope_bounded` is intentionally conservative and term-overlap based; it catches clear unsupported claims but can miss paraphrased hallucinations or fail on sparse evidence.
- Technology extraction uses capitalization and claim-context heuristics; unusual lowercase technologies may be skipped.
- Metric grounding checks numeric presence, not full semantic equivalence.
- `/ask-agent` still accepts `top_k` for request-shape parity, but the Phase 2 agent tools use their own default top-k.
- Real Anthropic API calls were not made during tests or demos; all agent model interactions were mocked.
- Raw repo-root `python -m pytest` can still hit pre-existing unreadable `tmp/soffice_*` directories. The intended suite command `.\.venv\Scripts\python.exe -m pytest tests` passes.

## 11. Deferred To Phase 3+

- 30-50 question benchmark
- comparative pipeline-vs-agent evaluation
- CI/CD eval gates
- PyPI packaging
- frontend validation dashboard
- multi-agent architecture
- agent memory
- LangChain/LangGraph integration
- LLM-judge or NLI-based entailment checks

## 12. Extraction Notes For Future PyPI Package

The assertion system is already isolated from FastAPI, Anthropic, and FAISS.
It depends on plain typed inputs:

- answer text
- `list[EvidenceItem]`
- project registry
- optional question text

This boundary should make extraction straightforward. The main future cleanup
would be replacing the current project-specific heuristics with configurable
claim extractors and optional domain dictionaries while preserving the same
`AssertionResult` / `ValidationResult` API.

---

# Phase 3 Report - Benchmark, Comparative Evaluation & Experimental Validation

## 1. Phase 3 Status

Complete as an evaluation infrastructure phase. A versioned benchmark,
three-way configuration runner, deterministic scoring, aggregation, failure
extraction, reproducibility metadata, and report generation now exist.

Important status: no real Anthropic/Groq benchmark was executed in this
environment because `ANTHROPIC_API_KEY` and `GROQ_API_KEY` were not set. The
generated results in `evals/results/mock_phase3_smoke/` are mocked smoke
results that verify machinery only. They are not evidence of live model
performance, and no A/B/C performance conclusion can yet be made.

## 2. Benchmark Size And Distribution

Dataset: `evals/datasets/interview_prep_v1.jsonl`

- Total questions: 43
- Single-hop: 12
- Multi-hop: 12
- Comparative: 9
- Adversarial / hallucination-inducing: 10

The dataset is intentionally close to the requested 45 questions while staying
within facts supported by the two-document corpus.

## 3. Ground-Truth Methodology

Ground truth is encoded per item with:

- `expected_projects`
- `required_facts`
- fact-level keyword checks
- `forbidden_claims`
- `expected_behavior`
- source references where practical
- difficulty and category

Facts were derived from `docs/uk-crime-data-pipeline.md`,
`docs/uk-retail-data-platform.md`, and the persisted chunk metadata in
`index/chunks.json`. The dataset validator checks duplicate IDs/questions,
invalid categories, invalid behaviours, unsupported projects, missing
keywords, malformed expected/refusal setup, and obvious required/forbidden
contradictions.

## 4. Evaluation Configurations Implemented

- `pipeline`: original baseline RAG pipeline.
- `agent_no_assertions`: same `ReActAgent` implementation with `enable_assertions=False`.
- `agent_with_assertions`: current Phase 2 agent with assertion validation and one correction attempt.

The same dataset runs against all three configurations. Individual assertions
can be disabled for ablations with:

```powershell
.venv\Scripts\python -m evals.runner --config agent_with_assertions --disable-assertion scope
```

## 5. Metrics Implemented

Automatic deterministic metrics:

- required-fact coverage
- factual faithfulness
- project/entity accuracy
- multi-hop completeness
- comparative completeness
- adversarial refusal success
- assertion pass/failure rates by type
- retry/correction rate
- safe fallback rate
- latency
- tool calls
- retrieval operations
- model calls
- token usage field where available

Human scoring support:

- `human_review_template.csv` is generated with 0-2 fields for correctness,
  completeness, relevance, and clarity.

## 6. Files Created

- `evals/__init__.py`
- `evals/schemas.py`
- `evals/scoring.py`
- `evals/metrics.py`
- `evals/reporting.py`
- `evals/runner.py`
- `evals/datasets/interview_prep_v1.jsonl`
- `tests/test_evals.py`
- `evals/results/mock_phase3_smoke/results.json`
- `evals/results/mock_phase3_smoke/summary.json`
- `evals/results/mock_phase3_smoke/results.csv`
- `evals/results/mock_phase3_smoke/failures.jsonl`
- `evals/results/mock_phase3_smoke/comparative_failures.json`
- `evals/results/mock_phase3_smoke/human_review_template.csv`
- `evals/results/mock_phase3_smoke/REPORT.md`

## 7. Files Modified

- `agent/agent.py`: Added `enable_assertions` so the same agent supports both experiment configurations B and C.
- `assertions/runner.py`: Added `disabled_assertions` for ablation runs.
- `README.md`: Added Phase 3 benchmark commands and output description.
- `REPORT.md`: Added this Phase 3 section.

## 8. Tests Added

`tests/test_evals.py` adds coverage for:

- dataset schema validation
- duplicate ID/question detection
- category validation
- unsupported project detection
- required-fact scoring
- adversarial refusal scoring
- aggregation
- assertion metric aggregation
- assertion disabling for ablation
- configuration distinction
- result serialization and failure extraction

Final test result:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\ahmad\Downloads\AI-Interview-prep
plugins: anyio-4.14.2
collected 68 items

tests\test_agent.py ........                                             [ 11%]
tests\test_api.py ...............                                        [ 33%]
tests\test_assertions.py ................                                [ 57%]
tests\test_chunking.py .......                                           [ 67%]
tests\test_evals.py ............                                         [ 85%]
tests\test_pipeline.py ....                                              [ 91%]
tests\test_retrieval.py ......                                           [100%]

======================= 68 passed, 2 warnings in 13.89s =======================
```

## 9. Evaluation Commands

Safe mocked smoke run:

```powershell
.venv\Scripts\python -m evals.runner --config all --runs 1 --mode mock
```

Live benchmark, only when credentials and cost are intended:

```powershell
.venv\Scripts\python -m evals.runner --config all --runs 1 --mode live
```

Repeated runs:

```powershell
.venv\Scripts\python -m evals.runner --config all --runs 3 --mode live
```

Assertion ablation:

```powershell
.venv\Scripts\python -m evals.runner --config agent_with_assertions --mode live --disable-assertion scope
```

## 10. Mocked Smoke Run

Command executed:

```powershell
.venv\Scripts\python -m evals.runner --config all --runs 1 --mode mock --output-dir evals\results\mock_phase3_smoke
```

Output files generated:

- `results.json`
- `summary.json`
- `results.csv`
- `failures.jsonl`
- `comparative_failures.json`
- `human_review_template.csv`
- `REPORT.md`

The mocked summary reports 43 questions per configuration and records
assertion retry causes such as `metrics_grounded`, `project_exists`,
`scope_bounded`, and `tech_stack_grounded`. Again: these values validate
the evaluation framework, not live system quality.

## 11. Important Failure Cases Discovered

Live failure cases are not available because the live benchmark was not run.
The mocked smoke run intentionally produces failures to verify failure
extraction, including adversarial false-premise answers for non-assertion
configurations and assertion-triggered retries for the assertion-enabled
configuration.

Implementation issue found and fixed during Phase 3:

- Mocked evaluation originally loaded the real sentence-transformer pipeline,
  causing a timeout. The fix was general: `--mode mock` now loads existing
  `chunks.json` into a lightweight in-memory store, while `--mode live` still
  uses the real pipeline/index path.

## 12. Limitations

- No live model-performance conclusion can be made until `--mode live` is run.
- Automatic scoring is keyword/fact based and should be supplemented with human review.
- The benchmark covers only the current two-project corpus.
- Source references are included where practical, but not every multi-hop fact has a chunk-level reference yet.
- Mock mode is intentionally synthetic and should not be used as a research result.
- No statistical significance testing is performed; repeated live runs can report variability, but the current smoke run is one mocked run.

## 13. Ready For Phase 4

Phase 4 can consume:

- `summary.json`
- `results.json`
- `results.csv`
- `failures.jsonl`
- `comparative_failures.json`

Metrics available for future CI gates include:

- single-hop fact coverage
- multi-hop fact coverage
- comparative completeness
- faithfulness
- adversarial refusal rate
- assertion pass rate
- correction rate
- safe fallback rate

No CI/CD gates were implemented in Phase 3.

---

# Phase 4 Report - CI/CD Evaluation Gates & Regression Protection

## 1. Phase 4 Status

Complete. The repository now has an ML-aware CI layer that combines software
tests, deterministic benchmark execution, approved mock-baseline comparison,
structured quality-gate output, and separate optional live model evaluation.

No live baseline was fabricated. The only approved baseline is the deterministic
mock baseline generated from an actual mock evaluation run.

## 2. CI Architecture Implemented

Tier 1 - deterministic PR gate:

```text
pytest
-> evals.runner --mode mock
-> evals.quality_gate against evals/baselines/mock_v1.json
-> upload artifacts / write GitHub summary
```

Tier 2 - live model evaluation:

```text
manual or weekly workflow
-> verify GitHub Secrets exist
-> evals.runner --mode live
-> if evals/baselines/live_v1.json exists, run live quality gate
-> upload artifacts
```

PR checks do not require Anthropic or Groq credentials.

## 3. Workflows Implemented

- `.github/workflows/pr-quality.yml`: Runs tests, deterministic mock eval, PR quality gate, job summary, and artifacts.
- `.github/workflows/live-eval.yml`: Manual/weekly live benchmark workflow using GitHub Secrets. If no approved live baseline exists, it reports that clearly rather than inventing one.

Suggested branch-protection required check:

```text
AI Quality Gate / Tests + Deterministic Evaluation Gate
```

Branch protection itself was not configured from code.

## 4. Quality-Gate Design

Created `evals/quality_gate.py`.

Supported gate features:

- structured `quality_gate.json`
- human-readable `QUALITY_GATE.md`
- exit code 0 on pass, nonzero on fail
- hard failures
- absolute minimums
- baseline-relative regression limits
- dataset/scoring/model compatibility checks
- configuration-specific metrics
- cross-configuration comparisons
- explicit missing/invalid metric failures

Example failing output:

```text
QUALITY GATE: FAIL
Policy: pr_gate
- regression.pipeline.fact_coverage_mean: FAIL current=0.5441860465116279 baseline=0.7441860465116279 reason=Metric must not regress by more than 0.001.
```

## 5. Policies Created

- `evals/policies/pr_gate.json`: Deterministic mock PR policy with structural checks, mock-baseline regressions, an adversarial-refusal minimum for the deterministic assertion config, and one cross-config rule.
- `evals/policies/live_gate.json`: Live policy ready for a future approved live baseline. It uses baseline-relative tolerances and avoids unsupported absolute live-quality claims.

## 6. Baseline Management

Created `evals/baseline.py`.

Supported operations:

```powershell
.venv\Scripts\python -m evals.baseline approve --result evals\results\<run>\summary.json --name mock_v1 --output-dir evals\baselines
.venv\Scripts\python -m evals.baseline validate --baseline evals\baselines\mock_v1.json
```

Baselines retain provenance: dataset version, scoring version, model,
configuration list, run metadata, source result path, creation timestamp, and
approved flag. Existing baselines cannot be overwritten unless `--force` is
explicitly passed.

## 7. Baseline Status

Mock baseline:

```text
evals/baselines/mock_v1.json
approved=true
dataset_version=interview_prep_v1
scoring_version=1
source_result=evals\results\mock_pr_gate_current\summary.json
```

Live baseline:

```text
Not present. Not fabricated.
```

The live workflow will run the benchmark but skip live regression gating until
`evals/baselines/live_v1.json` is deliberately approved.

## 8. Files Created

- `evals/quality_gate.py`
- `evals/baseline.py`
- `evals/policies/pr_gate.json`
- `evals/policies/live_gate.json`
- `evals/baselines/mock_v1.json`
- `tests/test_quality_gate.py`
- `.github/workflows/pr-quality.yml`
- `.github/workflows/live-eval.yml`
- `evals/results/mock_pr_gate_current/*`
- `evals/results/gate_demo/*`

## 9. Files Modified

- `evals/runner.py`: Added `SCORING_VERSION` metadata.
- `evals/quality_gate.py`: Added structured gate implementation.
- `README.md`: Added ML Quality CI documentation and exact local commands.
- `REPORT.md`: Added this Phase 4 report.

## 10. Tests Added

`tests/test_quality_gate.py` covers:

- passing gate
- allowed regression
- excessive regression
- absolute minimum failure
- missing metric failure
- invalid metric failure
- dataset mismatch
- scoring-version mismatch
- empty evaluation
- CLI exit codes
- baseline creation
- invalid baseline rejection
- no silent overwrite
- explicit force replacement
- provenance retention

Final local test result:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\ahmad\Downloads\AI-Interview-prep
plugins: anyio-4.14.2
collected 83 items

tests\test_agent.py ........                                             [  9%]
tests\test_api.py ...............                                        [ 27%]
tests\test_assertions.py ................                                [ 46%]
tests\test_chunking.py .......                                           [ 55%]
tests\test_evals.py ............                                         [ 69%]
tests\test_pipeline.py ....                                              [ 74%]
tests\test_quality_gate.py ...............                               [ 92%]
tests\test_retrieval.py ......                                           [100%]

======================= 83 passed, 2 warnings in 10.84s =======================
```

## 11. Local Verification Commands

Executed successfully:

```powershell
.venv\Scripts\python.exe -m pytest tests
.venv\Scripts\python.exe -m evals.runner --config all --runs 1 --mode mock --output-dir evals\results\mock_pr_gate_current
.venv\Scripts\python.exe -m evals.baseline approve --result evals\results\mock_pr_gate_current\summary.json --name mock_v1 --output-dir evals\baselines --force
.venv\Scripts\python.exe -m evals.baseline validate --baseline evals\baselines\mock_v1.json
.venv\Scripts\python.exe -m evals.quality_gate --summary evals\results\mock_pr_gate_current\summary.json --baseline evals\baselines\mock_v1.json --policy evals\policies\pr_gate.json --output-dir evals\results\mock_pr_gate_current
```

## 12. Three Gate Scenarios

Scenario A - healthy change:

```text
QUALITY GATE: PASS
Policy: pr_gate
```

Scenario B - minor allowed regression:

```text
QUALITY GATE: PASS
Policy: pr_gate
```

The synthetic current summary reduced `pipeline.fact_coverage_mean` by 0.0005,
within the PR policy tolerance of 0.001.

Scenario C - real regression:

```text
QUALITY GATE: FAIL
Policy: pr_gate
- regression.pipeline.fact_coverage_mean: FAIL current=0.5441860465116279 baseline=0.7441860465116279 reason=Metric must not regress by more than 0.001.
```

The excessive-regression CLI exited with code 1.

## 13. GitHub Actions Verification

GitHub Actions were not executed locally. The workflow commands themselves were
run locally where practical. YAML was statically reviewed in-repo. The workflows
do not print secrets and do not require paid API credentials in PR CI.

## 14. Security Considerations

- `.env` remains gitignored.
- PR workflow does not require API keys.
- Live workflow reads credentials only from GitHub Secrets.
- Secrets are not printed.
- Uploaded artifacts exclude raw agent trace directories.
- No live baseline is committed.

## 15. Known Limitations

- Mock PR gates validate deterministic infrastructure, not live model quality.
- Live model gating cannot compare until a real live baseline is approved.
- The PR policy uses engineering tolerances, not research-derived thresholds.
- GitHub branch protection must be configured manually in repository settings.
- GitHub Actions could not be fully executed from this local environment.

## 16. Deferred To Phase 5

- Exhaustive assertion ablations
- Human scoring workflow at scale
- Research article/write-up
- PyPI packaging
- Public release/presentation materials
- Live threshold tuning after real benchmark history exists

## 17. Ready For Required Status Check

Yes, the repository is ready to use the deterministic model-quality gate as a
required GitHub status check. Use:

```text
AI Quality Gate / Tests + Deterministic Evaluation Gate
```

This status check detects software failures, benchmark/schema failures,
serialization failures, and regressions against the approved deterministic mock
baseline. Live model quality gates are ready but should not be required until a
real live baseline has been run and deliberately approved.

---

# Phase 5 Report - Assertion Ablation Study

## 1. Status

Complete as an experiment infrastructure upgrade. Live ablation evidence is
not yet available because the prior Anthropic live call failed for insufficient
account credit. Current Phase 5 mock outputs must be read as:

```text
MOCK INFRASTRUCTURE VALIDATION ONLY
LIVE ABLATION STUDY NOT YET EXECUTED
```

## 2. What Was Added

- `evals/experiments/ablation.py` - CLI for full and focused assertion ablation runs.
- `evals/experiments/analysis.py` - architecture metrics, paired comparisons, marginal deltas, assertion/category matrix, correction effectiveness, safety/usefulness tradeoff, operational cost, and provisional API-freeze recommendations.
- `evals/experiments/failure_analysis.py` - failure taxonomy, false-positive candidates, false-negative candidates, correction-failure review queue, and human review sample.
- `evals/experiments/statistics.py` - mean/median/p95 helpers without extra dependencies.
- `tests/test_phase5_experiments.py` - API-free Phase 5 unit and mock smoke tests.

## 3. Experiment Configurations

The study compares the original pipeline, agent without assertions, agent
with all assertions, and leave-one-out ablations:

```text
agent_without_project_exists       -> disables project_exists
agent_without_technology_grounded  -> disables tech_stack_grounded
agent_without_metrics_grounded     -> disables metrics_grounded
agent_without_dates_grounded       -> disables no_fabricated_dates
agent_without_scope_bounded        -> disables scope_bounded
```

The implementation reuses the existing `AssertionRunner(disabled_assertions=...)`
architecture and does not duplicate the agent path.

## 4. How To Run

```powershell
.venv\Scripts\python -m evals.experiments.ablation --mode mock --runs 1
.venv\Scripts\python -m evals.experiments.ablation --mode mock --runs 1 --category adversarial --assertion metrics_grounded
```

Live run, only after provider credit is available:

```powershell
.venv\Scripts\python -m evals.experiments.ablation --mode live --runs 3
```

## 5. Outputs

Each run writes `manifest.json`, `results.json`, `results.csv`,
`summary.json`, `failures.jsonl`, `comparisons.json`,
`failure_analysis.json`, `PHASE5_REPORT.md`, `FAILURE_ANALYSIS.md`,
`human_review_phase5.csv`, `tables/*.csv`, and `charts/*.svg` under
`evals/results/experiments/assertion_ablation_<timestamp>/` unless an
explicit output directory is supplied.

## 6. Provisional API-Freeze Recommendation

Until live evidence exists, keep `EvidenceItem`, `AssertionResult`,
`ValidationResult`, `AssertionRunner(disabled_assertions=...)`, and individual
assertion names stable for experimentation. Rename nothing; add fields only
with defaults.

---

# Phase 6 Report - Standalone Assertion Package

## 1. Motivation

Phase 6 extracts the deterministic assertion engine into an independently
installable Python package so it can be reused outside the Interview Prep
Assistant without depending on the app, agent, API, evals, or any model
provider SDK.

## 2. Package Boundary

```text
packages/rag_assertions/
  pyproject.toml
  README.md
  LICENSE
  CHANGELOG.md
  CONTRIBUTING.md
  SECURITY.md
  PACKAGE_REPORT.md
  MANIFEST.in
  src/rag_assertions/
  tests/
  examples/
```

Distribution name: `rag-assertions`.
Import name: `rag_assertions`.
Version: `0.1.0`.
Package name availability: PACKAGE NAME AVAILABILITY NOT VERIFIED.

## 3. Public API

Stable for 0.1:

- `EvidenceItem`
- `ValidationContext`
- `AssertionResult`
- `ValidationResult`
- `AssertionRunner`
- `AssertionProtocol`
- `BaseAssertion`
- `EntityExistsAssertion` / `ProjectExistsAssertion`
- `TechnologyGroundedAssertion` / `TechStackGroundedAssertion`
- `MetricsGroundedAssertion`
- `DateGroundedAssertion` / `NoFabricatedDatesAssertion`

Experimental:

- `ScopeBoundedAssertion`

## 4. Genericisation

`EvidenceItem` now uses generic fields: `text`, `source`, `entity`,
`chunk_id`, `score`, and `metadata`. The old project/citation vocabulary is
available as compatibility properties/wrappers. Entity validation is generic;
the project assertion is a compatibility specialization. The package has no
runtime dependencies and no Anthropic, OpenAI, Groq, LangChain, LangGraph,
FastAPI, agent, API, or eval imports.

## 5. Parent Migration

`agent/agent.py`, `evals/runner.py`, and `evals/scoring.py` now consume
`rag_assertions` directly. The legacy `assertions/` directory remains only as
thin compatibility wrappers for older imports and tests. There is one source
of truth for assertion behavior.

## 6. Verification Results

```text
Package tests: 15 passed
Parent tests: 95 passed, 2 warnings
Ruff: All checks passed
Build: wheel and sdist built successfully
Metadata: twine check passed for wheel and sdist
Clean install: wheel installed in fresh venv; public API validation passed
Examples: basic_usage, rag_validation, custom_assertion all ran successfully
Phase 3 mock eval: evals/results/mock_phase6_regression
Phase 4 quality gate: QUALITY GATE: PASS
Phase 5 smoke: evals/results/experiments/assertion_ablation_phase6_smoke
```

No baseline was approved or changed.

## 7. Publication Status

PyPI publication: not performed.
TestPyPI publication: not performed.
GitHub release: not created.
External adoption: not claimed.

Manual future release commands are documented in `docs/RELEASE_CHECKLIST.md`.
Live ablation evidence is still pending; mock results are not empirical
model-quality claims.
