import pytest
from src.embedding_validation import validate_embeddings


@pytest.mark.parametrize("vectors", [None, [], [[0, 0]], [[float("nan"), 1]], [[float("inf"), 1]], [["1", 2]], [[True, 1]], [[1]], [None]])
def test_invalid_embeddings_are_rejected(vectors):
    with pytest.raises(RuntimeError):
        validate_embeddings(vectors, 1, 2)


def test_mixed_dimensions_are_rejected():
    with pytest.raises(RuntimeError):
        validate_embeddings([[1, 0], [1]], 2)


def test_valid_embedding_is_preserved():
    assert validate_embeddings([[1.0, 0.0]], 1, 2) == [[1.0, 0.0]]
