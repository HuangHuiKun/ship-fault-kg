import os, re
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get('DASHSCOPE_API_KEY'),
    base_url='https://dashscope.aliyuncs.com/compatible-mode/v1'
)

paper = ''
for f in sorted(os.listdir('C:/Users/Yijie/Documents/ARIS/paper/sections')):
    path = f'C:/Users/Yijie/Documents/ARIS/paper/sections/{f}'
    paper += open(path, encoding='utf-8').read() + '\n\n'

# Strip LaTeX
paper_clean = re.sub(r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}', '[ENV]', paper, flags=re.DOTALL)
paper_clean = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', paper_clean)
paper_clean = re.sub(r'\\[a-zA-Z]+', ' ', paper_clean)
paper_clean = re.sub(r'\s+', ' ', paper_clean).strip()

prompt = """You are a senior reviewer for Ocean Engineering (Elsevier, IF=4.4).
Review the following paper draft critically and rigorously.

Context: LLM-based maritime accident knowledge graph (KG) from 1,165 IMO GISIS reports.
HFACS framework. Validation: Precision=63.7%, Recall=85.1%, F1=72.8%.
Competitor: Liu 2024 (MAKG, 581 reports, F1=0.91, supervised model).

PAPER DRAFT:
""" + paper_clean[:11000] + """

Provide a structured review:

## 1. CRITICAL issues (rejection-level)
List each as: [C1], [C2]...
- Scientific flaws, missing experiments, unsupported major claims

## 2. MAJOR issues (must fix)
List each as: [M1], [M2]...
- Content gaps, thin sections, weak comparisons, missing analyses

## 3. MINOR issues
List each as: [m1], [m2]...
- Writing, figures, references

## 4. Verdict
- Decision: Reject / Major Revision / Minor Revision
- Estimated additional words needed for OE standard
- Top 3 priorities to fix first

Be specific, cite section names, be harsh."""

resp = client.chat.completions.create(
    model='qwen-plus',
    max_tokens=3000,
    messages=[{'role': 'user', 'content': prompt}]
)

review = resp.choices[0].message.content
with open('C:/Users/Yijie/Documents/ARIS/paper/REVIEW_ROUND1.md', 'w', encoding='utf-8') as f:
    f.write(review)
print(review)
