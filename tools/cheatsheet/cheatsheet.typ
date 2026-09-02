// UltraPlot cheatsheet — layout and typography.
//
// Every figure on these pages is rendered by a script in parts/ and dropped in
// assets/. This file only arranges them, the way matplotlib's own cheatsheets
// assemble their generated panels. Build with tools/cheatsheet/build.py.

#import "assets/palette.typ": batlow, rails
#import "assets/features.typ": features
#import "assets/icons.typ": commands

// ---------------------------------------------------------------- palette
#let paper = rgb("#f2f4f7")
#let panelbg = rgb("#ffffff")
#let ink = rgb("#0f151d")
#let inksoft = rgb("#4a5663")
#let inkfaint = rgb("#8593a1")
#let rule = rgb("#dbe1e8")
#let sunk = rgb("#f0f3f7")
#let accent = rgb("#3b638c")
#let badgecolor = rgb("#a8414f")
#let codeink = rgb("#243040")

// ---------------------------------------------------------------- page
#set page(
  paper: "a3",
  flipped: true,
  margin: (x: 10mm, top: 8mm, bottom: 9mm),
  fill: paper,
  footer: context [
    #set text(size: 6pt, fill: rgb("#8593a1"))
    #grid(columns: (1fr, auto), align: (left + horizon, right + horizon),
      [Figures rendered by #raw("tools/cheatsheet/parts/*.py"), assembled by
       #raw("cheatsheet.typ") · rails and swatches are real #raw("batlow") samples
       · ultraplot.readthedocs.io],
      [#counter(page).display() / #counter(page).final().first()],
    )
  ],
  footer-descent: 4mm,
)
#set text(font: ("IBM Plex Sans", "DejaVu Sans"), size: 7.4pt, fill: ink)
#set par(leading: 0.52em, spacing: 0.62em, justify: false)

// Code is set plain rather than syntax-coloured: a cheatsheet is scanned, and
// four token colours per block fight the section rails for attention.
#show raw: set text(font: ("IBM Plex Mono", "DejaVu Sans Mono"), size: 6.3pt, fill: codeink)
#show raw.where(block: true): block.with(
  fill: sunk,
  inset: (x: 4.5pt, y: 4pt),
  radius: 2pt,
  width: 100%,
)

// ---------------------------------------------------------------- pieces
#let chip(fill-color, text-color, label) = box(
  fill: fill-color,
  inset: (x: 3pt, y: 1.2pt),
  radius: 1.5pt,
  text(size: 5.2pt, font: "IBM Plex Mono", fill: text-color, weight: 500, label),
)

#let badge = chip(rgb("#fbeef0"), badgecolor, "de novo")
#let betterbadge = chip(rgb("#e9eff6"), accent, "enhancement")

#let note(body) = text(size: 6.2pt, fill: inksoft, style: "italic", body)

// One cheatsheet cell. Panels stretch to their row so a section reads as a
// tiled band rather than a ragged shelf.
#let panel(title, rail, body, kind: none) = block(
  fill: panelbg,
  stroke: (top: 2pt + rail, rest: 0.4pt + rule),
  radius: 2pt,
  inset: (x: 7pt, y: 6pt),
  width: 100%,
  height: 100%,
  breakable: false,
)[
  #grid(
    columns: (1fr, auto),
    align: (left + horizon, right + horizon),
    text(size: 8.4pt, weight: 600, tracking: -0.01em, title),
    if kind == "new" { badge } else if kind == "better" { betterbadge } else { none },
  )
  #v(1.5pt)
  #line(length: 100%, stroke: 0.4pt + rail.lighten(55%))
  #v(4pt)
  #body
]

#let band(label, rail, note-text) = block(width: 100%, above: 0pt, below: 3.5pt)[
  #grid(
    columns: (auto, 1fr, auto),
    column-gutter: 5pt,
    align: (left + horizon, left + horizon, right + horizon),
    box(width: 7pt, height: 7pt, radius: 1pt, fill: rail),
    text(size: 10.5pt, weight: 700, tracking: 0.04em, upper(label)),
    text(size: 6.8pt, fill: inkfaint, note-text),
  )
  #v(2pt)
  #line(length: 100%, stroke: 0.6pt + rule)
]

#let shot(path, caption: none, width: 100%) = block(width: 100%)[
  #align(center, image(path, width: width))
  #if caption != none [ #v(2pt) #note(caption) ]
]

#let newcolor = badgecolor
#let bettercolor = accent

// An UltraPlot-exclusive thumbnail gets a full outline and a corner badge, not
// just a coloured caption: it is the one thing on the page you cannot get from
// matplotlib at all, so it should be findable at arm's length.
#let exclusive-badge = box(
  fill: newcolor,
  inset: (x: 2.2pt, y: 0.7pt),
  radius: (bottom-left: 1.5pt),
  text(size: 4.2pt, font: "IBM Plex Sans", fill: white, weight: 600, tracking: 0.05em, "EXCLUSIVE"),
)

#let thumb(path, kind) = box(
  fill: panelbg,
  stroke: if kind == "new" { 1pt + newcolor } else if kind == "better" { (top: 1.6pt + bettercolor, rest: 0.4pt + rule) } else { 0.4pt + rule },
  radius: 1.5pt,
  inset: 0pt,
  clip: true,
  width: 100%,
)[
  #image(path, width: 100%)
  #if kind == "new" { place(top + right, exclusive-badge) }
]

// A command thumbnail. The caption colour says whether matplotlib has the
// command already, can be made to do it, or has nothing like it.
#let icon(entry) = block(width: 100%, breakable: false)[
  #thumb("assets/icons/" + entry.file + ".png", entry.kind)
  #v(1.5pt)
  #align(center, text(
    size: 5.4pt,
    font: "IBM Plex Mono",
    fill: if entry.kind == "new" { newcolor } else if entry.kind == "better" { bettercolor } else { inksoft },
    entry.name,
  ))
  #if entry.mpl != none [
    #v(0.8pt)
    #align(center, text(size: 4.5pt, fill: inkfaint, style: "italic", entry.mpl))
  ]
]

#let cells(..items) = grid(
  columns: (1fr,) * 4,
  rows: (100%,),
  gutter: 3.2mm,
  ..items,
)

// A page is bands and panel rows alternating. Panel rows are fractional so the
// page always fills and every panel in a band matches its neighbours' height;
// the weights below say which band needs the most room.
#let sheet(weights: none, ..blocks) = {
  let items = blocks.pos()
  let rows = ()
  let index = 0
  let band-index = 0
  for _ in items {
    if calc.even(index) {
      rows.push(auto)
    } else {
      let weight = if weights == none { 1.0 } else { weights.at(band-index) }
      rows.push(weight * 1fr)
      band-index += 1
    }
    index += 1
  }
  grid(columns: 1, rows: rows, row-gutter: 3.5mm, ..items)
}

// ---------------------------------------------------------------- masthead
#let masthead(subtitle) = block(width: 100%, below: 5pt)[
  #grid(
    columns: (auto, 1fr, auto),
    column-gutter: 10mm,
    align: (left + bottom, left + bottom, right + bottom),
    [
      #text(size: 34pt, weight: 700, tracking: -0.02em, "UltraPlot")
      #v(-11pt)
      #text(size: 10pt, weight: 600, fill: accent, tracking: 3.6pt, "CHEATSHEET")
    ],
    text(size: 7.8pt, fill: inksoft, subtitle),
    text(size: 7pt, font: "IBM Plex Mono", fill: inkfaint)[
      uplt.subplots() → fig, axs \
      axs.format(…) → everything \
      fig.save(…) → done
    ],
  )
  #v(4pt)
  #rect(width: 100%, height: 3.5pt, stroke: none, radius: 1pt,
        fill: gradient.linear(..batlow))
]

// ================================================================ PAGE ONE
#masthead[
  Everything assumes `import ultraplot as uplt`. UltraPlot subclasses matplotlib's
  `Figure`, `Axes` and `GridSpec`, so every matplotlib call still works — these pages
  are what UltraPlot *adds*, and #badge marks what has no matplotlib equivalent.
  #linebreak()
  Page 1 gets a figure laid out and labelled. Page 2 is what you can draw in it.
]

#sheet(
  weights: (1.00, 0.92, 1.08),
  band("Sharing and layout", rails.at(0), "the defaults that change a multi-panel figure before you have formatted anything"),
  cells(
    panel("Axis sharing is on", rails.at(0), kind: "better")[
      #grid(columns: (1fr, 1fr), gutter: 4pt,
        shot("assets/sharing_off.png"),
        shot("assets/sharing_on.png"),
      )
      #v(1pt)
      #grid(columns: (1fr, 1fr), gutter: 4pt,
        align(center, note[`share=False`]),
        align(center, note[`share=True`, the default]),
      )
      #v(4pt)
      ```
      uplt.subplots(nrows=2, ncols=2, share=True, span=True)
      # True | False | 'labels' | 'limits' | 0 | 1 | 2 | 3
      ```
      #note[Limits, ticks and labels are shared per row and column, and repeated labels collapse into one spanning label.]
    ],
    panel("Mosaic layouts", rails.at(0), kind: "better")[
      #shot("assets/mosaic.png", width: 88%)
      #v(4pt)
      ```
      fig, axs = uplt.subplots([[1, 1, 2],
                                [3, 4, 2]], refwidth=1.8)

      gs = uplt.GridSpec(nrows=2, ncols=2, pad=1)
      ax = fig.subplot(gs[:, 0])
      ```
      #note[Draw the layout as an array: `0` leaves a gap, a repeated number spans cells.]
    ],
    panel("Size in real units", rails.at(0), kind: "new")[
      ```
      refwidth   size of the reference subplot
      refheight  ... its height
      refaspect  ... its width:height
      figwidth   total figure width
      hratios    relative row sizes
      wratios    relative column sizes
      wspace     gaps; None = solve it
      pad        outer padding
      ```
      #note[Numbers are inches; strings work too — `'55mm'`, `'2cm'`, `'8em'`, `'120pt'`. Convert by hand with `uplt.units('3cm', 'in')`.]
      #v(2pt)
      ```
      axs[0]; axs[:, 0]; axs[1, 1:]   # SubplotGrid
      axs.format(...)                 # broadcasts
      ```
    ],
    panel("Panels, insets, twins", rails.at(0))[
      #shot("assets/panels.png", width: 94%)
      #v(4pt)
      ```
      px = ax.panel_axes('r', width='4em')
      ix = ax.inset_axes([.6, .6, .3, .3], zoom=True)
      axt = ax.altx(); axr = ax.alty(ylabel='mm')
      axd = ax.dualx(lambda x: 1 / x)
      ```
      #note[Outer panels take their own gridspec slot, so they never squeeze or distort the subplot.]
    ],
  ),

  band("format()", rails.at(1), "call it on a figure, an axes or a grid — or pass the same keywords straight into subplots()"),
  cells(
    grid.cell(colspan: 2, panel("The canonical call", rails.at(1))[
      ```
      axs.format(
          suptitle='Model intercomparison',      # figure
          toplabels=('Control', 'Perturbed'),    # column headers
          leftlabels=('DJF', 'JJA'),             # row headers
          abc='a.', abcloc='ul',                 # panel letters
          title='centre', urtitle='corner',      # axes titles
          xlabel='time (s)', ylabel='signal (mV)',
          xlim=(0, 10), ylim=(-1, 1), xscale='log',
          xlocator=2, xminorlocator=.5, xformatter='sci',
          xtickdir='inout', xtickloc='both', xrotation=45,
          grid=True, gridminor=False, facecolor='gray1',
          rc_kw={'font.size': 11},               # any rc setting
      )
      ```
      #note[Unrecognised keywords are read as rc settings, so `abcloc` sets `abc.loc` and `titlepad` sets `title.pad`.]
    ]),
    panel("Titles and panel letters", rails.at(1), kind: "new")[
      #shot("assets/titles.png", width: 94%)
      #v(4pt)
      ```
      abc = True | 'a.' | 'A.' | '(a)' | 'a)'
      abcloc = 'ul'   # l c r  ul uc ur  ll lc lr
      toplabels leftlabels rightlabels bottomlabels
      ```
      #note[The letter is placed for you, in or above the axes, and never over a tick label.]
    ],
    panel("Ticks", rails.at(1))[
      ```
      ax.format(
        xlocator=0.5,          # every 0.5
        xlocator=[0, 1, 5],    # exactly these
        xminorlocator=0.1,
        xformatter='sci',      # 'deg' 'pi' 'lat'
        xformatter='%.1f',
        xformatter=['a', 'b'], # literal labels
        xbounds=(0, 8),        # crop the spine
        xtickloc='both',
        xtickdir='inout',
      )

      uplt.arange(-3, 3, .5)   # endpoint kept
      ```
      #note[Locators and formatters are built from plain values — no importing `mticker`. `uplt.arange` keeps its endpoint, which is what level and tick lists want.]
    ],
  ),

  band("Colorbars and legends", rails.at(2), "outer guides take their own gridspec slot — they never steal space from the subplot"),
  cells(
    panel("Where guides go", rails.at(2))[
      #shot("assets/guides.png", width: 96%)
      #note[Outer sides `'l' 'r' 't' 'b'`; inset corners `'ul' 'ur' 'll' 'lr'`, plus `'uc'` and `'lc'`. Several guides on one side queue up.]
    ],
    panel("Building them", rails.at(2))[
      ```
      ax.pcolormesh(data, cmap='batlow', colorbar='r',
                    colorbar_kw={'label': 'K'})
      ax.plot(Y, labels=['a', 'b'], legend='b',
              legend_kw={'ncols': 3, 'frame': False})

      fig.colorbar(m, loc='b', col=1, length=.7)
      fig.legend(hs, loc='r', rows=(1, 2))
      ax.colorbar(lines, values=[1, 2, 3])
      ax.colorbar('Blues', values=range(10))
      ```
      #note[Legends find their own handles, and restyle in place through `lw=`, `color=`, `markersize=`. Width and length are physical units, not fractions of the axes.]
    ],
    grid.cell(colspan: 2, panel("Semantic legends", rails.at(2), kind: "new")[
      #grid(columns: (1.05fr, 1fr), gutter: 6pt,
        shot("assets/semantic.png"),
        [
          ```
          ax.catlegend(names, colors={...},
                       markers={...})
          ax.sizelegend([10, 50, 200],
                        labels=['S', 'M', 'L'])
          ax.numlegend(levels=[0, .25, .5, .75, 1],
                       cmap='viko', fmt='{:.2f}')
          ax.entrylegend([{...}, {...}])
          ax.geolegend([...])
          ```
          #note[These describe an *encoding*, so nothing invisible has to be plotted first just to make a handle. All exist on `fig` too, and `add=False` returns `(handles, labels)` for composing your own.]
        ],
      )
    ]),
  ),
)

#pagebreak()

// ================================================================ PAGE TWO
#masthead[
  What you can draw, and the colour you draw it in. Every thumbnail below is the
  output of the command it names, rendered by the scripts in `parts/` — none of it
  is a mock-up. The caption colour says how far it is from matplotlib.
]

#sheet(
  weights: (0.90, 1.00, 1.10),
  band("Plot types", rails.at(0), "one picture per command — grey: matplotlib has it · blue: matplotlib can, by hand · red: no equivalent"),
  block(
    fill: panelbg,
    stroke: (top: 2pt + rails.at(0), rest: 0.4pt + rule),
    radius: 2pt,
    inset: (x: 8pt, y: 7pt),
    width: 100%,
    height: 100%,
  )[
    #grid(
      columns: (1fr,) * 15,
      column-gutter: 2.6mm,
      row-gutter: 3mm,
      align: center + top,
      ..commands.filter(entry => entry.featured).map(icon),
    )
    #v(5pt)
    #grid(columns: (1fr, 1fr), gutter: 8mm,
      note[Every `x`-oriented 1D command has a `…x` sibling — `plotx`, `scatterx`, `areax` — that swaps the axes properly instead of transposing by hand. Feed any of them pandas or xarray objects and the labels, coordinates and units come along.],
      note[The polar family (`chord_diagram`, `radar_chart`, `phylogeny`, `circos_bed`) wants `proj='polar'`, and `taylor` is its own projection. These thirty span the kinds of plot; all fifty-six, the keyword variants and the swapped-axis siblings are on the companion poster, `ultraplot_plot_types.pdf`.],
    )
  ],

  band("Fields, distributions, colour", rails.at(1), "levels and norms, the statistics UltraPlot computes for you, and the maps it ships with"),
  cells(
    panel("Discrete levels by default", rails.at(1), kind: "better")[
      #shot("assets/norms.png")
      #v(3pt)
      ```
      ax.pcolormesh(x, y, z, cmap='roma',
          levels=11,                  # count or edges
          values=uplt.arange(-4, 4),  # level centres
          extend='both', discrete=True,
          norm='div', labels=True)
      ```
      #note[`values=` pins a diverging midpoint to the real zero. `labels=True` writes the value into every cell or contour, in a colour that stays legible on the fill.]
    ],
    panel("Statistics from raw samples", rails.at(1), kind: "new")[
      #shot("assets/statistics.png")
      #v(3pt)
      ```
      ax.plot(x, runs, mean=True, shadestd=1,
              fadepctile=(5, 95))
      ax.bar(x, runs, median=True, bars=True)
      ```
      #note[Hand the command the raw samples, one column per `x`, then pick the reduction (`mean`, `median`) and the indicator. Each takes a `…std`, `…pctile` or explicit `…data` form.]
    ],
    panel("Cycles", rails.at(2))[
      #shot("assets/cycles.png", width: 96%)
      #v(3pt)
      ```
      uplt.rc.cycle = 'colorblind'
      ax.plot(Y, cycle='538')
      ax.plot(Y, cycle='Blues', cycle_kw={'left': .2})
      uplt.Cycle(lw=3, dashes=[(1, .5), (3, 1.5)])
      ```
      #note[Hand a 2D array to a 1D command and every column takes the next colour.]
    ],
    panel("Build and check a colormap", rails.at(2), kind: "new")[
      ```
      uplt.Colormap('prussian blue', l=100, space='hpl')
      uplt.Colormap(['blue', 'white', 'red'])
      uplt.Colormap(h=(0, 360), c=50, l=70,
                    space='hcl', cyclic=True)
      uplt.Colormap('Blues4_r', 'Reds3', ratios=(1, 3))

      # cmap_kw: left right cut shift alpha gamma
      # suffixes: _r reverse, _s shift
      ```
      #v(2pt)
      #shot("assets/luminance.png", width: 80%)
      #note[A sound sequential map ramps luminance monotonically. `jet` does not.]
    ],
  ),

  band("Bundled colormaps", rails.at(2), "registered on import — uplt.show_cmaps() prints the full set"),
  cells(
    grid.cell(colspan: 2, panel("UltraPlot, cmOcean, Crameri", rails.at(2))[
      #grid(columns: (1fr, 1fr), gutter: 7pt,
        [
          #text(size: 6pt, weight: 600, fill: inksoft, "UltraPlot")
          #v(1pt)
          #shot("assets/cmaps_uplt.png")
          #v(4pt)
          #text(size: 6pt, weight: 600, fill: inksoft, "cmOcean")
          #v(1pt)
          #shot("assets/cmaps_cmocean.png")
        ],
        [
          #text(size: 6pt, weight: 600, fill: inksoft, "Scientific colour maps (Crameri)")
          #v(1pt)
          #shot("assets/cmaps_scientific.png")
        ],
      )
    ]),
    panel("Maps", rails.at(3))[
      #shot("assets/geo_projections.png")
      #v(2pt)
      ```
      fig, axs = uplt.subplots(
          proj=('robin', 'ortho', 'npstere'), ncols=3)
      ax.pcolormesh(lon, lat, data, cmap='roma')
      ```
      #note[Short names cover the usual set: `cyl moll hammer eqearth laea lcc geos npstere aeqd`. Projection arguments go through `proj_kw`; cartopy is the default backend.]
    ],
    panel("Features, rc, output", rails.at(3))[
      #shot("assets/geo_features.png", width: 68%)
      #v(2pt)
      ```
      ax.format(land=True, ocean=True, coast=True,
                borders=True, rivers=True,
                lonlim=(-15, 40), latlim=(33, 62),
                lonlabels='b', latlabels='l')
      ```
      #v(1pt)
      #v(2pt)
      ```
      uplt.rc.update({'fontsize': 11, 'tickdir': 'in'})
      ani = uplt.FuncAnimation(fig, update, 100)
      ani.save('waves.mp4')   # blit=True
      ```
    ],
  ),
)

#pagebreak()

// ============================================================== PAGE THREE
// The gallery is generated from assets/features.typ, which parts/features.py
// writes, so the classification lives with the drawing code.

#let newcolor = badgecolor
#let bettercolor = accent

#let feat(entry) = block(width: 100%, breakable: false)[
  #thumb("assets/features/" + entry.name + ".png", entry.kind)
  #v(1.8pt)
  #align(center, text(
    size: 5.4pt,
    font: "IBM Plex Mono",
    fill: if entry.kind == "new" { newcolor } else { bettercolor },
    entry.label,
  ))
  #if entry.mpl != none [
    #v(0.8pt)
    #align(center, text(size: 4.6pt, fill: inkfaint, style: "italic", entry.mpl))
  ]
]

#let gallery(rail, group) = {
  let items = features.filter(entry => entry.group == group)
  block(
    fill: panelbg,
    stroke: (top: 2pt + rail, rest: 0.4pt + rule),
    radius: 2pt,
    inset: (x: 8pt, y: 7pt),
    width: 100%,
    height: 100%,
  )[
    #grid(
      columns: (1fr,) * items.len(),
      column-gutter: 3mm,
      align: center + top,
      ..items.map(feat),
    )
  ]
}

#let kindkey = [
  #box(width: 6pt, height: 2pt, fill: newcolor, baseline: -1pt)
  #h(1.5pt) #text(fill: inksoft)[de novo: matplotlib has no equivalent]
  #h(7pt)
  #box(width: 6pt, height: 2pt, fill: bettercolor, baseline: -1pt)
  #h(1.5pt) #text(fill: inksoft)[enhancement: matplotlib can, but you assemble it — its counterpart is named underneath]
]

#masthead[
  What UltraPlot adds, one picture each, drawn by the feature it shows. Two kinds,
  and the difference matters: a handful of these have no matplotlib equivalent at
  all, but most are things matplotlib *can* do and UltraPlot does for you.
  #linebreak()
  #kindkey
]

#sheet(
  weights: (1.00, 0.86, 0.86, 1.28),

  band("Figures and subplots", rails.at(0), "the layout engine, and the labels that come with it"),
  gallery(rails.at(0), "layout"),

  band("Axes and guides", rails.at(1), "extra axes, and guides that take their own gridspec slot"),
  grid(columns: (5fr, 5fr), column-gutter: 3.2mm,
    gallery(rails.at(1), "axes"),
    gallery(rails.at(1), "guides"),
  ),

  band("Colour and data", rails.at(2), "the colour engine, and what UltraPlot reads off your data"),
  grid(columns: (6fr, 6fr), column-gutter: 3.2mm,
    gallery(rails.at(2), "color"),
    gallery(rails.at(2), "data"),
  ),

  band("Additions without a picture", rails.at(3), "the rest, where a thumbnail would say nothing"),
  cells(
    panel("Constructor functions", rails.at(3), kind: "better")[
      ```
      uplt.Colormap  uplt.Cycle   uplt.Norm
      uplt.Locator   uplt.Formatter
      uplt.Scale     uplt.Proj
      ```
      #note[Every `cmap=`, `cycle=`, `norm=`, `locator=`, `formatter=`, `scale=` and `proj=` argument is passed through the matching constructor, so a string, a number or a list works anywhere matplotlib would want a class instance.]
    ],
    panel("Registries and loading", rails.at(3), kind: "new")[
      ```
      uplt.register_cmaps(user=True)
      uplt.register_cycles()   uplt.register_colors()
      uplt.register_fonts()
      uplt.show_cmaps()   uplt.show_cycles()
      uplt.show_colors()  uplt.show_fonts()
      uplt.show_channels('fire')
      ```
      #note[Drop files in the config folder and they are registered on import; the `show_` commands print what is available, including the perceptual channels of a map.]
    ],
    panel("Units and helpers", rails.at(3), kind: "new")[
      ```
      uplt.units('5cm', 'in')
      uplt.arange(-3, 3, .5)   # endpoint kept
      uplt.edges(centres)      # centres → edges
      uplt.edges2d(grid)
      uplt.to_xyz(color, space='hcl')
      uplt.set_alpha  scale_luminance
      shift_hue       scale_saturation
      ```
      #note[Sizes, spaces, widths and font sizes accept `'55mm'`, `'2cm'`, `'8em'`, `'120pt'` wherever a number would do.]
    ],
    panel("Figure-level plumbing", rails.at(3), kind: "better")[
      ```
      fig.save('~/figure.pdf')   # ~ expanded
      uplt.config_inline_backend()
      uplt.rc.context({...})
      ax.format(style='ggplot')  # per axes
      ExternalAxesContainer      # host a
                                 # third-party axes
      ```
      #note[Tight layout runs before every draw and save, so what you see is what lands in the file, and journal-ready defaults are already set.]
    ],
  ),
)
