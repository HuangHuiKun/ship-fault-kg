"""V6 evidence probe: reuse the frozen lexical algorithm, not V5 data."""
import argparse
import json
from pathlib import Path
from ..v5 import retrieve as engine
OUT = Path(__file__).resolve().parent.parent / 'output' / 'v6_assistant'

def retrieve(query, k=5, max_depth=3):
    previous = engine.OUT
    try:
        engine.OUT = OUT
        result = engine.retrieve(query, k, max_depth)
    finally:
        engine.OUT = previous
    result['graph_version'] = '6.0'
    claims = {a['id']: a for a in (json.loads(line) for line in
              (OUT / 'assertions.jsonl').read_text(encoding='utf-8').splitlines() if line.strip())}
    for pack in result['results']:
        for fact in pack['facts']:
            claim = claims[fact['id']]
            for key in ('certainty_group', 'source_review_extent', 'schema_version', 'classification_role'):
                if key in claim:
                    fact[key] = claim[key]
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument('query')
    p.add_argument('--top-k', type=int, default=3)
    args = p.parse_args()
    result = retrieve(args.query, args.top_k)
    path = OUT / 'retrieval_example.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(graph_version=result['graph_version'],
          results=[dict(name=r['fault_name'], facts=len(r['facts'])) for r in result['results']],
          output=str(path)), ensure_ascii=False))

if __name__ == '__main__':
    main()
