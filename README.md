# Javier Thompson punto Ce Ele

El lugar donde estacioné la Madre Nodriza

Built with [pypost](https://github.com/darkestabed/pypost) — a minimal blog engine:
Markdown in, site out. No build step, no database.

## Run

```bash
uv sync --group dev
uv run python main.py
```

Locally:
→ `/` (es)

## Write

- **New post** — `posts/es/YYYYMMDD-my-slug.md` with frontmatter
  (see [REQUIREMENTS.md](REQUIREMENTS.md))
- **New static page** — drop a `.md` into `pages/es/`, route included
- **Customize** — everything user-facing lives in `config.py`; your look lives
  in `static/theme.css` (see [HOWTO.md](HOWTO.md))

## Update the engine

This blog was generated from the pypost template. Engine fixes and features land
there over time — pull them in with:

```bash
uvx copier update --trust
```

Your `config.py`, content, and styles survive; if an update touches a line you
also changed, you get standard conflict markers to resolve by hand. Keep custom
edits to `main.py` small and this stays painless.

## Test

```bash
uv run pytest -q     # routes, feeds, headers, traversal, pagination
```

CI runs the same suite on every push (`.github/workflows/ci.yml`).

## Deploy

Railway (or any uvicorn host):

```bash
uv sync
SITE_URL=https://your.blog uv run uvicorn main:app --host 0.0.0.0 --port $PORT
```
