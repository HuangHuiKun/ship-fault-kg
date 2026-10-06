"""LLM evidence selection followed by a source-checked diagnosis draft."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.request

from retrieve import CAUSAL_RELS, Retriever


HERE = Path(__file__).resolve().parent
QUERY = "标准化诊断结果：柴油发电机出现连杆轴瓦异常磨损，随后机组停机、全船失电并失去推进。分析可能故障链、检查项目和运维建议。"
GROUPS = {"fault_chain": CAUSAL_RELS | {"PRECEDED"},
          "checks": {"CHECKS"}, "actions": {"ADDRESSES", "PROMPTS"}}


def ask_model(facts: list[dict]) -> str:
    lines = [
        "你是船舶故障诊断证据筛选器，只选择最相关的已检索事实编号。",
        '严格输出JSON：{"fault_chain":[编号],"checks":[编号],"actions":[编号]}。',
        "fault_chain选因果关系，checks选检查关系，actions选运维行动关系。每类最多5、2、2条。不生成诊断文字。",
        "输入：" + QUERY,
    ]
    for i, fact in enumerate(facts, 1):
        lines.append(f"[{i}] {fact['case_name']}：{fact['subject']} {fact['relation_zh']} {fact['object']}；"
                     f"关系={fact['relation']}；确定性={fact['certainty']}；"
                     f"来源={fact['source_file']}第{fact['page']}页")
    payload = {"model": "qwen2.5:3b-instruct", "prompt": "\n".join(lines),
               "stream": False, "format": "json", "keep_alive": "5m",
               "options": {"temperature": 0.0, "num_ctx": 2048, "num_predict": 250}}
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8")).get("response", "")


def validate(raw: str, facts: list[dict], primary: str) -> tuple[dict, list[str]]:
    errors = []
    try:
        choice = json.loads(raw)
    except json.JSONDecodeError:
        choice = {}
        errors.append("模型未输出有效 JSON")
    selected = {}
    for field, relations in GROUPS.items():
        items = choice.get(field, [])
        if not isinstance(items, list):
            items = []
            errors.append(field + " 不是数组")
        valid = []
        for number in items:
            if (type(number) is int and 1 <= number <= len(facts)
                    and facts[number - 1]["relation"] in relations
                    and facts[number - 1]["case_id"] == primary):
                if number not in valid:
                    valid.append(number)
            else:
                errors.append(f"拒绝 {field} 中的无效编号 {number}")
        if not valid:
            valid = [i for i, fact in enumerate(facts, 1)
                     if fact["case_id"] == primary and fact["relation"] in relations]
            errors.append(field + " 由图谱事实补齐")
        selected[field] = valid[:{"fault_chain": 5, "checks": 2, "actions": 2}[field]]
    return selected, errors


def render(facts: list[dict], selected: dict, case_name: str) -> str:
    lines = ["# 船舶动力系统知识增强诊断草稿", "", "输入线索：" + QUERY, "",
             f"参考历史案例：{case_name}。本船具体根因仍需现场数据和检查结果确认。", "",
             "## 可能故障与因果解释", ""]
    for number in selected["fault_chain"]:
        fact = facts[number - 1]
        prefix = "可能促成" if fact["certainty"] in {"probable", "possible"} else fact["relation_zh"]
        lines.append(f"- {fact['subject']} {prefix} {fact['object']}。[{number}]")
    lines += ["", "## 建议检查", ""]
    for number in selected["checks"]:
        fact = facts[number - 1]
        lines.append(f"- {fact['subject']}，核查是否存在“{fact['object']}”。[{number}]"
                     + ("（由报告缺陷整理，需专业人员确认。）" if fact["certainty"] == "derived_action" else ""))
    lines += ["", "## 可参考的运维措施", ""]
    for number in selected["actions"]:
        fact = facts[number - 1]
        lines.append(f"- {fact['subject']}。[{number}]"
                     + ("（由报告缺陷整理，需专业人员确认。）" if fact["certainty"] == "derived_action" else ""))
    lines += ["", "## 来源证据", ""]
    numbers = sorted(set(sum((selected[field] for field in GROUPS), [])))
    for number in numbers:
        fact = facts[number - 1]
        lines.append(f"- [{number}] {fact['source_file']}，PDF第{fact['page']}页；"
                     f"[来源]({fact['source_url']})；确定性：{fact['certainty']}。")
    lines += ["", "这是图谱辅助草稿；实际运维决策需结合本船测点、报警与维修记录及制造商手册。", ""]
    return "\n".join(lines)


def main() -> None:
    result = Retriever().search(QUERY, top_cases=2, top_facts=10, top_passages=2)
    raw = ask_model(result["facts"])
    primary = result["cases"][0]["case_id"]
    selected, errors = validate(raw, result["facts"], primary)
    report = render(result["facts"], selected, result["cases"][0]["name"])
    output = {"created_utc": datetime.now(timezone.utc).isoformat(),
              "model": "qwen2.5:3b-instruct", "query": QUERY, "retrieval": result,
              "llm_selection_raw": raw, "validated_selection": selected,
              "selection_errors": errors,
              "final_report_method": "LLM选择证据；依据同一案例中的图谱事实和来源页码确定性生成正文",
              "final_report": report}
    (HERE / "output" / "demo_kg_rag_report.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    (HERE / "output" / "demo_kg_rag_report.md").write_text(report, encoding="utf-8")
    print(json.dumps({"selection": selected, "validation_errors": errors,
                      "report": report}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
