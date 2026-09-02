# UltraPlot cheatsheet

Two A3 pages in the spirit of [matplotlib's cheatsheets](https://matplotlib.org/cheatsheets/),
and built the same way: small Python scripts render the figures, and a document
engine assembles them. Matplotlib uses LaTeX for the assembly step; this uses
[Typst](https://typst.app), which keeps the layout in one readable file.

```
tools/cheatsheet/
├── build.py         # render the parts, compile the sheets, write the docs page
├── cheatsheet.typ   # the three-page sheet: palette, panels, grid, copy
├── poster.typ       # the companion plot-type poster (A3, every command)
├── docs_index.py    # writes docs/plot_types.rst from the same registry
├── parts/
│   ├── common.py    # shared drawing style and the save() helper
│   ├── layout.py    # axis sharing, mosaics, titles, panels
│   ├── icons.py     # one thumbnail per plotting command
│   ├── features.py  # one thumbnail per UltraPlot-only feature
│   ├── color.py     # bundled colormap tables, cycles, norms, palette.typ
│   ├── guides.py    # colorbars, legends, statistical indicators
│   └── geo.py       # projections and map features
└── assets/          # generated; safe to delete
```

## Build

```bash
micromamba run -n ultraplot-dev python tools/cheatsheet/build.py
```

writes, at the repository root, `ultraplot_cheatsheet.pdf` (three A3 pages),
`ultraplot_plot_types.pdf` (the one-page poster), PNGs of each, and
`docs/plot_types.rst` with its icons in `docs/_static/plot_types/`. Three flags
help while iterating:

```bash
python tools/cheatsheet/build.py --figures   # re-render the figures only
python tools/cheatsheet/build.py --typst     # re-lay out the sheets only
python tools/cheatsheet/build.py --docs      # rewrite the docs page only
```

Each part script also runs on its own, which is the fastest loop when you are
working on one figure:

```bash
cd tools/cheatsheet/parts && python icons.py
```

Requirements: an environment with UltraPlot, cartopy (for `geo.py`), networkx
and pandas (for a few icons), plus the `typst` binary and the IBM Plex fonts.
`geo.py` skips itself with a note if cartopy is missing rather than failing the
build.

## Conventions

- **Two icon sets, three kinds.** `icons.py` answers "what can I draw" (one
  thumbnail per plotting command); `features.py` answers "what does UltraPlot
  add", following the sections of `docs/why.rst`. Both registries classify each
  entry as `same` (matplotlib has the command), `better` (matplotlib can do it,
  but you assemble it yourself) or `new` (no equivalent), and name the
  matplotlib counterpart for the middle case. That distinction is the honest
  one: most of UltraPlot's value is the middle case, and the page says so
  rather than claiming everything is unprecedented.
- **The galleries are generated.** Each registry writes a Typst manifest —
  `assets/icons.typ` and `assets/features.typ` — and both `cheatsheet.typ` and
  `poster.typ` build their grids by filtering those. Adding an icon means adding
  one registry entry; the sheets, the poster and the docs page pick it up on the
  next build. The cheatsheet shows the thirty entries flagged `FEATURED`; the
  poster shows all of them.
- **One drawing vocabulary.** `common.py` holds the sample data every icon draws
  from — one wave, one cloud, one field, one set of categories — plus the colour
  roles and the stroke weights that survive being scaled to 10 mm. Two icons
  then differ only where the commands differ, which is the whole point of a
  small-multiples gallery.
- **Every figure is the real command.** No mock-ups: the `contourf` thumbnail is
  `ax.contourf`, the sharing comparison is two real figures with `share` set
  differently, and the colormap tables are read from
  `ultraplot.demos.CMAP_TABLE` — the same source `uplt.show_cmaps()` uses, so
  the sheet cannot drift from what is actually registered.
- **The palette comes from the plots.** `parts/color.py` writes
  `assets/palette.typ` with real `batlow` samples; the section rails and the
  masthead gradient in `cheatsheet.typ` import it.
- **Parts do not know about the page.** A part renders one figure at a sensible
  size and saves it. All sizing, cropping and captioning happens in Typst.
- **Panel heights are set per band.** `sheet(weights: (...))` gives each band a
  share of the page, and every panel in a band matches its neighbours. If a
  panel overflows, either trim its content or raise that band's weight — the
  weights are the tuning knob.

## Adding a panel

1. If it needs a figure, add a function to the relevant part script, save with
   `save(fig, "name.png")`, and check it renders on its own.
2. Add a `panel(...)` block to `cheatsheet.typ` in the right band.
3. Rebuild and look at the PNGs. Content that overflows its panel is visible
   immediately — Typst does not clip it, it runs over the frame.
