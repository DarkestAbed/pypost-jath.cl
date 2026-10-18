import os
import re
import time
from html import escape as html_escape
from html.parser import HTMLParser
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from email.utils import formatdate
from datetime import datetime

import frontmatter as fm
import mistune
from pygments import highlight as pygments_highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from starlette.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from fasthtml.common import *

from config import (
    SITE_NAME, SITE_URL, SITE_IMAGE, AUTHOR, PORT, POSTS_PER_PAGE, RSS_ITEMS,
    PYGMENTS_STYLE_DARK, PYGMENTS_STYLE_LIGHT,
    DEFAULT_LANG, SUPPORTED_LANGS, NAV_LINKS, UI_STRINGS,
)

# ── Syntax-highlighting Markdown renderer ─────────────────────────────────────

class TechnicalRenderer(mistune.HTMLRenderer):
    def block_code(self, code: str, info: str = None, **attrs) -> str:
        lang_clean = (info or "").strip().split()[0] if info else ""
        try:
            lexer = get_lexer_by_name(lang_clean) if lang_clean else TextLexer()
        except ClassNotFound:
            lexer = TextLexer()
        formatter = HtmlFormatter(cssclass="highlight", nowrap=False)
        highlighted = pygments_highlight(code, lexer, formatter)
        label = f'<span class="code-lang">{html_escape(lang_clean)}</span>' if lang_clean else ""
        copy_btn = '<button class="copy-btn" onclick="copyCode(this)" aria-label="Copy code">copy</button>'
        return f'<div class="code-block">{label}{copy_btn}{highlighted}</div>\n'

    def heading(self, text: str, level: int, **attrs) -> str:
        plain = re.sub(r"<[^>]+>", "", text)
        anchor = _slugify(plain) or "section"
        # Unique ids: duplicate heading texts get -2, -3, … suffixes
        seen = getattr(self, "_anchors", {})
        seen[anchor] = n = seen.get(anchor, 0) + 1
        self._anchors = seen
        if n > 1:
            anchor = f"{anchor}-{n}"
        return f'<h{level} id="{anchor}">{text}</h{level}>\n'


_md_renderer = TechnicalRenderer()
md = mistune.create_markdown(
    renderer=_md_renderer,
    plugins=["table", "strikethrough", "task_lists"],
)


def render_md(text: str) -> str:
    "Render one document; resets heading-anchor state so ids are unique per post/page."
    _md_renderer._anchors = {}
    return md(text)

# ── Pygments CSS (generated once at startup) ──────────────────────────────────

_dark_css  = HtmlFormatter(style=PYGMENTS_STYLE_DARK,  cssclass="highlight").get_style_defs(".highlight")
_light_css = HtmlFormatter(style=PYGMENTS_STYLE_LIGHT, cssclass="highlight").get_style_defs(".highlight")

PYGMENTS_CSS = (
    f"[data-theme='dark'] .highlight {{ background: var(--code-bg); }}\n"
    f"[data-theme='dark'] {_dark_css}\n"
    f"[data-theme='light'] {_light_css}\n"
)

_pygments_path = Path("static/pygments.css")
_pygments_path.parent.mkdir(exist_ok=True)
_pygments_path.write_text(PYGMENTS_CSS)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text)


class _TagStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str):
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _strip_html(html: str) -> str:
    p = _TagStripper()
    p.feed(html)
    return p.get_text()


def reading_time(html: str) -> int:
    words = len(_strip_html(html).split())
    return max(1, round(words / 200))


def build_toc(html: str) -> list[dict]:
    toc = []
    for m in re.finditer(r'<h([23])[^>]*id="([^"]+)"[^>]*>(.*?)</h\1>', html, re.DOTALL):
        level  = int(m.group(1))
        anchor = m.group(2)
        text   = re.sub(r"<[^>]+>", "", m.group(3)).strip()
        toc.append({"level": level, "anchor": anchor, "text": text})
    return toc


# ── Post loading ──────────────────────────────────────────────────────────────

_MONTHS_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
_MONTHS_EN = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _format_date(raw, lang: str) -> str:
    if not raw:
        return ""
    if hasattr(raw, "strftime"):
        if lang == "es":
            return f"{raw.day} de {_MONTHS_ES[raw.month]} de {raw.year}"
        return f"{_MONTHS_EN[raw.month]} {raw.day:02d}, {raw.year}"
    return str(raw)


def load_posts(lang: str) -> list[dict]:
    base = Path("posts") / lang
    if not base.exists():
        return []
    posts = []
    seen_slugs: dict[str, str] = {}

    for path in base.glob("*.md"):
        post = fm.load(str(path))
        if not post.get("published", False):
            continue

        title = post.get("title", path.stem)
        slug  = post.get("slug") or _slugify(title)

        if slug in seen_slugs:
            raise ValueError(
                f"Slug collision: '{slug}' from '{path}' conflicts with '{seen_slugs[slug]}'"
            )
        seen_slugs[slug] = str(path)

        raw_date     = post.get("date")
        content_html = render_md(post.content)

        posts.append({
            "slug":         slug,
            "title":        title,
            "date":         raw_date,
            "date_str":     _format_date(raw_date, lang),
            "author":       post.get("author", AUTHOR),
            "description":  post.get("description", ""),
            "tags":         post.get("tags", []),
            "translations": post.get("translations", {}),
            "series":       post.get("series", ""),
            "series_part":  post.get("series_part", None),
            "toc_enabled":  post.get("toc", True),
            "content_html": content_html,
            "reading_time": reading_time(content_html),
            "toc":          build_toc(content_html),
            "lang":         lang,
        })

    return sorted(posts, key=lambda p: p["date"] or datetime.min, reverse=True)


def load_page(path_str: str) -> tuple[str, str] | None:
    path = Path(path_str)
    if not path.exists():
        return None
    page = fm.load(str(path))
    return page.get("title", path.stem), render_md(page.content)


# ── Indexes (built once at startup) ───────────────────────────────────────────

POST_INDEX: dict[str, dict[str, dict]] = {
    lang: {p["slug"]: p for p in load_posts(lang)}
    for lang in SUPPORTED_LANGS
}


# Translation index: (lang, slug) -> {other_lang: other_slug}. Declaring a
# translation on one post of a pair is enough — the reverse edge is added here.
TRANSLATIONS: dict[tuple[str, str], dict[str, str]] = {}
for _lang in SUPPORTED_LANGS:
    for _post in POST_INDEX[_lang].values():
        for _other_lang, _other_slug in _post.get("translations", {}).items():
            TRANSLATIONS.setdefault((_lang, _post["slug"]), {})[_other_lang] = _other_slug
            TRANSLATIONS.setdefault((_other_lang, _other_slug), {})[_lang] = _post["slug"]
for (_lang, _slug), _targets in TRANSLATIONS.items():
    for _t_lang, _t_slug in _targets.items():
        if _t_slug not in POST_INDEX.get(_t_lang, {}):
            print(f"warning: translation {_t_lang}/{_t_slug} (from {_lang}/{_slug}) not found")


def get_post(slug: str, lang: str) -> dict | None:
    return POST_INDEX.get(lang, {}).get(slug)


def get_all_posts(lang: str) -> list[dict]:
    return sorted(POST_INDEX.get(lang, {}).values(),
                  key=lambda p: p["date"] or datetime.min, reverse=True)


# Tag index: tag -> list of posts across all languages
TAG_INDEX: dict[str, list[dict]] = {}
for _lang in SUPPORTED_LANGS:
    for _post in POST_INDEX[_lang].values():
        for _tag in _post["tags"]:
            TAG_INDEX.setdefault(_tag, []).append(_post)
for _tag in TAG_INDEX:
    TAG_INDEX[_tag].sort(key=lambda p: p["date"] or datetime.min, reverse=True)


# Series index: series_name -> posts sorted by series_part
SERIES_INDEX: dict[str, list[dict]] = {}
for _lang in SUPPORTED_LANGS:
    for _post in POST_INDEX[_lang].values():
        if _post["series"]:
            SERIES_INDEX.setdefault(_post["series"], []).append(_post)
for _s in SERIES_INDEX:
    SERIES_INDEX[_s].sort(key=lambda p: p["series_part"] or 0)


def get_series_neighbors(post: dict) -> tuple[dict | None, dict | None]:
    if not post["series"]:
        return None, None
    members = SERIES_INDEX.get(post["series"], [])
    for i, p in enumerate(members):
        if p["slug"] == post["slug"] and p["lang"] == post["lang"]:
            prev_p = members[i - 1] if i > 0 else None
            next_p = members[i + 1] if i < len(members) - 1 else None
            return prev_p, next_p
    return None, None


# Page index: lang -> sorted page stems (files under pages/{lang}/)
PAGES_INDEX: dict[str, list[str]] = {
    lang: sorted(p.stem for p in (Path("pages") / lang).glob("*.md"))
    for lang in SUPPORTED_LANGS
}

# Tag slugs: original tag -> URL-safe slug (unique), plus the reverse map.
TAG_SLUGS: dict[str, str] = {}
for _tag in sorted(TAG_INDEX):
    _slug, _base, _n = _slugify(_tag) or "tag", None, 2
    _base = _slug
    while _slug in TAG_SLUGS.values():
        _slug, _n = f"{_base}-{_n}", _n + 1
    TAG_SLUGS[_tag] = _slug
SLUG_TAGS: dict[str, str] = {v: k for k, v in TAG_SLUGS.items()}


# ── App setup ─────────────────────────────────────────────────────────────────

theme_init = Script("""
(function(){
  var m = document.cookie.match(/(?:^|;\\s*)theme=([^;]+)/);
  if (m) document.documentElement.setAttribute('data-theme', m[1]);
})();
""")

copy_script = Script("""
function copyCode(btn) {
  var block = btn.closest('.code-block').querySelector('.highlight pre');
  var text = block ? block.innerText : '';
  navigator.clipboard.writeText(text).then(function() {
    btn.textContent = 'copied!';
    setTimeout(function(){ btn.textContent = 'copy'; }, 1500);
  });
}
""")

favicon     = Link(rel="icon", href="/static/favicon.svg", type="image/svg+xml")
pico_css    = Link(rel="stylesheet", href="/static/vendor/pico.classless.min.css")
pygments_css = Link(rel="stylesheet", href="/static/pygments.css")
theme_css   = Link(rel="stylesheet", href="/static/theme.css")
custom_css  = Link(rel="stylesheet", href="/static/custom.css")

# default_hdrs=False drops FastHTML's CDN scripts (htmx, fasthtml.js, surreal,
# css-scope-inline) — this app uses no htmx attributes, so none are needed and
# no requests leave the site. charset/viewport are re-added explicitly.
def _lang_root(lang: str) -> str:
    "URL root for a language: '/' for the default language, '/{lang}/' otherwise."
    return "/" if lang == DEFAULT_LANG else f"/{lang}/"


def _next_lang(lang: str) -> str:
    "Language the nav toggle cycles to."
    return SUPPORTED_LANGS[(SUPPORTED_LANGS.index(lang) + 1) % len(SUPPORTED_LANGS)]


def _detect_lang(path: str) -> str:
    "Language of a URL path, inferred from a /{lang}/ prefix (default otherwise)."
    for lang in SUPPORTED_LANGS:
        if lang != DEFAULT_LANG and (path == f"/{lang}" or path.startswith(f"/{lang}/")):
            return lang
    return DEFAULT_LANG


def _before(req):
    # Per-request <html> attributes: language and theme (from the cookie, so
    # light-theme users don't get a dark flash before the inline script runs).
    req.htmlkw["lang"] = _detect_lang(req.url.path)
    theme = req.cookies.get("theme")
    if theme in ("dark", "light"):
        req.htmlkw["data-theme"] = theme


app = FastHTML(
    default_hdrs=False,
    before=_before,
    hdrs=(charset, viewport, favicon, theme_init, pico_css, pygments_css, theme_css, custom_css, copy_script),
    htmlkw={"data-theme": "dark"},
)

# Inline scripts (theme init, copy button, inline onclick handlers) are the only
# JS in the app, hence the single 'unsafe-inline' in script-src. All assets are
# self-hosted — no external origins are allowed.
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self'; "
    "font-src 'self'; "
    "img-src 'self' data: https:; "
    "connect-src 'self'; "
    "form-action 'self'; "
    "base-uri 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'none'"
)


class _ResponseHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        resp = await call_next(request)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        path = request.url.path
        if path.startswith(("/static/vendor/", "/static/fonts/")):
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path.startswith("/static/"):
            resp.headers["Cache-Control"] = "public, max-age=86400"
        else:
            resp.headers["Content-Security-Policy"] = _CSP
        return resp


app.add_middleware(_ResponseHeadersMiddleware)


# ── Components ────────────────────────────────────────────────────────────────

def _lang_toggle_href(path: str, current_lang: str) -> str:
    other = _next_lang(current_lang)
    other_index = _lang_root(other)

    # Language roots and the blog index swap to the other language's root
    if path in ("/", _lang_root(current_lang), f"/posts/{current_lang}/"):
        return other_index

    # Post pages: slugs differ per language — follow the translation map,
    # falling back to the other language's index when no translation exists.
    m = re.match(rf"^/posts/{current_lang}/(.+)$", path)
    if m:
        other_slug = TRANSLATIONS.get((current_lang, m.group(1)), {}).get(other)
        if other_slug:
            return f"/posts/{other}/{other_slug}"
        return other_index

    # Tag pages keep their location, switching the language root
    m = re.match(rf"^{_lang_root(current_lang)}tags(/[^/]+)?/?$", path)
    if m:
        return f"{other_index}tags{m.group(1) or ''}"

    # Everything else (pages, …): swap the language segment
    parts = path.split("/")
    for i, part in enumerate(parts):
        if part == current_lang:
            parts[i] = other
            return "/".join(parts)
    return other_index


def nav_bar(lang: str, current_path: str):
    s = UI_STRINGS[lang]
    links    = [Li(A(label, href=href)) for label, href in NAV_LINKS[lang]]
    lang_btn = A(s["switch_lang"], href=_lang_toggle_href(current_path, lang), cls="lang-btn")
    theme_btn = Button(
        s["toggle_theme"],
        cls="theme-btn",
        onclick=(
            "var h=document.documentElement,"
            "n=h.getAttribute('data-theme')==='dark'?'light':'dark';"
            "h.setAttribute('data-theme',n);"
            "var c='theme='+n+';path=/;max-age=31536000;samesite=lax'"
            "+(location.protocol==='https:'?';secure':'');"
            "document.cookie=c;"
        ),
    )
    home_href = _lang_root(lang)
    return Nav(
        Div(
            A(SITE_NAME, href=home_href, cls="nav-brand"),
            Ul(*links, cls="nav-links"),
            Div(lang_btn, theme_btn, cls="nav-controls"),
            cls="nav-inner",
        ),
        cls="site-nav",
    )


def site_footer(lang: str):
    return Footer(
        P(f"© {UI_STRINGS[lang]['footer']}"),
        cls="site-footer",
    )


def _og_tags(title: str, description: str, url: str,
             alternates: dict[str, str] | None = None):
    base_url = SITE_URL
    tags = [
        Meta(property="og:site_name",   content=SITE_NAME),
        Meta(property="og:type",        content="article"),
        Meta(property="og:title",       content=f"{title} | {SITE_NAME}"),
        Meta(property="og:description", content=description),
        Meta(property="og:url",         content=f"{base_url}{url}"),
        Meta(name="description",        content=description),
        Meta(name="twitter:card",        content="summary"),
        Meta(name="twitter:title",       content=f"{title} | {SITE_NAME}"),
        Meta(name="twitter:description", content=description),
    ]
    if SITE_IMAGE:
        tags += [
            Meta(property="og:image",    content=SITE_IMAGE),
            Meta(name="twitter:image",    content=SITE_IMAGE),
        ]
    if alternates:
        for alt_lang, alt_url in alternates.items():
            tags.append(Link(rel="alternate", hreflang=alt_lang, href=f"{base_url}{alt_url}"))
        tags.append(Link(rel="alternate", hreflang="x-default",
                          href=f"{base_url}{alternates.get(DEFAULT_LANG, url)}"))
    for lang in SUPPORTED_LANGS:
        feed = "/feed.xml" if lang == DEFAULT_LANG else f"/feed/{lang}.xml"
        tags.append(Link(rel="alternate", type="application/rss+xml",
                         title=f"{SITE_NAME} {lang.upper()}", href=feed))
    return tuple(tags)


def page_shell(title: str, lang: str, current_path: str, description: str = "",
               *content, alternates: dict[str, str] | None = None):
    return (
        Title(f"{title} | {SITE_NAME}"),
        *_og_tags(title, description, current_path, alternates),
        nav_bar(lang, current_path),
        Main(*content, cls="container"),
        site_footer(lang),
    )


def tag_badge(tag: str, lang: str):
    return A(tag, href=f"{_lang_root(lang)}tags/{TAG_SLUGS[tag]}", cls="tag")


def reading_time_badge(minutes: int, lang: str):
    s = UI_STRINGS[lang]
    return Span(f"{minutes} {s['reading_time']}", cls="reading-time")


def post_card(post: dict, lang: str):
    s    = UI_STRINGS[lang]
    href = f"/posts/{lang}/{post['slug']}"
    tags = [tag_badge(t, lang) for t in post.get("tags", [])]
    return Article(
        H2(A(post["title"], href=href)),
        P(
            Span(post["date_str"], cls="post-date"),
            Span(" · "),
            reading_time_badge(post["reading_time"], lang),
            cls="post-meta",
        ),
        P(post["description"], cls="post-description") if post.get("description") else "",
        Div(*tags, cls="post-tags") if tags else "",
        A(s["read_more"], href=href, cls="read-more"),
        cls="post-card",
    )


def toc_nav(toc: list[dict], lang: str):
    if not toc:
        return ""
    s     = UI_STRINGS[lang]
    items = []
    for entry in toc:
        cls = "toc-h2" if entry["level"] == 2 else "toc-h3"
        items.append(Li(A(entry["text"], href=f"#{entry['anchor']}"), cls=cls))
    return Nav(
        P(s["toc_label"], cls="toc-label"),
        Ul(*items, cls="toc-list"),
        cls="toc-nav",
    )


def series_nav(prev_post: dict | None, next_post: dict | None, lang: str):
    s     = UI_STRINGS[lang]
    items = []
    if prev_post:
        href = f"/posts/{prev_post['lang']}/{prev_post['slug']}"
        items.append(A(f"{s['series_prev']} {prev_post['title']}", href=href, cls="series-prev"))
    if next_post:
        href = f"/posts/{next_post['lang']}/{next_post['slug']}"
        items.append(A(f"{next_post['title']} {s['series_next']}", href=href, cls="series-next"))
    if not items:
        return ""
    return Nav(*items, cls="series-nav")


def post_page_content(post: dict, lang: str):
    s         = UI_STRINGS[lang]
    back_href = _lang_root(lang)
    tags      = [tag_badge(t, lang) for t in post.get("tags", [])]
    prev_p, next_p = get_series_neighbors(post)

    show_toc = post["toc_enabled"] and len(post["toc"]) >= 3
    toc_el   = toc_nav(post["toc"], lang) if show_toc else ""

    series_label = ""
    if post["series"] and post["series_part"]:
        series_label = Span(
            f"{s['series_part']} {post['series_part']}: {post['series']}",
            cls="series-label",
        )

    return (
        Header(
            series_label,
            H1(post["title"]),
            P(
                Span(post["date_str"], cls="post-date"),
                Span(" · "),
                reading_time_badge(post["reading_time"], lang),
                cls="post-meta",
            ),
            Div(*tags, cls="post-tags") if tags else "",
            cls="post-header",
        ),
        Div(
            toc_el,
            Div(NotStr(post["content_html"]), cls="post-body"),
            cls="post-layout",
        ),
        series_nav(prev_p, next_p, lang) if (prev_p or next_p) else "",
        Div(
            A(s["back_to_blog"], href=back_href, cls="back-link"),
            cls="post-footer",
        ),
    )


def not_found_page(lang: str):
    s         = UI_STRINGS[lang]
    back_href = _lang_root(lang)
    return Div(
        H1("404"),
        P(s["not_found"]),
        P(s["not_found_detail"], cls="post-meta"),
        A(s["back_to_blog"], href=back_href, cls="back-link"),
        cls="not-found",
    )


def pagination_nav(lang: str, page: int, total: int):
    pages = max(1, -(-total // POSTS_PER_PAGE))
    if pages <= 1:
        return ""
    s     = UI_STRINGS[lang]
    root  = _lang_root(lang)
    items = []
    if page > 1:
        items.append(A(s["newer_posts"], href=f"{root}?page={page - 1}", cls="pager-newer"))
    if page < pages:
        items.append(A(s["older_posts"], href=f"{root}?page={page + 1}", cls="pager-older"))
    return Nav(*items, cls="pagination")


def blog_index_content(posts: list[dict], lang: str, page: int = 1):
    s     = UI_STRINGS[lang]
    start = (page - 1) * POSTS_PER_PAGE
    cards = [post_card(p, lang) for p in posts[start:start + POSTS_PER_PAGE]]
    return (
        Div(
            H1(SITE_NAME),
            P(s["subtitle"], cls="page-subtitle"),
            cls="page-header",
        ),
        Div(*cards, cls="post-list") if cards else P(s["no_posts"], cls="post-meta"),
        pagination_nav(lang, page, len(posts)),
    )


# ── RSS ───────────────────────────────────────────────────────────────────────

def _build_rss(lang: str) -> str:
    s        = UI_STRINGS[lang]
    base     = SITE_URL
    root     = Element("rss", version="2.0")
    root.set("xmlns:atom", "http://www.w3.org/2005/Atom")
    root.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    channel  = SubElement(root, "channel")
    SubElement(channel, "title").text       = s["rss_title"]
    SubElement(channel, "link").text        = base
    SubElement(channel, "description").text = s["rss_description"]
    SubElement(channel, "language").text    = lang
    SubElement(channel, "lastBuildDate").text = formatdate()
    feed_path  = "/feed.xml" if lang == DEFAULT_LANG else f"/feed/{lang}.xml"
    atom_link  = SubElement(channel, "atom:link")
    atom_link.set("href", f"{base}{feed_path}")
    atom_link.set("rel",  "self")
    atom_link.set("type", "application/rss+xml")

    for post in get_all_posts(lang)[:RSS_ITEMS]:
        item = SubElement(channel, "item")
        SubElement(item, "title").text       = post["title"]
        SubElement(item, "link").text        = f"{base}/posts/{lang}/{post['slug']}"
        SubElement(item, "guid").text        = f"{base}/posts/{lang}/{post['slug']}"
        SubElement(item, "description").text = post.get("description", "")
        SubElement(item, "content:encoded").text = post["content_html"]
        raw = post["date"]
        if hasattr(raw, "timetuple"):
            SubElement(item, "pubDate").text = formatdate(time.mktime(raw.timetuple()))

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(root, encoding="unicode")


# ── Routes ─────────────────────────────────────────────────────────────────────

def _register_lang_routes(lang: str):
    "Register the full set of routes for one language — scales to N languages."
    root = _lang_root(lang)
    lang_alternates = {l: _lang_root(l) for l in SUPPORTED_LANGS}

    @app.get(root, name=f"blog_index_{lang}")
    @app.get(f"/posts/{lang}/", name=f"blog_posts_{lang}")
    def blog_index(req, page: int = 1):
        posts = get_all_posts(lang)
        last_page = max(1, -(-len(posts) // POSTS_PER_PAGE))
        if page < 1 or page > last_page:
            return FtResponse(page_shell("404", lang, root, "",
                              not_found_page(lang)), status_code=404)
        return page_shell("Blog", lang, root, UI_STRINGS[lang]["subtitle"],
                          *blog_index_content(posts, lang, page),
                          alternates=lang_alternates)

    @app.get(f"/posts/{lang}/{{slug}}", name=f"blog_post_{lang}")
    def blog_post(req, slug: str):
        post = get_post(slug, lang)
        if not post:
            return FtResponse(page_shell("404", lang, f"/posts/{lang}/{slug}", "",
                              not_found_page(lang)), status_code=404)
        alternates = {lang: f"/posts/{lang}/{slug}"}
        for other_lang, other_slug in TRANSLATIONS.get((lang, slug), {}).items():
            alternates[other_lang] = f"/posts/{other_lang}/{other_slug}"
        return page_shell(post["title"], lang, f"/posts/{lang}/{slug}",
                          post.get("description", ""),
                          *post_page_content(post, lang), alternates=alternates)

    @app.get(f"/pages/{lang}/{{page}}", name=f"static_page_{lang}")
    def static_page(req, page: str):
        if ".." in page or "/" in page:
            return FtResponse(page_shell("404", lang, f"/pages/{lang}/{page}", "",
                              not_found_page(lang)), status_code=404)
        loaded = load_page(f"pages/{lang}/{page}.md")
        if not loaded:
            return FtResponse(page_shell("404", lang, f"/pages/{lang}/{page}", "",
                              not_found_page(lang)), status_code=404)
        title, html = loaded
        return page_shell(title, lang, f"/pages/{lang}/{page}", "",
                          Div(NotStr(html), cls="about-body"))

    tags_path = "/tags/" if lang == DEFAULT_LANG else f"{root}tags/"

    @app.get(tags_path, name=f"tags_index_{lang}")
    def tags_index(req):
        s = UI_STRINGS[lang]
        sorted_tags = sorted(TAG_INDEX.items(), key=lambda kv: len(kv[1]), reverse=True)
        items = [
            Li(
                A(tag, href=f"{tags_path}{TAG_SLUGS[tag]}", cls="tag"),
                Span(f" ({len(posts)})", cls="tag-count"),
            )
            for tag, posts in sorted_tags
        ]
        return page_shell(s["all_tags"], lang, tags_path, "",
            Div(H1(s["all_tags"]), Ul(*items, cls="tag-cloud"), cls="tags-page")
        )

    @app.get(f"{tags_path}{{tag_slug}}", name=f"tag_view_{lang}")
    def tag_view(req, tag_slug: str):
        s = UI_STRINGS[lang]
        if tag_slug not in SLUG_TAGS:
            return FtResponse(page_shell("404", lang, f"{tags_path}{tag_slug}", "",
                              not_found_page(lang)), status_code=404)
        tag = SLUG_TAGS[tag_slug]
        posts = TAG_INDEX.get(tag, [])
        sections: list = []
        for l in SUPPORTED_LANGS:
            lang_posts = [p for p in posts if p["lang"] == l]
            if lang_posts:
                sections.append(H2(l.upper()))
                sections.extend([post_card(p, l) for p in lang_posts])
        content = Div(
            H1(f"{s['tag_posts']} #{tag}"),
            Div(*sections, cls="post-list") if sections else P(s["no_posts"], cls="post-meta"),
            cls="tags-page",
        )
        return page_shell(f"#{tag}", lang, f"{tags_path}{tag_slug}", "", content)


for _route_lang in SUPPORTED_LANGS:
    _register_lang_routes(_route_lang)


# ── Feeds ─────────────────────────────────────────────────────────────────────

def _register_feed_routes(lang: str):
    @app.get(f"/feed/{lang}.xml", name=f"rss_{lang}")
    def rss_lang(req):
        return Response(_build_rss(lang), media_type="application/rss+xml; charset=utf-8")
    if lang == DEFAULT_LANG:
        @app.get("/feed.xml", name="rss_default")
        def rss_default(req):
            return Response(_build_rss(lang), media_type="application/rss+xml; charset=utf-8")


for _feed_lang in SUPPORTED_LANGS:
    _register_feed_routes(_feed_lang)


# ── SEO: sitemap & robots ──────────────────────────────────────────────────────

@app.get("/sitemap.xml")
def sitemap(req):
    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    def add(loc: str, lastmod=None):
        u = SubElement(urlset, "url")
        SubElement(u, "loc").text = f"{SITE_URL}{loc}"
        if lastmod is not None:
            SubElement(u, "lastmod").text = lastmod.isoformat()

    for lang in SUPPORTED_LANGS:
        add(_lang_root(lang))
        for stem in PAGES_INDEX[lang]:
            add(f"/pages/{lang}/{stem}")
        for post in get_all_posts(lang):
            add(f"/posts/{lang}/{post['slug']}", post["date"])

    return Response('<?xml version="1.0" encoding="UTF-8"?>\n'
                    + tostring(urlset, encoding="unicode"),
                    media_type="application/xml; charset=utf-8")


@app.get("/robots.txt")
def robots(req):
    return Response(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n",
                    media_type="text/plain; charset=utf-8")


# ── Static files ──────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Catch-all 404 ──────────────────────────────────────────────────────────────

_REDIRECTABLE = (
    {"tags"} | set(SUPPORTED_LANGS)
    | {f"posts/{l}" for l in SUPPORTED_LANGS}
    | {f"{l}/tags" for l in SUPPORTED_LANGS if l != DEFAULT_LANG}
)

@app.get("/{path:path}")
def not_found_catchall(req, path: str):
    if path in _REDIRECTABLE:
        return Redirect(f"/{path}/")
    lang = _detect_lang(f"/{path}")
    return FtResponse(page_shell("404", lang, f"/{path}", "", not_found_page(lang)),
                      status_code=404)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    dev = os.environ.get("ENV", "development") != "production"
    serve(port=PORT, reload=dev, reload_includes=["*.md"] if dev else None)
