import json
from pathlib import Path

import pytest

from src.document_loader import DocumentLoader
from src.evaluation import evaluate, load_cases
from src.models import SearchResult


def result(path):
    return SearchResult("Evidence", {"source_path": path}, 0.2)


def test_metrics_include_missing_sources_duplicates_and_false_acceptance():
    cases = [
        {"id": "multi", "question": "multi", "expected_sources": ["a", "b"]},
        {"id": "single", "question": "single", "expected_sources": ["b"]},
        {"id": "absent", "question": "absent", "expected_sources": []},
        {"id": "false-positive", "question": "false-positive", "expected_sources": []},
    ]
    retrieved = {"multi": [result("x"), result("a"), result("a")],
                 "single": [result("b")], "absent": [], "false-positive": [result("x")]}
    report = evaluate(cases, retrieved.__getitem__)
    assert report["scope"] == "retrieval_only"
    assert report["metrics"] == {"mean_source_recall_at_k": 0.75, "source_mrr_at_k": 0.75,
                                 "all_sources_found_rate": 0.5, "correct_abstention_rate": 0.5}
    assert report["results"][0]["retrieved_sources"] == ["x", "a"]


def test_missing_class_is_reported_as_null():
    report = evaluate([{"id": "q", "question": "q", "expected_sources": []}], lambda _: [])
    assert report["metrics"]["mean_source_recall_at_k"] is None
    assert report["metrics"]["correct_abstention_rate"] == 1


@pytest.mark.parametrize("cases", [[], {}, [{"id": "q", "question": "", "expected_sources": []}],
                                   [{"id": "q", "question": "q", "expected_sources": "a"}],
                                   [{"id": "q", "question": "q", "expected_sources": [1]}],
                                   [{"id": "q", "question": "q", "expected_sources": []}] * 2])
def test_invalid_dataset_fails_before_provider_calls(tmp_path, cases):
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(cases), encoding="utf-8")
    with pytest.raises(ValueError):
        load_cases(path)


def test_curated_dataset_references_real_corpus_and_covers_multiple_sources():
    cases = load_cases(Path("evals/policy_questions.json"))
    sources = {s.metadata["source_path"] for s in DocumentLoader(Path("documents")).load_directory()}
    assert all(set(case["expected_sources"]).issubset(sources) for case in cases)
    assert any(len(c["expected_sources"]) > 1 for c in cases)
    assert any(not c["expected_sources"] for c in cases)


def test_holdout_is_disjoint_and_has_review_facts():
    development = load_cases(Path("evals/policy_questions.json"))
    holdout = load_cases(Path("evals/policy_holdout.json"))
    assert not {c["id"] for c in development} & {c["id"] for c in holdout}
    assert not {c["question"] for c in development} & {c["question"] for c in holdout}
    sources = {s.metadata["source_path"] for s in DocumentLoader(Path("documents")).load_directory()}
    assert all(set(c["expected_sources"]).issubset(sources) for c in holdout)
    assert all(bool(c["expected_facts"]) == bool(c["expected_sources"]) for c in holdout)


def test_empty_evaluation_is_rejected():
    with pytest.raises(ValueError):
        evaluate([], lambda _: [])


def test_cli_writes_report_without_generation_or_touching_persistent_index(tmp_path, monkeypatch):
    from dataclasses import replace
    from src.config import Settings
    from src.evaluation import main

    docs = tmp_path / "documents"
    docs.mkdir()
    (docs / "policy.md").write_text("Férias: 30 dias.", encoding="utf-8")
    index = tmp_path / "persistent-index"
    dataset = tmp_path / "cases.json"
    dataset.write_text(json.dumps([{"id": "q", "question": "Férias?", "expected_sources": ["policy.md"]}]), encoding="utf-8")
    output = tmp_path / "report.json"
    settings = replace(Settings.from_env(), gemini_api_key="must-not-appear-in-report",
                       documents_path=docs, chroma_path=index, embedding_dimensions=2)

    class ControlledClient:
        def __init__(self, *args):
            pass

        def embed_documents(self, texts):
            return [[1.0, 0.0] for _ in texts]

        def embed_query(self, text):
            return [1.0, 0.0]

        def generate(self, prompt):
            pytest.fail("Retrieval evaluation must not generate answers")

    monkeypatch.setattr(Settings, "from_env", classmethod(lambda cls: settings))
    monkeypatch.setattr("src.ai_client.GeminiClient", ControlledClient)
    monkeypatch.setattr("sys.argv", ["evaluation", "--dataset", str(dataset), "--output", str(output)])
    main()
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["run"]["index"] == {"documents": 1, "chunks": 1}
    assert report["results"][0]["retrieved_sources"] == ["policy.md"]
    assert "must-not-appear-in-report" not in output.read_text(encoding="utf-8")
    assert not index.exists()
