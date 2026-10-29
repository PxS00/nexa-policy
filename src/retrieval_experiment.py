"""Local retrieval experiment; does not change the application or generate answers."""
import json
import re
import hashlib
import subprocess
from pathlib import Path
from src.ai_client import OllamaEmbeddingClient
from src.config import Settings
from src.evaluation import evaluate, load_cases
from src.indexing import rebuild_index
from src.vector_store import VectorStore


def split_question(question):
    # Conservative Portuguese heuristic: only split before an explicit question word.
    parts = re.split(r'\s+e\s+(?=(?:qual|quais|quanto|quantos|quantas|onde|como|por qual)\b)', question, flags=re.I)
    return [part.strip() for part in parts][:3]


def main():
    settings = Settings.from_env()
    if settings.embedding_provider != 'ollama':
        raise ValueError('Este experimento exige Ollama local.')
    client = OllamaEmbeddingClient(settings.ollama_base_url, settings.ollama_model, settings.embedding_dimensions)
    store = VectorStore(settings.chroma_path, 'split-experiment', persistent=False)
    rebuild_index(settings, client, store)
    cache = {}

    def raw(q):
        if q not in cache:
            cache[q] = store.search(client.embed_query(q), store.count())
        return cache[q]

    def accepted(q):
        return [r for r in raw(q)[:settings.top_k] if r.distance <= settings.max_cosine_distance]

    def retrieve(q, mode):
        results = accepted(q)
        if mode == 'relative' and results:
            return [r for r in results if r.distance <= results[0].distance + .15]
        if mode in ('split', 'split_relative'):
            parts = split_question(q)
            if len(parts) > 1:
                merged = {}
                for r in results + [r for part in parts for r in accepted(part)]:
                    key = (r.metadata.get('source_path'), r.metadata.get('location'), r.text)
                    if key not in merged or r.distance < merged[key].distance:
                        merged[key] = r
                results = sorted(merged.values(), key=lambda r: r.distance)[:settings.top_k]
            if mode == 'split_relative' and results:
                results = [r for r in results if r.distance <= results[0].distance + .15]
        return results

    report = {'revision': subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(), 'working_tree_dirty': bool(subprocess.check_output(['git','status','--porcelain'])), 'dataset_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('evals').glob('*.json')}, 'settings': {'top_k':settings.top_k, 'threshold':settings.max_cosine_distance, 'model':settings.ollama_model}, 'datasets':{}}
    for name in ['policy_questions','policy_holdout','multisource_stress','retrieval_extra_cases','retrieval_gap_check']:
        cases = load_cases(Path('evals') / (name+'.json'))
        report['datasets'][name] = {}
        for mode in ['current','relative','split','split_relative']:
            result = evaluate(cases, lambda q: retrieve(q, mode))
            result['extra_sources'] = sum(len(set(r['retrieved_sources'])-set(r['expected_sources'])) for r in result['results'] if r['expected_sources'])
            report['datasets'][name][mode] = result
    q = load_cases(Path('evals/retrieval_gap_check.json'))[0]['question']
    report['diagnostic'] = {'question':q, 'parts':split_question(q), 'rankings':{part:[{'path':r.metadata['source_path'],'distance':r.distance} for r in raw(part)] for part in [q]+split_question(q)}}
    Path('evals/baselines/split-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for name, modes in report['datasets'].items():
        for mode, result in modes.items():
            print(name,mode,result['metrics'], 'extras',result['extra_sources'])
    print(json.dumps(report['diagnostic'],ensure_ascii=True))

if __name__ == '__main__':
    main()
