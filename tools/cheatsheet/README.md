# UltraPlot cheatsheet and docs icons

This folder contains the editable A3 draw.io cheatsheet and the renderers shared
with the documentation’s visual plot-type index.

- `ultraplot_cheatsheet.drawio`: the edited, self-contained diagram.
- `ultraplot_cheatsheet.svg` / `.png`: its existing previews.
- `drawio.py`: the reproducible layout generator, with serif text, Python
  highlighting, embedded SVG plots and editable colormap swatches.
- `fix_svg_seams.py`: repairs colorbar seams in an edited diagram without
  changing text, geometry or layout.
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
