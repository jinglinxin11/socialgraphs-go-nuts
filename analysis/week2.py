"""Week 2: what survives a degree-preserving shuffle, and the friendship paradox."""
import numpy as np
import networkx as nx

from common import *

G = marvel_graph()
U = G.to_undirected()
out = out_dir(2)
rng = np.random.default_rng(2)


def stats(D):
    Ud = D.to_undirected()
    return {
        "reciprocity": nx.reciprocity(D),
        "triangles": sum(nx.triangles(Ud).values()) // 3,
        "transitivity": nx.transitivity(Ud),
        "in_in_assortativity": nx.degree_assortativity_coefficient(D, x="in", y="in"),
        "giant_share": len(max(nx.weakly_connected_components(D), key=len)) / D.number_of_nodes(),
    }


real = stats(G)
N_SHUFFLES = 200
null = {k: [] for k in real}
for i in range(N_SHUFFLES):
    H = G.copy()
    # keep every node's in- and out-degree; ~10 swaps per edge
    nx.directed_edge_swap(H, nswap=10 * H.number_of_edges(), max_tries=10**7, seed=int(rng.integers(1e9)))
    for k, v in stats(H).items():
        null[k].append(v)

LABELS = {
    "reciprocity": "Reciprocity",
    "triangles": "Triangles",
    "transitivity": "Transitivity",
    "in_in_assortativity": "In–in assortativity",
    "giant_share": "Giant component share",
}

summary = {}
fig, axes = plt.subplots(1, 5, figsize=(14, 2.9))
for ax, k in zip(axes, real):
    vals = np.array(null[k])
    z = (real[k] - vals.mean()) / vals.std() if vals.std() > 0 else float("nan")
    summary[k] = {"real": round(real[k], 4), "null_mean": round(vals.mean(), 4),
                  "null_sd": round(vals.std(), 4), "z": round(z, 1),
                  "p_ge": float((vals >= real[k]).mean())}
    ax.hist(vals, bins=25, color=MUTED, alpha=.8)
    ax.axvline(real[k], color=ACCENT, lw=2)
    ax.set_title(LABELS[k])
    ax.set_yticks([])
    note = f"z = {z:.1f}" if vals.std() > 0 else f"identical in all {N_SHUFFLES}"
    ax.text(.98, .95, note, transform=ax.transAxes, ha="right", va="top",
            color=ACCENT, fontweight="bold", fontsize=9)
    if vals.std() == 0:
        ax.set_xlim(real[k] - .05, real[k] + .05)
fig.suptitle(f"Real Marvel network (red) vs {N_SHUFFLES} degree-preserving shuffles (grey)",
             fontweight="bold", y=1.04)
fig.savefig(out / "shuffle_test.png")
plt.close(fig)

# --- Friendship paradox (undirected, giant component) ----------------------------
deg = dict(U.degree())
nodes_with_friends = [v for v in U if deg[v] > 0]
mean_nbr = {v: np.mean([deg[u] for u in U[v]]) for v in nodes_with_friends}
paradox_share = np.mean([mean_nbr[v] > deg[v] for v in nodes_with_friends])
mean_k = np.mean([deg[v] for v in nodes_with_friends])
mean_nbr_k = np.mean([deg[u] for v in nodes_with_friends for u in U[v]])  # <k^2>/<k>
# who is more popular than every single neighbour?
local_kings = [v for v in nodes_with_friends if all(deg[v] > deg[u] for u in U[v])]
# who are the "popular friends": count how often a node is someone's most popular friend
top_friend = {}
for v in nodes_with_friends:
    u = max(U[v], key=deg.get)
    top_friend[u] = top_friend.get(u, 0) + 1

fig, ax = plt.subplots(figsize=(6.4, 5))
xs = np.array([deg[v] for v in nodes_with_friends])
ys = np.array([mean_nbr[v] for v in nodes_with_friends])
above = ys > xs
ax.scatter(xs[above], ys[above], s=14, color=ACCENT, alpha=.6, lw=0,
           label=f"friends more popular ({above.sum()})")
ax.scatter(xs[~above], ys[~above], s=14, color=ACCENT2, alpha=.8, lw=0,
           label=f"you are the popular one ({(~above).sum()})")
lim = max(xs.max(), ys.max()) * 1.15
ax.plot([.8, lim], [.8, lim], ls="--", color=MUTED, lw=1)
ax.set_xscale("log"); ax.set_yscale("log")
for v in local_kings[:8]:
    ax.annotate(pretty(v), (deg[v], mean_nbr[v]), fontsize=7.5, color=ACCENT2,
                xytext=(3, -9), textcoords="offset points")
ax.set_xlabel("your degree k (undirected)")
ax.set_ylabel("mean degree of your neighbours")
ax.set_title("The friendship paradox among superheroes")
ax.legend(frameon=False, fontsize=8, loc="upper right")
fig.savefig(out / "friendship_paradox.png")
plt.close(fig)

save_results(2, {
    "shuffle": summary,
    "n_shuffles": N_SHUFFLES,
    "undirected_edges_real": U.number_of_edges(),
    "paradox_share": round(float(paradox_share), 3),
    "n_with_friends": len(nodes_with_friends),
    "mean_k": round(float(mean_k), 2),
    "mean_k_of_neighbour": round(float(mean_nbr_k), 2),
    "local_kings": sorted([(pretty(v), deg[v]) for v in local_kings], key=lambda x: -x[1]),
    "popular_friends": sorted([(pretty(u), c) for u, c in top_friend.items()], key=lambda x: -x[1])[:6],
})
