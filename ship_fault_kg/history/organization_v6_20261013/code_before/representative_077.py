"""Storage helpers for manually reasoned claims from the frozen 77 sources.

No inference, auto-generated triples or review completion by selection.
"""
from .authoring import Batch
from .pipeline import OUT,rows
from .selection_077 import SOURCE_IDS
from functools import lru_cache

@lru_cache(maxsize=1)
def inventory():
 return {x['source_id']:x for x in rows(OUT/'source_complete_reading_queue.jsonl')}

def start():
 b=Batch();return b,b.records

def add(b,index,system,equipment,quote,triples,certainty='secondary_stated',notes=''):
 q=inventory()
 sid=SOURCE_IDS[index];title=q[sid]['title']
 r=b.excerpt(sid,title,system,equipment,
   '二手中文资料的代表性证据；仅限原机型或所述条件，不作为通用操作标准。',
   [{'text':quote}],False,notes)
 for a,rel,target in triples:b.fact(r,a,rel,target,quote,certainty)
 return r

def extra(b,r,quote,triples,certainty='secondary_stated',group=''):
 r['reviewed_excerpts'].append({'text':quote})
 for a,rel,target in triples:b.fact(r,a,rel,target,quote,certainty,group)

def omit(b,index,quote,reason):
 r=add(b,index,'fuel_air','柴油机装置',quote,[],notes=reason)
 r['exclusion_reason']=reason
 return r
