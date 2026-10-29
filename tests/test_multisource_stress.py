from pathlib import Path
from src.document_loader import DocumentLoader
from src.evaluation import load_cases


def test_stress_cases_cover_three_sources_and_absent_questions():
    cases = load_cases(Path("evals/multisource_stress.json"))
    sources = {s.metadata["source_path"] for s in DocumentLoader(Path("documents")).load_directory()}
    assert all(set(case["expected_sources"]).issubset(sources) for case in cases)
    assert sum(len(case["expected_sources"]) >= 3 for case in cases) == 3
    assert sum(not case["expected_sources"] for case in cases) == 3
