"""Validate the exact 77-source batch, including exclusions, before assembly."""
import collections
import json
from .pipeline import batches,registry,gate
from .selection_077 import SOURCE_IDS

def main():
 reg=registry();records=[r for r in batches() if r['source_id'] in SOURCE_IDS]
 errors=[]
 for r in records:
  try:gate(r,reg)
  except Exception as exc:
   errors.append(dict(source_id=r['source_id'],title=r['title'],error=str(exc)))
 selected=[r['source_id'] for r in records]
 if len(selected)!=77 or set(selected)!=set(SOURCE_IDS):
  errors.append({'error':'Selection is not exactly 77 unique reviewed sources'})
 report=dict(processed=len(records),claims=sum(len(r['facts']) for r in records),
  with_claims=sum(bool(r['facts']) for r in records),
  excluded=sum(not r['facts'] for r in records),
  extent=dict(collections.Counter(r['review'] for r in records)),errors=errors)
 print(json.dumps(report,ensure_ascii=False,indent=2))
 if errors:raise SystemExit(1)

if __name__=='__main__':main()
