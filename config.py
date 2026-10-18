import os

# ── Site identity ─────────────────────────────────────────────────────────────
SITE_NAME        = "Javier Thompson punto Ce Ele"
SITE_DESCRIPTION = "El lugar donde estacion\u00e9 la Madre Nodriza"
AUTHOR           = "Javier Thompson"
PORT             = int(os.environ.get("PORT", 8000))
SITE_URL         = os.environ.get("SITE_URL", "https://blog.jath.cl")
SITE_IMAGE       = os.environ.get("SITE_IMAGE", "")  # absolute URL for og:image / twitter:image (optional)

# ── Language ──────────────────────────────────────────────────────────────────
DEFAULT_LANG    = "es"  # serves at /  (other langs at /{lang}/)
SUPPORTED_LANGS = ["es"]
POSTS_PER_PAGE  = int(os.environ.get("POSTS_PER_PAGE", 10))

# ── Feeds & code highlighting ─────────────────────────────────────────────────
RSS_ITEMS            = 20          # posts per RSS feed
PYGMENTS_STYLE_DARK  = "monokai"   # code theme in dark mode
PYGMENTS_STYLE_LIGHT = "friendly"  # code theme in light mode

# ── Navigation links per language ─────────────────────────────────────────────
NAV_LINKS = {
    "es": [("Blog", "/"), ("Temas", "/tags/"), ("Sobre mí", "/pages/es/about")],
}

# ── UI strings ────────────────────────────────────────────────────────────────
UI_STRINGS = {
    "es": {
        "read_more":      "Leer →",
        "back_to_blog":   "← Volver",
        "toggle_theme":   "☀ / ☾",
        "switch_lang":    "English",
        "not_found":      "Página no encontrada.",
        "not_found_detail": "Este artículo no existe o fue movido.",
        "reading_time":   "min de lectura",
        "all_tags":       "Todos los temas",
        "no_posts":       "Sin publicaciones aún.",
        "series_prev":    "← Anterior",
        "series_next":    "Siguiente →",
        "series_part":    "Parte",
        "toc_label":      "En este artículo",
        "tag_posts":      "Artículos sobre",
        "subtitle":       "Publicaciones recientes.",
        "newer_posts":    "← Recientes",
        "older_posts":    "Anteriores →",
        "footer":         SITE_NAME,
        "rss_title":      f"{SITE_NAME} — Blog",
        "rss_description": SITE_DESCRIPTION,
    },
}
