"""Week 1: who gets linked to, who links out, and who is left out."""
import collections

import numpy as np
import networkx as nx

from common import *

G = marvel_graph()
U = G.to_undirected()
out = out_dir(1)

indeg = dict(G.in_degree())
outdeg = dict(G.out_degree())
n, m = G.number_of_nodes(), G.number_of_edges()

# --- Figure 1: in vs out degree distributions on log-log (k+1) -------------
fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
for ax, (label, deg, color) in zip(axes, [("In-degree", indeg, ACCENT), ("Out-degree", outdeg, ACCENT2)]):
    counts = collections.Counter(deg.values())
    ks = np.array(sorted(counts))
    pk = np.array([counts[k] for k in ks]) / n
    ax.loglog(ks + 1, pk, "o", color=color, ms=5, alpha=.85)
    ax.set_title(f"{label} (max {max(deg.values())})")
    ax.set_xlabel("k + 1 (shifted so isolates show)")
    ax.set_xlim(.8, 150)
axes[0].set_ylabel("P(k)")
fig.suptitle("Being linked has no ceiling; linking out does", fontweight="bold", y=1.02)
fig.savefig(out / "degree_distributions.png")
plt.close(fig)

# --- Figure 2: in vs out scatter ---------------------------------------------
fig, ax = plt.subplots(figsize=(7, 5.2))
xs = np.array([outdeg[v] for v in G])
ys = np.array([indeg[v] for v in G])
jit = np.random.default_rng(1).uniform(-.25, .25, size=(2, n))
ax.scatter(xs + jit[0], ys + jit[1], s=14, color=MUTED, alpha=.6, lw=0)
ax.plot([0, 30], [0, 30], ls="--", color=MUTED, lw=1)
ax.text(27, 30, "in = out", color=MUTED, fontsize=8, ha="right")
gap = sorted(G, key=lambda v: indeg[v] - outdeg[v])
label_these = set(gap[-7:]) | set(gap[:5])
NUDGE = {"Hank Pym": (-44, -12), "Luke Cage": (5, 4), "U.S. Agent": (-18, 9), "Noh-Varr": (-10, -13),
         "Adam Warlock": (-20, 9), "Betsy Braddock": (-30, 9), "Cloak and Dagger (characters)": (-60, 9)}
for v in label_these:
    c = ACCENT if indeg[v] > outdeg[v] else ACCENT2
    ax.scatter(outdeg[v], indeg[v], s=30, color=c, zorder=3)
    ax.annotate(pretty(v).replace(" (characters)", ""), (outdeg[v], indeg[v]),
                xytext=NUDGE.get(pretty(v), (4, 3)), textcoords="offset points", fontsize=8, color=c)
ax.set_xlabel("out-degree (links this page writes)")
ax.set_ylabel("in-degree (links other pages give it)")
ax.set_title("Famous vs. chatty: in- against out-degree for all 303 characters")
fig.savefig(out / "in_vs_out.png")
plt.close(fig)

# --- Components: giant, islands, isolates -----------------------------------
comps = sorted(nx.connected_components(U), key=len, reverse=True)
giant = comps[0]
islands = [c for c in comps[1:] if len(c) > 1]
isolates = [next(iter(c)) for c in comps if len(c) == 1]

# --- Figure 3: the network, giant component + island highlighted -------------
# Lay out the giant component on its own, then park the island and the isolates beside it,
# so 17 lonely dots do not squeeze the interesting part into the middle of the canvas.
Ug = U.subgraph(giant)
pos = nx.spring_layout(Ug, seed=7, k=.35, iterations=300)
xs_, ys_ = np.array([p[0] for p in pos.values()]), np.array([p[1] for p in pos.values()])
right, top, bottom = xs_.max(), ys_.max(), ys_.min()
for c in islands:
    sub = nx.spring_layout(U.subgraph(c), seed=1, scale=.12)
    pos.update({v: (right + .3 + p[0], top - .15 + p[1]) for v, p in sub.items()})
for i, v in enumerate(sorted(isolates)):
    pos[v] = (right + .12 + .08 * (i % 5), bottom + .1 + .09 * (i // 5))
fig, ax = plt.subplots(figsize=(9, 7))
nx.draw_networkx_edges(U, pos, ax=ax, edge_color="#c9ced6", width=.35, alpha=.7)
sizes = [8 + 2.2 * indeg[v] for v in U]
colors = [ACCENT2 if v in giant else (ACCENT3 if any(v in c for c in islands) else INK) for v in U]
nx.draw_networkx_nodes(U, pos, ax=ax, node_size=sizes, node_color=colors, linewidths=0, alpha=.9)
for v in sorted(G, key=indeg.get, reverse=True)[:6]:
    ax.annotate(pretty(v), pos[v], fontsize=8, fontweight="bold", color=INK,
                xytext=(5, 5), textcoords="offset points")
ax.text(right + .3, top + .02, "the island:\nStrikeforce: Morituri", fontsize=8, color=ACCENT3,
        fontweight="bold", ha="center")
ax.text(right + .28, bottom + .1 + .09 * 3.6, "17 isolates", fontsize=8, color=INK,
        fontweight="bold", ha="center")
ax.set_title("The Marvel network: giant component (blue), the island (gold), isolates (black)")
ax.axis("off")
fig.savefig(out / "network.png")
plt.close(fig)

nodes = marvel_nodes().set_index("node_id")
save_results(1, {
    "n": n, "m_directed": m, "m_undirected": U.number_of_edges(),
    "reciprocal_pairs": m - U.number_of_edges(),
    "avg_k_undirected": round(2 * U.number_of_edges() / n, 2),
    "density": round(nx.density(U), 4),
    "top_in": [(pretty(v), indeg[v]) for v in sorted(G, key=indeg.get, reverse=True)[:8]],
    "top_out": [(pretty(v), outdeg[v]) for v in sorted(G, key=outdeg.get, reverse=True)[:8]],
    "most_linked_vs_linking": [(pretty(v), indeg[v], outdeg[v]) for v in gap[-7:][::-1]],
    "most_linking_vs_linked": [(pretty(v), indeg[v], outdeg[v]) for v in gap[:5]],
    "zero_in_count": sum(1 for v in G if indeg[v] == 0),
    "zero_in_positive_out": sum(1 for v in G if indeg[v] == 0 and outdeg[v] > 0),
    "giant_size": len(giant),
    "islands": [sorted(pretty(v) for v in c) for c in islands],
    "island_blurbs": {pretty(v): nodes.loc[v, "description"] for c in islands for v in c},
    "isolates": sorted(pretty(v) for v in isolates),
    "spider_share_of_nodes_linking": round(indeg["Spider-Man"] / n, 3) if "Spider-Man" in G else None,
    "corr_in_out": round(float(np.corrcoef(xs, ys)[0, 1]), 3),
})
