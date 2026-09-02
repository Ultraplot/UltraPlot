// UltraPlot plot-type poster — every command, one picture each.
//
// A companion to cheatsheet.typ, sharing its assets and its palette. Where the
// cheatsheet has to earn its space with code, this is only the small plots:
// bigger, grouped by what the command is for, and captioned with the call.

#import "assets/palette.typ": batlow, rails
#import "assets/icons.typ": commands

#let paper = rgb("#f2f4f7")
#let panelbg = rgb("#ffffff")
#let ink = rgb("#0f151d")
#let inksoft = rgb("#4a5663")
#let inkfaint = rgb("#8593a1")
#let rule = rgb("#dbe1e8")
#let accent = rgb("#3b638c")
#let badgecolor = rgb("#a8414f")

#set page(
  paper: "a3",
  flipped: false,
  margin: (x: 11mm, top: 10mm, bottom: 9mm),
  fill: paper,
  footer: context [
    #set text(size: 7pt, fill: inkfaint)
    #grid(columns: (1fr, auto), align: (left + horizon, right + horizon),
      [Every picture is the output of the command it names, drawn by
       #raw("tools/cheatsheet/parts/icons.py") · ultraplot.readthedocs.io],
      [#counter(page).display()],
    )
  ],
  footer-descent: 5mm,
)
#set text(font: ("IBM Plex Sans", "DejaVu Sans"), size: 8pt, fill: ink)
#set par(leading: 0.5em)
#show raw: set text(font: ("IBM Plex Mono", "DejaVu Sans Mono"), size: 7.6pt)

// How far a command is from matplotlib, as a colour. Written on one line: a
// multi-line if/else chain in markup mode does not bind as one expression.
#let tone-of(kind) = if kind == "new" { badgecolor } else if kind == "better" { accent } else { ink }
#let rail-of(kind) = if kind == "new" { badgecolor } else if kind == "better" { accent } else { rule }

#let exclusive-badge = box(
  fill: badgecolor,
  inset: (x: 2.6pt, y: 0.9pt),
  radius: (bottom-left: 2pt),
  text(size: 4.8pt, font: "IBM Plex Sans", fill: white, weight: 600, tracking: 0.05em, "EXCLUSIVE"),
)

// One thumbnail. An UltraPlot-exclusive command gets a full outline and a
// corner badge; the rest carry a section rail only.
#let tile(entry) = block(width: 100%, breakable: false)[
  #box(
    fill: panelbg,
    stroke: if entry.kind == "new" { 1.2pt + badgecolor } else if entry.kind == "better" { (top: 2pt + accent, rest: 0.5pt + rule) } else { 0.5pt + rule },
    radius: 2pt,
    inset: 0pt,
    clip: true,
    width: 100%,
  )[
    #image("assets/icons/" + entry.file + ".png", width: 100%)
    #if entry.kind == "new" { place(top + right, exclusive-badge) }
  ]
  #v(2.5pt)
  #let parts = entry.name.split("(")
  #align(center, text(size: 5.9pt, font: "IBM Plex Mono", fill: tone-of(entry.kind),
    if parts.len() > 1 [
      #parts.at(0) \ #text(size: 5.4pt)[(#parts.at(1)]
    ] else [
      #entry.name
    ],
  ))
  #if entry.mpl != none [
    #v(1pt)
    #align(center, text(size: 5pt, fill: inkfaint, style: "italic", entry.mpl))
  ]
]

#let section(title, blurb, group, columns: 13) = {
  let items = commands.filter(entry => entry.group == group)
  block(width: 100%, breakable: false, above: 11pt, below: 2pt)[
    #grid(columns: (auto, 1fr), column-gutter: 7pt, align: (left + bottom, left + bottom),
      text(size: 11pt, weight: 700, tracking: 0.03em, upper(title)),
      text(size: 7pt, fill: inkfaint, blurb),
    )
    #v(2.5pt)
    #line(length: 100%, stroke: 0.7pt + rule)
    #v(5pt)
    #grid(
      columns: (1fr,) * columns,
      column-gutter: 2.4mm,
      row-gutter: 3mm,
      align: center + top,
      ..items.map(tile),
    )
  ]
}

// ------------------------------------------------------------- masthead
#block(width: 100%, below: 8pt)[
  #grid(columns: (auto, 1fr), column-gutter: 14mm, align: (left + bottom, left + bottom),
    [
      #text(size: 34pt, weight: 700, tracking: -0.02em, "UltraPlot")
      #v(-11pt)
      #text(size: 10pt, weight: 600, fill: accent, tracking: 4pt, "PLOT TYPES")
    ],
    [
      #text(size: 8pt, fill: inksoft)[
        Every command UltraPlot can draw, one picture each — and each picture is
        that command's own output, at 26 mm. Assumes `import ultraplot as uplt`,
        then `fig, ax = uplt.subplots()`.
      ]
      #v(4pt)
      #text(size: 7.2pt)[
        #box(width: 8pt, height: 2.5pt, fill: rule, baseline: -1pt) #h(2pt)
        #text(fill: inksoft)[matplotlib has the command] #h(9pt)
        #box(width: 8pt, height: 2.5pt, fill: accent, baseline: -1pt) #h(2pt)
        #text(fill: inksoft)[matplotlib can, but you assemble it] #h(9pt)
        #box(width: 8pt, height: 2.5pt, fill: badgecolor, baseline: -1pt) #h(2pt)
        #text(fill: inksoft)[UltraPlot exclusive]
      ]
    ],
  )
  #v(6pt)
  #rect(width: 100%, height: 4pt, stroke: none, radius: 1pt,
        fill: gradient.linear(..batlow))
]

#section("Relational", "how one variable relates to another", "relational")
#section("Distributions", "the shape and spread of a sample", "distribution")
#section("Fields", "a value over a two-dimensional grid", "field")
#section("Vectors", "direction and magnitude on a grid", "vector")
#section("Networks and diagrams", "relationships that are not a grid", "network")
#section("Maps", "a projection by name, with anything drawn on top in lon/lat", "maps")
#section("What one keyword does", "the same command, changed by a single argument", "keyword")
#section("Swapped axes", "the siblings that put the categories on the other axis", "swapped")
