"""Run a reviewable answer evaluation using real services; no automatic semantic grading."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from src.ai_client import GeminiClient, IncompleteGeneration
from src.config import Settings
from src.evaluation import load_cases
from src.indexing import rebuild_index
from src.rag import FALLBACK_ANSWER, RagAgent
from src.vector_store import VectorStore


def evaluate_answers(cases, ask, on_row=lambda rows: None):
    """Stop after any provider error, preserving prior results for manual review."""
    rows = []
    for case in cases:
        row = {"id": case["id"], "question": case["question"],
               "expected_sources": case["expected_sources"]}
        try:
            response = ask(case["question"])
            row.update(status="abstained" if response.answer == FALLBACK_ANSWER else "answered",
                       answer=response.answer, evidence=[asdict(source) for source in response.sources],
                       review={"facts_supported": None, "citations_supported": None, "notes": ""})
        except Exception as exc:
            # Do not persist provider messages: they can contain sensitive details.
            row.update(status="error", error_type=type(exc).__name__, error_code=getattr(exc, "code", None))
            if isinstance(exc, IncompleteGeneration):
                row["finish_reason"] = exc.reason
            rows.append(row)
            on_row(rows)
            break
        rows.append(row)
        on_row(rows)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("evals/policy_questions.json"))
    parser.add_argument("--output", type=Path, default=Path("evals/reports/answers-review.json"))
    args = parser.parse_args()
    cases = load_cases(args.dataset)
    settings = Settings.from_env()
    settings.require_api_key()
    client = GeminiClient(settings.gemini_api_key, settings.llm_model, settings.embedding_model,
                          settings.embedding_dimensions, settings.llm_fallback_model)
    store = VectorStore(settings.chroma_path, "answer-evaluation", persistent=False)
    indexed = rebuild_index(settings, client, store)
    agent = RagAgent(settings, client, store)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=False)
    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "revision": revision.stdout.strip() or None, "working_tree_dirty": bool(dirty.stdout.strip()),
              "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
              "settings": {k: getattr(settings, k) for k in ("llm_model", "llm_fallback_model", "embedding_model",
                           "embedding_dimensions", "chunk_size", "chunk_overlap", "top_k", "max_cosine_distance")},
              "index": asdict(indexed), "total_cases": len(cases), "results": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def save(rows):
        report["results"] = rows
        report["complete"] = len(rows) == len(cases) and all(r["status"] != "error" for r in rows)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rows = evaluate_answers(cases, agent.ask, save)
    print(f"{len(rows)}/{len(cases)} casos registrados; completo={report['complete']}; relatório: {args.output}")
    if not report["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
