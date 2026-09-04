#!/usr/bin/env python3
"""Generate the real UltraPlot figure used by the alias explorer."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import ultraplot as uplt  # noqa: E402


def main():
    output = ROOT / "docs" / "_static" / "alias-map.svg"
    preview = Path("/tmp/ultraplot-alias-map.png")
    x = np.linspace(0, 10, 100)
    baseline = 0.32 * np.sin(1.15 * x) + 0.07 * x
    comparison = 0.25 * np.cos(0.9 * x + 0.5) + 0.055 * x + 0.18

    with uplt.rc.context(
        {
            "font.size": 10,
            "axes.grid": True,
            "svg.hashsalt": "ultraplot-alias-map",
        }
    ):
        fig, ax = uplt.subplots(refwidth=4.6, refheight=2.9)
        ax.plot(
            x,
            baseline,
            color="#168f83",
            linewidth=2.2,
            label="Observed",
        )
        ax.plot(
            x,
            comparison,
            color="#3976d3",
            linewidth=2.0,
            linestyle="--",
            label="Reference",
        )
        points = ax.scatter(
            x[::10],
            baseline[::10],
            c=x[::10],
            cmap="batlow",
            s=28,
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )
        ax.legend(location="upper right", frameon=True, ncols=1)
        ax.colorbar(
            points,
            location="right",
            label="Progress",
            shrink=0.78,
            ticks=[0, 5, 10],
        )
        inset = ax.inset([0.07, 0.63, 0.27, 0.25])
        inset.plot(
            x[:35],
            baseline[:35],
            color="#168f83",
            linewidth=1.3,
        )
        inset.format(
            title="Inset",
            xlocator=[],
            ylocator=[],
            grid=False,
        )
        ax.format(
            xlabel="Time",
            ylabel="Signal",
            lefttitle="Primary title",
            righttitle="Context",
            xlocator=2,
            ylocator=0.25,
            grid=True,
            gridalpha=0.18,
        )
        fig.format(
            suptitle="Where aliases act",
            leftlabels=["Left labels"],
            rightlabels=["Right labels"],
        )
        fig.savefig(output, transparent=False, metadata={"Date": None})
        source = output.read_text()
        output.write_text("\n".join(line.rstrip() for line in source.splitlines()) + "\n")
        fig.savefig(preview, dpi=180, transparent=False)
        uplt.close(fig)


if __name__ == "__main__":
    main()
