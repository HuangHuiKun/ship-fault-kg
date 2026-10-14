"""Lossless raw originals + versioned document registry + addressable passages."""
import csv, hashlib, json, re
from pathlib import Path
from pypdf import PdfReader

PROJECT = Path(__file__).resolve().parents[2]
DATA = PROJECT / 'ship_fault_kg_data'
KG = PROJECT / 'ship_fault_kg'
OUT = KG / 'output' / 'v5'
CORPUS = DATA / '01_datasets/marine_diesel_RAG_corpus_All_data/All_data'

def hid(prefix, *parts):
    return prefix + ':' + hashlib.sha256('\x1f'.join(map(str, parts)).encode()).hexdigest()[:24]

def norm(text):
    return ' '.join(text.split())

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def jsonl(path, rows):
    with path.open('w', encoding='utf-8') as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False) + '\n')

class Registry:
    def __init__(self):
        self.sources = {}; self.by_file = {}; self.by_path = {}; self.pages = {}
        self.passages = {}; self.issues = []; self.records = []; self.parameters = []
        self.manifests = {}
        for file in sorted((DATA / '05_metadata').glob('source_manifest*.csv')):
            for row in csv.DictReader(file.open(encoding='utf-8-sig', newline='')):
                if row.get('local_item'):
                    self.manifests[row['local_item'].replace('\\','/')] = row

    def add(self, path, category, url='', title=''):
        relative = path.relative_to(DATA).as_posix()
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        sid = hid('src', sha)
        meta = self.manifests.get(relative, {})
        row = self.sources.setdefault(sid, dict(id=sid, sha256=sha, version_id=sha,
            title=title or meta.get('title') or path.stem, paths=[], category=category,
            url=url or meta.get('source_url',''), license=meta.get('license_or_reuse','见原始资料授权'),
            source_tier=('secondary_corpus' if category=='corpus_article' else
                         'official_investigation' if path.name.startswith('MAIB') else
                         'manufacturer' if path.name.startswith(('MAN','STAMFORD')) else category),
            raw_preserved=True, expert_review='not_performed'))
        row['paths'].append(relative)
        self.by_file[path.name] = sid; self.by_path[relative] = sid
        return sid

    def add_page(self, sid, raw, locator, page=None):
        text = norm(raw)
        self.pages[(sid, str(page) if page is not None else '')] = (raw,text,locator)
        # Chunk without overlap: source-local offsets, not invented document pages.
        for start in range(0,len(text),1200):
            chunk = text[start:start+1200]
            pid = hid('passage',sid,page,start,start+len(chunk))
            self.passages[pid] = dict(id=pid,source_id=sid,page=page,locator=locator,
                normalized_start=start,normalized_end=start+len(chunk),text=chunk,
                source_version=self.sources[sid]['sha256'])

    def locate(self, file_or_path, quote, page=None):
        sid = self.by_path.get(file_or_path) or self.by_file.get(file_or_path)
        if sid is None:
            raise ValueError('Unregistered source: '+file_or_path)
        raw,text,locator = self.pages[(sid,str(page) if page is not None else '')]
        anchor = norm(quote)
        start = text.casefold().find(anchor.casefold())
        if start<0:
            raise ValueError('Quotation absent: '+file_or_path+':'+str(page)+':'+anchor)
        end = start+len(anchor)
        # Map normalized character span to the extracted raw page/article.
        matches=list(re.finditer(r'\S+',raw)); offset=0; raw_start=raw_end=None
        for match in matches:
            nend=offset+len(match.group())
            if raw_start is None and start<nend:
                raw_start=match.start()+max(0,start-offset)
            if end<=nend:
                raw_end=match.start()+max(0,end-offset); break
            offset=nend+1
        if raw_start is None or raw_end is None:
            raise ValueError('Raw locator mapping failed')
        pid=hid('passage',sid,page,'quote',start,end)
        row=dict(id=pid,source_id=sid,page=page,locator=locator,
            normalized_start=start,normalized_end=end,raw_start=raw_start,raw_end=raw_end,
            line_start=raw[:raw_start].count('\n')+1,line_end=raw[:raw_end].count('\n')+1,
            text=text[start:end],source_version=self.sources[sid]['sha256'],exact_quote=True)
        self.passages[pid]=row
        return row

    def run(self):
        OUT.mkdir(parents=True,exist_ok=True)
        # Cache extracted pages, but only reuse when all raw files and source
        # manifests are unchanged. Annotation changes do not re-parse 1,000+ pages.
        inputs=sorted([*(DATA/'02_reports').glob('*.pdf'),*(DATA/'03_papers').glob('*.pdf'),
                       *CORPUS.rglob('*.md'),*(DATA/'05_metadata').glob('source_manifest*.csv'),
                       *(DATA/'01_datasets/Marine_Engine_Fault_Data_v1').rglob('variable_dictionary.csv'),
                       *(DATA/'01_datasets/Marine_Engine_Fault_Data_v1').rglob('dataset_index.csv')])
        fingerprint=hid('preprocess',*(str(p.relative_to(DATA))+hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs))
        cache=OUT/'preprocessed_pages.jsonl';meta=OUT/'preprocess_cache.json'
        if cache.exists() and meta.exists() and json.loads(meta.read_text(encoding='utf-8')).get('fingerprint')==fingerprint:
            self.sources={row['id']:row for row in self.read_rows(OUT/'sources.jsonl')}
            for sid,row in self.sources.items():
                for path in row['paths']:
                    self.by_file[Path(path).name]=sid;self.by_path[path]=sid
            for row in self.read_rows(cache): self.pages[(row['source_id'],row['page_key'])]=(row['raw'],row['text'],row['locator'])
            self.passages={row['id']:row for row in self.read_rows(OUT/'passages.jsonl')}
            self.records=self.read_rows(OUT/'dataset_records.jsonl');self.parameters=self.read_rows(OUT/'parameter_dictionary.jsonl')
            self.issues=json.loads((OUT/'preprocessing_report.json').read_text(encoding='utf-8'))['issues']
            return self
        for folder in ('02_reports','03_papers'):
            for path in sorted((DATA / folder).glob('*.pdf')):
                sid=self.add(path,'technical_report' if folder=='02_reports' else 'research_paper')
                try:
                    for page,item in enumerate(PdfReader(str(path)).pages,1):
                        raw=item.extract_text() or ''
                        if not norm(raw): self.issues.append(dict(file=str(path),page=page,issue='No text; OCR/review required'))
                        self.add_page(sid,raw,path.relative_to(DATA).as_posix(),page)
                except Exception as exc:
                    self.issues.append(dict(file=str(path),issue=type(exc).__name__+':'+str(exc)))
        for path in sorted(CORPUS.rglob('*.md')):
            sid=self.add(path,'corpus_article','https://zenodo.org/records/20258638')
            self.add_page(sid,path.read_text(encoding='utf-8-sig'),path.relative_to(DATA).as_posix())
        # Dataset file index and native dictionaries are metadata, not Run nodes.
        for path in sorted((DATA/'01_datasets/Marine_Engine_Fault_Data_v1').rglob('*.csv')):
            if path.name not in {'dataset_index.csv','variable_dictionary.csv'}: continue
            sid=self.add(path,'dataset_metadata','https://zenodo.org/records/19857425')
            self.add_page(sid,path.read_text(encoding='utf-8-sig'),path.relative_to(DATA).as_posix())
            rows=list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))
            for i,row in enumerate(rows,2):
                target=self.records if path.name=='dataset_index.csv' else self.parameters
                target.append(dict(record_id=hid('record',sid,i),source_id=sid,line=i,**row))
        self.save()
        jsonl(cache,[dict(source_id=sid,page_key=page,raw=raw,text=text,locator=loc) for (sid,page),(raw,text,loc) in self.pages.items()])
        write_json(meta,dict(fingerprint=fingerprint,raw_file_count=len(inputs)))
        return self

    @staticmethod
    def read_rows(path):
        with path.open(encoding='utf-8') as f: return [json.loads(line) for line in f if line.strip()]

    def save(self):
        jsonl(OUT/'sources.jsonl', sorted(self.sources.values(),key=lambda r:r['id']))
        jsonl(OUT/'passages.jsonl', sorted(self.passages.values(),key=lambda r:r['id']))
        jsonl(OUT/'dataset_records.jsonl',self.records)
        jsonl(OUT/'parameter_dictionary.jsonl',self.parameters)
        write_json(OUT/'preprocessing_report.json',dict(source_count=len(self.sources),
            corpus_files=len(list(CORPUS.rglob('*.md'))),duplicate_paths=sum(len(r['paths'])-1 for r in self.sources.values()),
            passages=len(self.passages),dataset_records=len(self.records),parameters=len(self.parameters),issues=self.issues,
            note='数据集原有train/val/test目录仅为来源信息，不作为新检索实验的划分；来源注册数量不等于Neo4j Source节点数。'))

if __name__=='__main__':
    r=Registry().run(); print(json.dumps(dict(sources=len(r.sources),passages=len(r.passages),issues=len(r.issues)),ensure_ascii=False))
