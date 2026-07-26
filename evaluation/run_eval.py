"""Run the evaluation set through the RAG pipeline and report real results.

Two layers of measurement:
1. Retrieval accuracy — did the retrieved chunks actually contain the
   documented fact (verbatim keyword check) and come from the right project?
2. Generation faithfulness — did the generated answer state the documented
   fact, and did off-topic questions get an honest refusal? (Requires
   GROQ_API_KEY; skipped with a clear notice otherwise, or with
   --retrieval-only.)

Usage:
    python -m evaluation.run_eval [--retrieval-only] [--index-dir index]

Writes evaluation/results.json with the full raw output of the run.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.generation import _load_dotenv_key  # noqa: E402
from rag.pipeline import NO_RESULT_ANSWER, load_pipeline  # noqa: E402

EVAL_SET = Path(__file__).parent / "eval_set.json"
RESULTS_OUT = Path(__file__).parent / "results.json"


def contains_all(haystack: str, needles: list[str]) -> bool:
    hay = haystack.lower()
    return all(n.lower() in hay for n in needles)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--retrieval-only", action="store_true")
    args = parser.parse_args()

    cases = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    pipeline = load_pipeline(args.index_dir)

    run_generation = not args.retrieval_only and bool(
        os.environ.get("GROQ_API_KEY") or _load_dotenv_key()
    )
    if not run_generation:
        reason = "--retrieval-only flag" if args.retrieval_only else "GROQ_API_KEY not set"
        print(f"NOTE: generation evaluation skipped ({reason}); retrieval-only run.\n")

    records = []
    retrieval_hits = retrieval_total = 0
    answer_hits = answer_total = 0
    refusal_hits = refusal_total = 0

    for case in cases:
        question = case["question"]
        results = pipeline.retrieve(question)
        retrieved = [
            {"citation": r.chunk.citation(), "score": round(r.score, 3)} for r in results
        ]
        record = {"id": case["id"], "type": case["type"], "question": question,
                  "retrieved": retrieved}
        print(f"[{case['id']}] {question}")

        if case["type"] == "grounded":
            retrieval_total += 1
            all_text = "\n".join(r.chunk.text for r in results)
            keyword_hit = contains_all(all_text, case["retrieval_keywords"])
            project_hit = any(
                r.chunk.project == case["expected_project"] for r in results
            )
            hit = keyword_hit and project_hit
            retrieval_hits += hit
            record["retrieval_hit"] = hit
            record["retrieval_keyword_found"] = keyword_hit
            record["expected_project_retrieved"] = project_hit
            status = "HIT" if hit else "MISS"
            print(f"  retrieval: {status}  "
                  f"(keywords={'yes' if keyword_hit else 'NO'}, "
                  f"project={'yes' if project_hit else 'NO'})")
            for r in retrieved:
                print(f"    [{r['score']:.3f}] {r['citation']}")
        else:
            refusal_total += 1
            record["retrieval_returned_chunks"] = bool(results)
            if results:
                print("  WARNING: off-topic question retrieved chunks above threshold:")
                for r in retrieved:
                    print(f"    [{r['score']:.3f}] {r['citation']}")

        if run_generation:
            answer = pipeline.ask(question)
            record["answer"] = answer.answer
            record["grounded"] = answer.grounded
            if case["type"] == "grounded":
                answer_total += 1
                ok = answer.grounded and contains_all(
                    answer.answer, case["answer_keywords"]
                )
                answer_hits += ok
                record["answer_hit"] = ok
                print(f"  answer:    {'FAITHFUL' if ok else 'FAILED'}")
                print(f"    {answer.answer[:200].replace(chr(10), ' ')}")
            else:
                refused = (not answer.grounded) or (
                    "does not contain" in answer.answer.lower()
                )
                refusal_hits += refused
                record["honest_refusal"] = refused
                print(f"  refusal:   {'HONEST' if refused else 'HALLUCINATED'}")
                print(f"    {answer.answer[:200].replace(chr(10), ' ')}")
            time.sleep(2)  # stay well inside Groq free-tier rate limits
        elif case["type"] == "no_result":
            # the no-result path needs no LLM: pipeline.ask short-circuits
            answer = pipeline.ask(question)
            refused = not answer.grounded and answer.answer == NO_RESULT_ANSWER
            refusal_hits += refused
            record["honest_refusal"] = refused
            print(f"  refusal:   {'HONEST' if refused else 'FAILED'} (no LLM needed)")

        print()
        records.append(record)

    print("=" * 60)
    print(f"Retrieval accuracy: {retrieval_hits}/{retrieval_total}")
    if run_generation:
        print(f"Answer faithfulness: {answer_hits}/{answer_total}")
    print(f"Honest refusals (off-topic): {refusal_hits}/{refusal_total}")

    summary = {
        "retrieval_accuracy": f"{retrieval_hits}/{retrieval_total}",
        "answer_faithfulness": f"{answer_hits}/{answer_total}" if run_generation else "skipped",
        "honest_refusals": f"{refusal_hits}/{refusal_total}",
        "generation_ran": run_generation,
    }
    RESULTS_OUT.write_text(
        json.dumps({"summary": summary, "cases": records}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nFull results written to {RESULTS_OUT}")


if __name__ == "__main__":
    main()
