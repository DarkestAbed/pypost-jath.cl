---
title: Bienvenido a pypost
date: 2026-03-25
published: true
slug: demo-bienvenida
description: "Un framework de blog limpio y desplegable con Python, FastHTML y Markdown."
tags: [meta, fasthtml]
# translations: {en: welcome}
---

**pypost** es un framework de blog minimalista construido sobre [FastHTML](https://fastht.ml), [Mistune](https://mistune.lepture.com) y [Pygments](https://pygments.org). Sin paso de compilación, sin base de datos — solo archivos Markdown y Python.

## Cómo funciona

Los artículos son archivos `.md` simples con frontmatter YAML. Deja un archivo en `posts/es/` o `posts/en/` y aparece en el blog inmediatamente tras reiniciar el servidor.

```
posts/
├── en/
│   └── my-post.md
└── es/
    └── mi-articulo.md
```

## Campos del frontmatter

| Campo | Requerido | Descripción |
|---|---|---|
| `title` | sí | Título del artículo |
| `date` | sí | Fecha de publicación (`YYYY-MM-DD`) |
| `published` | sí | Poner `true` para que sea visible |
| `slug` | no | Slug en la URL (se genera desde el título) |
| `description` | no | Se muestra en las tarjetas y en RSS |
| `tags` | no | Lista de etiquetas |
| `series` | no | Nombre de la serie para artículos multiparte |
| `series_part` | no | Número de parte dentro de la serie |
| `toc` | no | Poner `false` para deshabilitar el índice automático |

## ¿Qué sigue?

Lee el artículo **Demo de características** para ver el resaltado de sintaxis, el índice de contenidos y la navegación de series en acción.
