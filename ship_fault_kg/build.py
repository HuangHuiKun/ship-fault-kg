"""Build a provenance-first ship propulsion fault knowledge graph.

Run with a Python environment containing pypdf:
    python ship_fault_kg/build.py

All outputs are deterministic and scoped to ship_fault_kg/output. No existing
Neo4j database is changed by this builder.
"""

from __future__ import annotations

import csv
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import os

from pypdf import PdfReader

from curated_cases import CASES
from expanded_cases import EXPANDED_CASES, ORIGINAL_CONTEXT
from schema import VERSION, SUBSYSTEMS, RELATION_ZH, KIND_ZH, DIAGNOSTIC_RELS, CAUSAL_RELS
from fault_profiles import PROFILES, IMPORTANT_SENSORS

ALL_CASES = CASES + EXPANDED_CASES


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
    "IN_SUBSYSTEM", "BELONGS_TO_SUBSYSTEM", "OF_VESSEL_TYPE", "MONITORS",
    "INSTANCE_OF",
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
SENSOR_ALIASES.update(IMPORTANT_SENSORS)
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
        for manifest in (MANIFEST, MANIFEST.with_name('source_manifest_v3.csv')):
            with manifest.open(encoding="utf-8-sig", newline="") as stream:
                for row in csv.DictReader(stream):
                    self.source_by_file[Path(row["local_item"]).name] = row

    def node(self, kind: str, name: str, aliases: str = "", **props) -> str:
        name = clean(name)
        ident = node_id(kind, name)
        if ident not in self.nodes:
            self.nodes[ident] = {"id": ident, "kind": kind, "name": name,
                                 "aliases": clean(aliases), "props": props}
        else:
            self.nodes[ident]["props"].update(props)
            if aliases and clean(aliases) not in self.nodes[ident]["aliases"]:
                self.nodes[ident]["aliases"] = clean(self.nodes[ident]["aliases"] + " " + aliases)
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
        row = self.source_by_file[filename]
        kind = row['primary_use'] if row['category']=='reference_pdf' and row['primary_use']!='field_report' else 'report'
        return self.evidence_row(filename, f"PDF page {page}", excerpt, kind, page)

    def build_cases(self) -> None:
        for case in ALL_CASES:
            source = case["source"]
            overview = self.pdf_evidence(source, case["summary_page"], case["summary_anchor"])
            case_node = self.node("Case", case["name"], case["id"],
                                  case_id=case["id"], data_origin="field_report",
                                  anonymous_vessel=case.get("anonymous", False))
            vessel_node = self.node("Vessel", case["vessel"],
                                    anonymous=case.get("anonymous", False))
            system_node = self.node("System", case["system"]) if case["system"] else None
            if case["id"] in CASE_ASSETS:
                equipment_name, components = CASE_ASSETS[case["id"]]
            else:
                equipment_name, components = case["equipment"], case["assets"]
            equipment = self.node("Equipment", equipment_name, case["system"] or "")
            self.edge(case_node, "DOCUMENTED_BY", self.source(source), overview, case["id"])
            self.edge(vessel_node, "HAS_CASE", case_node, overview, case["id"])
            if system_node:
                self.edge(case_node, "IN_SYSTEM", system_node, overview, case["id"])
            self.edge(case_node, "HAS_EQUIPMENT", equipment, overview, case["id"])
            vessel_type, subsystems = ORIGINAL_CONTEXT.get(case["id"],
                (case.get("vessel_type", "未确认船型"), case.get("subsystems", [])))
            vt = self.node("VesselType", vessel_type)
            self.edge(vessel_node, "OF_VESSEL_TYPE", vt, overview, case["id"], "curated_classification")
            for subsystem in subsystems:
                sub = self.node("Subsystem", SUBSYSTEMS[subsystem], subsystem,
                                classification_basis="研究用途分类，按报告涉及的设备功能组织")
                self.edge(case_node, "IN_SUBSYSTEM", sub, overview, case["id"], "curated_classification")
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

    def organise_subsystems(self) -> None:
        """Classify existing entities using their names and dictionary metadata.

        These links are taxonomy links, not new engineering causal claims.
        Their original evidence is retained and certainty explicitly records
        that the classification was supplied by the researcher.
        """
        patterns = {
            "fuel_air": r"燃油|喷油|排气|滤清器|增压|空冷|fuel|injection|exhaust|turbine|air.cooler|charge air|filter loss",
            "lubrication": r"润滑|滑油|轴承|轴瓦|连杆|油道|油雾|oil|bearing|babbitt|wear|ring",
            "cooling": r"冷却|海水|压载|舱底|进水|水密|water|coolant|cavitation",
            "transmission": r"轴系|联轴器|离合|盘车|推进|螺距|桨|shaft|gear|pitch|propeller|coupling|torsion|torque|speed",
            "electrical": r"电网|谐波|电容|发电|失电|电机|保护|联锁|报警|控制|指示灯|voltage|generator|electric|power|alarm|interlock",
        }
        allowed = {"Equipment", "Component", "Fault", "Cause", "Condition", "Symptom",
                   "Check", "Action", "Sensor", "Observation"}
        references = {}
        classified = {(e['source'],e['target']) for e in self.edges.values() if e['relation']=='BELONGS_TO_SUBSYSTEM'}
        for edge in sorted(self.edges.values(), key=lambda x: x["id"]):
            for ident in (edge["source"], edge["target"]):
                references.setdefault(ident, edge["evidence_id"])
        for ident, node in list(self.nodes.items()):
            if node["kind"] not in allowed or ident not in references:
                continue
            text = node["name"] + " " + node["aliases"]
            for key, pattern in patterns.items():
                if re.search(pattern, text, re.I):
                    sub = self.node("Subsystem", SUBSYSTEMS[key], key)
                    if (ident,sub) in classified:
                        continue
                    self.edge(ident, "BELONGS_TO_SUBSYSTEM", sub, references[ident],
                              certainty="curated_classification", classification_rule=key)

    def build_fault_profiles(self) -> None:
        for profile in PROFILES:
            scope = profile['id']
            root = self.node('FaultType', profile['name'], profile['aliases'],
                             knowledge_id=scope, applicability=profile['applicability'],
                             coupling_domains=profile['domains'], data_origin='reference_knowledge')
            touched, sources = set(), set()
            first_ev = None
            for raw_a, rel, raw_b, filename, page, anchor, certainty in profile['facts']:
                a = self.node(*parse_node(raw_a))
                b = self.node(*parse_node(raw_b))
                ev = self.pdf_evidence(filename, page, anchor)
                first_ev = first_ev or ev
                origin = self.source_by_file[filename]['primary_use']
                self.edge(a, rel, b, ev, scope, certainty,
                          context_id=scope, knowledge_layer='reference', data_origin=origin,
                          applicability=profile['applicability'], coupling_domains=profile['domains'])
                for ident in (a, b):
                    if ident not in touched:
                        self.edge(root, 'INVOLVES', ident, ev, scope, 'curated_classification')
                        touched.add(ident)
                if filename not in sources:
                    self.edge(root, 'DOCUMENTED_BY', self.source(filename), ev, scope)
                    sources.add(filename)
            for key in profile['subsystems']:
                sub = self.node('Subsystem', SUBSYSTEMS[key], key)
                self.edge(root, 'IN_SUBSYSTEM', sub, first_ev, scope, 'curated_classification')
            for name in [profile['main_fault']] + profile['instances']:
                ident = node_id('Fault', name)
                if ident not in self.nodes:
                    raise ValueError('Fault category target missing: ' + name)
                reference = next((e['evidence_id'] for e in self.edges.values()
                                  if ident in (e['source'], e['target']) and e['case_id']==scope), first_ev)
                self.edge(ident, 'INSTANCE_OF', root, reference, scope, 'curated_classification',
                          classification_basis='人工审核术语分类；不是由该文献证明所有实例根因相同')

    def normalise_display_names(self) -> None:
        # Preserve V2 IDs/links while changing user-visible names.
        for node in self.nodes.values():
            if node['kind'] in {'Vessel', 'VesselType', 'Case'} and node['name'].startswith('匿名'):
                node['props']['original_name'] = node['name']
                node['props']['vessel_identity_status'] = '船名未公开；保留来源案例编号，不推定真实船名'
                node['name'] = node['name'][2:]

    def enrich_captions(self) -> None:
        for node in self.nodes.values():
            display = node["name"]
            if node["name"] in SCENARIO_ALIASES:
                display = SCENARIO_ALIASES[node["name"]].split()[0]
            elif node["kind"] == "Sensor" and node["name"] in SENSOR_ALIASES:
                display = SENSOR_ALIASES[node["name"]]
            node["props"].update(display_name=display, kind_zh=KIND_ZH[node["kind"]], graph_version=VERSION)
            if node["kind"] == "Fault":
                name = node["name"].casefold()
                semantic = "failure_or_event"
                if name in {"normal", "normal operation", "normal wear trend"}:
                    semantic = "normal_reference"
                elif "unconfirmed" in name or "warning" in name:
                    semantic = "unconfirmed_warning"
                elif "退化" in name or "degradation" in name:
                    semantic = "degradation"
                elif any(word in name for word in ("保护跳闸", "序列启动", "停放")):
                    semantic = "protective_event"
                node["props"]["semantic_class"] = semantic
        for edge in self.edges.values():
            edge["props"].update(name=RELATION_ZH[edge["relation"]], graph_version=VERSION,
                                 is_causal=edge["relation"] in CAUSAL_RELS)

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
            if row['full_name'] not in IMPORTANT_SENSORS:
                continue
            sensor = self.node("Sensor", row["full_name"],
                               " ".join((row["symbol"], SENSOR_ALIASES.get(row["full_name"], ""))),
                               unit=row["unit"], category=row["category"],
                               in_reference=row["in_reference"],
                               in_scenario_files=row["in_scenario_files"],
                               selection_reason='保留热状态、润滑冷却、燃烧与轴功率核心诊断变量；不是实船电气测点',
                               note=row['note'])
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
            if row["category"] not in {"report", "reference_pdf"}:
                continue
            for page, text in enumerate(self.pdf_pages(filename), 1):
                if len(text) < 80:
                    continue
                ident = f"passage:{hashlib.sha1((filename+'|'+str(page)).encode()).hexdigest()[:16]}"
                self.passages[ident] = {"id": ident, "source_file": filename,
                                        "source_url": row["source_url"], "page": page,
                                        "kind": "report_page" if row['category']=='report' else 'reference_page', "title": row["title"],
                                        "text": text[:15000]}

        terms = ("轴瓦", "轴承", "连杆", "润滑", "喷油", "冷却", "增压", "轴系", "发电机", "联轴器", "振动", "拉缸", "烧瓦", "汽蚀", "调速", "燃油", "失电")
        selected: dict[Path, str] = {}
        for term in terms:
            matches = sorted(p for p in CORPUS.rglob("*.md") if term in p.name)
            for path in matches[:12]:
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
                                    "text": text[:6000], "locator": rel}

    def validate(self) -> None:
        for edge in self.edges.values():
            if edge["source"] not in self.nodes or edge["target"] not in self.nodes:
                self.errors.append(f"orphan edge: {edge['id']}")
            if edge["evidence_id"] not in self.evidence:
                self.errors.append(f"edge without evidence: {edge['id']}")
            if edge["certainty"] not in {"reported", "probable", "possible", "reported_action", "derived_action", "dataset_label", "simulated", "curated_classification", "guidance", "research_observation"}:
                self.errors.append(f"unknown certainty: {edge['id']}")
        if self.errors:
            raise ValueError("\n".join(self.errors))

    def write_csv(self, filename: str, rows: list[dict], fields: list[str]) -> None:
        with (OUTPUT / filename).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: json.dumps(row[key], ensure_ascii=False) if key == "props" else row.get(key, "") for key in fields})

    def write_outputs(self, export_csv: bool = False) -> None:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        nodes = sorted(self.nodes.values(), key=lambda x: x["id"])
        edges = sorted(self.edges.values(), key=lambda x: x["id"])
        evidence = sorted(self.evidence.values(), key=lambda x: x["id"])
        passages = sorted(self.passages.values(), key=lambda x: x["id"])
        if export_csv:
            self.write_csv("nodes.csv", nodes, ["id", "kind", "name", "aliases", "props"])
            self.write_csv("edges.csv", edges, ["id", "source", "relation", "target", "evidence_id", "case_id", "certainty", "props"])
            self.write_csv("evidence.csv", evidence, ["id", "source_file", "source_url", "source_kind", "page", "locator", "quote"])
            self.write_csv("passages.csv", passages, ["id", "source_file", "source_url", "page", "kind", "title", "text", "locator"])

        db = OUTPUT / "ship_fault_kg.building.sqlite"
        if db.exists():
            raise RuntimeError("Previous temporary build exists; inspect it before rebuilding")
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
        os.replace(db, OUTPUT / "ship_fault_kg.sqlite")

        report = {
            "graph_version": VERSION, "case_count": len(ALL_CASES), "node_count": len(nodes), "edge_count": len(edges),
            "fault_reference_count": len(PROFILES),
            "sensor_count": sum(n['kind']=='Sensor' for n in nodes),
            "evidence_count": len(evidence), "passage_count": len(passages),
            "node_types": dict(Counter(x["kind"] for x in nodes)),
            "relation_types": dict(Counter(x["relation"] for x in edges)),
            "certainty": dict(Counter(x["certainty"] for x in edges)),
            "passage_types": dict(Counter(x["kind"] for x in passages)),
            "source_report_pages": {name: len(pages) for name, pages in self.page_cache.items()},
            "validation_errors": self.errors,
            "evidence_types": dict(Counter(x["source_kind"] for x in evidence)),
            "diagnostic_edge_count": sum(x["relation"] in DIAGNOSTIC_RELS for x in edges),
            "causal_edge_count": sum(x["relation"] in CAUSAL_RELS for x in edges),
            "anonymous_vessel_count": sum(x["kind"] == "Vessel" and x["props"].get("anonymous", False) for x in nodes),
            "audit_csv_exported": export_csv,
            "target_check": {"entities_200_500": 200 <= len(nodes) <= 500,
                             "relationships_600_1500": 600 <= len(edges) <= 1500,
                             "subsystems_3_5": 3 <= sum(x["kind"] == "Subsystem" for x in nodes) <= 5},
        }
        (OUTPUT / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-csv", action="store_true", help="Optional audit tables; not required for Neo4j import")
    args = parser.parse_args()
    builder = Builder()
    builder.build_cases()
    builder.build_engine_dataset()
    builder.build_azimuth_dataset()
    builder.build_other_datasets()
    # Preserve historical taxonomy evidence/IDs before new references are added.
    builder.organise_subsystems()
    builder.build_fault_profiles()
    builder.organise_subsystems()
    builder.normalise_display_names()
    builder.enrich_captions()
    builder.build_passages()
    builder.validate()
    builder.write_outputs(args.export_csv)


if __name__ == "__main__":
    main()
