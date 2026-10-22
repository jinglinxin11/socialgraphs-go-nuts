# Marvel, Mined — Go nuts posts for 02805

Weekly "Go nuts with your LLM" posts for 02805 Social Graphs and Interactions (DTU, autumn 2026).

| folder | what |
|---|---|
| `data/` | course data from https://sunelehmann.com/socialgraphs2026-web/data/ |
| `analysis/weekN.py` | one script per week: writes figures to `docs/assets/weekN/` and numbers to `analysis/results/weekN.json` |
| `site/posts/weekN.md` | the post text (front matter + Markdown) |
| `site/build.py` | turns the posts into HTML in `docs/` |
| `docs/` | the finished static site (GitHub Pages: serve from `main` → `/docs`) |

## Rebuild

```bash
cd analysis
python week1.py   # ... week7.py (week2 takes about a minute: 200 shuffles)
cd ..
python site/build.py
python -m http.server 8765 --directory docs
```

Needs: `networkx>=3.3`, `pandas`, `numpy`, `scipy`, `matplotlib`, `scikit-learn`, `markdown`.

## Publish on GitHub Pages

1. Create a public repository and push this folder.
2. Settings → Pages → Source: *Deploy from a branch*, branch `main`, folder `/docs`.
3. Post the site link in the week's Teams channel.
