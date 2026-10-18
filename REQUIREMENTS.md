# pypost — Developer Guide

A minimal, bilingual blog framework. No build step, no database.
Stack: **FastHTML** · **Mistune** · **Pygments** · **PicoCSS** · **Uvicorn**

> **Generated blog?** This project came from the pypost Copier template; your
> answers live in `.copier-answers.yml`. Run `uvx copier update --trust` to pull
> upstream engine updates — your config, content, and styles are preserved.

---

## Running locally

```bash
# Install deps (uv recommended)
uv sync --group dev

# Start dev server (auto-reload)
uv run python main.py
# → http://localhost:8000
```

Set `ENV=production` to run without auto-reload. Default lang (ES) is at `/`, secondary lang (EN) at `/en/`.

## Tests

```bash
uv run pytest -q          # full suite (routes, feeds, security headers, traversal, pagination)
uv run python -m pyflakes main.py config.py   # ignore "...defined from star imports" lines —
                                              # they're noise from `from fasthtml.common import *`
```

The suite includes raw-ASGI path-traversal regression tests that bypass HTTP client URL normalization. CI runs both on every push/PR (`.github/workflows/ci.yml`).

---

## Project structure

```text
pypost/
├── main.py           # App: post loading, components, routes
├── config.py         # Site identity, languages, nav, UI strings
├── tests/
│   └── test_app.py   # Pytest suite (Starlette TestClient)
├── .github/workflows/ci.yml
├── static/
│   ├── theme.css     # Colors & fonts (yours — never overwritten by update)
│   ├── custom.css    # Layout & components (template-owned, rarely edited)
│   ├── vendor/       # Vendored PicoCSS (self-hosted, no CDN)
│   ├── fonts/        # Self-hosted Inter + JetBrains Mono (woff2)
│   ├── favicon.svg
│   └── pygments.css  # Auto-generated on startup — do not edit
├── posts/
│   ├── en/           # English posts (*.md)
│   └── es/           # Spanish posts (*.md)
├── pages/
│   ├── en/about.md
│   └── es/about.md
├── pyproject.toml
├── uv.lock
├── requirements.txt
└── Procfile          # Railway deployment
```

---

## Adding a post

1. Create `posts/{lang}/YYYYMMDD-my-slug.md`
2. Add frontmatter at the top
3. Restart the server (or it will auto-reload in dev mode).

```markdown
---
title: My Post Title
date: 2026-04-01
published: true
slug: my-post           # optional — auto-derived from title
description: "One-line summary shown on cards and in RSS."
tags: [python, demo]
series: "My Series"     # optional
series_part: 1          # required if series is set
toc: true               # default true; set false to hide ToC
---

Your content here...
```

### Frontmatter reference

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `title` | string | filename stem | Required in practice |
| `date` | date | — | `YYYY-MM-DD` format |
| `published` | bool | `false` | Must be `true` to appear |
| `slug` | string | slugified title | Must be unique per language |
| `description` | string | `""` | Cards, RSS, og:description |
| `tags` | list | `[]` | Creates tag index pages |
| `translations` | dict | `{}` | Maps to translated slugs, e.g. `{en: my-post-en}`. Declaring it on one post of a pair is enough — the reverse link is built automatically. Posts without a translation fall back to the other language's index. |
| `series` | string | `""` | Groups posts into a series |
| `series_part` | int | `null` | Order within the series |
| `toc` | bool | `true` | Show ToC when ≥3 headings |

### Markdown content

Raw HTML in post/page Markdown is **escaped by design** (Mistune runs with `escape=True`). If you need an embed (e.g. a YouTube iframe), render it as a link instead — or change the renderer consciously, knowing it opts into author-controlled HTML.

### Assets

All frontend assets are self-hosted — no CDN requests leave the site:

- `static/vendor/pico.classless.min.css` — PicoCSS v2 (MIT), vendored as-is
- `static/fonts/` — Inter and JetBrains Mono (latin subsets, variable), referenced by `@font-face` rules in `static/theme.css`

---

## Adding a static page

1. Create `pages/{lang}/mypage.md` — it is automatically served at `/pages/{lang}/mypage`. No route registration needed.

2. Optionally add it to `NAV_LINKS` in `config.py`:

```python
NAV_LINKS = {
    "en": [..., ("My Page", "/pages/en/mypage")],
    "es": [..., ("Mi página", "/pages/es/mypage")],
}
```

---

## Configuring the site

Edit `config.py`:

| Variable | Description |
| --- | --- |
| `SITE_NAME` | Shown in nav, footer, title tags |
| `SITE_DESCRIPTION` | Default meta description |
| `AUTHOR` | Default post author |
| `PORT` | Dev port (overridden by `$PORT` in production) |
| `SITE_URL` | Canonical URL used in og tags, RSS, sitemap and hreflang (set the `SITE_URL` env var in production; defaults to `http://localhost:$PORT`) |
| `SITE_IMAGE` | Absolute URL of a social-share image, used for `og:image` / `twitter:image` (optional, via `SITE_IMAGE` env var) |
| `DEFAULT_LANG` | Language served at `/` |
| `SUPPORTED_LANGS` | Both languages, e.g. `["es", "en"]` |
| `NAV_LINKS` | Per-language nav items |
| `UI_STRINGS` | All button labels, messages, RSS strings |
| `POSTS_PER_PAGE` | Posts per index page (via `POSTS_PER_PAGE` env var, default 10) |
| `RSS_ITEMS` | Posts included in each RSS feed (default 20) |
| `PYGMENTS_STYLE_DARK` / `PYGMENTS_STYLE_LIGHT` | Pygments styles for code highlighting per theme (defaults `monokai` / `friendly`) |

Adding a third language: add its code to `SUPPORTED_LANGS`, create `posts/{lang}/` and `pages/{lang}/` directories, and add its nav links and `UI_STRINGS` entries. Routes are generated automatically.

---

## Changing the theme

All colors and fonts are CSS variables in `static/theme.css` — the file you
edit. (`static/custom.css` holds the layout and references those variables; it
belongs to the template.) Edit the `:root / [data-theme="dark"]` block for
dark mode, `[data-theme="light"]` for light mode, and `--font-body` /
`--font-mono` for the typefaces.

Key variables:

| Variable | Role |
| --- | --- |
| `--bg` | Page background |
| `--bg-surface` | Card / nav background |
| `--accent` | Links, h3, tags, borders |
| `--text` | Body text |
| `--text-heading` | h1/h2 color |
| `--text-muted` | Dates, meta, muted text |
| `--code-bg` | Inline and block code background |

The `pygments.css` file (syntax highlighting) is auto-generated from Pygments styles on startup. Change the styles in `config.py`:

```python
PYGMENTS_STYLE_DARK  = "monokai"
PYGMENTS_STYLE_LIGHT = "friendly"
```

Run `python -c "from pygments.styles import get_all_styles; print(list(get_all_styles()))"` to list available styles.

---

## Series

Posts with the same `series` string are grouped. Add `series_part` (integer) to define order. pypost auto-injects prev/next navigation at the bottom of each post.

Series work across languages — part 1 can be in ES and part 2 in EN.

---

## Tags

Any value in a post's `tags` list creates:

- A tag badge on the post card and post page
- An entry on `/tags/` (localized: `/en/tags/`)
- A filtered list page at `/tags/{slug}` — tags keep their original text but get URL-safe slugs (e.g. `#ciencia de datos` → `/tags/ciencia-de-datos`). Slugs are shared across languages, so tag pages exist in both even if the tag text only appears in one.

## Pagination

The blog index shows `POSTS_PER_PAGE` posts per page (default 10); older posts are paginated at `/?page=2` (and `/en/?page=2`). The nav is hidden when everything fits on one page.

## SEO

- `/sitemap.xml` — all index, page and post URLs with `lastmod`, with hreflang alternates per entry
- `/robots.txt` — points crawlers at the sitemap
- `hreflang` `<link>` alternates + `x-default` on every page, per-language RSS autodiscovery links
- Open Graph + Twitter card tags (`og:image` / `twitter:image` only if `SITE_IMAGE` is set)
- Correct `<html lang>` per language, real 404 status codes on missing content

---

## Table of Contents

When a post has 3 or more h2/h3 headings, a sticky sidebar ToC is generated. Headings get `id` attributes automatically from their slugified text.

Set `toc: false` in frontmatter to disable for a specific post.

---

## RSS feeds

- Default lang feed: `/feed.xml`
- Secondary lang feed: `/feed/{lang}.xml` (e.g. `/feed/en.xml`)

Feeds include the `RSS_ITEMS` most recent posts (default 20), with full HTML content (`content:encoded`) per item. Autodiscovery `<link>` tags are injected into every page.

---

## Deploying on Railway

1. Push the repo to GitHub
2. Create a new Railway project from the repo
3. Railway detects the `Procfile` and sets `$PORT` automatically
4. Set environment variables in Railway:
   - `SITE_URL` — your production URL (used for og tags, RSS, sitemap and hreflang)
   - `ENV=production` — disables dev auto-reload when running via `python main.py` (the `Procfile` runs uvicorn directly and never reloads, so this is optional there)

The `static/pygments.css` file is gitignored and regenerated at startup.
