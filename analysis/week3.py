"""Week 3: six degrees of Spider-Man, and which removals break the network."""
import numpy as np
import networkx as nx

from common import *

G = marvel_graph()
U = G.to_undirected()
out = out_dir(3)
SPIDEY = "Spider-Man"

# --- Six degrees of Spider-Man (undirected and directed: who can *reach* him) -----
dist_u = nx.single_source_shortest_path_length(U, SPIDEY)
dist_to = nx.single_source_shortest_path_length(G.reverse(copy=False), SPIDEY)  # A -> ... -> Spider-Man
hist_u = np.bincount(list(dist_u.values()))
hist_to = np.bincount(list(dist_to.values()))
farthest = max(dist_to, key=dist_to.get)
far_chain = nx.shortest_path(G, farthest, SPIDEY)
far_u = max(dist_u, key=dist_u.get)
far_u_chain = nx.shortest_path(U, far_u, SPIDEY)
# giant-component nodes that cannot reach Spider-Man by following links forward
giant = max(nx.connected_components(U), key=len)
cant_reach = sorted(v for v in giant if v not in dist_to)

fig, ax = plt.subplots(figsize=(6.4, 3.4))
w = .38
d = np.arange(max(len(hist_u), len(hist_to)))
ax.bar(d[:len(hist_u)] - w / 2, hist_u, w, color=ACCENT2, label="ignore direction")
ax.bar(d[:len(hist_to)] + w / 2, hist_to, w, color=ACCENT, label="follow links to him")
ax.set_xlabel("steps to Spider-Man")
ax.set_ylabel("characters")
ax.set_xticks(d)
ax.legend(frameon=False)
ax.set_title("How far is every character from Spider-Man?")
fig.savefig(out / "spidey_distance.png")
plt.close(fig)

# --- Attack: remove nodes in order of a measure, track giant component ----------
def giant_curve(order, steps=120):
    H = U.copy()
    sizes = [len(max(nx.connected_components(H), key=len)) / U.number_of_nodes()]
    for v in order[:steps]:
        H.remove_node(v)
        sizes.append(len(max(nx.connected_components(H), key=len)) / U.number_of_nodes())
    return sizes


def adaptive(measure, steps=120):
    """Recompute the measure after every removal."""
    H = U.copy()
    sizes = [len(max(nx.connected_components(H), key=len)) / U.number_of_nodes()]
    removed = []
    for _ in range(steps):
        scores = measure(H)
        v = max(scores, key=scores.get)
        removed.append(v)
        H.remove_node(v)
        sizes.append(len(max(nx.connected_components(H), key=len)) / U.number_of_nodes())
    return sizes, removed


deg = dict(U.degree())
btw = nx.betweenness_centrality(U)
pr = nx.pagerank(G)
orders = {
    "degree": sorted(U, key=deg.get, reverse=True),
    "betweenness": sorted(U, key=btw.get, reverse=True),
    "PageRank (directed)": sorted(U, key=pr.get, reverse=True),
}
curves = {k: giant_curve(v) for k, v in orders.items()}
curves["betweenness, recomputed"], adaptive_removed = adaptive(nx.betweenness_centrality)
rng = np.random.default_rng(3)
rand = np.array([giant_curve(list(rng.permutation(list(U)))) for _ in range(30)])

fig, ax = plt.subplots(figsize=(7, 4.2))
x = np.arange(len(rand[0]))
ax.fill_between(x, rand.min(0), rand.max(0), color=MUTED, alpha=.25, lw=0, label="random (30 runs)")
styles = {"degree": ACCENT2, "betweenness": ACCENT3, "PageRank (directed)": "#6b4fa0",
          "betweenness, recomputed": ACCENT}
for k, c in styles.items():
    ax.plot(x, curves[k], color=c, lw=2 if "recomputed" in k else 1.4, label=k)
ax.set_xlabel("characters removed")
ax.set_ylabel("giant component (share of 303)")
ax.set_title("Taking the Marvel universe apart")
ax.legend(frameon=False, fontsize=8)
fig.savefig(out / "attack.png")
plt.close(fig)


def first_below(curve, frac=.5):
    return next((i for i, s in enumerate(curve) if s < frac), None)


# --- Direction: the biggest gaps between in-rank and out-rank --------------------
pr_rev = nx.pagerank(G.reverse(copy=False))  # "hub-like": points to important pages

save_results(3, {
    "spidey_mean_dist_undirected": round(float(np.mean([v for k, v in dist_u.items() if k != SPIDEY])), 2),
    "spidey_mean_dist_directed": round(float(np.mean([v for k, v in dist_to.items() if k != SPIDEY])), 2),
    "hist_undirected": hist_u.tolist(),
    "hist_directed": hist_to.tolist(),
    "reach_spidey_directed": len(dist_to) - 1,
    "giant_cant_reach_spidey": [pretty(v) for v in cant_reach],
    "farthest_directed_chain": [pretty(v) for v in far_chain],
    "farthest_undirected_chain": [pretty(v) for v in far_u_chain],
    "top_betweenness": [(pretty(v), round(btw[v], 3)) for v in orders["betweenness"][:8]],
    "top_degree": [(pretty(v), deg[v]) for v in orders["degree"][:8]],
    "top_pagerank": [(pretty(v), round(pr[v], 4)) for v in orders["PageRank (directed)"][:8]],
    "removals_to_halve_giant": {k: first_below(c) for k, c in curves.items()},
    "removals_to_halve_giant_random_median": int(np.median([first_below(c) or 999 for c in rand])),
    "adaptive_first_10": [pretty(v) for v in adaptive_removed[:10]],
    "giant_after_20": {k: round(c[20], 3) for k, c in curves.items()},
    "giant_after_20_random_mean": round(float(rand[:, 20].mean()), 3),
})
