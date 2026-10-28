from src.evaluate_answers import evaluate_answers
from src.models import AgentResponse
from src.rag import FALLBACK_ANSWER


def test_answer_evaluation_preserves_partial_results_and_stops_on_error():
    cases = [{"id": str(i), "question": str(i), "expected_sources": []} for i in range(3)]
    snapshots = []

    def ask(question):
        if question == "1":
            raise RuntimeError("secret provider details")
        return AgentResponse(FALLBACK_ANSWER)

    rows = evaluate_answers(cases, ask, lambda rows: snapshots.append(len(rows)))
    assert snapshots == [1, 2]
    assert [r["status"] for r in rows] == ["abstained", "error"]
    assert "secret provider details" not in str(rows)
    assert rows[0]["review"]["facts_supported"] is None
