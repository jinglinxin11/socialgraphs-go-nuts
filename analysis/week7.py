"""Week 7: can text build a useful network? Name mentions vs Wikipedia hyperlinks."""
import collections
import re

import numpy as np
import networkx as nx

from common import *

G = marvel_graph()
pages = marvel_pages()
nodes = marvel_nodes().set_index("node_id")
out = out_dir(7)
V = sorted(G)

# --- Aliases: the page title (minus disambiguators) and the real name in the blurb ---
corpus_lower = collections.Counter(w for t in pages.values() for w in re.findall(r"[a-z]+", t))


def common_word(alias):
    """A one-word alias that also shows up often in lower case is an English word (Storm, Nomad)."""
    return " " not in alias and corpus_lower[alias.lower()] >= 5


GENERIC_DISAMB = {"character", "comics", "marvel comics", "marvel comics character", "marvel"}
raw, canonical = {}, {}
for v in V:
    al = set()
    full = v.replace("_", " ")
    base = re.sub(r"\s*\(.*?\)", "", full).strip()
    d = re.search(r"\(([^)]+)\)$", full)
    disamb = d.group(1) if d else None
    canonical[v] = disamb is None or disamb.lower() in GENERIC_DISAMB
    if canonical[v]:
        al.add(base)
    elif len(disamb.split()) >= 2 and all(w[0].isupper() for w in disamb.split()) and not re.search(
            r"Marvel|Ultimate|film|series|Mangaverse|universe|New Universe|Earth", disamb):
        al.add(disamb)                       # Hawkeye (Kate Bishop) -> "Kate Bishop"
    m = re.search(r"\(([^)]+)\)", str(nodes.loc[v, "description"]))
    if m and len(m.group(1).split()) >= 2:
        al.add(m.group(1).strip())           # real name from the blurb
    raw[v] = {a for a in al if len(a) > 3 and not common_word(a)}

# An alias claimed by several pages is ambiguous and is dropped.
owners = collections.defaultdict(list)
for v, al in raw.items():
    for a in al:
        owners[a].append(v)
aliases = {v: set() for v in V}
collisions = {}
for a, vs in owners.items():
    if len(vs) == 1:
        aliases[vs[0]].add(a)
    else:
        collisions[a] = [pretty(v) for v in vs]   # ambiguous: belongs to nobody

dropped = sorted(pretty(v) for v in V if not aliases[v])
# (?<![\w-]) rather than \b, so that "Hulk" does not match inside "She-Hulk"
patterns = {v: re.compile(r"(?<![\w-])(" + "|".join(re.escape(a) for a in sorted(aliases[v], key=len, reverse=True)) + r")(?![\w-])")
            for v in V if aliases[v]}

T = nx.DiGraph()
T.add_nodes_from(V)
mention_count = collections.Counter()
for a in V:
    text = pages[a]
    for b, pat in patterns.items():
        if a == b:
            continue
        k = len(pat.findall(text))
        if k:
            T.add_edge(a, b, weight=k)
            mention_count[(a, b)] = k

L = set(G.edges())
M = set(T.edges())
both, only_link, only_text = L & M, L - M, M - L

# Strong text-only edges: mentioned many times, never linked
strong_text_only = sorted(only_text, key=lambda e: mention_count[e], reverse=True)[:12]
# Why are links missed by text? sample + count those whose target has no usable alias
link_missed_noalias = sum(1 for a, b in only_link if not aliases[b])

# --- Figure 1: overlap, and how mention count predicts whether there is a link -------
fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), gridspec_kw={"width_ratios": [1, 1.3]})
ax = axes[0]
ax.barh(["links only", "both", "mentions only"], [len(only_link), len(both), len(only_text)],
        color=[ACCENT2, INK, ACCENT])
for i, vv in enumerate([len(only_link), len(both), len(only_text)]):
    ax.text(vv + 20, i, str(vv), va="center", fontsize=9)
ax.set_title("Edges in the hyperlink vs mention network")
ax.set_xlim(0, max(len(only_link), len(both), len(only_text)) * 1.2)
ax = axes[1]
by_k = collections.defaultdict(list)
for e in M:
    by_k[min(mention_count[e], 10)].append(e in L)
ks = sorted(by_k)
ax.plot(ks, [np.mean(by_k[k]) for k in ks], "o-", color=ACCENT)
for k in ks:
    ax.text(k, np.mean(by_k[k]) + .03, f"n={len(by_k[k])}", ha="center", fontsize=7, color=MUTED)
ax.set_xticks(ks, [str(k) if k < 10 else "10+" for k in ks])
ax.set_ylim(0, 1.05)
ax.set_xlabel("times A's page names B")
ax.set_ylabel("share also hyperlinked A → B")
ax.set_title("Name a character often enough and you link them")
fig.savefig(out / "overlap.png")
plt.close(fig)

# --- Figure 2: who is talked about vs who is linked ------------------------------
lin = dict(G.in_degree())
tin = dict(T.in_degree())
fig, ax = plt.subplots(figsize=(6.6, 5))
x = np.array([lin[v] for v in V]); y = np.array([tin[v] for v in V])
ax.scatter(x, y, s=14, color=MUTED, alpha=.6, lw=0)
ax.plot([0, 110], [0, 110], ls="--", color=MUTED, lw=1)
ratio = {v: (tin[v] + 1) / (lin[v] + 1) for v in V}
for v in sorted(V, key=ratio.get, reverse=True)[:2] + [x for x in V if pretty(x) in ("Captain Marvel", "Spider-Woman", "Storm", "Venom")] + sorted(V, key=lin.get, reverse=True)[:4]:
    c = ACCENT if ratio[v] > 1.5 else (MUTED if tin[v] == 0 else ACCENT2)
    ax.scatter(lin[v], tin[v], s=26, color=c, zorder=3)
    ax.annotate(pretty(v), (lin[v], tin[v]), fontsize=7.5, color=c, xytext=(4, 2), textcoords="offset points")
ax.set_xlabel("in-degree, hyperlinks")
ax.set_ylabel("in-degree, name mentions")
ax.set_title("Talked about vs linked to")
fig.savefig(out / "mentions_vs_links.png")
plt.close(fig)


def context(a, b, width=110):
    m = patterns[b].search(pages[a])
    if not m:
        return ""
    s = pages[a][max(0, m.start() - width): m.end() + width].replace("\n", " ")
    return "…" + s + "…"


save_results(7, {
    "aliases_example": {pretty(v): sorted(aliases[v]) for v in ["Spider-Man", "Hulk", "Abomination_(character)", "Storm_(Marvel_Comics)"] if v in aliases},
    "no_usable_alias": dropped,
    "alias_collisions": collisions,
    "n_link_edges": len(L), "n_mention_edges": len(M),
    "both": len(both), "only_link": len(only_link), "only_text": len(only_text),
    "jaccard": round(len(both) / len(L | M), 3),
    "share_links_recovered": round(len(both) / len(L), 3),
    "share_mentions_linked": round(len(both) / len(M), 3),
    "link_missed_target_has_no_alias": link_missed_noalias,
    "p_linked_by_mentions": {str(k): round(float(np.mean(by_k[k])), 3) for k in ks},
    "strong_text_only": [(pretty(a), pretty(b), mention_count[(a, b)], context(a, b)) for a, b in strong_text_only],
    "only_link_sample": [(pretty(a), pretty(b), sorted(aliases[b])) for a, b in sorted(only_link)[:15]],
    "talked_not_linked": [(pretty(v), lin[v], tin[v]) for v in sorted(V, key=ratio.get, reverse=True)[:8]],
    "corr_in": round(float(np.corrcoef(x, y)[0, 1]), 3),
    "text_components": nx.number_weakly_connected_components(T),
    "text_isolates": sorted(pretty(v) for v in nx.isolates(T)),
})
