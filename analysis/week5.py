"""Week 5: does network fame buy you more words?"""
import re

import numpy as np
from scipy import stats

from common import *

G = marvel_graph()
pages = marvel_pages()
out = out_dir(5)

TOKEN = re.compile(r"[a-z0-9]+(?:['’][a-z]+)?")
words = {v: len(TOKEN.findall(t.lower())) for v, t in pages.items()}
indeg = dict(G.in_degree())
V = sorted(G)

x = np.log10(np.array([indeg[v] + 1 for v in V]))
y = np.log10(np.array([words[v] for v in V]))
fit = stats.linregress(x, y)
rho = stats.spearmanr([indeg[v] for v in V], [words[v] for v in V])
resid = dict(zip(V, y - (fit.intercept + fit.slope * x)))
above = sorted(V, key=resid.get, reverse=True)[:8]
below = sorted(V, key=resid.get)[:8]

# How much of a long page is "publication history" rather than story?
HEAD = re.compile(r"^(={2,}\s*)?(publication history|in other media|reception|"
                  r"collected editions|other versions|powers and abilities)\s*(={2,})?\s*$",
                  re.I | re.M)


def section_words(text):
    """Split on heading-like lines (lines with <= 5 words and no final period)."""
    secs, cur, buf = {}, "lead", []
    for line in text.splitlines():
        s = line.strip().strip("=").strip()
        if s and len(s.split()) <= 5 and not s.endswith((".", ":", '"')) and s[0].isupper():
            secs[cur] = secs.get(cur, 0) + len(TOKEN.findall(" ".join(buf).lower()))
            cur, buf = s.lower(), []
        else:
            buf.append(line)
    secs[cur] = secs.get(cur, 0) + len(TOKEN.findall(" ".join(buf).lower()))
    return secs


media_share = {}
for v in V:
    s = section_words(pages[v])
    tot = sum(s.values()) or 1
    media_share[v] = sum(c for k, c in s.items() if "in other media" in k or "video game" in k
                         or "film" in k or "television" in k) / tot

fig, ax = plt.subplots(figsize=(7.2, 5))
ax.scatter(10 ** x, 10 ** y, s=14, color=MUTED, alpha=.6, lw=0)
xx = np.linspace(x.min(), x.max(), 50)
ax.plot(10 ** xx, 10 ** (fit.intercept + fit.slope * xx), color=INK, lw=1.2,
        label=f"fit: words ∝ (k_in+1)^{fit.slope:.2f}")
for v, c in [(v, ACCENT) for v in above[:6]] + [(v, ACCENT2) for v in below[:3]]:
    ax.scatter(indeg[v] + 1, words[v], s=28, color=c, zorder=3)
    ax.annotate(pretty(v), (indeg[v] + 1, words[v]), fontsize=7.5, color=c,
                xytext=(4, 2), textcoords="offset points")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("in-degree + 1 (how many Marvel pages link here)")
ax.set_ylabel("words on the Wikipedia page")
ax.set_title("Fame buys words, but slowly")
ax.legend(frameon=False, fontsize=8, loc="lower right")
fig.savefig(out / "fame_vs_words.png")
plt.close(fig)

# media share vs in-degree: does fame come with film/TV/games sections?
fig, ax = plt.subplots(figsize=(6.4, 3.6))
bins = [0, 1, 3, 10, 200]
labels = ["0", "1–2", "3–9", "10+"]
groups = [[media_share[v] for v in V if lo <= indeg[v] < hi] for lo, hi in zip(bins[:-1], bins[1:])]
ax.boxplot(groups, tick_labels=[f"{l}\n(n={len(g)})" for l, g in zip(labels, groups)],
           medianprops={"color": ACCENT}, showfliers=False)
ax.set_xlabel("in-degree")
ax.set_ylabel("share of words in media sections")
ax.set_title("More famous pages give a bigger share to films, TV and games")
fig.savefig(out / "media_share.png")
plt.close(fig)


def peek(v):
    lines = [l.strip() for l in pages[v].splitlines() if l.strip()]
    return " ".join(lines[1:3])[:240] if len(lines) > 1 else lines[0][:240]


save_results(5, {
    "slope": round(fit.slope, 3), "r2": round(fit.rvalue ** 2, 3),
    "spearman": round(rho.statistic, 3),
    "median_words": int(np.median(list(words.values()))),
    "min_words": [pretty(min(words, key=words.get)), min(words.values())],
    "max_words": [pretty(max(words, key=words.get)), max(words.values())],
    "above": [(pretty(v), indeg[v], words[v], round(10 ** resid[v], 1)) for v in above],
    "below": [(pretty(v), indeg[v], words[v], round(10 ** resid[v], 2)) for v in below],
    "media_share_median_by_bin": {l: round(float(np.median(g)), 3) for l, g in zip(labels, groups)},
    "peek_above": {pretty(v): peek(v) for v in above[:4]},
    "peek_below": {pretty(v): peek(v) for v in below[:4]},
    "headings_sample": {pretty(v): list(section_words(pages[v]).keys())[:14] for v in [above[0], below[0], "Spider-Man"]},
})
