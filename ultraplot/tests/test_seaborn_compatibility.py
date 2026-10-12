"""Smoke coverage of Seaborn's public statistical plotting interfaces.

Axes-level functions accept UltraPlot axes, with auto detection or external().
Figure-level relplot/displot/catplot/lmplot/jointplot/pairplot/clustermap and
FacetGrid/PairGrid/JointGrid own their figures: use axes-level counterparts for
embedding. They are not evidence of UltraPlot axes compatibility. Deprecated
distplot is replaced by histplot/kdeplot/rugplot. The objects Plot.on(ax)
interface is tested separately. Targeted image/legend regressions remain in
 test_integration.py; these tests check creation, semantics, and drawing.
"""

from contextlib import nullcontext

import numpy as np
import pytest

import ultraplot as uplt

sns = pytest.importorskip("seaborn")
pd = pytest.importorskip("pandas")


@pytest.fixture
def seaborn_data():
    rng = np.random.default_rng(51423)
    x = np.tile(np.arange(12), 6)
    return pd.DataFrame(
        dict(
            x=x,
            y=0.3 * x + rng.normal(size=x.size),
            group=np.repeat(["a", "b"], 36),
            category=np.tile(["one", "two", "three"], 24),
        )
    )


CASES = [
    ("scatterplot", dict(x="x", y="y", hue="group", size="x")),
    ("lineplot", dict(x="x", y="y", hue="group", n_boot=20, seed=0)),
    ("histplot", dict(x="y", hue="group", multiple="stack", bins=8)),
    ("histplot", dict(x="x", y="y", bins=8, cbar=True)),
    ("kdeplot", dict(x="y", hue="group", fill=True)),
    ("kdeplot", dict(x="x", y="y", fill=True)),
    ("ecdfplot", dict(x="y", hue="group")),
    ("rugplot", dict(x="x", y="y", hue="group")),
    *[
        (name, dict(x="category", y="y", hue="group"))
        for name in ("stripplot", "swarmplot", "boxplot", "violinplot", "boxenplot")
    ],
    ("boxplot", dict(y="category", x="y", hue="group", orient="h")),
    ("pointplot", dict(x="category", y="y", hue="group", n_boot=20, seed=0)),
    ("barplot", dict(x="category", y="y", hue="group", n_boot=20, seed=0)),
    ("countplot", dict(x="category", hue="group")),
    ("regplot", dict(x="x", y="y", n_boot=20, seed=0)),
    ("residplot", dict(x="x", y="y")),
    ("heatmap", dict(annot=True, cbar=True)),
]


@pytest.mark.parametrize("external", [False, True], ids=["auto", "external"])
@pytest.mark.parametrize(
    "name,kwargs", CASES, ids=[f"{name}-{i}" for i, (name, _) in enumerate(CASES)]
)
def test_seaborn_axes_api(name, kwargs, external, seaborn_data):
    fig, axs = uplt.subplots()
    ax = axs[0]
    data = seaborn_data[["x", "y"]].corr() if name == "heatmap" else seaborn_data
    before = len(ax.lines) + len(ax.collections) + len(ax.patches)
    try:
        with ax.external() if external else nullcontext():
            result = getattr(sns, name)(data=data, ax=ax, **kwargs)
        assert result is ax
        assert len(ax.lines) + len(ax.collections) + len(ax.patches) > before
        ax.format(title=f"Seaborn {name}")
        fig.canvas.draw()
        if "hue" in kwargs and name not in ("histplot", "kdeplot"):
            assert ax.get_legend() is not None
            labels = {text.get_text() for text in ax.get_legend().get_texts()}
            assert {"a", "b"} <= labels
        assert ax._integration_external is None
    finally:
        uplt.close(fig)


@pytest.mark.parametrize("mark,stat", [("Dot", None), ("Bar", "Hist"), ("Line", "Agg")])
def test_seaborn_objects_on_ultraplot_axes(mark, stat, seaborn_data):
    so = pytest.importorskip("seaborn.objects")
    fig, axs = uplt.subplots()
    ax = axs[0]
    try:
        plot = so.Plot(seaborn_data, x="x", **({} if stat == "Hist" else {"y": "y"}))
        layers = [getattr(so, mark)()]
        if stat:
            layers.append(getattr(so, stat)())
        with ax.external():
            plot.add(*layers).on(ax).plot()
        assert ax.lines or ax.collections or ax.patches
        fig.canvas.draw()
    finally:
        uplt.close(fig)


@pytest.mark.parametrize(
    "name,kwargs",
    [
        ("relplot", dict(x="x", y="y", hue="group")),
        ("displot", dict(x="y", hue="group")),
        ("catplot", dict(x="category", y="y", hue="group")),
        ("lmplot", dict(x="x", y="y", hue="group", n_boot=20, seed=0)),
        ("jointplot", dict(x="x", y="y")),
        ("pairplot", dict(vars=["x", "y"], hue="group", diag_kind="hist")),
        ("clustermap", dict()),
    ],
    ids=[
        "relplot",
        "displot",
        "catplot",
        "lmplot",
        "jointplot",
        "pairplot",
        "clustermap",
    ],
)
def test_seaborn_figure_api_owns_figure(name, kwargs, seaborn_data):
    """Figure-level APIs coexist, but do not draw into the current UltraPlot axes."""
    fig, axs = uplt.subplots()
    ax = axs[0]
    grid = None
    try:
        data = seaborn_data[["x", "y"]] if name == "clustermap" else seaborn_data
        grid = getattr(sns, name)(data=data, **kwargs)
        assert grid.figure is not fig
        assert not (ax.lines or ax.collections or ax.patches)
        grid.figure.canvas.draw()
        ax.plot([0, 1], [0, 1])
        fig.canvas.draw()
    finally:
        if grid is not None:
            uplt.close(grid.figure)
        uplt.close(fig)
