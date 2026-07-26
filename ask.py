"""Ask a question against the indexed project documentation.

Usage:
    python ask.py "What was the BigQuery bytes-scanned reduction?"
    python ask.py --retrieval-only "..."   # no LLM call, shows retrieved chunks
"""

from __future__ import annotations

import argparse
from pathlib import Path

from rag.pipeline import load_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Show retrieved chunks and scores without calling the LLM",
    )
    args = parser.parse_args()

    pipeline = load_pipeline(args.index_dir)

    if args.retrieval_only:
        results = pipeline.retrieve(args.question, top_k=args.top_k)
        if not results:
            print("No chunks above the relevance threshold.")
            return
        for r in results:
            print(f"[{r.score:.3f}] {r.chunk.citation()}")
            print(r.chunk.text[:300].replace("\n", " "))
            print()
        return

    result = pipeline.ask(args.question, top_k=args.top_k)
    print(result.answer)
    if result.grounded:
        print("\nRetrieved sources:")
        for r in result.results:
            print(f"  [{r.score:.3f}] {r.chunk.citation()}")


if __name__ == "__main__":
    main()
