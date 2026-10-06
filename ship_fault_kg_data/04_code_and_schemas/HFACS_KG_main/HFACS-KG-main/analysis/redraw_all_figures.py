"""
Publication-quality figure redrawing for Ocean Engineering submission.
Style: Nature/Elsevier standard — clean, colorblind-safe, 300 DPI.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.gridspec as gridspec
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# ── Global style ──────────────────────────────────────────────────────────────
PALETTE = {
    'blue':   '#2166AC',
    'orange': '#D6604D',
    'teal':   '#4DAC26',
    'purple': '#762A83',
    'grey':   '#999999',
    'navy':   '#053061',
    'red':    '#B2182B',
    'green':  '#1A7837',
    'gold':   '#B8860B',
    'slate':  '#4F6272',
}
# colorblind-safe sequential
LEVEL_COLORS = ['#4393C3', '#74ADD1', '#F46D43', '#D73027']  # L1-L4
CAT_COLORS = ['#2166AC','#D6604D','#4DAC26','#762A83','#B8860B',
              '#4F6272','#1A7837','#B2182B','#053061','#999999']

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'font.size': 9,
    'axes.titlesize': 10,
    'axes.labelsize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'legend.fontsize': 8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.facecolor': 'white',
})

OUT = 'paper/figures/'

# ── Load data ─────────────────────────────────────────────────────────────────
acc = pd.read_csv('kg_export/nodes_accident.csv')
hf  = pd.read_csv('results/R002b_hfacs_with_categories.csv')
ev  = pd.read_csv('kg_export/nodes_event.csv')
led = pd.read_csv('kg_export/rel_led_to.csv')

print("Data loaded.")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 1  Accident type distribution  (horizontal bar, sorted)
# ─────────────────────────────────────────────────────────────────────────────
def fig_acc_dist():
    counts = acc['accident_type'].value_counts()
    top = counts.head(15).sort_values()

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    bars = ax.barh(top.index, top.values,
                   color=PALETTE['blue'], edgecolor='white', linewidth=0.4,
                   height=0.65)

    # value labels
    for bar, v in zip(bars, top.values):
        pct = v / len(acc) * 100
        ax.text(bar.get_width() + 4, bar.get_y() + bar.get_height()/2,
                f'{v}  ({pct:.1f}%)', va='center', ha='left',
                fontsize=7.5, color='#333333')

    ax.set_xlabel('Number of accident reports', labelpad=6)
    ax.set_title('Distribution of accident reports by type\n'
                 f'(n = {len(acc):,} total)', pad=8, fontweight='bold')
    ax.set_xlim(0, top.max() * 1.28)
    ax.tick_params(axis='y', length=0)
    ax.axvline(0, color='#333', lw=0.6)
    ax.grid(axis='x', lw=0.4, color='#ddd', zorder=0)

    plt.tight_layout()
    plt.savefig(OUT + 'R001_accident_distribution.png')
    plt.close()
    print("  saved R001")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 2  HFACS category distribution  (colored by HFACS level)
# ─────────────────────────────────────────────────────────────────────────────
def fig_hfacs_dist():
    level_map = {
        'Situational Awareness': 1, 'Human Error & Decision Making': 1,
        'Violation & Non-compliance': 1, 'Specific Operational Failures': 1,
        'Navigation & Passage Planning': 1,
        'Fatigue & Workload': 2, 'Communication': 2,
        'Bridge & Crew Resource Management': 2, 'Medical & Physical Condition': 2,
        'PPE & Personal Safety': 2, 'Risk Perception & Normalization of Deviation': 2,
        'Inter-vessel & Team Coordination': 2,
        'Supervision & Oversight': 3, 'Training & Competency': 3,
        'Manning & Crewing': 3, 'Emergency Response': 3,
        'Contingency & Emergency Planning': 3,
        'Procedures & SMS': 4, 'Organizational & Regulatory': 4,
        'Safety Culture & Pressure': 4, 'Maintenance & Equipment': 4,
        'Vessel Design & Stability': 4, 'Resource Allocation & Planning': 4,
        'Cargo & Lifting Operations': 4, 'Fire & Explosion Safety': 4,
        'Enclosed Space & Atmosphere': 4, 'Lessons Learned & Documentation': 4,
        'Physical Hazard & Immediate Cause': 4, 'Voyage & Weather Planning': 4,
        'Other / Unclassified': 0,
    }
    counts = hf['category'].value_counts()
    # include unclassified
    data = pd.DataFrame({'category': counts.index, 'n': counts.values})
    data['level'] = data['category'].map(level_map).fillna(0).astype(int)
    data = data.sort_values('n', ascending=True)

    level_colors = {0: '#BBBBBB', 1: '#4393C3', 2: '#74ADD1',
                    3: '#F46D43', 4: '#D73027'}
    colors = [level_colors[l] for l in data['level']]

    fig, ax = plt.subplots(figsize=(7, 7))
    bars = ax.barh(data['category'], data['n'], color=colors,
                   edgecolor='white', linewidth=0.3, height=0.72)

    for bar, v in zip(bars, data['n']):
        ax.text(bar.get_width() + 30, bar.get_y() + bar.get_height()/2,
                f'{v:,}', va='center', fontsize=6.5, color='#444')

    ax.set_xlabel('Number of factor instances', labelpad=6)
    ax.set_title('HFACS factor instances by semantic category\n'
                 f'(n = {len(hf):,} total factors)', pad=8, fontweight='bold')
    ax.set_xlim(0, data['n'].max() * 1.18)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', lw=0.3, color='#ddd', zorder=0)

    # legend
    patches = [mpatches.Patch(color=level_colors[l],
               label=f'HFACS Level {l}' if l > 0 else 'Unclassified')
               for l in [1,2,3,4,0]]
    ax.legend(handles=patches, loc='lower right', frameon=True,
              framealpha=0.9, edgecolor='#ccc', fontsize=7.5)

    plt.tight_layout()
    plt.savefig(OUT + 'R002b_hfacs_categories.png')
    plt.close()
    print("  saved R002b")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 3  Type × Factor heatmap  (row-normalised)
# ─────────────────────────────────────────────────────────────────────────────
def fig_heatmap():
    top_types = acc['accident_type'].value_counts().head(10).index.tolist()
    top_cats  = [c for c in hf['category'].value_counts().head(13).index
                 if c != 'Other / Unclassified']

    acc_files = acc[acc['accident_type'].isin(top_types)].copy()
    hf_sub    = hf[hf['category'].isin(top_cats)].copy()

    rows = []
    for atype in top_types:
        files = set(acc_files[acc_files['accident_type']==atype]['source_file'])
        n     = len(files)
        for cat in top_cats:
            n_rep = hf_sub[(hf_sub['category']==cat) &
                           (hf_sub['source_file'].isin(files))]['source_file'].nunique()
            rows.append({'type': atype, 'category': cat,
                         'pct': n_rep/n*100 if n else 0})

    df = pd.DataFrame(rows).pivot(index='type', columns='category', values='pct')
    # row-normalise
    df_norm = df.div(df.sum(axis=1), axis=0) * 100
    # shorten labels
    short_cats = {c: c.replace(' & ', '\n& ').replace('Passage Planning','PP')
                  for c in top_cats}
    df_norm.columns = [short_cats.get(c,c) for c in df_norm.columns]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    cmap = sns.color_palette("YlOrRd", as_cmap=True)
    im = ax.imshow(df_norm.values, aspect='auto', cmap=cmap,
                   vmin=0, vmax=df_norm.values.max())

    ax.set_xticks(range(len(df_norm.columns)))
    ax.set_xticklabels(df_norm.columns, rotation=35, ha='right', fontsize=7.5)
    ax.set_yticks(range(len(df_norm.index)))
    ax.set_yticklabels(df_norm.index, fontsize=8)

    # annotate cells
    for i in range(len(df_norm.index)):
        for j in range(len(df_norm.columns)):
            v = df_norm.values[i,j]
            if v > 1:
                tc = 'white' if v > df_norm.values.max()*0.65 else '#333'
                ax.text(j, i, f'{v:.0f}%', ha='center', va='center',
                        fontsize=6.5, color=tc, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax, pad=0.01, shrink=0.85)
    cbar.set_label('Row-normalised prevalence (%)', fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    ax.set_title('Row-normalised HFACS category prevalence by accident type',
                 pad=10, fontweight='bold')
    ax.tick_params(length=0)

    plt.tight_layout()
    plt.savefig(OUT + 'R004_type_factor_heatmap.png')
    plt.close()
    print("  saved R004")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 4  Event chain length  (left: histogram, right: mean by type)
# ─────────────────────────────────────────────────────────────────────────────
def fig_chains():
    ev_ev = led[(led['src_label']=='EventNode') & (led['dst_label']=='EventNode')]
    id2sf = ev.set_index('id')['source_file'].to_dict()

    chain = {}
    for _, row in ev_ev.iterrows():
        sf = id2sf.get(row['src'])
        if sf:
            chain[sf] = chain.get(sf, 0) + 1

    acc2 = acc.copy()
    acc2['chain'] = acc2['source_file'].map(chain).fillna(0)

    by_type = (acc2.groupby('accident_type')['chain']
               .agg(['mean','count'])
               .query('count >= 10')
               .sort_values('mean', ascending=True))

    fig = plt.figure(figsize=(10, 4))
    gs  = gridspec.GridSpec(1, 2, width_ratios=[1,1.3], wspace=0.35)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    # Left: histogram
    chain_vals = acc2['chain'].values
    bins = np.arange(0, min(chain_vals.max()+2, 22)) - 0.5
    ax1.hist(chain_vals[chain_vals < 21], bins=bins,
             color=PALETTE['blue'], edgecolor='white', linewidth=0.4)
    ax1.set_xlabel('Event chain length (edges)', labelpad=5)
    ax1.set_ylabel('Number of accident reports', labelpad=5)
    ax1.set_title('Distribution of event\nchain lengths', fontweight='bold')
    ax1.grid(axis='y', lw=0.3, color='#ddd', zorder=0)

    med = np.median(chain_vals)
    ax1.axvline(med, color=PALETTE['orange'], lw=1.5, ls='--', label=f'Median = {med:.0f}')
    ax1.legend(fontsize=7.5, frameon=False)
    ax1.text(0.98, 0.97, f'n = {(chain_vals >= 21).sum()} reports\nhave chains > 20',
             transform=ax1.transAxes, ha='right', va='top', fontsize=6.5,
             color='#666', style='italic')

    # Right: mean chain by type
    colors2 = [PALETTE['blue'] if v < by_type['mean'].quantile(0.6)
                else PALETTE['orange'] for v in by_type['mean']]
    ax2.barh(by_type.index, by_type['mean'], color=colors2,
             edgecolor='white', linewidth=0.4, height=0.65)
    for i, (idx, row) in enumerate(by_type.iterrows()):
        ax2.text(row['mean'] + 0.03, i,
                 f"{row['mean']:.2f}  (n={int(row['count'])})",
                 va='center', fontsize=7, color='#333')
    ax2.set_xlabel('Mean event chain length', labelpad=5)
    ax2.set_title('Mean chain length by accident type\n(≥10 reports)', fontweight='bold')
    ax2.set_xlim(0, by_type['mean'].max() * 1.45)
    ax2.tick_params(axis='y', length=0)
    ax2.grid(axis='x', lw=0.3, color='#ddd', zorder=0)

    plt.savefig(OUT + 'R005_chain_length_dist.png')
    plt.close()
    print("  saved R005")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 5  Causal roles  (left: chain initiators, right: direct causes)
# ─────────────────────────────────────────────────────────────────────────────
def fig_causal_roles():
    hf_ids  = set(hf['id'])
    ev_ids  = set(ev['id'])
    id2cat  = hf.set_index('id')['category'].to_dict()

    # Chain initiators: HFACS -> EventNode
    init = led[(led['src_label']=='HFACS_Factor') & (led['dst_label']=='EventNode')]
    init_cats = [id2cat.get(i,'') for i in init['src']]
    init_counts = (pd.Series(init_cats)
                   .replace({'Other / Unclassified': None})
                   .dropna().value_counts().head(10))

    # Direct causes: HFACS -> Accident
    direct = led[(led['src_label']=='HFACS_Factor') & (led['dst_label']=='Accident')]
    dir_cats = [id2cat.get(i,'') for i in direct['src']]
    dir_counts = (pd.Series(dir_cats)
                  .replace({'Other / Unclassified': None})
                  .dropna().value_counts().head(10))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    def hbar(ax, data, color, title, xlabel):
        data_s = data.sort_values()
        bars = ax.barh(data_s.index, data_s.values, color=color,
                       edgecolor='white', linewidth=0.4, height=0.65)
        for bar, v in zip(bars, data_s.values):
            ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2,
                    str(v), va='center', fontsize=7.5, color='#333')
        ax.set_xlabel(xlabel, labelpad=5)
        ax.set_title(title, fontweight='bold', pad=8)
        ax.set_xlim(0, data_s.max() * 1.22)
        ax.tick_params(axis='y', length=0)
        ax.grid(axis='x', lw=0.3, color='#ddd', zorder=0)

    hbar(ax1, init_counts, PALETTE['blue'],
         'Top HFACS categories:\nEvent chain initiators',
         'HFACS→EventNode edges (LED_TO)')
    hbar(ax2, dir_counts, PALETTE['orange'],
         'Top HFACS categories:\nDirect accident causes',
         'HFACS→Accident edges (LED_TO)')

    plt.suptitle('Causal roles of HFACS categories', fontsize=11,
                 fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(OUT + 'R006_causal_roles.png')
    plt.close()
    print("  saved R006_causal_roles")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 6  Top 20 two-hop causal paths
# ─────────────────────────────────────────────────────────────────────────────
def fig_causal_paths():
    id2cat  = hf.set_index('id')['category'].to_dict()
    id2acc  = acc.set_index('id')['accident_type'].to_dict()
    id2ev_n = ev.set_index('id')['name'].to_dict()

    # HFACS → EventNode
    h2e = led[(led['src_label']=='HFACS_Factor') & (led['dst_label']=='EventNode')]
    # EventNode → Accident
    e2a = led[(led['src_label']=='EventNode')    & (led['dst_label']=='Accident')]

    ev2acc = e2a.set_index('src')['dst'].to_dict()
    paths  = []
    for _, row in h2e.iterrows():
        cat  = id2cat.get(row['src'], '')
        if cat == 'Other / Unclassified' or not cat: continue
        atype = id2acc.get(ev2acc.get(row['dst'], ''), '')
        if atype:
            paths.append(f"{cat}\n→ {atype}")

    path_counts = pd.Series(paths).value_counts().head(20).sort_values()

    # Color by category (first token before \n→)
    unique_cats = list({p.split('\n→')[0] for p in path_counts.index})
    cat_color = {c: CAT_COLORS[i % len(CAT_COLORS)]
                 for i, c in enumerate(unique_cats)}
    bar_colors = [cat_color[p.split('\n→')[0]] for p in path_counts.index]

    fig, ax = plt.subplots(figsize=(9, 7.5))
    bars = ax.barh(range(len(path_counts)), path_counts.values,
                   color=bar_colors, edgecolor='white', linewidth=0.3, height=0.72)
    ax.set_yticks(range(len(path_counts)))
    ax.set_yticklabels(path_counts.index, fontsize=7)
    for bar, v in zip(bars, path_counts.values):
        ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height()/2,
                str(v), va='center', fontsize=7.5, color='#333')

    ax.set_xlabel('Number of two-hop paths\n(HFACS category → EventNode → Accident type)',
                  labelpad=5)
    ax.set_title('Top 20 two-hop causal paths', fontweight='bold', pad=8)
    ax.set_xlim(0, path_counts.max() * 1.18)
    ax.tick_params(axis='y', length=0)
    ax.grid(axis='x', lw=0.3, color='#ddd', zorder=0)

    plt.tight_layout()
    plt.savefig(OUT + 'R006_top_causal_paths.png')
    plt.close()
    print("  saved R006_top_paths")

# ─────────────────────────────────────────────────────────────────────────────
# RUN ALL
# ─────────────────────────────────────────────────────────────────────────────
print("Generating publication-quality figures...")
fig_acc_dist()
fig_hfacs_dist()
fig_heatmap()
fig_chains()
fig_causal_roles()
fig_causal_paths()
print("Done. All 6 figures saved to paper/figures/")
