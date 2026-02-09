"""
Circos from BED
===============

Build sectors from a BED file and render on UltraPlot polar axes.
"""

import tempfile
from pathlib import Path

import numpy as np

import ultraplot as uplt

bed_text = "chr1\t0\t100\nchr2\t0\t140\n"

with tempfile.TemporaryDirectory() as tmpdir:
    bed_path = Path(tmpdir) / "mini.bed"
    bed_path.write_text(bed_text, encoding="utf-8")

    fig, ax = uplt.subplots(proj="polar", refwidth=3.6)
    ax = ax[0]  # pycirclize expects a PolarAxes, not a SubplotGrid wrapper
    circos = ax.circos_bed(bed_path, plot=False)

    for sector in circos.sectors:
        x = np.linspace(sector.start, sector.end, 8)
        y = np.linspace(0, 50, 8)
        track = sector.add_track((60, 90), r_pad_ratio=0.1)
        track.axis()
        track.line(x, y)

    circos.plotfig(ax=ax)
    ax.format(title="BED sectors")
    fig.show()
