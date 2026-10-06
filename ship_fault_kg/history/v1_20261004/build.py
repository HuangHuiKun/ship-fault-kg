"""Build a provenance-first ship propulsion fault knowledge graph.

Run with a Python environment containing pypdf:
    python ship_fault_kg/build.py

All outputs are deterministic and scoped to ship_fault_kg/output. No existing
Neo4j database is changed by this builder.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from pypdf import PdfReader

from curated_cases import CASES


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
DATA = PROJECT / "ship_fault_kg_data"
OUTPUT = HERE / "output"
MANIFEST = DATA / "05_metadata" / "source_manifest.csv"
REPORTS = DATA / "02_reports"
ENGINE = DATA / "01_datasets" / "Marine_Engine_Fault_Data_v1" / "Marine_Engine_Fault_Data"
AZIMUTH = DATA / "01_datasets" / "Azimuth_Thruster_CBM_Dataset" / "data"
TSRF = DATA / "04_code_and_schemas" / "TSRF_main" / "TSRF-main" / "data"
CORPUS = DATA / "01_datasets" / "marine_diesel_RAG_corpus_All_data" / "All_data"

RELATIONS = {
    "DOCUMENTED_BY", "HAS_CASE", "INVOLVES", "IN_SYSTEM", "TESTS_FAULT",
    "HAS_EQUIPMENT", "HAS_COMPONENT", "AFFECTS_COMPONENT",
    "HAS_RUN", "AT_LOAD", "HAS_CHANNEL", "HAS_STATUS", "SHOWS_CONDITION",
    "HAS_RECOMMENDED_ACTION", "CAUSES", "CONTRIBUTED_TO", "LEADS_TO",
    "INCREASES_RISK_OF", "PRECEDED", "PROMPTS", "REDUCES_EFFECTIVENESS_OF",
    "ASSOCIATED_WITH", "LIMITS_DETECTION_OF", "ADDRESSES", "CHECKS",
    "INDICATES", "MAY_CONTRIBUTE_TO", "INCREASES_SEVERITY_OF", "TRIGGERS",
    "WORSENS",
}
SCENARIO_ALIASES = {
    "Air-cooler fouling": "空气冷却器污损 增压空气冷却器结垢",
    "Air-filter clogging (compressor)": "压气机空气滤清器堵塞 进气滤芯堵塞",
    "Injection-valve nozzle clogging": "喷油嘴堵塞 喷油器喷孔堵塞",
    "Cooling-water pump cavitation": "冷却水泵汽蚀 冷却泵空化",
    "Turbine degradation": "涡轮退化 涡轮背压异常",
}
SENSOR_ALIASES = {
    "Engine Speed": "发动机转速",
    "Compressor Filter Loss": "压气机滤清器压损",
    "Turbine Back Pressure": "涡轮背压",
    "Charge Air Press.": "增压空气压力",
}
CASE_ASSETS = {
    "kommandor_susan_dg1_2025": ("Kommandor Susan DG1柴油发电机", [
        ("DG1 5号连杆大端轴瓦", "连杆大端轴瓦", "连杆大端轴瓦失效", 5, "connecting rod bearing number five")]),
    "windcat8_port_engine_2017": ("Windcat 8左舷主机", [
        ("左舷主机6号连杆大端轴瓦", "连杆大端轴瓦", "连杆大端轴瓦失效", 1, "piston connecting rod big end shell bearing")]),
    "wight_sky_me_2017": ("Wight Sky 2017故障主机", [
        ("故障主机5号主轴承", "主轴承瓦片", "主轴承瓦片转位", 14, "main bearing 5")]),
    "finlandia_seaways_me_2018": ("Finlandia Seaways主机", [
        ("主机A5连杆小端", "连杆小端", "连杆小端疲劳断裂", 9, "connecting rod small end")]),
    "wight_sky_me2_2018": ("Wight Sky ME2主机", [
        ("ME2 5号主轴承", "主轴承瓦片", "主轴承瓦片转位", 84, "number five main journal bearing")]),
    "wight_sky_me4_2018": ("Wight Sky ME4主机", [
        ("ME4连杆大端轴承盖", "连杆大端轴承盖", "连杆盖配合面微动磨损", 84,
         "matched connecting rod big end bearing caps")]),
    "spirit_of_discovery_pods_2023": ("Spirit of Discovery吊舱推进系统", [
        ("吊舱推进电机", "推进电机", "推进电机超速", 42, "propulsion motor"),
        ("吊舱舱底液位传感器", "舱底传感器", "进水停机序列启动", 43, "bilge sensor")]),
}


def clean(value: str) -> str:
    return " ".join(str(value or "").split())


def node_id(kind: str, name: str) -> str:
    digest = hashlib.sha1(f"{kind}|{name}".encode("utf-8")).hexdigest()[:12]
    return f"shipkg:{kind.lower()}:{digest}"


def parse_node(raw: str) -> tuple[str, str, str]:
    kind, name, *aliases = raw.split("|")
    return kind, name, "|".join(aliases)


class Builder:
    def __init__(self) -> None:
        self.nodes: dict[str, dict] = {}
        self.edges: dict[str, dict] = {}
        self.evidence: dict[str, dict] = {}
        self.passages: dict[str, dict] = {}
        self.source_by_file: dict[str, dict] = {}
        self.page_cache: dict[str, list[str]] = {}
        self.errors: list[str] = []
        for row in csv.DictReader(MANIFEST.open(encoding="utf-8-sig", newline="")):
            self.source_by_file[Path(row["local_item"]).name] = row

    def node(self, kind: str, name: str, aliases: str = "", **props) -> str:
        name = clean(name)
        ident = node_id(kind, name)
        if ident not in self.nodes:
            self.nodes[ident] = {"id": ident, "kind": kind, "name": name,
                                 "aliases": clean(aliases), "props": props}
        return ident

    def source(self, filename: str) -> str:
        row = self.source_by_file[filename]
        return self.node("Source", row["title"], filename,
                         url=row["source_url"], local_item=row["local_item"],
                         license=row["license_or_reuse"], category=row["category"])

    def evidence_row(self, source_file: str, locator: str, quote: str,
                     kind: str, page: int | None = None) -> str:
        key = f"{source_file}|{locator}|{clean(quote)}"
        ident = "ev:" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
        if ident not in self.evidence:
            source = self.source_by_file[source_file]
            self.evidence[ident] = {
                "id": ident, "source_file": source_file,
                "source_url": source["source_url"], "source_kind": kind,
                "page": page or "", "locator": locator, "quote": clean(quote),
            }
        return ident

    def edge(self, source: str, relation: str, target: str, evidence_id: str,
             case_id: str = "", certainty: str = "reported", **props) -> str:
        if relation not in RELATIONS:
            raise ValueError(f"Unknown relation: {relation}")
        key = f"{source}|{relation}|{target}|{evidence_id}|{case_id}"
        ident = "edge:" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
        self.edges[ident] = {
            "id": ident, "source": source, "relation": relation,
            "target": target, "evidence_id": evidence_id,
            "case_id": case_id, "certainty": certainty, "props": props,
        }
        return ident

    def pdf_pages(self, filename: str) -> list[str]:
        if filename not in self.page_cache:
            self.page_cache[filename] = [clean(p.extract_text() or "")
                                         for p in PdfReader(REPORTS / filename).pages]
        return self.page_cache[filename]

    def pdf_evidence(self, filename: str, page: int, anchor: str) -> str:
        pages = self.pdf_pages(filename)
        if not (1 <= page <= len(pages)):
            raise ValueError(f"Invalid page {page}: {filename}")
        text = pages[page - 1]
        where = text.casefold().find(clean(anchor).casefold())
        if where < 0:
            raise ValueError(f"Anchor absent from {filename} PDF page {page}: {anchor}")
        excerpt = text[max(0, where - 130): min(len(text), where + len(anchor) + 230)]
        return self.evidence_row(filename, f"PDF page {page}", excerpt, "report", page)

    def build_cases(self) -> None:
        for case in CASES:
            source = case["source"]
            overview = self.pdf_evidence(source, case["summary_page"], case["summary_anchor"])
            case_node = self.node("Case", case["name"], case["id"],
                                  case_id=case["id"], data_origin="field_report")
            vessel_node = self.node("Vessel", case["vessel"])
            system_node = self.node("System", case["system"])
            equipment_name, components = CASE_ASSETS[case["id"]]
            equipment = self.node("Equipment", equipment_name, case["system"])
            self.edge(case_node, "DOCUMENTED_BY", self.source(source), overview, case["id"])
            self.edge(vessel_node, "HAS_CASE", case_node, overview, case["id"])
            self.edge(case_node, "IN_SYSTEM", system_node, overview, case["id"])
            self.edge(case_node, "HAS_EQUIPMENT", equipment, overview, case["id"])
            for component_name, alias, fault_name, page, anchor in components:
                ev = self.pdf_evidence(source, page, anchor)
                component = self.node("Component", component_name, alias)
                fault = self.node("Fault", fault_name)
                self.edge(equipment, "HAS_COMPONENT", component, ev, case["id"])
                self.edge(fault, "AFFECTS_COMPONENT", component, ev, case["id"])
            touched: set[str] = set()
            for source_raw, relation, target_raw, page, anchor, certainty in case["facts"]:
                sk, sn, sa = parse_node(source_raw)
                tk, tn, ta = parse_node(target_raw)
                a = self.node(sk, sn, sa)
                b = self.node(tk, tn, ta)
                ev = self.pdf_evidence(source, page, anchor)
                self.edge(a, relation, b, ev, case["id"], certainty)
                for touched_node in (a, b):
                    if touched_node not in touched:
                        self.edge(case_node, "INVOLVES", touched_node, ev, case["id"])
                        touched.add(touched_node)

    def build_engine_dataset(self) -> None:
        source_file = "Marine_Engine_Fault_Data_v1.zip"
        source_node = self.source(source_file)
        ds = self.node("Dataset", "Marine Engine Fault Dataset (MU323DGSC)",
                       "船用柴油机实机故障试验数据", data_origin="controlled_experiment")
        base_ev = self.evidence_row(source_file, "dataset_index.csv", "MU323DGSC controlled fault scenarios; see dataset_index.csv", "dataset")
        self.edge(ds, "DOCUMENTED_BY", source_node, base_ev)
        faults: dict[str, str] = {}
        index_path = ENGINE / "dataset_index.csv"
        for row in csv.DictReader(index_path.open(encoding="utf-8", newline="")):
            run = self.node("Run", row["file_name"], "",
                            data_rows=int(row["data_rows"]), columns=int(row["columns"]),
                            anomaly_state=row["anomaly_state"], schema_type=row["schema_type"],
                            data_origin="controlled_experiment")
            ev = self.evidence_row(source_file, f"dataset_index.csv:{row['file_name']}",
                                   "; ".join(f"{k}={v}" for k, v in row.items() if v), "dataset")
            self.edge(ds, "HAS_RUN", run, ev)
            if row["scenario"]:
                fault = faults.setdefault(row["scenario"], self.node("Fault", row["scenario"],
                                                                      SCENARIO_ALIASES.get(row["scenario"], "")))
                self.edge(run, "TESTS_FAULT", fault, ev)
            if row["nominal_load"]:
                load = self.node("Condition", "负载 " + row["nominal_load"], row["nominal_load"])
                self.edge(run, "AT_LOAD", load, ev)
        for row in csv.DictReader((ENGINE / "variable_dictionary.csv").open(encoding="utf-8", newline="")):
            if row["category"] == "time / labeling":
                continue
            sensor = self.node("Sensor", row["full_name"],
                               " ".join((row["symbol"], SENSOR_ALIASES.get(row["full_name"], ""))),
                               unit=row["unit"], category=row["category"],
                               in_reference=row["in_reference"],
                               in_scenario_files=row["in_scenario_files"])
            ev = self.evidence_row(source_file, f"variable_dictionary.csv:{row['full_name']}",
                                   "; ".join(f"{k}={v}" for k, v in row.items() if v), "dataset")
            self.edge(ds, "HAS_CHANNEL", sensor, ev)

    def build_azimuth_dataset(self) -> None:
        source_file = "Azimuth_Thruster_CBM_Dataset.zip"
        ds = self.node("Dataset", "Azimuth Thruster CBM Dataset", "方位推进器状态监测数据",
                       data_origin="anonymised_field_summary")
        base_ev = self.evidence_row(source_file, "README.md", "Anonymised vibration, lubricant and availability dataset for tugboat propulsion systems", "dataset")
        self.edge(ds, "DOCUMENTED_BY", self.source(source_file), base_ev)
        path = AZIMUTH / "table3_lti_by_fault_type_anonymised.csv"
        for index, row in enumerate(csv.DictReader(path.open(encoding="utf-8-sig", newline="")), 1):
            case_name = row["System / engine-family case"]
            observation = self.node("Observation", case_name, "",
                                    data_origin="anonymised_field_summary", record=index,
                                    warning_hours=row["Warning (h)"],
                                    warning_months=row["LTI / warning (mo)"],
                                    reference_class=row["Reference class"])
            ev = self.evidence_row(source_file, f"table3_lti_by_fault_type_anonymised.csv:row{index}",
                                   "; ".join(f"{k}={v}" for k, v in row.items() if v), "dataset")
            self.edge(ds, "HAS_CASE", observation, ev)
            fault = self.node("Fault", row["Fault or condition"])
            self.edge(observation, "SHOWS_CONDITION", fault, ev, certainty="dataset_label")
            if row["Recommended CBM action"]:
                action = self.node("Action", row["Recommended CBM action"])
                self.edge(observation, "HAS_RECOMMENDED_ACTION", action, ev, certainty="dataset_label")

    def build_other_datasets(self) -> None:
        uci_file = "UCI_Naval_Propulsion_CBM.zip"
        uci = self.node("Dataset", "UCI Naval Propulsion CBM", "护卫舰燃气轮机推进仿真数据",
                        data_origin="simulation", instances=11934)
        ev = self.evidence_row(uci_file, "README.txt", "Frigate gas-turbine propulsion numerical simulator; compressor and turbine decay coefficients", "dataset")
        self.edge(uci, "DOCUMENTED_BY", self.source(uci_file), ev)
        for name in ("燃气轮机压气机退化", "燃气轮机涡轮退化"):
            fault = self.node("Fault", name)
            self.edge(uci, "SHOWS_CONDITION", fault, ev, certainty="simulated")
        tsrf_file = "TSRF_main.zip"
        tsrf = self.node("Dataset", "TSRF marine diesel combustion-chamber fault CSVs", "燃烧室热力仿真故障数据",
                         data_origin="thermodynamic_simulation")
        tev = self.evidence_row(tsrf_file, "README.md", "Six health states in TSRF data directory; thermodynamic simulation assisted diagnosis", "code")
        self.edge(tsrf, "DOCUMENTED_BY", self.source(tsrf_file), tev)
        for path in sorted(TSRF.glob("*.csv")):
            fault = self.node("Fault", path.stem.replace("Linner", "Liner"))
            ev = self.evidence_row(tsrf_file, f"data/{path.name}", path.name, "code")
            self.edge(tsrf, "SHOWS_CONDITION", fault, ev, certainty="simulated")

    def build_passages(self) -> None:
        for filename, row in self.source_by_file.items():
            if row["category"] != "report":
                continue
            for page, text in enumerate(self.pdf_pages(filename), 1):
                if len(text) < 80:
                    continue
                ident = f"passage:{hashlib.sha1((filename+'|'+str(page)).encode()).hexdigest()[:16]}"
                self.passages[ident] = {"id": ident, "source_file": filename,
                                        "source_url": row["source_url"], "page": page,
                                        "kind": "report_page", "title": row["title"],
                                        "text": text[:15000]}

        terms = ("轴瓦", "轴承", "连杆", "润滑", "喷油", "冷却", "增压", "轴系", "发电机", "联轴器", "振动", "拉缸", "烧瓦", "汽蚀")
        selected: dict[Path, str] = {}
        for term in terms:
            matches = sorted(p for p in CORPUS.rglob("*.md") if term in p.name)
            for path in matches[:8]:
                selected[path] = term
        corpus_file = "marine_diesel_RAG_corpus_All_data.zip"
        row = self.source_by_file[corpus_file]
        for path in sorted(selected):
            try:
                text = clean(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                text = clean(path.read_text(encoding="gbk", errors="replace"))
            if len(text) < 80:
                continue
            rel = path.relative_to(CORPUS).as_posix()
            ident = f"passage:{hashlib.sha1(rel.encode('utf-8')).hexdigest()[:16]}"
            self.passages[ident] = {"id": ident, "source_file": corpus_file,
                                    "source_url": row["source_url"], "page": "",
                                    "kind": "corpus_article", "title": path.stem,
                                    "text": text[:2500], "locator": rel}

    def validate(self) -> None:
        for edge in self.edges.values():
            if edge["source"] not in self.nodes or edge["target"] not in self.nodes:
                self.errors.append(f"orphan edge: {edge['id']}")
            if edge["evidence_id"] not in self.evidence:
                self.errors.append(f"edge without evidence: {edge['id']}")
            if edge["certainty"] not in {"reported", "probable", "possible", "reported_action", "derived_action", "dataset_label", "simulated"}:
                self.errors.append(f"unknown certainty: {edge['id']}")
        if self.errors:
            raise ValueError("\n".join(self.errors))

    def write_csv(self, filename: str, rows: list[dict], fields: list[str]) -> None:
        with (OUTPUT / filename).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: json.dumps(row[key], ensure_ascii=False) if key == "props" else row.get(key, "") for key in fields})

    def write_outputs(self) -> None:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        nodes = sorted(self.nodes.values(), key=lambda x: x["id"])
        edges = sorted(self.edges.values(), key=lambda x: x["id"])
        evidence = sorted(self.evidence.values(), key=lambda x: x["id"])
        passages = sorted(self.passages.values(), key=lambda x: x["id"])
        self.write_csv("nodes.csv", nodes, ["id", "kind", "name", "aliases", "props"])
        self.write_csv("edges.csv", edges, ["id", "source", "relation", "target", "evidence_id", "case_id", "certainty", "props"])
        self.write_csv("evidence.csv", evidence, ["id", "source_file", "source_url", "source_kind", "page", "locator", "quote"])
        self.write_csv("passages.csv", passages, ["id", "source_file", "source_url", "page", "kind", "title", "text", "locator"])

        db = OUTPUT / "ship_fault_kg.sqlite"
        if db.exists():
            db.unlink()
        conn = sqlite3.connect(db)
        try:
            conn.executescript("""
                CREATE TABLE nodes(id TEXT PRIMARY KEY, kind TEXT, name TEXT, aliases TEXT, props TEXT);
                CREATE TABLE edges(id TEXT PRIMARY KEY, source TEXT, relation TEXT, target TEXT,
                                   evidence_id TEXT, case_id TEXT, certainty TEXT, props TEXT);
                CREATE TABLE evidence(id TEXT PRIMARY KEY, source_file TEXT, source_url TEXT,
                                      source_kind TEXT, page TEXT, locator TEXT, quote TEXT);
                CREATE TABLE passages(id TEXT PRIMARY KEY, source_file TEXT, source_url TEXT,
                                      page TEXT, kind TEXT, title TEXT, text TEXT, locator TEXT);
                CREATE INDEX edge_source ON edges(source);
                CREATE INDEX edge_target ON edges(target);
                CREATE INDEX edge_case ON edges(case_id);
            """)
            for table, rows, fields in (
                ("nodes", nodes, ["id", "kind", "name", "aliases", "props"]),
                ("edges", edges, ["id", "source", "relation", "target", "evidence_id", "case_id", "certainty", "props"]),
                ("evidence", evidence, ["id", "source_file", "source_url", "source_kind", "page", "locator", "quote"]),
                ("passages", passages, ["id", "source_file", "source_url", "page", "kind", "title", "text", "locator"]),
            ):
                placeholders = ",".join("?" for _ in fields)
                conn.executemany(f"INSERT INTO {table} VALUES ({placeholders})",
                                 [tuple(json.dumps(row[key], ensure_ascii=False) if key == "props" else row.get(key, "") for key in fields) for row in rows])
            conn.commit()
        finally:
            conn.close()

        report = {
            "case_count": len(CASES), "node_count": len(nodes), "edge_count": len(edges),
            "evidence_count": len(evidence), "passage_count": len(passages),
            "node_types": dict(Counter(x["kind"] for x in nodes)),
            "relation_types": dict(Counter(x["relation"] for x in edges)),
            "certainty": dict(Counter(x["certainty"] for x in edges)),
            "passage_types": dict(Counter(x["kind"] for x in passages)),
            "source_report_pages": {name: len(pages) for name, pages in self.page_cache.items()},
            "validation_errors": self.errors,
        }
        (OUTPUT / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))


def main() -> None:
    builder = Builder()
    builder.build_cases()
    builder.build_engine_dataset()
    builder.build_azimuth_dataset()
    builder.build_other_datasets()
    builder.build_passages()
    builder.validate()
    builder.write_outputs()


if __name__ == "__main__":
    main()
