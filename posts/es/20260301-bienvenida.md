---
title: "Bienvenido a jath.cl"
date: 2026-03-01
author: jath
published: true
slug: bienvenida
description: "El primer artículo de este blog técnico. Qué esperar, por qué existe, y cómo está construido."
tags: [meta, fasthtml, python]
toc: false
#   - meta
#   - fasthtml
#   - python
---

Este blog existe porque escribir es la forma más honesta de verificar que realmente entiendes algo.

## Por qué otro blog técnico

Hay miles de blogs de tecnología. La mayoría están optimizados para SEO, no para el lector. Aquí el objetivo es distinto: ideas escritas en extenso, con vueltas innecesarias, como una conversación. Porque siento mucho que eso falta: una _conversación_.

Siempre pensé en escribir en inglés. Mal que mal, es el idioma en el que toda la tecnología se escribe. Pero aquí, en este lugar, se habla español; como primer idioma, al menos.

## Stack

Este blog es una pequeña proeza técnica, también. No tiene un CMS detrás, es todo código y nada WYSIWYG.

El sitio está construido con:

- **Python 3.13**
- **FastHTML** — servidor web que genera HTML directamente desde Python
- **PicoCSS** — base de estilos mínima y accesible
- **Mistune** — parser de Markdown con soporte para tablas y listas de tareas
- **Pygments** — syntax highlighting en el servidor, sin JavaScript

No hay framework de JavaScript. No hay base de datos. Los posts son archivos de texto plano que se parsean en tiempo de compilación.

```python
# Así se ve el cargador de posts
def load_posts(lang: str) -> list[dict]:
    base = Path("posts") / lang
    posts = []
    for path in base.glob("*.md"):
        post = fm.load(str(path))
        if not post.get("published", False):
            continue
        posts.append({
            "slug": post.get("slug") or slugify(post.get("title", "")),
            "title": post.get("title", path.stem),
            "content_html": md(post.content),
            # ...
        })
    return sorted(posts, key=lambda p: p["date"], reverse=True)
```

## Qué viene

- Artículos sobre infraestructura, tecnología moderna y sistemas de ayer y hoy
- Harto de Python
- Herramientas de línea de comandos y automatización
- Ocasionalmente: reflexiones sobre el oficio de escribir software

Bienvenidos a mi pequeña casita técnica en internet.
