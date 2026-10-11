#!/usr/bin/env python3
"""Compare Seaborn rendering on Matplotlib and UltraPlot axes.

Examples
--------
python tools/check_seaborn_interop.py --baseline-only
python tools/check_seaborn_interop.py --modes direct external native --output seaborn-report.json
python tools/check_seaborn_interop.py --modes external --strict

This diagnostic runner (not a screenshot diff) compares artist geometry,
legend semantics, axis metadata and drawing errors independently. It keeps
running through errors and produces a machine-readable report. Figure-level
Seaborn functions manage their own layouts and are smoke-tested separately.
"""

import argparse
import json
import traceback
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import collections as mcollections
from matplotlib import patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns


# Public axes-level plotting APIs in Seaborn 0.13.x.
AXES_FUNCTIONS = (
    "scatterplot", "lineplot", "histplot", "kdeplot", "ecdfplot", "rugplot",
    "stripplot", "swarmplot", "boxplot", "violinplot", "boxenplot",
    "pointplot", "barplot", "countplot", "regplot", "residplot", "heatmap",
)
FIGURE_FUNCTIONS = (
    "relplot", "displot", "catplot", "lmplot", "jointplot", "pairplot",
    "clustermap",
)
OBJECT_STATISTICS = ("Agg", "Count", "Est", "Hist", "KDE", "Norm", "Perc", "PolyFit")


def make_data():
    rng = np.random.default_rng(103)
    x = np.tile(np.linspace(0.2, 4.4, 25), 3)
    group = np.repeat(["A", "B", "C"], 25)
    y = np.sin(x) + np.repeat([0, 0.7, 1.5], 25) + rng.normal(0, 0.22, len(x))
    return pd.DataFrame({
        "x": x, "y": y, "group": group,
        "category": np.tile(["one", "two", "three"], 25),
        "value": y + 2,
    })


def axes_kwargs(name, data):
    xy = {"data": data, "x": "x", "y": "y"}
    cat = {"data": data, "x": "category", "y": "value", "hue": "group"}
    if name in ("scatterplot", "lineplot"):
        return dict(xy, hue="group", **({"seed": 14} if name == "lineplot" else {}))
    if name in ("histplot", "kdeplot", "ecdfplot", "rugplot"):
        return {"data": data, "x": "value", "hue": "group"}
    if name in ("stripplot", "swarmplot", "boxplot", "violinplot", "boxenplot", "pointplot", "barplot"):
        return dict(cat, seed=14) if name in ("pointplot", "barplot") else cat
    if name == "countplot":
        return {"data": data, "x": "category", "hue": "group"}
    if name == "regplot":
        return dict(xy, seed=14)
    if name == "residplot":
        return xy
    if name == "heatmap":
        return {"data": np.arange(20, dtype=float).reshape(4, 5), "cbar": False}
    raise KeyError(name)


def figure_kwargs(name, data):
    if name == "relplot":
        return {"data": data, "x": "x", "y": "y", "hue": "group", "col": "group"}
    if name == "displot":
        return {"data": data, "x": "value", "hue": "group", "col": "group"}
    if name == "catplot":
        return {"data": data, "x": "category", "y": "value", "col": "group", "kind": "box"}
    if name == "lmplot":
        return {"data": data, "x": "x", "y": "y", "col": "group", "ci": None}
    if name == "jointplot":
        return {"data": data, "x": "x", "y": "y", "kind": "scatter"}
    if name == "pairplot":
        return {"data": data, "vars": ["x", "y"], "hue": "group"}
    if name == "clustermap":
        return {"data": np.arange(25, dtype=float).reshape(5, 5) + np.eye(5), "cbar_pos": None}
    raise KeyError(name)


def objects_plot(name, data):
    import seaborn.objects as so
    if name == "Agg":
        return so.Plot(data, x="group", y="value").add(so.Dot(), so.Agg())
    if name == "Count":
        return so.Plot(data, x="group").add(so.Bar(), so.Count())
    if name == "Est":
        return so.Plot(data, x="x", y="y", color="group").add(so.Line(), so.Est())
    if name == "Hist":
        return so.Plot(data, x="value").add(so.Bars(), so.Hist())
    if name == "KDE":
        return so.Plot(data, x="value").add(so.Line(), so.KDE())
    if name == "Norm":
        return so.Plot(data, x="value").add(so.Bars(), so.Hist(), so.Norm())
    if name == "Perc":
        return so.Plot(data, x="group", y="value").add(so.Dot(), so.Perc())
    if name == "PolyFit":
        return so.Plot(data, x="x", y="y").add(so.Line(), so.PolyFit())
    raise KeyError(name)


def number_array(value):
    arr = np.ma.asarray(value)
    if arr.dtype.kind not in "buifc":
        return str(value)
    arr = np.asarray(np.ma.filled(arr, np.nan), dtype=float)

    def convert(v):
        if isinstance(v, list):
            return [convert(x) for x in v]
        if np.isnan(v):
            return "NaN"
        if np.isposinf(v):
            return "+Infinity"
        if np.isneginf(v):
            return "-Infinity"
        return v

    return convert(np.round(arr, 7).tolist())


def snapshot(ax):
    """Compare geometry in data coordinates instead of theme-specific colors."""
    lines = [number_array(line.get_xydata()) for line in ax.lines]
    patches = []
    for patch in ax.patches:
        if isinstance(patch, mpatches.Rectangle):
            patches.append(["Rectangle", number_array(patch.get_bbox().bounds)])
        elif isinstance(patch, mpatches.PathPatch):
            patches.append(["PathPatch", number_array(patch.get_path().vertices)])
        else:
            patches.append([type(patch).__name__])
    collections = []
    for coll in ax.collections:
        if isinstance(coll, mcollections.PathCollection):
            collections.append(["PathCollection", number_array(coll.get_offsets())])
        elif isinstance(coll, mcollections.QuadMesh):
            collections.append(["QuadMesh", number_array(coll.get_coordinates())])
        elif isinstance(coll, mcollections.LineCollection):
            collections.append(["LineCollection", [number_array(a) for a in coll.get_segments()]])
        elif isinstance(coll, mcollections.PolyCollection):
            collections.append(["PolyCollection", [number_array(p.vertices) for p in coll.get_paths()]])
        else:
            collections.append([type(coll).__name__])
    legend = ax.get_legend()
    return {
        "artists": {"lines": lines, "patches": patches, "collections": collections},
        "legend": [t.get_text() for t in legend.get_texts()] if legend else [],
        "axis": {
            "xlabel": ax.get_xlabel(), "ylabel": ax.get_ylabel(),
            "xscale": ax.get_xscale(), "yscale": ax.get_yscale(),
            "xlim": number_array(ax.get_xlim()), "ylim": number_array(ax.get_ylim()),
            "xticklabels": [t.get_text() for t in ax.get_xticklabels()],
            "yticklabels": [t.get_text() for t in ax.get_yticklabels()],
        },
    }


def compare(baseline, candidate):
    result = {}
    for section in ("artists", "legend"):
        result[section] = "match" if baseline[section] == candidate[section] else "different"
    for part in ("xlabel", "ylabel", "xscale", "yscale", "xlim", "ylim", "xticklabels", "yticklabels"):
        result[part] = (
            "match" if baseline["axis"][part] == candidate["axis"][part] else "different"
        )
    return result


def plot_on_axes(kind, name, ax, data):
    if kind == "axes":
        # Identical jitter on reference and candidate, without altering caller RNG.
        state = np.random.get_state()
        try:
            np.random.seed(4103)
            return getattr(sns, name)(ax=ax, **axes_kwargs(name, data))
        finally:
            np.random.set_state(state)
    if kind == "objects":
        return objects_plot(name, data).on(ax).plot()
    raise KeyError(kind)


def run_axes(kind, name, mode, data, uplt=None):
    if mode == "reference":
        fig, ax = plt.subplots()
    else:
        fig, axs = uplt.subplots()
        ax = axs[0]  # Real Axes rather than a SubplotGrid wrapper.
    try:
        if mode == "external":
            with ax.external():
                plot_on_axes(kind, name, ax, data)
        elif mode == "native":
            # Diagnosis only: an UltraPlot private internal, NOT a public API.
            from ultraplot.internals import context
            with ax.external(), context._state_context(ax, _internal_call=True):
                plot_on_axes(kind, name, ax, data)
        else:
            plot_on_axes(kind, name, ax, data)
        fig.canvas.draw()
        return {"status": "ok", "snapshot": snapshot(ax)}
    except Exception as exc:
        return {
            "status": "error", "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=5),
        }
    finally:
        plt.close(fig)


def run_figure(name, data):
    try:
        grid = getattr(sns, name)(**figure_kwargs(name, data))
        fig = grid.fig
        fig.canvas.draw()
        result = {"status": "ok", "axes": len(fig.axes)}
        plt.close(fig)
        return result
    except Exception as exc:
        plt.close("all")
        return {
            "status": "error", "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=5),
        }


def run(args):
    uplt = None
    if not args.baseline_only:
        import ultraplot as uplt
    data = make_data()
    entries = []
    for kind, cases in (("axes", AXES_FUNCTIONS), ("objects", OBJECT_STATISTICS)):
        for name in cases:
            ref = run_axes(kind, name, "reference", data)
            entries.append({"api": f"{kind}.{name}", "mode": "reference", **ref})
            for mode in (() if args.baseline_only else args.modes):
                candidate = run_axes(kind, name, mode, data, uplt)
                if candidate["status"] == "ok" and ref["status"] == "ok":
                    candidate["comparison"] = compare(ref["snapshot"], candidate["snapshot"])
                entries.append({"api": f"{kind}.{name}", "mode": mode, **candidate})
            outcome = [e for e in entries if e["api"] == f"{kind}.{name}"]
            print(f"{kind}.{name:14s} " + "  ".join(
                f"{e['mode']}:{'ERROR' if e['status']=='error' else ('DIFF' if 'different' in e.get('comparison',{}).values() else 'OK')}"
                for e in outcome
            ), flush=True)
    for name in FIGURE_FUNCTIONS:
        result = run_figure(name, data)
        entries.append({"api": f"figure.{name}", "mode": "standalone", **result})
        print(f"figure.{name:14s} standalone:{result['status']}", flush=True)
    counts = Counter(
        "error" if e["status"] == "error" else
        "different" if "different" in e.get("comparison", {}).values() else "ok"
        for e in entries
    )
    report = {
        "versions": {
            "matplotlib": matplotlib.__version__, "seaborn": sns.__version__,
            "ultraplot": getattr(uplt, "__version__", None),
        },
        "counts": dict(counts), "entries": entries,
        "notes": (
            "Native mode uses an UltraPlot private flag, not a public API. "
            "Figure-level functions are standalone smoke tests, not UltraPlot integrations."
        ),
    }
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print("\nResults:", dict(counts))
    return 1 if args.strict and (counts["error"] or counts["different"]) else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-only", action="store_true", help="Smoke test Seaborn on Matplotlib without UltraPlot")
    parser.add_argument("--modes", nargs="+", choices=("direct", "external", "native"),
                        default=("direct", "external", "native"))
    parser.add_argument("--output", default="seaborn-interop-report.json")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero for rendering mismatches or exceptions")
    args = parser.parse_args()
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
