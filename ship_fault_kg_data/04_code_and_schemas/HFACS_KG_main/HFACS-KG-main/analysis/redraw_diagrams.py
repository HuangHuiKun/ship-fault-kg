"""
Redraw pipeline_diagram and graphrag_pipeline with publication quality.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'savefig.dpi': 300,
    'savefig.facecolor': 'white',
    'savefig.bbox': 'tight',
})

OUT = 'paper/figures/'

# ── Shared helpers ────────────────────────────────────────────────────────────
def rounded_box(ax, x, y, w, h, facecolor, label, sublabel=None,
                textcolor='white', fontsize=9, radius=0.12):
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle=f"round,pad=0.04,rounding_size={radius}",
                         facecolor=facecolor, edgecolor='white',
                         linewidth=1.5, zorder=3, alpha=0.95)
    ax.add_patch(box)
    cy = y + h / 2
    if sublabel:
        ax.text(x+w/2, cy+h*0.13, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=textcolor, zorder=4)
        ax.text(x+w/2, cy-h*0.18, sublabel, ha='center', va='center',
                fontsize=fontsize-1.5, color=textcolor, alpha=0.88, zorder=4)
    else:
        ax.text(x+w/2, cy, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=textcolor, zorder=4)

def arrow(ax, x1, x2, y, color='#444444', lw=1.6, label=None):
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                connectionstyle='arc3,rad=0'), zorder=5)
    if label:
        mx = (x1+x2)/2
        ax.text(mx, y+0.08, label, ha='center', va='bottom',
                fontsize=6.5, color=color, style='italic')

# ─────────────────────────────────────────────────────────────────────────────
# FIG A  Two-stage pipeline
# ─────────────────────────────────────────────────────────────────────────────
def fig_pipeline():
    C = {'input':  '#2166AC',
         's1':     '#D6604D',
         's2':     '#1A7837',
         'db':     '#762A83',
         'export': '#4F6272',
         'valid':  '#B8860B'}

    fig, ax = plt.subplots(figsize=(13, 4.8))
    ax.set_xlim(0, 13); ax.set_ylim(0, 4.8)
    ax.axis('off')

    # main pipeline row  y=2.0..3.8  (height=1.8)
    BH = 1.8; BY = 1.4
    specs = [
        (0.15,  1.7,  C['input'],  'IMO GISIS\nPDF Reports',  '1,165 reports\n(English)'),
        (2.15,  1.7,  C['input'],  'PDF Text\nExtraction',    'pdfplumber'),
        (4.15,  2.05, C['s1'],     'Stage 1\nQwen-Max',       'Entities · Events\nCausal factors'),
        (6.5,   2.05, C['s2'],     'Stage 2\nQwen-Max',       'HFACS mapping\n4 levels'),
        (8.85,  1.7,  C['db'],     'Neo4j 5.x\nKG Import',    '42,679 nodes\n47,468 edges'),
        (10.85, 1.5,  C['export'], 'CSV Export\n& Analysis',  '11 files'),
    ]
    xs = []
    for x, w, color, lab, sub in specs:
        rounded_box(ax, x, BY, w, BH, color, lab, sub, fontsize=8.5)
        xs.append((x, w))

    # horizontal arrows
    gaps = [(xs[i][0]+xs[i][1], xs[i+1][0]) for i in range(len(xs)-1)]
    for x1, x2 in gaps:
        arrow(ax, x1+0.02, x2-0.02, BY+BH/2)

    # Stage labels above
    ax.text(5.17, BY+BH+0.18, 'Stage 1: Entity & Event Extraction',
            ha='center', fontsize=8, color=C['s1'], style='italic')
    ax.text(7.52, BY+BH+0.18, 'Stage 2: HFACS Mapping',
            ha='center', fontsize=8, color=C['s2'], style='italic')
    # bracket under stage 1 & 2
    for xb, xe, col in [(4.15, 6.2, C['s1']), (6.5, 8.55, C['s2'])]:
        ax.plot([xb, xe], [BY-0.12, BY-0.12], color=col, lw=1.5, solid_capstyle='round')

    # Cross-model validation arc (below)
    ax.annotate('', xy=(8.85+1.025, BY-0.05), xytext=(6.5+1.025, BY-0.05),
                arrowprops=dict(arrowstyle='<->', color='#B2182B', lw=1.4,
                                connectionstyle='arc3,rad=0.45'), zorder=5)
    ax.text(8.17, 0.6, 'Cross-model validation\nQwen-Plus (n = 49 reports)',
            ha='center', va='center', fontsize=7.5, color='#B2182B', style='italic')

    # Title
    ax.text(6.5, 4.55, 'Two-Stage LLM Maritime Accident Knowledge Graph Construction Pipeline',
            ha='center', fontsize=11, fontweight='bold', color='#1a1a2e')

    plt.savefig(OUT + 'pipeline_diagram.png')
    plt.close()
    print("  saved pipeline_diagram")

# ─────────────────────────────────────────────────────────────────────────────
# FIG B  GraphRAG pipeline
# ─────────────────────────────────────────────────────────────────────────────
def fig_graphrag():
    C = {'query':   '#2166AC',
         'decomp':  '#4F6272',
         'kg':      '#1A7837',
         'llm':     '#762A83',
         'answer':  '#D6604D',
         's1':      '#B2182B',
         's2':      '#0571B0',
         's3':      '#008837'}

    fig, ax = plt.subplots(figsize=(13, 5.6))
    ax.set_xlim(0, 13); ax.set_ylim(0, 5.6)
    ax.axis('off')

    # Title
    ax.text(6.5, 5.35, 'GraphRAG Pipeline for Maritime Accident Safety Querying',
            ha='center', fontsize=11, fontweight='bold', color='#1a1a2e')

    # ── TOP ROW: main pipeline ──────────────────────────────────
    BH = 1.6; BY = 3.3
    main = [
        (0.1,  1.75, C['query'],  'Natural Language\nQuery',          None),
        (2.2,  1.75, C['decomp'], 'Query\nDecomposer',                'strategy selection'),
        (4.3,  2.1,  C['kg'],     'KG Retrieval',                     'pandas / Cypher'),
        (6.7,  2.1,  C['kg'],     'Subgraph\nJSON Context',           'structured facts'),
        (9.1,  1.75, C['llm'],    'Qwen-Max\nLLM',                    'answer synthesis'),
        (11.2, 1.55, C['answer'], 'Safety\nAnswer',                   None),
    ]
    mxs = []
    for x, w, color, lab, sub in main:
        rounded_box(ax, x, BY, w, BH, color, lab, sub, fontsize=8.5)
        mxs.append((x, w))

    for i in range(len(mxs)-1):
        x1 = mxs[i][0]+mxs[i][1]+0.02
        x2 = mxs[i+1][0]-0.02
        arrow(ax, x1, x2, BY+BH/2)

    # Layer labels
    for xc, lbl, col in [(1.0,'Query layer','#777'),
                         (5.3,'Retrieval layer','#777'),
                         (10.0,'Generation layer','#777')]:
        ax.text(xc, BY-0.22, lbl, ha='center', fontsize=7.5,
                color=col, style='italic')

    # ── BOTTOM ROW: 3 strategies ────────────────────────────────
    SH = 1.5; SY = 0.4
    strategies = [
        (0.8,  3.5, C['s1'], 'Q1: Type-Filter\nLookup',
         'filter by accident_type\n→ HFACS category counts'),
        (4.4,  3.5, C['s2'], 'Q2: Chain Complexity\nQuery',
         'EventNode→EventNode edges\n→ mean chain length / type'),
        (8.1,  3.5, C['s3'], 'Q3: Two-Hop\nCausal Path',
         'HFACS→EventNode→Accident\n→ downstream outcomes'),
    ]
    # target x positions spread across KG Retrieval box bottom edge
    target_xs = [4.55, 5.35, 6.15]
    for i, ((x, w, color, lab, sub), tx) in enumerate(zip(strategies, target_xs)):
        rounded_box(ax, x, SY, w, SH, color, lab, sub, fontsize=8, radius=0.1)
        cx = x + w/2
        ax.annotate('', xy=(tx, BY),
                    xytext=(cx, SY+SH+0.02),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.2,
                                    linestyle='dashed',
                                    connectionstyle='arc3,rad=0'), zorder=4)

    # KG store badge — placed below and clear of layer label
    ax.text(5.35, BY-0.38, '42,679 nodes · 47,468 edges',
            ha='center', va='top', fontsize=6.5, color='#555', style='italic')

    plt.savefig(OUT + 'graphrag_pipeline.png')
    plt.close()
    print("  saved graphrag_pipeline")

fig_pipeline()
fig_graphrag()
print("Architecture diagrams done.")
