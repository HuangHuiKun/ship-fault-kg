#!/usr/bin/env python3
"""normalize.py - provenance script for the Marine Engine Fault Dataset (v1.0).
Reproduces the released package from the raw bench exports:
  - UTF-8 (no BOM), LF line endings
  - units row: ℃ -> °C
  - label fixes: 'Anomaly state'->'Anomaly State'; 'Mechanicall Efficiency'->'Mechanical Efficiency';
    'Loss with colling water'->'Loss with cooling water'
  - single canonical 73-column schema/order on all scenario files (empty dPf/dPex where not recorded)
  - space-free folder names; Reference_Data.csv kept on its own 70-column schema
Run: python normalize.py --src <raw_dir> --out <release_dir>
"""
import argparse, csv, io, codecs, glob, os
FOLDER_RENAME = {"AF Clogging":"AF_Clogging","AC Fouling":"AC_Fouling","Injector Nozzle":"Injector_Nozzle",
                 "Pump Cavitation":"Pump_Cavitation","Turbine Degradation":"Turbine_Degradation"}
FULLNAME_FIX = {"Anomaly state":"Anomaly State","Mechanicall Efficiency":"Mechanical Efficiency",
                "Loss with colling water":"Loss with cooling water"}
TEMPLATE_REL = "AC Fouling/AC_Fouling_40_Load.csv"
def read_enc(p):
    raw=open(p,"rb").read()
    if raw.startswith(codecs.BOM_UTF8): return raw.decode("utf-8-sig")
    try: return raw.decode("utf-8")
    except UnicodeDecodeError: return raw.decode("latin-1")
def parse(p):
    r=list(csv.reader(io.StringIO(read_enc(p)))); return r[0],r[1],r[2],r[3:]
def norm_unit(u): return (u or "").strip().replace("\u2103","\u00b0C")
def fix_full(cs): return [FULLNAME_FIX.get(c.strip(),c.strip()) for c in cs]
def write_csv(path,hdr,data):
    os.makedirs(os.path.dirname(path),exist_ok=True)
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,lineterminator="\n")
        for r in hdr: w.writerow(r)
        for r in data: w.writerow(r)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--src",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
    tf,ts,tu,_=parse(os.path.join(a.src,TEMPLATE_REL)); tf=fix_full(tf)
    CANON=list(tf); SHORT={f:s.strip() for f,s in zip(tf,ts)}; UNIT={f:norm_unit(u) for f,u in zip(tf,tu)}
    files=sorted(p for p in glob.glob(os.path.join(a.src,"**/*.csv"),recursive=True)
                 if os.path.basename(p) not in ("variable_dictionary.csv","Reference_Data.csv"))
    for src in files:
        full,short,unit,data=parse(src); full=fix_full(full); present={f:i for i,f in enumerate(full)}
        assert all(f in CANON for f in full), f"{src}: unknown column"
        nd=[[] for _ in data]; nf=[];ns=[];nu=[]
        for f in CANON:
            nf.append(f); ns.append(SHORT[f]); nu.append(UNIT[f]); j=present.get(f)
            for k,r in enumerate(data): nd[k].append(r[j] if (j is not None and j<len(r)) else "")
        rel=os.path.relpath(src,a.src); top,rest=rel.split(os.sep,1)
        write_csv(os.path.join(a.out,FOLDER_RENAME.get(top,top),rest),[nf,ns,nu],nd)
    rf,rs,ru,rd=parse(os.path.join(a.src,"Reference_Data.csv"))
    write_csv(os.path.join(a.out,"Reference_Data.csv"),[fix_full(rf),[s.strip() for s in rs],[norm_unit(u) for u in ru]],rd)
    print("Normalisation complete ->",a.out)
if __name__=="__main__": main()
