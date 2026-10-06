"""
GraphRAG Demo: Lightweight graph retrieval + LLM answer generation
Uses pandas-based KG queries (no Neo4j required) + DashScope API
Demonstrates 3 natural language questions over the maritime accident KG
"""

import os
import pandas as pd
import json
import re
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get('DASHSCOPE_API_KEY'),
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
)

# ── Load KG data ──────────────────────────────────────────────────────────────
acc  = pd.read_csv('kg_export/nodes_accident.csv')
hf   = pd.read_csv('results/R002b_hfacs_with_categories.csv')
ev   = pd.read_csv('kg_export/nodes_event.csv')
led  = pd.read_csv('kg_export/rel_led_to.csv')
orig = pd.read_csv('kg_export/rel_originated_from.csv')

# Build lookup dicts
id2acc  = acc.set_index('id').to_dict('index')
id2hf   = hf.set_index('id').to_dict('index')
id2ev   = ev.set_index('id').to_dict('index')

print("KG loaded. Nodes:", len(acc)+len(hf)+len(ev), "| LED_TO edges:", len(led))


# ── Graph retrieval functions ─────────────────────────────────────────────────

def retrieve_q1(accident_type_keyword):
    """Q1: Top HFACS categories for a given accident type"""
    # Find accidents matching keyword
    target_accs = acc[acc['accident_type'].str.contains(
        accident_type_keyword, case=False, na=False)]
    target_files = set(target_accs['source_file'])
    n_reports = len(target_files)

    # Get HFACS factors for those reports (by source_file join)
    hf_sub = hf[hf['source_file'].isin(target_files)]
    hf_sub = hf_sub[hf_sub['category'] != 'Other / Unclassified']

    # Count categories
    cat_counts = hf_sub['category'].value_counts().head(8)
    # Report-level prevalence
    cat_prev = {}
    for cat in cat_counts.index:
        reports_with = hf_sub[hf_sub['category']==cat]['source_file'].nunique()
        cat_prev[cat] = (reports_with, round(reports_with/n_reports*100, 1))

    # Top 5 factor texts
    top_factors = hf_sub['name'].value_counts().head(5).index.tolist()

    context = {
        'accident_type': accident_type_keyword,
        'n_reports': n_reports,
        'n_factors': len(hf_sub),
        'top_categories': {cat: cat_prev[cat] for cat in list(cat_counts.index)[:6]},
        'example_factors': top_factors
    }
    return context


def retrieve_q2():
    """Q2: Event chain complexity by accident type + most common intermediate events"""
    # EventNode->EventNode edges
    ev_ev = led[(led['src_label']=='EventNode') & (led['dst_label']=='EventNode')]
    # EventNode->Accident edges to get accident type
    ev_acc = led[(led['src_label']=='EventNode') & (led['dst_label']=='Accident')]

    # Chain length per source_file
    chain_by_file = {}
    for _, row in ev_ev.iterrows():
        src_id = row['src']
        if src_id in id2ev:
            sf = id2ev[src_id]['source_file']
            chain_by_file[sf] = chain_by_file.get(sf, 0) + 1

    # Join to accident type
    acc_chain = acc.copy()
    acc_chain['chain_len'] = acc_chain['source_file'].map(chain_by_file).fillna(0)
    by_type = acc_chain.groupby('accident_type')['chain_len'].agg(['mean','count'])
    by_type = by_type[by_type['count'] >= 10].sort_values('mean', ascending=False).head(6)

    # Most common event texts overall
    common_events = ev['name'].value_counts().head(8).to_dict()

    context = {
        'chain_length_by_type': by_type[['mean','count']].round(2).to_dict('index'),
        'top_events': common_events
    }
    return context


def retrieve_q3(hfacs_category):
    """Q3: Two-hop path: HFACS category -> EventNode -> Accident type"""
    # Step 1: find HFACS factor IDs in this category
    hf_cat = hf[hf['category'].str.contains(hfacs_category, case=False, na=False)]
    hf_ids = set(hf_cat['id'])

    # Step 2: HFACS_Factor -> EventNode edges (LED_TO)
    hf_to_ev = led[(led['src_label']=='HFACS_Factor') &
                   (led['dst_label']=='EventNode') &
                   (led['src'].isin(hf_ids))]
    ev_ids = set(hf_to_ev['dst'])

    # Step 3: EventNode -> Accident edges
    ev_to_acc = led[(led['src_label']=='EventNode') &
                    (led['dst_label']=='Accident') &
                    (led['src'].isin(ev_ids))]
    acc_ids = set(ev_to_acc['dst'])

    # Get accident types
    matched_accs = acc[acc['id'].isin(acc_ids)]
    type_counts = matched_accs['accident_type'].value_counts().head(6).to_dict()

    # Most common intermediate EventNodes
    ev_sub = ev[ev['id'].isin(ev_ids)]
    top_events = ev_sub['name'].value_counts().head(5).to_dict()

    # Direct HFACS -> Accident (LED_TO, no event hop)
    hf_to_acc = led[(led['src_label']=='HFACS_Factor') &
                    (led['dst_label']=='Accident') &
                    (led['src'].isin(hf_ids))]
    direct_acc = acc[acc['id'].isin(set(hf_to_acc['dst']))]
    direct_types = direct_acc['accident_type'].value_counts().head(4).to_dict()

    context = {
        'hfacs_category': hfacs_category,
        'n_hfacs_factors': len(hf_cat),
        'two_hop_outcomes': type_counts,
        'intermediate_events': top_events,
        'direct_outcomes': direct_types,
        'total_paths': len(ev_to_acc)
    }
    return context


# ── LLM answer generation ─────────────────────────────────────────────────────

def generate_answer(question, context_dict):
    context_str = json.dumps(context_dict, indent=2, ensure_ascii=False)
    prompt = f"""You are a maritime safety analyst. Answer the following question using ONLY the structured knowledge graph data provided. Be specific, cite numbers, and draw safety-relevant conclusions.

Question: {question}

Knowledge Graph Data:
{context_str}

Provide a concise but insightful answer (3-5 sentences). Include specific numbers and end with one practical safety implication."""

    resp = client.chat.completions.create(
        model='qwen-max',
        max_tokens=400,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return resp.choices[0].message.content


# ── Run three demo queries ────────────────────────────────────────────────────

queries = [
    {
        'id': 'Q1',
        'question': 'What are the most prevalent HFACS human factor categories in Enclosed Space accidents, and how does this profile differ from the overall accident population?',
        'retrieve': lambda: retrieve_q1('Enclosed Space')
    },
    {
        'id': 'Q2',
        'question': 'Which accident types produce the most complex event chains, and what are the most frequently occurring intermediate events across the accident corpus?',
        'retrieve': lambda: retrieve_q2()
    },
    {
        'id': 'Q3',
        'question': 'What accident outcomes do Navigation & Passage Planning failures most frequently lead to through event chain propagation, and which intermediate events are most commonly involved?',
        'retrieve': lambda: retrieve_q3('Navigation & Passage Planning')
    },
]

results = []
for q in queries:
    print(f"\n{'='*60}")
    print(f"{q['id']}: {q['question']}")
    print('Retrieving subgraph...')
    ctx = q['retrieve']()
    print('Context:', json.dumps(ctx, indent=2, ensure_ascii=False)[:500])
    print('Generating answer...')
    answer = generate_answer(q['question'], ctx)
    # clean for ASCII output
    answer_safe = answer.encode('ascii','replace').decode('ascii')
    print('Answer:', answer_safe)
    results.append({
        'query_id': q['id'],
        'question': q['question'],
        'context': ctx,
        'answer': answer
    })

# Save results
with open('results/graphrag_demo_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print('\n\nAll results saved to results/graphrag_demo_results.json')