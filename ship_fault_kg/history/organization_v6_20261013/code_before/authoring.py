"""Helpers for explicit assistant-authored triples, never automatic extraction."""
class Batch:
    def __init__(self):self.records=[]
    def article(self,sid,title,system,equipment,scope,case=False,notes=''):
        r=dict(source_id=sid,title=title,system=system,equipment=equipment,scope=scope,
            case=case,review='full_text',notes=notes,facts=[])
        self.records.append(r);return r
    def fact(self,r,a,rel,b,q,certainty='secondary_stated',group=''):
        f=(a,rel,b,q,certainty)
        if group:f+= (None,group)
        r['facts'].append(f)
    def excerpt(self,sid,title,system,equipment,scope,excerpts,case=False,notes=''):
        r=self.article(sid,title,system,equipment,scope,case,notes)
        r.update(review='representative_excerpt',reviewed_excerpts=excerpts)
        return r
    def chain(self,r,tokens,q,certainty='secondary_stated',group=''):
        for a,b in zip(tokens,tokens[1:]):self.fact(r,a,'CAUSES',b,q,certainty,group)
    def checks(self,r,items,q,group=''):
        for a,b in items:self.fact(r,'C|'+a,'CHECKS',b,q,'guidance',group)
    def actions(self,r,items,q,group=''):
        for a,b in items:self.fact(r,'A|'+a,'ADDRESSES',b,q,'guidance',group)
    def exclude(self,sid,title,reason,notes=''):
        r=dict(source_id=sid,title=title,review='full_text',facts=[],
               exclusion_reason=reason,notes=notes)
        self.records.append(r);return r
