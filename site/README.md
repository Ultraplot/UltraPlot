# UltraPlot Astro Docs Prototype

This directory is a migration prototype for moving docs presentation to
Astro/Astrowind without splitting docs into a separate repository.

## What This Prototype Includes

- Astro content-based docs pages (`src/content/docs`).
- A Python API extraction script:
  `../tools/docs/generate_astro_api.py`.
- A dynamic docs route that renders generated markdown pages.

## Local Usage

```bash
cd site
npm install
npm run dev
```

The `docs:sync` step runs before `dev` and `build` and regenerates API pages
from the `ultraplot/` package source.

## Migration Strategy

1. Keep source docs and package in one repo.
2. Keep Sphinx temporarily for existing pages while Astro matures.
3. Generate API markdown into Astro content as part of CI.
4. Gradually port narrative pages from `docs/*.rst` to `site/src/content/docs`.
