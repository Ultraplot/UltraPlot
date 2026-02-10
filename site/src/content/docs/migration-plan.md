---
title: "Migration Plan"
description: "Implementation plan for moving UltraPlot docs to Astro/Astrowind."
order: 2
---

# Migration Plan

This prototype keeps package and docs in one repository and introduces a script-driven API pipeline.

## Why No Repo Split Is Required

- API and examples are tightly coupled to `ultraplot/` source.
- CI can generate docs content directly from the checked-out commit.
- Versioning remains aligned with package tags/branches.

## Required Build Steps

1. Run API extraction script to generate markdown from package source.
2. Build Astro site from generated + hand-authored markdown.
3. Publish static output and serve route redirects for legacy Sphinx links.

## Optional Transitional Setup

- Keep Sphinx docs as source of truth while Astro pages are migrated.
- Maintain a redirect table from old `.html`/`.rst` routes to `/docs/*`.
