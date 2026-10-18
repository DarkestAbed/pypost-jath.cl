---
title: "Demo de características: Código, Índice y Series"
date: 2026-03-25
published: true
slug: demo-caracteristicas
description: "Demuestra el resaltado de sintaxis, el índice de contenidos y la navegación de series."
tags: [demo, python]
translations: {en: features-demo}
series: "Primeros pasos"
series_part: 1
toc: true
---

Este artículo muestra las tres características avanzadas de pypost: **resaltado de sintaxis del lado del servidor**, **índice de contenidos generado automáticamente** y **navegación de series**.

## Resaltado de sintaxis

Los bloques de código son resaltados por [Pygments](https://pygments.org) en el servidor — sin JavaScript. Solo rodea el código con el nombre del lenguaje.

```python
def cargar_articulos(lang: str) -> list[dict]:
    base = Path("posts") / lang
    articulos = []
    for ruta in base.glob("*.md"):
        articulo = fm.load(str(ruta))
        if not articulo.get("published", False):
            continue
        articulos.append({"slug": articulo["slug"], "title": articulo["title"]})
    return sorted(articulos, key=lambda p: p["date"], reverse=True)
```

Se soportan múltiples lenguajes:

```bash
uv run python main.py
# Inicia en http://localhost:8000
```

```yaml
title: Mi artículo
date: 2026-03-25
published: true
tags: [python, demo]
```

## Índice de contenidos

Cuando un artículo tiene **3 o más encabezados h2/h3**, se genera automáticamente una barra lateral con el índice. Lo estás viendo ahora mismo. Establece `toc: false` en el frontmatter para desactivarlo en un artículo específico.

### Comportamiento del índice

- Los encabezados h2 se convierten en entradas de nivel superior
- Los encabezados h3 aparecen indentados bajo su h2 padre
- La barra lateral es pegajosa en escritorio
- En móvil aparece como un bloque plano sobre el contenido

## Navegación de series

Los artículos de la misma serie se enlazan con navegación anterior/siguiente. Configura `series` y `series_part` en el frontmatter:

```yaml
series: "Primeros pasos"
series_part: 1
```

La barra de navegación al final de este artículo mostrará un enlace "Siguiente →" si existe una parte 2. Funciona entre idiomas — las partes pueden estar en distintos idiomas dentro de la misma serie.

### Añadir más partes

Crea un nuevo artículo con el mismo valor de `series` y el siguiente número de `series_part`. pypost construye el índice de series al iniciar e inyecta la navegación automáticamente.
