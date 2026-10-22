"""Shared loaders and plotting style for the Go nuts posts."""
import json
import urllib.parse
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ASSETS = ROOT / "docs" / "assets"
RESULTS = ROOT / "analysis" / "results"

INK = "#1f2933"
MUTED = "#8a94a0"
ACCENT = "#c8102e"   # Marvel-ish red
ACCENT2 = "#1f6fb2"
ACCENT3 = "#e0a100"

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 160,
    "savefig.bbox": "tight",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.titleweight": "bold",
    "axes.titlesize": 11,
})


def marvel_nodes():
    return pd.read_csv(DATA / "week1_nodes.tsv", sep="\t", comment="#", quoting=3)


def marvel_graph(weighted=False):
    """Directed Marvel network, isolates included."""
    nodes = marvel_nodes()
    G = nx.DiGraph()
    G.add_nodes_from(nodes.node_id)
    if weighted:
        edges = pd.read_csv(DATA / "week4_edges_weighted.tsv", sep="\t", comment="#")
        edges.columns = ["source", "target", "weight"]
        for s, t, w in edges.itertuples(index=False):
            G.add_edge(s, t, weight=w)
    else:
        edges = pd.read_csv(DATA / "week1_edges.tsv", sep="\t", comment="#",
                            names=["source", "target"])
        G.add_edges_from(edges.itertuples(index=False))
    return G


def philosophers():
    nodes = pd.read_csv(DATA / "week4_philosophers_nodes.tsv", sep="\t", comment="#", quoting=3)
    edges = pd.read_csv(DATA / "week4_philosophers_edges.tsv", sep="\t", comment="#")
    G = nx.Graph()
    G.add_nodes_from(nodes.node_id)
    for s, t, w in edges.itertuples(index=False):
        if G.has_edge(s, t):
            G[s][t]["weight"] += w
        else:
            G.add_edge(s, t, weight=w)
    return nodes, G


def marvel_pages():
    with zipfile.ZipFile(DATA / "marvel_pages.zip") as z:
        return {
            urllib.parse.unquote(n.split("/")[-1][:-4]): z.read(n).decode("utf-8")
            for n in z.namelist()
            if n.endswith(".txt") and "README" not in n
        }


def pretty(node_id):
    """Spider-Man_(character) -> Spider-Man"""
    name = node_id.replace("_", " ")
    for suffix in (" (character)", " (comics)", " (Marvel Comics)", " (Marvel Comics character)"):
        name = name.replace(suffix, "")
    return name


def out_dir(week):
    d = ASSETS / f"week{week}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_results(week, obj):
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"week{week}.json"
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))
