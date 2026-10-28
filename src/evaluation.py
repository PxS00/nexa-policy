"""Source-level retrieval evaluation. Does not grade generated answers."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from src.models import SearchResult


def load_cases(path: Path) -> list[dict]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("A avaliação exige uma lista não vazia de casos.")
    ids = set()
    for case in cases:
        if (
            not isinstance(case, dict)
            or not isinstance(case.get("id"), str)
            or not case["id"].strip()
            or case["id"] in ids
            or not isinstance(case.get("question"), str)
            or not case["question"].strip()
            or not isinstance(case.get("expected_sources"), list)
            or any(not isinstance(s, str) or not s.strip() for s in case["expected_sources"])
        ):
            raise ValueError("Cada caso exige id único, question e expected_sources (lista de caminhos).")
        ids.add(case["id"])
    return cases


def evaluate(cases: list[dict], retrieve: Callable[[str], list[SearchResult]]) -> dict:
    """Score accepted results; missing classes produce null metrics, never invented scores."""
    if not cases:
        raise ValueError("A avaliação exige pelo menos um caso.")
    rows = []
    recalls, reciprocal_ranks, complete, abstentions = [], [], [], []
    for case in cases:
        started = perf_counter()
        results = retrieve(case["question"])
        elapsed_ms = (perf_counter() - started) * 1000
        # Rank unique source paths rather than counting overlapping chunks twice.
        paths = list(dict.fromkeys(str(r.metadata.get("source_path", "")) for r in results))
        expected = set(case["expected_sources"])
        row = {"id": case["id"], "question": case["question"],
               "expected_sources": sorted(expected), "retrieved_sources": paths,
               "distances": [r.distance for r in results], "retrieval_ms": elapsed_ms}
        if expected:
            recall = len(expected.intersection(paths)) / len(expected)
            rr = next((1 / rank for rank, path in enumerate(paths, 1) if path in expected), 0.0)
            recalls.append(recall)
            reciprocal_ranks.append(rr)
            complete.append(expected.issubset(paths))
            row.update(source_recall=recall, reciprocal_rank=rr, all_sources_found=complete[-1])
        else:
            abstentions.append(not results)
            row["correct_abstention"] = abstentions[-1]
        rows.append(row)

    def mean(values):
        return sum(values) / len(values) if values else None

    return {"scope": "retrieval_only", "cases": len(rows),
            "answerable_cases": len(recalls), "unanswerable_cases": len(abstentions),
            "metrics": {"mean_source_recall_at_k": mean(recalls),
                        "source_mrr_at_k": mean(reciprocal_ranks),
                        "all_sources_found_rate": mean(complete),
                        "correct_abstention_rate": mean(abstentions)}, "results": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("evals/policy_questions.json"))
    parser.add_argument("--output", type=Path, default=Path("evals/reports/retrieval.json"))
    args = parser.parse_args()
    cases = load_cases(args.dataset)
    # Import service dependencies only for the explicit live evaluation command.
    from src.ai_client import GeminiClient
    from src.config import Settings
    from src.document_loader import SUPPORTED_EXTENSIONS
    from src.indexing import rebuild_index
    from src.rag import RagAgent
    from src.vector_store import VectorStore

    settings = Settings.from_env()
    settings.require_api_key()
    corpus = hashlib.sha256()
    for path in sorted(settings.documents_path.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            corpus.update(path.relative_to(settings.documents_path).as_posix().encode())
            corpus.update(hashlib.sha256(path.read_bytes()).digest())
    client = GeminiClient(settings.gemini_api_key, settings.llm_model,
                          settings.embedding_model, settings.embedding_dimensions,
                          settings.llm_fallback_model)
    # Never replace the application's persistent collection during evaluation.
    store = VectorStore(settings.chroma_path, "evaluation", persistent=False)
    indexed = rebuild_index(settings, client, store)
    agent = RagAgent(settings, client, store)
    report = evaluate(cases, agent.retrieve)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=False)
    report["run"] = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
                     "revision": revision.stdout.strip() or None,
                     "working_tree_dirty": bool(dirty.stdout.strip()),
                     "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
                     "corpus_sha256": corpus.hexdigest(), "index": asdict(indexed),
                     "settings": {key: getattr(settings, key) for key in
                                  ("embedding_model", "embedding_dimensions", "chunk_size",
                                   "chunk_overlap", "top_k", "max_cosine_distance")}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["metrics"], ensure_ascii=False, indent=2))
    print(f"Relatório: {args.output}")


if __name__ == "__main__":
    main()
