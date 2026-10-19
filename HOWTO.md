# pypost — How to use this template

This is a guide for making **your** blog with pypost. Generate a blog with
`uvx copier copy --trust <pypost repo> my-blog` (see the README), or work
directly in a clone of this repo. For reference-style documentation (every
frontmatter field, every config variable), see [`REQUIREMENTS.md`](REQUIREMENTS.md).

---

## What you get out of the box

- A bilingual (ES/EN) blog with zero build step and no database — content is
  plain Markdown files
- Server-side syntax highlighting, auto Table of Contents, series navigation,
  tags with URL-safe slugs
- Dark/light theme with a persistent cookie (no flash on reload)
- SEO basics: sitemap, robots.txt, hreflang alternates, Open Graph/Twitter
  cards, per-language RSS feeds
- A pytest suite and CI workflow
- Everything self-hosted: no CDN requests leave your site

---

## Quick start

```bash
uv sync --group dev      # install runtime + dev dependencies
uv run python main.py    # dev server with auto-reload on *.py AND *.md
```

Open <http://localhost:8000>. ES lives at `/`, EN at `/en/`.

To run without auto-reload (e.g. in a container):

```bash
ENV=production uv run python main.py
```

## First 10 minutes of customization

1. **Delete the demo content** — remove the files inside `posts/` and `pages/`
   and drop in your own Markdown (keep the folder structure, see below).
2. **Set your identity** in `config.py`:

   ```python
   SITE_NAME        = "myblog"
   SITE_DESCRIPTION = "Notes on things I build."
   AUTHOR           = "Your Name"
   ```

3. **Restrain the nav** — `NAV_LINKS` in `config.py` controls the header menu
   per language. Remove the "About" links if you don't want static pages.
4. **Recolor it** — edit the CSS variables in `static/theme.css` (see
   [Theme and colors](#theme-and-colors) below).

That's a complete, working personal blog.

---

## Writing content

### Posts

Create `posts/{lang}/YYYYMMDD-my-slug.md`:

```markdown
---
title: My Post Title
date: 2026-04-01
published: true
description: "One-line summary for cards, RSS and og:description."
tags: [python, demo]
---

Body in **Markdown**.
```

Rules worth knowing:

- `published: true` or the post never appears anywhere (this is your draft flag)
- Omit `slug` and it's derived from the title; set it to pick the URL yourself
- The filename's date and the frontmatter `date` are independent — sorting uses
  frontmatter
- Tag pages live at `/tags/{slug}` (slugified, shared across languages), so
  `tags: [ciencia de datos]` links fine from both ES and EN indexes
- Raw HTML in posts is **escaped by design** — link to embeds instead of
  inlining them

In dev mode, saving the file is enough — the server reloads on `*.md` changes.

### Translations

To link a post to its counterpart in the other language (the 🌐 nav button),
declare it on **one** side only:

```yaml
# posts/es/my-post.md
translations: {en: my-post-en}   # slug of the EN post
```

The reverse link is built automatically. Posts without a translation fall back
to the other language's index — the toggle never 404s.

### Series

Give posts the **same** `series` string and consecutive `series_part` numbers:

```yaml
series: "Building a blog"
series_part: 1
```

pypost injects prev/next navigation at the bottom of each part. This works
across languages (part 1 in ES, part 2 in EN) as long as the `series` value
matches exactly — the demo posts show a working example.

### Static pages

Drop a file in `pages/{lang}/` and it's served automatically — no route
registration, no code edits:

```text
pages/es/sobre-mi.md   →   /pages/es/sobre-mi
```

Add it to `NAV_LINKS` if you want it in the menu.

---

## Customizing

### Site identity and behavior

Everything lives in `config.py` — the file is short and commented. The
frequently-touched pieces:

| What | Where |
|---|---|
| Site name, description, author | `SITE_NAME`, `SITE_DESCRIPTION`, `AUTHOR` |
| Nav menu | `NAV_LINKS` (per language) |
| Button/label text ("Read →", "min read", …) | `UI_STRINGS` (per language) |
| Posts per index page / RSS feed | `POSTS_PER_PAGE` (or env var) / `RSS_ITEMS` |
| Code highlight themes | `PYGMENTS_STYLE_DARK`, `PYGMENTS_STYLE_LIGHT` |

### Adding a language

1. Add its code to `SUPPORTED_LANGS` (e.g. `["es", "en", "fr"]`)
2. Create `posts/fr/` and `pages/fr/` directories
3. Copy a full `UI_STRINGS` and `NAV_LINKS` entry for the new language — every
   key must be present, missing ones raise `KeyError` at render time

Routes, feeds, sitemap entries and hreflang tags are generated automatically
from that list. URL layout: `DEFAULT_LANG` is served at `/`, every other
language at `/{lang}/`. The 🌐 nav button cycles through `SUPPORTED_LANGS` in
list order — with two languages it's a toggle; with three, ES → FR → EN → ES.

### Theme and colors

All colors and fonts are CSS variables in `static/theme.css` — **yours to
edit** (it's written once at generation and `copier update` never overwrites
it). The dark and light palettes:

```css
:root, [data-theme="dark"] { --bg: #0d0f12; --accent: #4da8fa; ... }
[data-theme="light"]       { --bg: #f6f7f9; --accent: #0b6ab3; ... }
```

Change the variables and the whole site re-skins, because `static/custom.css`
(the layout, template-owned) only references variables — never touch it. The
theme toggle in the nav stores a cookie server-side, so there's no flash on
reload.

### Page width and spacing

The layout reads five variables. Their defaults live in `static/custom.css`;
override any of them in `static/theme.css` (a commented block is there):

```css
:root {
  --content-width: 1180px;                  /* nav, main and footer */
  --gutter:        clamp(1rem, 3vw, 2rem);  /* left/right page padding */
  --toc-width:     240px;                   /* post table of contents */
  --measure:       70ch;                    /* max line length of prose */
  --font-size-max: 112.5%;                  /* caps Pico's font scaling */
}
```

Pico grows the base font from 16px up to 21px on wide screens;
`--font-size-max` stops it at 18px so wide screens get more text per line,
not just bigger text. Set it to `131.25%` to restore Pico's full scaling.

### Fonts

Fonts are self-hosted woff2 files in `static/fonts/`, wired up by `@font-face`
rules at the top of `static/theme.css`. To swap them:

1. Put your woff2 in `static/fonts/`
2. Update the `src: url(...)` paths and `font-weight` ranges in those
   `@font-face` blocks
3. Point `--font-body` / `--font-mono` (same file, `:root` block) at them — the
   layout picks the variables up everywhere

### Syntax highlighting style

`static/pygments.css` is **generated at startup** — don't edit it. The styles
come from two config variables:

```python
PYGMENTS_STYLE_DARK  = "monokai"   # code theme in dark mode
PYGMENTS_STYLE_LIGHT = "friendly"  # code theme in light mode
```

Pick any style from
`uv run python -c "from pygments.styles import get_all_styles; print(list(get_all_styles()))"`
and restart.

### Favicon and social image

- Replace `static/favicon.svg` with your own icon
- Set `SITE_IMAGE` (env var) to an absolute URL of a social-share image, and
  `og:image` + `twitter:image` tags appear automatically

---

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `PORT` | Listen port | `8000` |
| `SITE_URL` | Canonical URL — used by og tags, RSS, sitemap, hreflang | `http://localhost:$PORT` |
| `SITE_IMAGE` | Absolute URL for og:image / twitter:image | *(unset)* |
| `POSTS_PER_PAGE` | Index pagination size | `10` |
| `ENV` | Set `production` to disable dev auto-reload | `development` |

---

## Testing your changes

```bash
uv run pytest -q                # 27 tests: routes, feeds, headers, traversal, pagination
uv run python -m pyflakes main.py config.py
```

The suite includes path-traversal regression tests against the original
security bug — run it before deploys. The suite is **config-driven**: it reads
`config.py` and the content indexes, so it stays green for any combination of
languages and content. CI (`.github/workflows/ci.yml`) runs both
on every push and pull request.

## Updating from the template

If your blog was generated with Copier (`uvx copier copy`), it remembers its
answers in `.copier-answers.yml`. To pull in upstream fixes and features:

```bash
uvx copier update --trust
```

Copier replays the new template version against your saved answers and merges
the result. Your `config.py`, `posts/`, `pages/`, and `static/theme.css` are
preserved (`theme.css` is skip-if-exists, so it's never even offered); if an
upstream change touches a line you also edited (typically in `main.py` or
`tests/`), you get standard conflict markers to resolve by hand.
Keep engine edits small and updates stay painless.

## Deploying

**Railway:** push to GitHub, create a project from the repo — the `Procfile`
is picked up and `$PORT` is set for you. Set `SITE_URL` to your production
URL. That's the whole config.

**Anywhere else** (Fly, Render, a VPS): it's a standard uvicorn app —

```bash
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port $PORT
```

Set `SITE_URL` wherever you deploy; everything else is optional.