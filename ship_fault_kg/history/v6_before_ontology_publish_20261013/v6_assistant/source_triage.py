"""Build a source-complete reading queue, not knowledge statements.

The ranking below is mechanical. A selected excerpt is *not* an assistant
review, a validated claim, or evidence of full-document reading.
"""
import collections
import json
import re

from .pipeline import OUT, batches, registry, rows, BASE

SIGNALS = ('故障', '失效', '原因', '导致', '造成', '引起', '检查', '发现', '排查',
           '维修', '更换', '泄漏', '振动', '磨损', '烧瓦', '拉缸', '报警', '停机',
           'failure', 'cause', 'damage', 'inspect', 'maintenance', 'bearing',
           'overheat', 'vibration', 'fault', 'recommend')
HARD = ('导致', '造成', '引起', '原因', 'resulted in', 'caused by', 'due to',
        'contributed to', '检查发现', 'investigation found')

def windows(text):
    # Sentence boundaries are used for ranking only. Excerpts remain literal
    # substrings of the normalized, source-hashed text in the V5 registry.
    starts = [0] + [m.end() for m in re.finditer(r'[。！？;；\n]', text)]
    for pos in starts:
        s = text[pos:pos+500].strip()
        if len(s) < 28:
            continue
        yield s

def score(s):
    low = s.lower()
    value = sum(2 for x in SIGNALS if x in low)
    value += sum(3 for x in HARD if x in low)
    if re.search(r'\b\d+(?:\.\d+)?\s*(?:mm|MPa|kPa|°C|kW)\b', s, re.I):
        value += 1
    return value

def build():
    reg = registry()
    done = {r['source_id']:('assistant_no_claim' if not r['facts'] else
            'assistant_full_text_review' if r['review']=='full_text' else
            'assistant_excerpt_review') for r in batches()}
    base_used = {e['props']['source_id'] for e in rows(BASE/'relationships.jsonl')}
    grouped = collections.defaultdict(list)
    fallback = {}
    for (sid, key), (_, text, path) in reg.pages.items():
        if text.strip() and sid not in fallback:
            fallback[sid] = (key, path, text.strip()[:500])
        for excerpt in windows(text):
            strength = score(excerpt)
            if strength:
                grouped[sid].append((-strength, key, path, excerpt))
    inventory=[]
    for sid, source in sorted(reg.sources.items()):
        ranked=sorted(grouped[sid],key=lambda item:(item[0],item[1],item[3]))
        chosen=[]; seen=set()
        for neg, key, path, excerpt in ranked:
            fingerprint=excerpt[:90]
            if fingerprint in seen:continue
            seen.add(fingerprint)
            chosen.append(dict(page_key=key,locator=path,keyword_score=-neg,
                               exact_excerpt=excerpt))
            if len(chosen)==2:break
        if not chosen and sid in fallback:
            key,path,excerpt=fallback[sid]
            chosen=[dict(page_key=key,locator=path,keyword_score=0,
                         exact_excerpt=excerpt)]
        inventory.append(dict(source_id=sid,title=source['title'],paths=source['paths'],
            source_sha256=source['sha256'],source_type=source['paths'][0].rsplit('.',1)[-1].lower(),
            pages_in_cache=sum(1 for (s,_) in reg.pages if s==sid),
            selection_method='literal_keyword_window_rank_no_inference',
            excerpt_selection_model_reviewed=False,
            prior_status=(done[sid] if sid in done else
                          'baseline_selected_evidence_only' if sid in base_used else
                          'pending_assistant_review'),
            representative_excerpts=chosen))
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'source_complete_reading_queue.jsonl').open('w',encoding='utf-8') as f:
        for record in inventory:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    stats=dict(total_sources=len(inventory),with_representative_excerpts=sum(bool(x['representative_excerpts']) for x in inventory),
               without_signal_excerpts=sum(not x['representative_excerpts'] for x in inventory),
               status=dict(collections.Counter(x['prior_status'] for x in inventory)),
               method='mechanical indexing only; not assistant inference or knowledge declarations')
    (OUT/'source_complete_reading_queue_report.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=='__main__':build()
