"""Build the static Go nuts site: site/posts/*.md -> docs/*.html (GitHub Pages serves docs/)."""
import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "site" / "posts"
DOCS = ROOT / "docs"
SITE_TITLE = "Marvel, Mined"
SITE_SUB = "Weekly “Go nuts” posts for 02805 Social Graphs and Interactions, DTU, autumn 2026"

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{root}style.css">
</head>
<body>
<header class="site">
  <a class="brand" href="{root}index.html">{site}</a>
  <nav>{nav}</nav>
</header>
<main>
{body}
</main>
<footer>{site} · 02805 Social Graphs and Interactions · code and data in <code>analysis/</code></footer>
</body>
</html>
"""


def read_post(path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
        for line in front.strip().splitlines():
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, body


def main():
    posts = []
    for p in sorted(POSTS.glob("week*.md"), key=lambda p: int(re.search(r"\d+", p.stem).group())):
        meta, body = read_post(p)
        posts.append((p.stem, meta, body))

    nav = lambda root: " ".join(
        f'<a href="{root}{slug}.html">W{meta["week"]}</a>' for slug, meta, _ in posts)

    for slug, meta, body in posts:
        md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "md_in_html"])
        content = md.convert(body)
        header = (f'<p class="kicker">Week {meta["week"]} · {html.escape(meta["topic"])}</p>'
                  f'<h1>{html.escape(meta["title"])}</h1>'
                  f'<p class="dek">{html.escape(meta["dek"])}</p>')
        (DOCS / f"{slug}.html").write_text(PAGE.format(
            title=f'{meta["title"]} · {SITE_TITLE}', root="", site=SITE_TITLE, nav=nav(""),
            body=f'<article>{header}{content}</article>'), encoding="utf-8")

    cards = "\n".join(
        f'<a class="card" href="{slug}.html"><span class="kicker">Week {meta["week"]} · '
        f'{html.escape(meta["topic"])}</span><h2>{html.escape(meta["title"])}</h2>'
        f'<p>{html.escape(meta["dek"])}</p>'
        f'<img src="{meta["thumb"]}" alt="" loading="lazy"></a>'
        for slug, meta, _ in reversed(posts))
    body = (f'<section class="hero"><h1>{SITE_TITLE}</h1><p>{SITE_SUB}. One question per week, '
            f'asked of the same 303 Marvel superheroes (and, in week 4, 1,444 philosophers).</p></section>'
            f'<section class="cards">{cards}</section>')
    (DOCS / "index.html").write_text(PAGE.format(
        title=SITE_TITLE, root="", site=SITE_TITLE, nav=nav(""), body=body), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"built {len(posts)} posts")


if __name__ == "__main__":
    main()
