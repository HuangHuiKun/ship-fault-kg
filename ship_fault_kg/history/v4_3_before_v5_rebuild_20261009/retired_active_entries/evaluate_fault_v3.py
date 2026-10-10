"""24 source-derived development queries; not an independent expert benchmark."""
import json
from pathlib import Path
from fault_profiles import PROFILES
from retrieve import Retriever
from build import node_id
from schema import VERSION

HERE=Path(__file__).resolve().parent
PARAPHRASES=[
 '主机疑似拉缸，如何补充机理解释和检查建议？',
 '船舶主机烧瓦与抱轴，应检查哪些原因和证据？',
 '冷却水通道堵塞与热过载如何解释和处置？',
 '冷却回路汽蚀与冷却器低流量有何关系？',
 '扭振减振器失效，润滑和异响有什么意义？',
 '轴带发电机对中异常与振动损伤，风浪和热膨胀怎样影响？',
 '发电机轴承机械磨损与缺少润滑脂如何核查？',
 '电机与发电机轴承电蚀为什么会发生？',
 '发电机绕组绝缘劣化和绝缘电阻降低怎么检查？',
 '联轴器故障造成CPP运动传递失效的来源依据？',
 '轴系扭振与联轴器过载风险需要哪些分析和验证？',
 '船舶电网耦合振荡的原因、来源与检查是什么？',
]

def main():
    r=Retriever(); rows=[]
    for profile,paraphrase in zip(PROFILES,PARAPHRASES):
        # Stable IDs prevent translated display names from changing gold labels.
        gold={(node_id(*f[0].split('|')[:2]),f[1],node_id(*f[2].split('|')[:2])) for f in profile['facts']}
        for wording,query in [('名称',profile['name']),('改写',paraphrase)]:
            result=r.search(query,top_facts=12)
            units=[x['knowledge_id'] for x in result['knowledge_units']]
            rr=1/(units.index(profile['id'])+1) if profile['id'] in units else 0
            found=[(r.edges[f['id']]['source'],f['relation'],r.edges[f['id']]['target']) for f in result['facts']]
            record={'query':query,'query_kind':wording,'expected_context':profile['id'],
                    'gold_fact_count':len(gold),'returned_fact_count':len(found),
                    'mrr_at_3':rr,'coverage':result['coverage'],'focused_reference':result['focused_reference']}
            for k in (5,10):
                hits=sum(x in gold for x in found[:k])
                record[f'recall_at_{k}']=hits/len(gold)
                record[f'precision_at_{k}']=hits/len(found[:k]) if found[:k] else 0
            rows.append(record)
    summary={'question_count':len(rows), 'reference_unit_count':len(PROFILES)}
    for key in ('mrr_at_3','recall_at_5','recall_at_10','precision_at_5','precision_at_10'):
        summary[key]=round(sum(x[key] for x in rows)/len(rows),4)
    output={'summary':summary,'details':rows,
            'limitation':'同源人工编写的开发自检；故障名称/别名被用于对齐，不能作为独立泛化性能或诊断准确率。精度分母为实际返回K以内数量；gold为对应单元全部人工整理诊断关系，不含分类边。'}
    (HERE/'output'/f"fault_retrieval_evaluation_v{VERSION.split('.')[0]}.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
