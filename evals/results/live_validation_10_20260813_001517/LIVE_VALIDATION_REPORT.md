# Controlled Live Validation Report

## 1. Purpose

Controlled 10-question live validation before deciding whether to spend credits on the complete 43-question benchmark.

## 2. Configuration

- Mode: `live`
- Model: `claude-sonnet-4-6`
- Dataset: `interview_prep_v1`
- Temperature: `0`
- Scoring version: `1`
- Selected IDs: single_001, single_007, single_011, multi_001, multi_006, multi_010, comp_001, comp_008, adv_001, adv_008
- Scoring notes: Rescored saved answers after fixing negated adversarial forbidden-claim detection; no new API calls were made.

## 3. Dataset Subset

- single_hop: 3
- multi_hop: 3
- comparative: 2
- adversarial: 2

## 4. Completion

- Expected records: 30
- Actual records: 30
- Complete: True

## 5. Architecture Comparison

| Configuration | Count | Fact | Faithfulness | Project | Multi-hop | Comparative | Adv Refusal | Latency ms | Model Calls | Tool Calls | Total Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| agent_no_assertions | 10 | 0.650 | 0.800 | 0.800 | 0.500 | 0.500 | 0.500 | 20214.153 | 4 | 4.800 | 131298 |
| agent_with_assertions | 10 | 0.300 | 0.700 | 0.300 | 0.000 | 0.000 | 1.000 | 17057.152 | 4.600 | 5 | 125705 |
| pipeline | 10 | 0.600 | 0.700 | 0.750 | 0.333 | 0.000 | 1.000 | 288.859 | 0.800 | 0 | 6991 |

## 6. Assertion Behaviour

{
  "total_run": 35,
  "total_passed": 20,
  "total_failed": 15,
  "pass_rate": 0.5714285714285714,
  "by_type": {
    "metrics_grounded": {
      "run": 6,
      "passed": 2,
      "failed": 4,
      "pass_rate": 0.3333333333333333,
      "failure_rate": 0.6666666666666666
    },
    "project_exists": {
      "run": 12,
      "passed": 7,
      "failed": 5,
      "pass_rate": 0.5833333333333334,
      "failure_rate": 0.4166666666666667
    },
    "scope_bounded": {
      "run": 9,
      "passed": 9,
      "failed": 0,
      "pass_rate": 1.0,
      "failure_rate": 0.0
    },
    "tech_stack_grounded": {
      "run": 8,
      "passed": 2,
      "failed": 6,
      "pass_rate": 0.25,
      "failure_rate": 0.75
    }
  },
  "retry_causes": {
    "metrics_grounded": 3,
    "project_exists": 3,
    "tech_stack_grounded": 3
  }
}

## 7. Representative Cases

```json
{
  "question_id": "single_001",
  "label": "pipeline_vs_agent_no_assertions",
  "left_config": "pipeline",
  "left_scores": {
    "fact": 1.0,
    "faithfulness": 1.0,
    "project": 1.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "left_answer": "The UK Crime Data Pipeline uses DuckDB as its warehouse, as indicated by the command `python -m warehouse.setup_duckdb` in the setup instructions.\nSources: uk-crime-data-pipeline > 3. Load the sample data (no AWS needed to start)",
  "right_config": "agent_no_assertions",
  "right_scores": {
    "fact": 1.0,
    "faithfulness": 0.0,
    "project": 1.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "right_answer": "The UK Crime Data Pipeline uses **DuckDB** as its data warehouse.\n\nSpecifically, the warehouse layer is handled by `warehouse/setup_duckdb.py`, which creates DuckDB schemas, loads CSV data, and deduplicates records on `crime_id`. DuckDB reads from AWS S3 via its **httpfs extension**, meaning no Redshift or other cloud warehouse is needed. The raw data lands in a `raw.crimes` table, which is then transformed by dbt into staging models and analytical marts.\n\n**Sources:** uk-crime-data-pipeline > P"
}
```

```json
{
  "question_id": "single_001",
  "label": "agent_no_assertions_vs_agent_with_assertions",
  "left_config": "agent_no_assertions",
  "left_scores": {
    "fact": 1.0,
    "faithfulness": 0.0,
    "project": 1.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "left_answer": "The UK Crime Data Pipeline uses **DuckDB** as its data warehouse.\n\nSpecifically, the warehouse layer is handled by `warehouse/setup_duckdb.py`, which creates DuckDB schemas, loads CSV data, and deduplicates records on `crime_id`. DuckDB reads from AWS S3 via its **httpfs extension**, meaning no Redshift or other cloud warehouse is needed. The raw data lands in a `raw.crimes` table, which is then transformed by dbt into staging models and analytical marts.\n\n**Sources:** uk-crime-data-pipeline > P",
  "right_config": "agent_with_assertions",
  "right_scores": {
    "fact": 0.0,
    "faithfulness": 0.0,
    "project": 0.0,
    "adversarial": null,
    "safe_fallback": true
  },
  "right_answer": "I could not verify enough of the generated answer against the retrieved project evidence, so I won't return it as factual. Failed assertions: tech_stack_grounded."
}
```

```json
{
  "question_id": "single_011",
  "label": "agent_no_assertions_vs_agent_with_assertions",
  "left_config": "agent_no_assertions",
  "left_scores": {
    "fact": 1.0,
    "faithfulness": 1.0,
    "project": 1.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "left_answer": "The geospatial dashboard in the **UK Crime Data Pipeline** project is built using **Streamlit + Folium**:\n\n- **Streamlit** provides the interactive web dashboard framework (charts, UI components, etc.).\n- **Folium** handles the geospatial/map layer, rendering interactive crime maps within the Streamlit app.\n\nThe dashboard is launched via `streamlit run dashboard/app.py` and is accessible at `http://localhost:8501` (also available as a Docker Compose service).\n\n**Sources:** `uk-crime-data-pipelin",
  "right_config": "agent_with_assertions",
  "right_scores": {
    "fact": 0.0,
    "faithfulness": 0.0,
    "project": 0.0,
    "adversarial": null,
    "safe_fallback": true
  },
  "right_answer": "I could not verify enough of the generated answer against the retrieved project evidence, so I won't return it as factual. Failed assertions: tech_stack_grounded."
}
```

```json
{
  "question_id": "multi_001",
  "label": "agent_no_assertions_vs_agent_with_assertions",
  "left_config": "agent_no_assertions",
  "left_scores": {
    "fact": 1.0,
    "faithfulness": 1.0,
    "project": 1.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "left_answer": "Both projects use Docker. Here's a detailed breakdown of the role Docker plays in each:\n\n---\n\n## 🐳 Docker Usage Across Ahmad's Projects\n\n### 1. `uk-crime-data-pipeline`\n**Docker is the primary local deployment mechanism for the entire service stack.**\n\n- **Docker Compose** is used to spin up and coordinate multiple services together: **Airflow** (orchestration), **PostgreSQL** (Airflow metadata DB), **Redis** (Celery broker), **Streamlit** (dashboard), and the **FastAPI** REST API service. A sin",
  "right_config": "agent_with_assertions",
  "right_scores": {
    "fact": 0.0,
    "faithfulness": 0.0,
    "project": 0.0,
    "adversarial": null,
    "safe_fallback": true
  },
  "right_answer": "I could not verify enough of the generated answer against the retrieved project evidence, so I won't return it as factual. Failed assertions: project_exists, tech_stack_grounded, metrics_grounded."
}
```

```json
{
  "question_id": "multi_006",
  "label": "pipeline_vs_agent_no_assertions",
  "left_config": "pipeline",
  "left_scores": {
    "fact": 0.0,
    "faithfulness": 1.0,
    "project": 1.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "left_answer": "The projects that discuss data quality are the uk-retail-data-platform. The quality controls documented include:\n- Implementing upstream data validation at the point of entry to prevent corrupted pricing data (11% of products had corrupted pricing data).\n- Detecting and dropping zero-price rows with a logged warning.\n- Imputing missing values with column medians rather than zero.\n- Replacing rating values of 0 (indicating missing data) with the median before model training.\n- Log-transforming re",
  "right_config": "agent_no_assertions",
  "right_scores": {
    "fact": 0.5,
    "faithfulness": 1.0,
    "project": 1.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "right_answer": "I now have comprehensive evidence from both projects. Here is a full breakdown:\n\n---\n\n## 📊 Data Quality Across Ahmad's Projects\n\nBoth projects discuss data quality, but with notably different levels of formalization.\n\n---\n\n### 1. 🔵 UK Crime Data Pipeline — Multi-Layer Quality Controls\n\nThis project has the most mature and explicitly documented data quality architecture, built in **three complementary layers**:\n\n#### Layer 1: Airflow DAG Row-Count Gates\n- **`_validate_raw`** — checks that the raw"
}
```

```json
{
  "question_id": "multi_006",
  "label": "agent_no_assertions_vs_agent_with_assertions",
  "left_config": "agent_no_assertions",
  "left_scores": {
    "fact": 0.5,
    "faithfulness": 1.0,
    "project": 1.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "left_answer": "I now have comprehensive evidence from both projects. Here is a full breakdown:\n\n---\n\n## 📊 Data Quality Across Ahmad's Projects\n\nBoth projects discuss data quality, but with notably different levels of formalization.\n\n---\n\n### 1. 🔵 UK Crime Data Pipeline — Multi-Layer Quality Controls\n\nThis project has the most mature and explicitly documented data quality architecture, built in **three complementary layers**:\n\n#### Layer 1: Airflow DAG Row-Count Gates\n- **`_validate_raw`** — checks that the raw",
  "right_config": "agent_with_assertions",
  "right_scores": {
    "fact": 0.0,
    "faithfulness": 1.0,
    "project": 0.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "right_answer": "Let me re-examine the source material carefully before answering."
}
```

```json
{
  "question_id": "multi_010",
  "label": "pipeline_vs_agent_no_assertions",
  "left_config": "pipeline",
  "left_scores": {
    "fact": 0.0,
    "faithfulness": 0.0,
    "project": 0.5,
    "adversarial": null,
    "safe_fallback": false
  },
  "left_answer": "The provided project documentation does not contain information to answer this. \nSources: uk-retail-data-platform > What This System Does; uk-retail-data-platform > Technology Stack",
  "right_config": "agent_no_assertions",
  "right_scores": {
    "fact": 0.0,
    "faithfulness": 1.0,
    "project": 0.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "right_answer": "Stopped after reaching max_iterations before Claude returned a final text-only answer."
}
```

```json
{
  "question_id": "comp_001",
  "label": "pipeline_vs_agent_no_assertions",
  "left_config": "pipeline",
  "left_scores": {
    "fact": 0.0,
    "faithfulness": 0.0,
    "project": 0.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "left_answer": "The provided project documentation does not contain information to answer this.",
  "right_config": "agent_no_assertions",
  "right_scores": {
    "fact": 1.0,
    "faithfulness": 1.0,
    "project": 1.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "right_answer": "I now have comprehensive evidence from both projects. Here's the full comparison:\n\n---\n\n## 🏭 Warehouse Comparison: UK Retail Data Platform vs. UK Crime Data Pipeline\n\n### UK Retail Data Platform — A Multi-Tier, Multi-Warehouse Architecture\n\nThe Retail platform takes a **layered, environment-aware approach** with multiple warehouse backends that coexist rather than replace each other:\n\n| Environment | Warehouse | Why |\n|---|---|---|\n| **Local / CI** | **SQLite** | Zero-server, file-based (`retail"
}
```

```json
{
  "question_id": "comp_001",
  "label": "agent_no_assertions_vs_agent_with_assertions",
  "left_config": "agent_no_assertions",
  "left_scores": {
    "fact": 1.0,
    "faithfulness": 1.0,
    "project": 1.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "left_answer": "I now have comprehensive evidence from both projects. Here's the full comparison:\n\n---\n\n## 🏭 Warehouse Comparison: UK Retail Data Platform vs. UK Crime Data Pipeline\n\n### UK Retail Data Platform — A Multi-Tier, Multi-Warehouse Architecture\n\nThe Retail platform takes a **layered, environment-aware approach** with multiple warehouse backends that coexist rather than replace each other:\n\n| Environment | Warehouse | Why |\n|---|---|---|\n| **Local / CI** | **SQLite** | Zero-server, file-based (`retail",
  "right_config": "agent_with_assertions",
  "right_scores": {
    "fact": 0.0,
    "faithfulness": 1.0,
    "project": 0.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "right_answer": "Stopped after reaching max_iterations before Claude returned a final text-only answer."
}
```

```json
{
  "question_id": "comp_008",
  "label": "pipeline_vs_agent_no_assertions",
  "left_config": "pipeline",
  "left_scores": {
    "fact": 0.0,
    "faithfulness": 0.0,
    "project": 0.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "left_answer": "No relevant information was found in the indexed project documentation for this question, so I won't attempt an answer.",
  "right_config": "agent_no_assertions",
  "right_scores": {
    "fact": 0.0,
    "faithfulness": 1.0,
    "project": 1.0,
    "adversarial": null,
    "safe_fallback": false
  },
  "right_answer": "I now have comprehensive evidence from both projects. Here is the full comparison:\n\n---\n\n## Orchestration Design Comparison\n\nBoth projects use **Apache Airflow** as their orchestration engine and share Docker Compose as the deployment vehicle, but their DAG topologies, scheduling philosophies, and quality-gate strategies differ meaningfully.\n\n---\n\n### 1. DAG Topology & Task Structure\n\n| Dimension | UK Crime Data Pipeline | UK Retail Data Platform |\n|---|---|---|\n| **DAG file** | `dags/crime_pipe"
}
```

## 8. Operational Usage

{
  "tokens": {
    "total": {
      "input_tokens": 247239,
      "output_tokens": 16755,
      "total_tokens": 263994
    },
    "by_configuration": {
      "agent_no_assertions": {
        "input_tokens": 122475,
        "output_tokens": 8823,
        "total_tokens": 131298
      },
      "agent_with_assertions": {
        "input_tokens": 118276,
        "output_tokens": 7429,
        "total_tokens": 125705
      },
      "pipeline": {
        "input_tokens": 6488,
        "output_tokens": 503,
        "total_tokens": 6991
      }
    }
  },
  "runtime_seconds": 376.58
}

## 9. Full Benchmark Estimate

{
  "scale_factor": 4.3,
  "estimated_runtime_seconds": 1619.29,
  "estimated_model_calls": 404,
  "estimated_input_tokens": 1063128,
  "estimated_output_tokens": 72046,
  "estimated_total_tokens": 1135174
}

## 10. Limitations

- This is a 10-question validation subset, not a statistically significant benchmark.
- Negative results are preserved and should not trigger prompt/assertion tuning without review.
- Token-to-cost estimates are not embedded here because provider pricing is not configured in the repo.

## 11. GO / NO-GO

GO WITH CAUTION - benchmark infrastructure completed; review disagreements and credit estimate before the full 43-question run.

## 12. Next Command

```powershell
.\.venv\Scripts\python.exe -m evals.runner --config all --mode live --runs 1 --output-dir evals\results\live_full_43_<timestamp>
```

## Assertion Failure Details

```json
{
  "question_id": "single_001",
  "question": "What warehouse does the UK Crime Data Pipeline use?",
  "answer": "I could not verify enough of the generated answer against the retrieved project evidence, so I won't return it as factual. Failed assertions: tech_stack_grounded.",
  "failed_assertions": [
    {
      "assertion": "tech_stack_grounded",
      "claim": "Pipeline",
      "reason": "Claimed technology was not found in the supplied evidence.",
      "evidence": [
        {
          "text": "[data.police.uk](https://data.police.uk) — UK government open data, updated monthly.\nNo authentication required. Coverage: all 43 territorial police forces in England and Wales.\nNatural incremental loading story: new months appear on the 5th of the following month.",
          "source": "uk-crime-data-pipeline > Data Source",
          "entity": "uk-crime-data-pipeline",
          "chunk_id": null,
          "score": 0.319,
          "metadata": {
            "tool_name": "search_technical_details",
            "query": "data warehouse"
          },
          "citation": "uk-crime-data-pipeline > Data Source",
          "project": "uk-crime-data-pipeline"
        },
        {
          "text": "| Layer | File | What it does |\n|---|---|---|\n| Download | [ingestion/download_data.py](ingestion/download_data.py) | Downloads CSVs from data.police.uk, extracts from zip |\n| Watermark | [ingestion/watermark.py](ingestion/watermark.py) | Tracks last processed month per force — incremental loading |\n| S3 Upload | [ingestion/upload_to_s3.py](ingestion/upload_to_s3.py) | Uploads with Hive partitioning, idempotent via HEAD check |\n| Warehouse | [warehouse/setup_duckdb.py](warehouse/setup_duckdb.py) | Creates DuckDB schemas, loads CSV, deduplicates on crime_id |\n| Staging | [dbt_crime/models/staging/stg_crimes.sql](dbt_crime/models/staging/stg_crimes.sql) | Cleans nulls, derives year/month/district columns |\n| Mart: category | [dbt_crime/models/marts/crime_by_category.sql](dbt_crime/models/marts/crime_by_category.sql) | Crime counts + % under investigation by type/force/month |\n| Mart: trend | [dbt_crime/models/marts/crime_by_month.sql](dbt_crime/models/marts/crime_by_month.sql) | Monthly totals with YoY % change |\n| Mart: force | [dbt_crime/models/marts/crime_by_force.sql](dbt_crime/models/marts/crime_by_force.sql) | Outcome rates (resolved / no suspect / open) per force |\n| Mart: hotspots | [dbt_crime/models/marts/crime_hotspots.sql](dbt_crime/models/marts/crime_hotspots.sql) | LSOA centroid + crime breakdown + High/Medium/Low tier |\n| DAG | [dags/crime_pipeline_dag.py](dags/crime_pipeline_dag.py) | 9-task Airflow DAG with validation gates and watermark update |\n| Data Quality | [data_quality/validate_raw_crimes.py](data_quality/validate_raw_crimes.py) | Great Expectations suite for raw.crimes, run as a DAG task |\n| Streaming Producer | [streaming/producer.py](streaming/producer.py) | Publishes a CSV's rows to Kafka one at a time, with pacing |\n| Streaming Consumer | [streaming/consumer.py](streaming/consumer.py) | Micro-batches, validates via the same GE suite, writes to DuckDB/S3 |\n| Dashboard | [dashboard/app.py](dashboard/app.py) | Streamlit: trends, breakdown, Folium map, force comparison |\n| Tests | [tests/](tests/) | 40+ pytest tests — mocked S3/Kafka, in-memory DuckDB, GE suite |\n| CI | [.github/workflows/ci.yml](.github/workflows/ci.yml) | pytest + dbt compile on push |\n\n---",
          "source": "uk-crime-data-pipeline > Pipeline Components",
          "entity": "uk-crime-data-pipeline",
          "chunk_id": null,
          "score": 0.318,
          "metadata": {
            "tool_name": "search_technical_details",
            "query": "data warehouse"
          },
          "citation": "uk-crime-data-pipeline > Pipeline Components",
          "project": "uk-crime-data-pipeline"
        }
      ]
    }
  ],
  "retry_occurred": true,
  "safe_fallback": true,
  "trace_stages": [
    "session_start",
    "iteration",
    "tool_result",
    "iteration",
    "tool_result",
    "iteration",
    "draft_answer",
    "validation",
    "correction_retry",
    "corrected_answer",
    "validation",
    "validation_failed_final",
    "final_answer"
  ]
}
```

```json
{
  "question_id": "single_011",
  "question": "What dashboard technology is used for the crime pipeline's geospatial dashboard?",
  "answer": "I could not verify enough of the generated answer against the retrieved project evidence, so I won't return it as factual. Failed assertions: tech_stack_grounded.",
  "failed_assertions": [
    {
      "assertion": "tech_stack_grounded",
      "claim": "UK, Crime",
      "reason": "Claimed technology was not found in the supplied evidence.",
      "evidence": [
        {
          "text": "| Layer | Tool | Reason |\n|---|---|---|\n| Storage | AWS S3 | Cloud credential, Hive partitioning |\n| Processing | Python + Pandas | Data wrangling, type safety |\n| Warehouse | DuckDB | Free, S3-native via httpfs, dbt-compatible |\n| Transformation | dbt | Modular SQL, schema tests, lineage |\n| Orchestration | Airflow | DAG with validation gates and watermarks |\n| Testing | pytest + moto | Mocked S3, in-memory DuckDB |\n| CI/CD | GitHub Actions | pytest + dbt compile on every push |\n| Dashboard | Streamlit + Folium | Interactive charts and geospatial map |\n| REST API | FastAPI + SQLAlchemy | JWT-authenticated endpoints, deployed on Railway |\n| IaC | Terraform | Provisions the S3 bucket + least-privilege IAM, replacing manual console setup |\n| Data Quality | Great Expectations | Formalizes the pipeline's hand-written validation into an Expectation Suite + Data Docs |\n| Streaming | Kafka (KRaft) + kafka-python | Producer/consumer architecture demo — see honesty note below |\n\n---",
          "source": "uk-crime-data-pipeline > Stack",
          "entity": "uk-crime-data-pipeline",
          "chunk_id": null,
          "score": 0.266,
          "metadata": {
            "tool_name": "search_technical_details",
            "query": "geospatial dashboard technology"
          },
          "citation": "uk-crime-data-pipeline > Stack",
          "project": "uk-crime-data-pipeline"
        },
        {
          "text": "| Layer | Tool | Reason |\n|---|---|---|\n| Storage | AWS S3 | Cloud credential, Hive partitioning |\n| Processing | Python + Pandas | Data wrangling, type safety |\n| Warehouse | DuckDB | Free, S3-native via httpfs, dbt-compatible |\n| Transformation | dbt | Modular SQL, schema tests, lineage |\n| Orchestration | Airflow | DAG with validation gates and watermarks |\n| Testing | pytest + moto | Mocked S3, in-memory DuckDB |\n| CI/CD | GitHub Actions | pytest + dbt compile on every push |\n| Dashboard | Streamlit + Folium | Interactive charts and geospatial map |\n| REST API | FastAPI + SQLAlchemy | JWT-authenticated endpoints, deployed on Railway |\n| IaC | Terraform | Provisions the S3 bucket + least-privilege IAM, replacing manual console setup |\n| Data Quality | Great Expectations | Formalizes the pipeline's hand-written validation into an Expectation Suite + Data Docs |\n| Streaming | Kafka (KRaft) + kafka-python | Producer/consumer architecture demo — see honesty note below |\n\n---",
          "source": "uk-crime-data-pipeline > Stack",
          "entity": "uk-crime-data-pipeline",
          "chunk_id": null,
          "score": 0.266,
          "metadata": {
            "tool_name": "search_technical_details",
            "query": "geospatial dashboard technology"
          },
          "citation": "uk-crime-data-pipeline > Stack",
          "project": "uk-crime-data-pipeline"
        }
      ]
    }
  ],
  "retry_occurred": true,
  "safe_fallback": true,
  "trace_stages": [
    "session_start",
    "iteration",
    "tool_result",
    "iteration",
    "tool_result",
    "iteration",
    "draft_answer",
    "validation",
    "correction_retry",
    "corrected_answer",
    "validation",
    "validation_failed_final",
    "final_answer"
  ]
}
```

```json
{
  "question_id": "multi_001",
  "question": "Which indexed projects use Docker, and what role does Docker play in each?",
  "answer": "I could not verify enough of the generated answer against the retrieved project evidence, so I won't return it as factual. Failed assertions: project_exists, tech_stack_grounded, metrics_grounded.",
  "failed_assertions": [
    {
      "assertion": "project_exists",
      "claim": "The project",
      "reason": "Entity-like reference 'The project' is not in the known entity registry.",
      "evidence": []
    },
    {
      "assertion": "tech_stack_grounded",
      "claim": "Bringing, Infrastructure, Code, Structure, Engineer",
      "reason": "Claimed technology was not found in the supplied evidence.",
      "evidence": [
        {
          "text": "| | BigQuery | Snowflake |\n|---|---|---|\n| Partitioning | A separate, explicit mechanism — `PARTITION BY DATE(event_timestamp)` prunes whole day-partitions | **Doesn't exist as a separate concept.** Every table is auto-divided into micro-partitions (~50–500MB uncompressed each) regardless of configuration |\n| Clustering | A second, independent mechanism — `CLUSTER BY product_id` sorts within partitions | The *only* mechanism — `CLUSTER BY (event_timestamp, product_id)` is defined once, doing the job BigQuery splits across two features |\n| Clustering maintenance cost | Free, folded into background storage optimisation | **Not free** — Snowflake's Automatic Clustering service re-sorts micro-partitions as data changes, and this background service itself consumes credits (Snowflake's own docs note you can suspend it \"to control cost\") |\n| Cost model | Pay per bytes scanned ($6.25/TiB on-demand), a **free dry-run** estimates this with zero execution | Pay per warehouse-size × time (e.g. X-Small = 1 credit/hour, billed per-second, 60s minimum) — **no free dry-run equivalent exists** |\n| How this repo measures efficiency | `job_config.dry_run=True` — real bytes-scanned figures, zero query cost | Query must actually **run** on a warehouse, then `INFORMATION_SCHEMA.QUERY_HISTORY()` reports real `partitions_scanned`/`partitions_total`/`bytes_scanned`/elapsed time — a small, real, unavoidable cost, not a script limitation |\n\n**Why the fact table is clustered on `(event_timestamp, product_id)` together, not split:** every representative query filters on both a date range and a specific `product_id` (the same query `bigquery_cost_comparison.py` uses). BigQuery hands the date filter to partitioning and the product filter to clustering; Snowflake has nowhere else to send the date filter, so the same clustering key has to serve both — date first (coarser, more selective at this table's size), product_id second.",
          "source": "uk-retail-data-platform > 🆚 Cloud Data Warehouse Comparison (BigQuery vs Snowflake) (part 2)",
          "entity": "uk-retail-data-platform",
          "chunk_id": null,
          "score": 0.219,
          "metadata": {
            "tool_name": "search_technical_details",
            "query": "Docker usage role containerization"
          },
          "citation": "uk-retail-data-platform > 🆚 Cloud Data Warehouse Comparison (BigQuery vs Snowflake) (part 2)",
          "project": "uk-retail-data-platform"
        },
        {
          "text": "[uk-crime-data-pipeline > UK Crime Data Pipeline (Introduction)]\n[![CI](https://github.com/syedahmadbokhari/UK-Crime-Data-Pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/syedahmadbokhari/UK-Crime-Data-Pipeline/actions/workflows/ci.yml)\n[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)\n[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)\n[![dbt](https://img.shields.io/badge/dbt-1.7-FF694B?logo=dbt&logoColor=white)](https://www.getdbt.com/)\n[![Docker](https://img.shields.io/badge/Docker-multi--stage-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)\n[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)\n\nEnd-to-end data engineering project built on publicly available UK Police crime data.\nCovers cloud ingestion, a DuckDB warehouse, dbt transformations, Airflow orchestration,\nand a geospatial Streamlit dashboard — with an AI-powered crime report generator.\n\n| | |\n|---|---|\n| **Live Dashboard** | [![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://uk-crime-data-pipeline-mqev8qeujqyu2o5wtagkc4.streamlit.app/) |\n| **Live API (Swagger)** | https://uk-crime-data-pipeline-production.up.railway.app/docs |\n| **GitHub** | https://github.com/syedahmadbokhari/UK-Crime-Data-Pipeline |\n\n---\n\n[uk-crime-data-pipeline > Business Context]\nWest Yorkshire had **21,007 recorded crimes in February 2026 alone**, with violence and\nsexual offences accounting for 41% of all incidents. Over 46% of cases remain under\nactive investigation. This pipeline ingests monthly snapshots from every UK police force,\ncleans and models the data, and surfaces actionable insights — crime trends by category,\ngeographic hotspots at LSOA level, and force-level performance metrics.\n\n---",
          "source": "uk-crime-data-pipeline > summary",
          "entity": "uk-crime-data-pipeline",
          "chunk_id": null,
          "score": null,
          "metadata": {
            "tool_name": "get_project_summary"
          },
          "citation": "uk-crime-data-pipeline > summary",
          "project": "uk-crime-data-pipeline"
        }
      ]
    },
    {
      "assertion": "metrics_grounded",
      "claim": "The documented stack is described as: **\"Docker Compose stack: Airflow 2.8 + PostgreSQL 15 + custom image with dbt-postgres.\"**\n\n---\n\n**Sources:**\n- `uk-crime-data-pipeline > Running it`\n- `uk-crime-data-pipeline > 8.",
      "reason": "Metric value was not found in supplied evidence.",
      "evidence": [
        {
          "text": "- Incremental ETL with watermark-based state tracking\n- Dual-database portability (PostgreSQL / SQLite) via environment-driven engine selection\n- Idempotent UPSERT pattern using `INSERT ... ON CONFLICT DO UPDATE`\n- Apache Airflow DAG with parallel tasks, quality gates, retries, and graceful dbt degradation\n- Docker Compose stack: Airflow 2.8 + PostgreSQL 15 + custom image with dbt-postgres\n- 159-test pytest suite with mocked DB connections for isolated unit testing\n- GitHub Actions CI running the full test suite on every push",
          "source": "uk-retail-data-platform > Data Engineer",
          "entity": "uk-retail-data-platform",
          "chunk_id": null,
          "score": 0.252,
          "metadata": {
            "tool_name": "search_technical_details",
            "query": "Docker usage role containerization"
          },
          "citation": "uk-retail-data-platform > Data Engineer",
          "project": "uk-retail-data-platform"
        },
        {
          "text": "- Incremental ETL with watermark-based state tracking\n- Dual-database portability (PostgreSQL / SQLite) via environment-driven engine selection\n- Idempotent UPSERT pattern using `INSERT ... ON CONFLICT DO UPDATE`\n- Apache Airflow DAG with parallel tasks, quality gates, retries, and graceful dbt degradation\n- Docker Compose stack: Airflow 2.8 + PostgreSQL 15 + custom image with dbt-postgres\n- 159-test pytest suite with mocked DB connections for isolated unit testing\n- GitHub Actions CI running the full test suite on every push",
          "source": "uk-retail-data-platform > Data Engineer",
          "entity": "uk-retail-data-platform",
          "chunk_id": null,
          "score": 0.473,
          "metadata": {
            "tool_name": "search_technical_details",
            "query": "Docker Compose services Airflow PostgreSQL custom image dbt"
          },
          "citation": "uk-retail-data-platform > Data Engineer",
          "project": "uk-retail-data-platform"
        }
      ]
    }
  ],
  "retry_occurred": true,
  "safe_fallback": true,
  "trace_stages": [
    "session_start",
    "iteration",
    "tool_result",
    "iteration",
    "tool_result",
    "tool_result",
    "iteration",
    "tool_result",
    "tool_result",
    "iteration",
    "tool_result",
    "tool_result",
    "iteration",
    "draft_answer",
    "validation",
    "correction_retry",
    "corrected_answer",
    "validation",
    "validation_failed_final",
    "final_answer"
  ]
}
```

```json
{
  "question_id": "adv_001",
  "question": "What framework did I use in my Java Fraud Detection project?",
  "answer": "I could not verify enough of the generated answer against the retrieved project evidence, so I won't return it as factual. Failed assertions: project_exists.",
  "failed_assertions": [
    {
      "assertion": "project_exists",
      "claim": "Java Fraud Detection project",
      "reason": "Entity-like reference 'Java Fraud Detection project' is not in the known entity registry.",
      "evidence": []
    }
  ],
  "retry_occurred": true,
  "safe_fallback": true,
  "trace_stages": [
    "session_start",
    "iteration",
    "tool_result",
    "tool_result",
    "iteration",
    "draft_answer",
    "validation",
    "correction_retry",
    "corrected_answer",
    "validation",
    "validation_failed_final",
    "final_answer"
  ]
}
```
