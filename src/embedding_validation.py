import math


def validate_embeddings(vectors, count: int, dimensions: int | None = None):
    """Reject malformed, nonfinite and zero vectors before indexing or querying."""
    if not isinstance(vectors, list) or len(vectors) != count:
        raise RuntimeError("Quantidade de embeddings incompatível.")
    for vector in vectors:
        if (not isinstance(vector, list) or not vector or (dimensions is not None and len(vector) != dimensions)
                or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in vector)
                or not any(v != 0 for v in vector)):
            raise RuntimeError("Valor ou dimensão de embedding incompatível.")
    if vectors and any(len(v) != len(vectors[0]) for v in vectors):
        raise RuntimeError("Dimensões de embeddings inconsistentes.")
    return vectors
