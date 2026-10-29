"""Experimental lexical/semantic union; no production retrieval changes."""
import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from time import perf_counter
from src.ai_client import OllamaEmbeddingClient
from src.config import Settings
from src.evaluation import evaluate, load_cases
from src.indexing import rebuild_index, index_fingerprint
from src.vector_store import VectorStore

STOP = set('a o as os um uma de da do das dos em no na nos nas e ou para por com qual quais quanto quantos quantas como onde que sao ser posso devo meu minha empresa'.split())


def tokens(text):
    text = ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if not unicodedata.combining(c))
    return set(re.findall(r'[a-z0-9]+', text)) - STOP


def lexical_results(question, results):
    terms = tokens(question)
    ranked = [(len(terms & tokens(r.text)), i, r) for i, r in enumerate(results)]
    return [r for count, _, r in sorted(ranked, key=lambda x: (-x[0], x[1])) if count >= 2][:2]


def select(question, raw, mode, settings):
    semantic = [r for r in raw[:settings.top_k] if r.distance <= settings.max_cosine_distance]
    lexical = lexical_results(question, raw)
    if mode == 'current':
        return semantic
    if mode == 'lexical':
        return lexical
    # Reciprocal rank fusion over eligible semantic and lexical results.
    scores, candidates = {}, {}
    for ranking in (semantic, lexical):
        for rank, result in enumerate(ranking, 1):
            key = (result.metadata.get('source_path'), result.text)
            candidates[key] = result
            scores[key] = scores.get(key, 0) + 1 / (60 + rank)
    return [candidates[k] for k in sorted(scores, key=lambda k: (-scores[k], k))[:settings.top_k]]


def main():
    settings = Settings.from_env()
    if settings.embedding_provider != 'ollama':
        raise ValueError('Este experimento exige Ollama local.')
    client = OllamaEmbeddingClient(settings.ollama_base_url, settings.ollama_model, settings.embedding_dimensions)
    store = VectorStore(settings.chroma_path, 'hybrid-experiment', persistent=False)
    rebuild_index(settings, client, store)
    dataset = Path('evals/hybrid_prospective.json')
    cases = load_cases(dataset)
    report = {'revision':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),
              'working_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'])),
              'dataset_sha256':hashlib.sha256(dataset.read_bytes()).hexdigest(),
              'index_fingerprint':index_fingerprint(settings), 'results':{}}
    for mode in ['current','lexical','hybrid']:
        calls = 0
        def retrieve(q):
            nonlocal calls
            calls += 1
            raw = store.search(client.embed_query(q), store.count())
            return select(q, raw, mode, settings)
        started = perf_counter()
        result = evaluate(cases, retrieve)
        result['elapsed_seconds'] = perf_counter()-started
        result['embedding_requests'] = calls
        result['extra_sources'] = sum(len(set(r['retrieved_sources'])-set(r['expected_sources'])) for r in result['results'] if r['expected_sources'])
        report['results'][mode] = result
        print(mode,result['metrics'],result['extra_sources'],result['elapsed_seconds'])
    Path('evals/baselines/hybrid-prospective.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__ == '__main__':
    main()
