"""Week 6: textually close, structurally far — and how much of it is just names."""
import re

import numpy as np
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from common import *

G = marvel_graph()
U = G.to_undirected()
pages = marvel_pages()
nodes = marvel_nodes().set_index("node_id")
out = out_dir(6)
V = sorted(G)
docs = [pages[v] for v in V]

# --- Name tokens: words from page titles + real names in the blurbs "(Emil Blonsky)" ---
name_tokens = set()
for v in V:
    name_tokens |= set(re.findall(r"[a-z]+", v.lower().replace("_", " ")))
    m = re.search(r"\(([^)]+)\)", str(nodes.loc[v, "description"]))
    if m:
        name_tokens |= set(re.findall(r"[a-z]+", m.group(1).lower()))
GENERIC = {"man", "woman", "captain", "the", "of", "and", "character", "comics", "marvel",
           "black", "white", "red", "blue", "doctor", "iron", "girl", "boy", "lady", "king",
           "american", "agent", "kid", "mister", "miss", "ms", "mr", "super", "night", "star",
           "dark", "human", "power", "golden", "silver", "new", "first", "big", "war", "dog"}
name_tokens -= GENERIC


def tfidf(stop):
    vec = TfidfVectorizer(stop_words=stop, sublinear_tf=True, min_df=2, max_df=.5,
                          token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z'-]+\b", lowercase=True)
    X = vec.fit_transform(docs)
    return vec, X, cosine_similarity(X)


from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
vec_a, X_a, S_a = tfidf(list(ENGLISH_STOP_WORDS))
vec_b, X_b, S_b = tfidf(list(ENGLISH_STOP_WORDS | name_tokens))

dist = dict(nx.all_pairs_shortest_path_length(U))
INF = 99
iu = np.triu_indices(len(V), 1)
D = np.array([dist[V[i]].get(V[j], INF) for i, j in zip(*iu)])


def by_distance(S):
    vals = S[iu]
    return {d: vals[D == d] for d in [1, 2, 3, 4, INF] if (D == d).any()}


bd_a, bd_b = by_distance(S_a), by_distance(S_b)

fig, ax = plt.subplots(figsize=(7, 3.8))
keys = list(bd_a)
pos = np.arange(len(keys))
for off, bd, c, lab in [(-.18, bd_a, ACCENT, "all words"), (.18, bd_b, ACCENT2, "names removed")]:
    bp = ax.boxplot([bd[k] for k in keys], positions=pos + off, widths=.32, showfliers=False,
                    patch_artist=True, medianprops={"color": "white"})
    for b in bp["boxes"]:
        b.set_facecolor(c); b.set_edgecolor(c)
    ax.plot([], [], color=c, lw=6, label=lab)
ax.set_xticks(pos, [str(k) if k != INF else "no path" for k in keys])
ax.set_xlabel("network distance between the two characters")
ax.set_ylabel("TF-IDF cosine similarity")
ax.set_title("Text similarity fades with network distance, and names carry a lot of it")
ax.legend(frameon=False)
fig.savefig(out / "cosine_by_distance.png")
plt.close(fig)


def top_far(S, min_d=3, k=12):
    cand = [(S[i, j], V[i], V[j], D[n]) for n, (i, j) in enumerate(zip(*iu)) if D[n] >= min_d]
    return sorted(cand, reverse=True)[:k]


def shared_terms(vec, X, a, b, k=6):
    ia, ib = V.index(a), V.index(b)
    prod = X[ia].multiply(X[ib]).toarray().ravel()
    terms = vec.get_feature_names_out()
    return [terms[t] for t in prod.argsort()[::-1][:k] if prod[t] > 0]


far_a = top_far(S_a)
far_b = top_far(S_b)

# Name-driven vs story-driven: how much does the similarity drop when names go?
name_driven = []
for n, (i, j) in enumerate(zip(*iu)):
    if S_a[i, j] > .25:
        name_driven.append((S_a[i, j] - S_b[i, j], S_a[i, j], S_b[i, j], V[i], V[j], D[n]))
name_driven.sort(reverse=True)

# --- Figure 2: the scatter of with-names vs without-names similarity ----------------
fig, ax = plt.subplots(figsize=(6, 5))
sa, sb = S_a[iu], S_b[iu]
ax.scatter(sa, sb, s=3, color=MUTED, alpha=.25, lw=0)
ax.plot([0, .8], [0, .8], ls="--", color=MUTED, lw=1)
for drop, a_, b_, x, y, d in name_driven[:5]:
    ax.scatter(a_, b_, s=22, color=ACCENT, zorder=3)
    if pretty(x) in ("Scaredycat", "Nomad", "Guardian"):
        ax.annotate(f"{pretty(x)} / {pretty(y)}".replace(" (Morituri)", ""), (a_, b_), fontsize=7,
                    color=ACCENT, xytext=(5, -3), textcoords="offset points")
for s, x, y, d in far_b[:2]:
    i, j = V.index(x), V.index(y)
    ax.scatter(S_a[i, j], S_b[i, j], s=22, color=ACCENT2, zorder=3)
    ax.annotate(f"{pretty(x)} / {pretty(y)}", (S_a[i, j], S_b[i, j]), fontsize=7, color=ACCENT2,
                xytext=(-70, 8 if "Blue" in x else 14), textcoords="offset points")
ax.set_xlabel("cosine, all words")
ax.set_ylabel("cosine, character names removed")
ax.set_title("Below the diagonal = similarity that was only names")
fig.savefig(out / "names_vs_story.png")
plt.close(fig)

save_results(6, {
    "vocab": [len(vec_a.vocabulary_), len(vec_b.vocabulary_)],
    "name_tokens_removed": len(name_tokens),
    "median_cos_by_dist_all": {str(k): round(float(np.median(v)), 3) for k, v in bd_a.items()},
    "median_cos_by_dist_noname": {str(k): round(float(np.median(v)), 3) for k, v in bd_b.items()},
    "pairs_by_dist": {str(k): int(len(v)) for k, v in bd_a.items()},
    "far_close_all_words": [(pretty(a), pretty(b), "no path" if d == INF else d, round(s, 3),
                             shared_terms(vec_a, X_a, a, b)) for s, a, b, d in far_a],
    "far_close_no_names": [(pretty(a), pretty(b), "no path" if d == INF else d, round(s, 3),
                            shared_terms(vec_b, X_b, a, b)) for s, a, b, d in far_b],
    "most_name_driven": [(pretty(x), pretty(y), round(a_, 3), round(b_, 3), "no path" if d == INF else d,
                          shared_terms(vec_a, X_a, x, y, 4))
                         for _, a_, b_, x, y, d in name_driven[:10]],
})
