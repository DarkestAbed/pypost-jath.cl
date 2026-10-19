"""Test suite for pypost. Run from the repo root: `uv run --group dev pytest -q`.

Config-driven: expectations are derived from config.py and the content indexes
rather than hardcoded languages or demo slugs, so the same suite validates any
generated instance — single-language, no demo content, or both.
"""
import asyncio
import xml.etree.ElementTree as ET
from html import escape as html_escape

import pytest

import main
from main import (
    DEFAULT_LANG, SUPPORTED_LANGS, UI_STRINGS,
    POST_INDEX, PAGES_INDEX, TAG_INDEX, TAG_SLUGS, SLUG_TAGS, TRANSLATIONS,
)
from starlette.testclient import TestClient

client = TestClient(main.app)

CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _tags_root(lang: str) -> str:
    return "/tags/" if lang == DEFAULT_LANG else f"/{lang}/tags/"


# ── Pages ──────────────────────────────────────────────────────────────────────

def test_index_pages():
    for lang in SUPPORTED_LANGS:
        r = client.get(main._lang_root(lang))
        assert r.status_code == 200
        assert UI_STRINGS[lang]["subtitle"] in r.text


def test_all_posts_render():
    for lang, posts in POST_INDEX.items():
        for slug, post in posts.items():
            r = client.get(f"/posts/{lang}/{slug}")
            assert r.status_code == 200
            assert html_escape(post["title"]) in r.text


def test_static_pages_served():
    for lang, stems in PAGES_INDEX.items():
        for stem in stems:
            assert client.get(f"/pages/{lang}/{stem}").status_code == 200


def test_missing_post_is_404():
    r = client.get(f"/posts/{DEFAULT_LANG}/no-existe")
    assert r.status_code == 404
    assert "site-nav" in r.text  # styled, not a bare Starlette 404


def test_missing_page_is_404():
    assert client.get(f"/pages/{DEFAULT_LANG}/missing-page").status_code == 404


def test_unknown_path_is_styled_404():
    paths = ["/whatever"] + [f"/{l}/whatever" for l in SUPPORTED_LANGS if l != DEFAULT_LANG]
    for path in paths:
        r = client.get(path)
        assert r.status_code == 404
        assert "site-nav" in r.text


def test_no_slash_redirects():
    pairs = []
    for lang in SUPPORTED_LANGS:
        pairs.append((_tags_root(lang).rstrip("/"), _tags_root(lang)))
        pairs.append((f"/posts/{lang}", f"/posts/{lang}/"))
        if lang != DEFAULT_LANG:
            pairs.append((f"/{lang}", f"/{lang}/"))
    for path, target in pairs:
        r = client.get(path, follow_redirects=False)
        assert r.status_code in (301, 302, 303, 307, 308)
        assert target in r.headers.get("location", "")


# ── Language handling ──────────────────────────────────────────────────────────

def test_lang_button_hidden_with_one_language(monkeypatch):
    monkeypatch.setattr(main, "SUPPORTED_LANGS", [DEFAULT_LANG])
    assert "lang-btn" not in main.to_xml(main.nav_bar(DEFAULT_LANG, "/"))


def test_html_lang_attribute():
    for lang in SUPPORTED_LANGS:
        assert f'lang="{lang}"' in client.get(main._lang_root(lang)).text


def test_theme_cookie_applied_server_side():
    themed = TestClient(main.app, cookies={"theme": "light"})
    r = themed.get("/")
    assert 'data-theme="light"' in r.text


def test_translation_toggle_hrefs():
    if not TRANSLATIONS:
        pytest.skip("no post declares a translation")
    (lang, slug), others = next(iter(TRANSLATIONS.items()))
    r = client.get(f"/posts/{lang}/{slug}")
    for other_lang, other_slug in others.items():
        assert f'href="/posts/{other_lang}/{other_slug}" class="lang-btn"' in r.text


# ── Tags ───────────────────────────────────────────────────────────────────────

def test_tags_index_localized():
    for lang in SUPPORTED_LANGS:
        assert UI_STRINGS[lang]["all_tags"] in client.get(_tags_root(lang)).text


def test_tag_view_by_slug():
    if not TAG_INDEX:
        pytest.skip("no tagged content")
    tag = next(iter(TAG_INDEX))
    slug = TAG_SLUGS[tag]
    assert SLUG_TAGS[slug] == tag
    for lang in SUPPORTED_LANGS:
        r = client.get(f"{_tags_root(lang)}{slug}")
        assert r.status_code == 200
        assert UI_STRINGS[lang]["tag_posts"] in r.text


def test_unknown_tag_slug_is_404():
    assert client.get(f"{_tags_root(DEFAULT_LANG)}nosuchtag").status_code == 404


# ── Feeds, sitemap, robots ─────────────────────────────────────────────────────

def test_rss_feeds():
    feeds = [(f"/feed/{lang}.xml", lang) for lang in SUPPORTED_LANGS]
    feeds.append(("/feed.xml", DEFAULT_LANG))
    for path, lang in feeds:
        r = client.get(path)
        assert r.status_code == 200
        channel = ET.fromstring(r.text).find("channel")
        assert channel.find("lastBuildDate") is not None
        assert main.SITE_URL in channel.find("link").text
        items = channel.findall("item")
        assert len(items) == min(len(main.get_all_posts(lang)), main.RSS_ITEMS)
        if items:
            assert items[0].find(f"{CONTENT_NS}encoded") is not None


def test_sitemap():
    r = client.get("/sitemap.xml")
    locs = [u.findtext(f"{SITEMAP_NS}loc") for u in ET.fromstring(r.text).findall(f"{SITEMAP_NS}url")]
    expected = []
    for lang in SUPPORTED_LANGS:
        expected.append(main._lang_root(lang))
        expected += [f"/pages/{lang}/{stem}" for stem in PAGES_INDEX[lang]]
        expected += [f"/posts/{lang}/{p['slug']}" for p in main.get_all_posts(lang)]
    for e in expected:
        assert f"{main.SITE_URL}{e}" in locs


def test_robots_txt():
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert f"Sitemap: {main.SITE_URL}/sitemap.xml" in r.text


# ── Static files & security ────────────────────────────────────────────────────

def test_static_assets():
    for f in ("/static/custom.css", "/static/theme.css",
              "/static/vendor/pico.classless.min.css",
              "/static/fonts/inter-var.woff2", "/static/favicon.svg",
              "/static/pygments.css"):
        assert client.get(f).status_code == 200


def test_layout_uses_tokens():
    "Widths and gutters come from overridable variables, not fixed values."
    css = client.get("/static/custom.css").text
    for token in ("--content-width", "--gutter", "--toc-width", "--measure", "--font-size-max"):
        assert f"var({token})" in css, token
    assert "900px" not in css


def _raw_status(path: str) -> int:
    "Call the app with a literal (undecoded) path, bypassing any client normalization."
    scope = {"type": "http", "http_version": "1.1", "method": "GET",
             "path": path, "raw_path": path.encode(), "query_string": b"",
             "headers": [], "root_path": "", "scheme": "http",
             "client": ("testclient", 50000), "server": ("testserver", 80)}
    status = {}
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    async def send(msg):
        if msg["type"] == "http.response.start":
            status["code"] = msg["status"]
    asyncio.run(main.app(scope, receive, send))
    return status["code"]


def test_path_traversal_blocked():
    for path in ("/static/../config.py", "/static/../.sesskey",
                 "/static/../../etc/passwd", "/static/..%2fmain.py"):
        assert _raw_status(path) == 404, path


def test_page_slug_traversal_blocked():
    assert _raw_status(f"/pages/{DEFAULT_LANG}/..") == 404


def test_security_headers():
    r = client.get("/")
    assert "default-src 'self'" in r.headers.get("content-security-policy", "")
    assert r.headers.get("x-content-type-options") == "nosniff"


def test_cache_headers():
    r = client.get("/static/fonts/inter-var.woff2")
    assert "immutable" in r.headers.get("cache-control", "")
    r = client.get("/static/custom.css")
    assert r.headers.get("cache-control") == "no-cache"
    r = client.get("/static/custom.css", headers={"if-none-match": r.headers["etag"]})
    assert r.status_code == 304


def test_theme_css_loads_after_custom_css():
    html = client.get("/").text
    assert html.index("/static/custom.css") < html.index("/static/theme.css")


def test_pygments_rules_scoped_to_theme():
    rules = [l for l in main.PYGMENTS_CSS.splitlines() if l.strip()]
    assert rules
    for line in rules:
        assert line.startswith(("[data-theme='dark'] .highlight",
                                "[data-theme='light'] .highlight")), line
    # the --code-bg override must come after the style's own dark background
    assert rules[-1] == "[data-theme='dark'] .highlight { background: var(--code-bg); }"


def test_no_external_asset_urls():
    html = client.get("/").text
    assert "cdn.jsdelivr.net" not in html
    assert "fonts.googleapis.com" not in html


# ── Series ──────────────────────────────────────────────────────────────────────

def test_series_nav_links_neighbors():
    linked = False
    for members in main.SERIES_INDEX.values():
        for post in members:
            prev_p, next_p = main.get_series_neighbors(post)
            if next_p:
                r = client.get(f"/posts/{post['lang']}/{post['slug']}")
                assert 'class="series-nav"' in r.text
                assert f"/posts/{next_p['lang']}/{next_p['slug']}" in r.text
                linked = True
            if prev_p:
                r = client.get(f"/posts/{post['lang']}/{post['slug']}")
                assert 'class="series-nav"' in r.text
                assert f"/posts/{prev_p['lang']}/{prev_p['slug']}" in r.text
                linked = True
    if not linked:
        pytest.skip("no series with neighbors in content")


def test_series_label_shows_part():
    for members in main.SERIES_INDEX.values():
        for post in members:
            if post["series_part"]:
                r = client.get(f"/posts/{post['lang']}/{post['slug']}")
                s = UI_STRINGS[post["lang"]]
                assert f'{s["series_part"]} {post["series_part"]}' in r.text
                return
    pytest.skip("no series with parts in content")


# ── Pagination ──────────────────────────────────────────────────────────────────

def test_pagination_matches_post_count():
    total = len(main.get_all_posts(DEFAULT_LANG))
    html = client.get("/").text
    if total <= main.POSTS_PER_PAGE:
        assert 'class="pagination"' not in html
    else:
        assert 'class="pagination"' in html


def test_out_of_range_page_is_404():
    total = len(main.get_all_posts(DEFAULT_LANG))
    last_page = max(1, -(-total // main.POSTS_PER_PAGE))
    assert client.get(f"/?page={last_page + 1}").status_code == 404
    assert client.get("/?page=0").status_code == 404


def test_pagination_nav():
    orig = main.POSTS_PER_PAGE
    main.POSTS_PER_PAGE = 2
    try:
        xml = main.to_xml(main.pagination_nav(DEFAULT_LANG, 1, 5))
        assert "page=2" in xml and "page=1" not in xml
        xml = main.to_xml(main.pagination_nav(DEFAULT_LANG, 2, 5))
        assert "page=1" in xml and "page=3" in xml
        assert main.pagination_nav(DEFAULT_LANG, 1, 2) == ""
    finally:
        main.POSTS_PER_PAGE = orig
