# UltraPlot cheatsheet and docs icons

This folder contains the editable A3 draw.io cheatsheet and the renderers shared
with the documentation’s visual plot-type index.

- `ultraplot_cheatsheet.drawio`: the edited, self-contained six-page diagram.
  Page 1 is the visual reference; page 2 pairs runnable Python recipes with
  their rendered results. Page 2 is taller to preserve code and plot legibility.
  Page 3 adapts Matplotlib's dense five-column cheatsheet to UltraPlot: anatomy,
  plotting, scales, projections, ticks, guides, formatting and physical units.
  The final three pages provide Beginner, Intermediate and Advanced entry points.
- `ultraplot_cheatsheet.svg` / `.png`: the first-page previews.
- `ultraplot_cheatsheet-code.svg` / `.png`: the code-page previews.
- `ultraplot_cheatsheet-reference.svg` / `.png`: the quick-reference previews.
- `drawio.py`: the reproducible layout generator, with serif text, Python
  highlighting, embedded SVG plots and editable colormap swatches.
- `fix_svg_seams.py`: repairs colorbar seams in an edited diagram without
  changing text, geometry or layout.
- `code_page.py`: the second-page recipes, cached SVG previews, layout and
  selective page updater. Previews use the printed data and plotting calls,
  with presentation defaults adjusted for their size on the page.
- `reference_page.py`: the third-page layout and cached UltraPlot renders for
  the figure anatomy, scales, tick locators, tick formatters, lines and markers.
- `level_pages.py`: the task-based learning pages, with larger reading text,
  category navigation and result → key argument → minimal code cards.
- `ultraplot_cheatsheet-beginner.svg`, `-intermediate.svg`, `-advanced.svg`:
  previews of the learning pages (with ignored PNG companions).
- `docs_index.py`: validates API links and generates `docs/plot_types.rst` plus
  its PNG thumbnails in `docs/_static/plot_types/`.
- `parts/icons.py`: the plot-type registry and renderers used by the docs.
- `parts/features.py`: the feature icons used by the draw.io sheet.
- `parts/drawio_details.py`: sharing comparisons, legends, geography and
  registered colormap samples.
- `parts/common.py`: shared style, sample data and paired SVG/PNG exports.
- `assets/`: generated assets; safe to regenerate.

## Build

```bash
python tools/cheatsheet/build.py             # assets + docs index
python tools/cheatsheet/build.py --figures   # assets only
python tools/cheatsheet/build.py --docs      # docs; render missing icons
```

These commands preserve the edited draw.io file and its previews. To generate a
fresh layout explicitly, choose a separate output path:

```bash
python tools/cheatsheet/build.py --drawio /tmp/ultraplot-regenerated.drawio
```

The diagram generator reads existing assets. Render them first on a clean
checkout. Regenerating at the edited diagram’s path replaces manual edits, so
use a separate filename when comparing changes. Update embedded images in the
edited diagram selectively when preserving manual edits.

Fresh layouts include all six pages. To regenerate only the code page, preserving
the first page exactly (this replaces manual edits on page 2):

```bash
python tools/cheatsheet/code_page.py --replace-page --png
```

Without `--replace-page`, the command appends the code page only if it does not
already exist. The exact snippets printed on page 2 can be checked independently:

```bash
MPLBACKEND=Agg python tools/cheatsheet/code_page.py --check
```

This runs each recipe with the shared sample data and renders it in a temporary
directory. Map recipes require Cartopy and its geographic data.

To regenerate page 3 while preserving both earlier pages:

```bash
python tools/cheatsheet/reference_page.py --replace-page --png
```

Page 3 follows the visual organization of the [Matplotlib cheatsheet](https://matplotlib.org/cheatsheets/_images/cheatsheets-1.png),
using UltraPlot APIs and feature-specific replacements for generic animation,
keyboard-shortcut and style sections. It is a compact API reference; page 2
contains complete runnable examples. Existing rendered assets are reused;
additional previews are cached and regenerated when their source changes.

## Learning pages

The appended pages preserve the existing reference material while offering
clearer entry points:

- **Beginner:** create, label and explain a figure; six everyday tasks.
- **Intermediate:** arrange, link and extend axes; six layout and guide tasks.
  Sharing is explained with colored range groups, rather than tiny repeated plots.
- **Advanced:** eight tasks grouped by encodings, distributions and flows,
  polar/diagnostic plots, path annotations, plot variants and guide layout.

Category colors match the navigation and card headers. Each card presents its
result, searchable API/argument, minimal code and a short interpretation. The
plot gallery is grouped by purpose. Run the common setup before a card; all
20 printed snippets can be executed by the check command.

```bash
python tools/cheatsheet/level_pages.py --png  # append the three pages once
python tools/cheatsheet/level_pages.py --replace-pages --png
MPLBACKEND=Agg python tools/cheatsheet/level_pages.py --check
```

The replacement command updates only the three learning pages. The first three
pages, including manual edits, are preserved byte-for-byte.

Individual renderers also run directly:

```bash
python tools/cheatsheet/parts/icons.py
python tools/cheatsheet/parts/features.py
python tools/cheatsheet/parts/drawio_details.py
```

Rendering requires UltraPlot and the optional libraries used by the selected
plot types, including pandas, networkx and cartopy for maps. Layout generation
requires Pygments, DejaVu Serif and DejaVu Sans Mono; PNG previews require
CairoSVG. SVG plots preserve their aspect ratios and remain sharp when scaled;
plot contents are embedded images, while page text and boxes are editable.

## Docs and packaging

`docs/_scripts/build_plot_types.py` invokes `docs_index.py` during the docs build.
The Python icon registry is the source of truth; no document-engine manifests
are needed. Missing icons are checked by filename, including PNGs required by
the docs rather than just their SVG counterparts.

The cheatsheet stays in the repository but is excluded from wheels and source
distributions. Docs builds should run from a repository checkout.

To repair SVG seams without rebuilding a manually edited diagram:

```bash
python tools/cheatsheet/fix_svg_seams.py path/to/sheet.drawio
```
