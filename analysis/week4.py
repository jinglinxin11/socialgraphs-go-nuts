"""Week 4: do weights change the communities of philosophy?"""
import numpy as np
import networkx as nx
from sklearn.metrics import normalized_mutual_info_score as nmi

from common import *

nodes, G = philosophers()
out = out_dir(4)
giant = G.subgraph(max(nx.connected_components(G), key=len)).copy()
V = sorted(giant)
era = nodes.set_index("node_id")["era"]
ERAS = ["centuries BC", "1st through 10th centuries", "11th through 14th centuries",
        "15th and 16th centuries", "17th century", "18th century", "19th century"]
ERA_SHORT = ["BC", "1–10th", "11–14th", "15–16th", "17th", "18th", "19th"]

SEEDS = range(10)


def labels(partition):
    lab = {}
    for i, c in enumerate(partition):
        for v in c:
            lab[v] = i
    return [lab[v] for v in V]


runs = {"unweighted": [], "weighted": []}
parts = {"unweighted": [], "weighted": []}
for s in SEEDS:
    for key, w in [("unweighted", None), ("weighted", "weight")]:
        p = nx.community.louvain_communities(giant, weight=w, seed=s)
        parts[key].append(p)
        runs[key].append(labels(p))

Q = {key: [nx.community.modularity(giant, p, weight=("weight" if key == "weighted" else None))
           for p in parts[key]] for key in parts}


def mean_nmi(a, b, same=False):
    vals = [nmi(x, y) for i, x in enumerate(a) for j, y in enumerate(b) if not (same and i >= j)]
    return float(np.mean(vals))


stab_u = mean_nmi(runs["unweighted"], runs["unweighted"], same=True)
stab_w = mean_nmi(runs["weighted"], runs["weighted"], same=True)
cross = mean_nmi(runs["unweighted"], runs["weighted"])
era_lab = [ERAS.index(era[v]) for v in V]
nmi_era_u = float(np.mean([nmi(era_lab, r) for r in runs["unweighted"]]))
nmi_era_w = float(np.mean([nmi(era_lab, r) for r in runs["weighted"]]))

# null: Louvain on a degree-preserving shuffle (does Q mean anything?)
H = nx.configuration_model([d for _, d in giant.degree()], seed=4)
H = nx.Graph(H); H.remove_edges_from(nx.selfloop_edges(H))
Q_null = nx.community.modularity(H, nx.community.louvain_communities(H, seed=0))

# --- Figure 1: era composition of the weighted communities -------------------
best_w = max(parts["weighted"], key=lambda p: nx.community.modularity(giant, p, weight="weight"))
best_u = max(parts["unweighted"], key=lambda p: nx.community.modularity(giant, p))
big = sorted(best_w, key=len, reverse=True)[:10]
deg = dict(giant.degree(weight="weight"))
M = np.array([[sum(era[v] == e for v in c) / len(c) for e in ERAS] for c in big])
names = [", ".join(n.split(",")[0].replace("_", " ") for n in sorted(c, key=deg.get, reverse=True)[:3])
         for c in big]
fig, ax = plt.subplots(figsize=(8.5, 5.2))
ax.imshow(M, cmap="Reds", aspect="auto", vmin=0, vmax=1)
ax.set_xticks(range(len(ERAS)), ERA_SHORT)
ax.set_yticks(range(len(big)), [f"{nm}  (n={len(c)})" for nm, c in zip(names, big)], fontsize=8)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        if M[i, j] >= .1:
            ax.text(j, i, f"{M[i, j]:.0%}", ha="center", va="center", fontsize=7,
                    color="white" if M[i, j] > .55 else INK)
ax.set_title("Ten largest weighted-Louvain communities, by era (row = 100%)")
ax.spines[:].set_visible(False)
fig.savefig(out / "era_heatmap.png")
plt.close(fig)

# --- Who moves when weights are switched on? ----------------------------------
def mates(partition):
    m = {}
    for c in partition:
        for v in c:
            m[v] = c
    return m


mu, mw = mates(best_u), mates(best_w)
jac = {v: len(mu[v] & mw[v]) / len(mu[v] | mw[v]) for v in V}
famous = sorted(V, key=lambda v: giant.degree(v), reverse=True)[:150]

# A move only counts if it is not seed noise: the philosopher must keep the same
# community-mates across seeds *within* each version, and lose them *across* versions.
all_u = [mates(p) for p in parts["unweighted"]]
all_w = [mates(p) for p in parts["weighted"]]


def j(a, b):
    return len(a & b) / len(a | b)


def within(ms, v):
    return np.mean([j(ms[a][v], ms[b][v]) for a in range(len(ms)) for b in range(a + 1, len(ms))])


stable = {v: min(within(all_u, v), within(all_w, v)) for v in famous}
across = {v: np.mean([j(a[v], b[v]) for a in all_u for b in all_w]) for v in famous}
jac = {v: across[v] for v in famous} | {v: jac[v] for v in V if v not in across}

# Consensus view: P(two philosophers share a community) over the 10 seeds, per version.
# The pairs whose probability flips are changes caused by the weights, not by the seed.
idx = {v: i for i, v in enumerate(famous)}


def coassign(ms):
    P = np.zeros((len(famous), len(famous)))
    for m in ms:
        for v in famous:
            for w in m[v]:
                if w in idx:
                    P[idx[v], idx[w]] += 1
    return P / len(ms)


Pu, Pw = coassign(all_u), coassign(all_w)
D = Pw - Pu
pairs = [(famous[a], famous[b], Pu[a, b], Pw[a, b]) for a in range(len(famous))
         for b in range(a + 1, len(famous))]
flips = sorted(pairs, key=lambda p: -abs(p[3] - p[2]))
flipped_pairs = [p for p in pairs if abs(p[3] - p[2]) >= .7]
move_score = {v: np.abs(D[idx[v]]).sum() for v in famous}
movers = sorted(famous, key=move_score.get, reverse=True)[:10]


def top_mates(v, part, k=4):
    return [n.replace("_", " ") for n in sorted(part[v] - {v}, key=deg.get, reverse=True)[:k]]


# --- Figure 2: stability vs cross-weighting NMI --------------------------------
fig, ax = plt.subplots(figsize=(6, 3))
bars = [("unweighted vs itself\n(10 seeds)", stab_u), ("weighted vs itself\n(10 seeds)", stab_w),
        ("unweighted vs weighted", cross), ("weighted vs era", nmi_era_w)]
ax.barh([b[0] for b in bars][::-1], [b[1] for b in bars][::-1],
        color=[MUTED, ACCENT2, ACCENT, ACCENT][::-1])
for i, (_, v) in enumerate(bars[::-1]):
    ax.text(v + .01, i, f"{v:.2f}", va="center", fontsize=9)
ax.set_xlim(0, 1)
ax.set_xlabel("NMI")
ax.set_title("How much do partitions agree?")
fig.savefig(out / "nmi.png")
plt.close(fig)

save_results(4, {
    "giant": [giant.number_of_nodes(), giant.number_of_edges()],
    "n_comms": {k: [len(p) for p in parts[k]] for k in parts},
    "Q": {k: [round(min(v), 3), round(max(v), 3)] for k, v in Q.items()},
    "Q_null_unweighted": round(Q_null, 3),
    "stability_nmi_unweighted": round(stab_u, 3),
    "stability_nmi_weighted": round(stab_w, 3),
    "cross_nmi": round(cross, 3),
    "nmi_era_unweighted": round(nmi_era_u, 3),
    "nmi_era_weighted": round(nmi_era_w, 3),
    "big_communities": [{"top": nm, "size": len(c),
                         "main_era": ERA_SHORT[int(np.argmax(row))], "share": round(float(row.max()), 2)}
                        for nm, c, row in zip(names, big, M)],
    "stable_famous_share": round(float(np.mean([stable[v] >= .6 for v in famous])), 2),
    "n_pairs": len(pairs),
    "n_flipped_pairs_07": len(flipped_pairs),
    "top_flips": [(a.replace("_", " "), b.replace("_", " "), round(pu, 1), round(pw, 1)) for a, b, pu, pw in flips[:15]],
    "movers": [{"who": v.replace("_", " "), "score": round(float(move_score[v]), 1), "within": round(stable[v], 2),
                "unweighted_with": top_mates(v, mu), "weighted_with": top_mates(v, mw)} for v in movers],
    "aristotle": {"unweighted_with": top_mates("Aristotle", mu, 8), "weighted_with": top_mates("Aristotle", mw, 8),
                  "jaccard": round(jac["Aristotle"], 2)},
})
