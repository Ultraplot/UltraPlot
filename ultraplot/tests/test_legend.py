import numpy as np
import pandas as pd
import pytest
from matplotlib import colors as mcolors
from matplotlib import legend_handler as mhandler
from matplotlib import patches as mpatches

import ultraplot as uplt
from ultraplot.axes import Axes as UAxes


@pytest.mark.mpl_image_compare
def test_auto_legend(rng):
    """
    Test retrieval of legends from panels, insets, etc.
    """
    fig, ax = uplt.subplots()
    ax.line(rng.random((5, 3)), labels=list("abc"))
    px = ax.panel_axes("right", share=False)
    px.linex(rng.random((5, 3)), labels=list("xyz"))
    # px.legend(loc='r')
    ix = ax.inset_axes((-0.2, 0.8, 0.5, 0.5), zoom=False)
    ix.line(rng.random((5, 2)), labels=list("pq"))
    ax.legend(loc="b", order="F", edgecolor="red9", edgewidth=3)
    return fig


@pytest.mark.mpl_image_compare
def test_singleton_legend():
    """
    Test behavior when singleton lists are passed.
    Ensure this does not trigger centered-row legends.
    """
    fig, ax = uplt.subplots()
    h1 = ax.plot([0, 1, 2], label="a")
    h2 = ax.plot([0, 1, 1], label="b")
    ax.legend(loc="best")
    ax.legend([h1, h2], loc="bottom")
    return fig


@pytest.mark.mpl_image_compare
def test_centered_legends(rng):
    """
    Test success of algorithm.
    """
    # Basic centered legends
    fig, axs = uplt.subplots(ncols=2, nrows=2, axwidth=2, share=True)
    hs = axs[0].plot(rng.random((10, 6)))
    locs = ["l", "t", "r", "uc", "ul", "ll"]
    locs = ["l", "t", "uc", "ll"]
    labels = ["a", "bb", "ccc", "ddddd", "eeeeeeee", "fffffffff"]
    for ax, loc in zip(axs, locs):
        ax.legend(hs, loc=loc, ncol=3, labels=labels, center=True)

    # Pass centered legends with keywords or list-of-list input.
    fig, ax = uplt.subplots()
    hs = ax.plot(rng.random((10, 5)), labels=list("abcde"))
    ax.legend(hs, center=True, loc="b")
    ax.legend(hs + hs[:1], loc="r", ncol=1)
    ax.legend([hs[:2], hs[2:], hs[0]], loc="t")
    return fig


@pytest.mark.mpl_image_compare
def test_manual_labels():
    """
    Test mixed auto and manual labels. Passing labels but no handles does nothing
    This is breaking change but probably best. We should not be "guessing" the
    order objects were drawn in then assigning labels to them. Similar to using
    OO interface and rejecting pyplot "current axes" and "current figure".
    """
    fig, ax = uplt.subplots()
    (h1,) = ax.plot([0, 1, 2], label="label1")
    (h2,) = ax.plot([0, 1, 1], label="label2")
    for loc in ("best", "bottom"):
        ax.legend([h1, h2], loc=loc, labels=[None, "override"])
    fig, ax = uplt.subplots()
    ax.plot([0, 1, 2])
    ax.plot([0, 1, 1])
    for loc in ("best", "bottom"):
        # ax.legend(loc=loc, labels=['a', 'b'])
        ax.legend(["a", "b"], loc=loc)  # same as above
    return fig


@pytest.mark.mpl_image_compare
def test_contour_legend_with_label(rng):
    """
    Support contour element labels. If has no label should trigger warning.
    """
    figs = []
    label = "label"

    fig, axs = uplt.subplots(ncols=2)
    ax = axs[0]
    ax.contour(rng.random((5, 5)), color="k", label=label, legend="b")
    ax = axs[1]
    ax.pcolor(rng.random((5, 5)), label=label, legend="b")
    return fig


@pytest.mark.mpl_image_compare
def test_contour_legend_without_label(rng):
    """
    Support contour element labels. If has no label should trigger warning.
    """
    label = None
    fig, axs = uplt.subplots(ncols=2)
    ax = axs[0]
    ax.contour(rng.random((5, 5)), color="k", label=label, legend="b")
    ax = axs[1]
    ax.pcolor(rng.random((5, 5)), label=label, legend="b")
    return fig


@pytest.mark.mpl_image_compare
def test_histogram_legend(rng):
    """
    Support complex histogram legends.
    """
    with uplt.rc.context({"inlineformat": "svg"}):
        fig, ax = uplt.subplots()
        res = ax.hist(
            rng.random((500, 2)), 4, labels=("label", "other"), edgefix=True, legend="b"
        )
        ax.legend(
            res, loc="r", ncol=1
        )  # should issue warning after ignoring numpy arrays
        df = pd.DataFrame(
            {"length": [1.5, 0.5, 1.2, 0.9, 3], "width": [0.7, 0.2, 0.15, 0.2, 1.1]},
            index=["pig", "rabbit", "duck", "chicken", "horse"],
        )
        fig, axs = uplt.subplots(ncols=3)
        ax = axs[0]
        res = ax.hist(df, bins=3, legend=True, lw=3)
        ax.legend(loc="b")
        for ax, meth in zip(axs[1:], ("bar", "area")):
            hs = getattr(ax, meth)(df, legend="ul", lw=3)
            ax.legend(hs, loc="b")
    return fig


@pytest.mark.mpl_image_compare
def test_multiple_calls(rng):
    """
    Test successive plotting additions to guides.
    """
    fig, ax = uplt.subplots()
    ax.pcolor(rng.random((10, 10)), colorbar="b")
    ax.pcolor(rng.random((10, 5)), cmap="grays", colorbar="b")
    ax.pcolor(rng.random((10, 5)), cmap="grays", colorbar="b")

    fig, ax = uplt.subplots()
    data = rng.random((10, 5))
    for i in range(data.shape[1]):
        ax.plot(data[:, i], colorbar="b", label=f"x{i}", colorbar_kw={"label": "hello"})
    return fig


@pytest.mark.mpl_image_compare
def test_tuple_handles(rng):
    """
    Test tuple legend handles.
    """
    from matplotlib import legend_handler

    fig, ax = uplt.subplots(refwidth=3, abc="A.", abcloc="ul", span=False)
    patches = ax.fill_between(rng.random((10, 3)), stack=True)
    lines = ax.line(1 + 0.5 * (rng.random((10, 3)) - 0.5).cumsum(axis=0))
    # ax.legend([(handles[0], lines[1])], ['joint label'], loc='bottom', queue=True)
    for hs in (lines, patches):
        ax.legend(
            [tuple(hs[:3]) if len(hs) == 3 else hs],
            ["joint label"],
            loc="bottom",
            queue=True,
            ncol=1,
            handlelength=4.5,
            handleheight=1.5,
            handler_map={tuple: legend_handler.HandlerTuple(pad=0, ndivide=3)},
        )
    return fig


@pytest.mark.mpl_image_compare
def test_legend_col_spacing(rng):
    """
    Test legend column spacing.
    """
    fig, ax = uplt.subplots()
    ax.plot(rng.random(10), label="short")
    ax.plot(rng.random(10), label="longer label")
    ax.plot(rng.random(10), label="even longer label")
    for idx in range(3):
        spacing = f"{idx}em"
        if idx == 2:
            spacing = 3
        ax.legend(loc="bottom", ncol=3, columnspacing=spacing)

    with pytest.raises(ValueError):
        ax.legend(loc="bottom", ncol=3, columnspacing="15x")
    return fig


def test_legend_align_opts_mapping():
    """
    Basic sanity check for legend alignment mapping.
    """
    from ultraplot.legend import ALIGN_OPTS

    assert ALIGN_OPTS[None]["center"] == "center"
    assert ALIGN_OPTS["left"]["top"] == "upper right"
    assert ALIGN_OPTS["right"]["bottom"] == "lower left"
    assert ALIGN_OPTS["top"]["center"] == "lower center"
    assert ALIGN_OPTS["bottom"]["right"] == "upper right"


def test_legend_builder_smoke():
    """
    Ensure the legend builder path returns a legend object.
    """
    import matplotlib.pyplot as plt

    fig, ax = uplt.subplots()
    ax.plot([0, 1, 2], label="a")
    leg = ax.legend(loc="right", align="center")
    assert leg is not None
    plt.close(fig)


def test_legend_normalize_em_kwargs():
    """
    Ensure em-based legend kwargs are converted to numeric values.
    """
    from ultraplot.legend import _normalize_em_kwargs

    out = _normalize_em_kwargs({"labelspacing": "2em"}, fontsize=10)
    assert isinstance(out["labelspacing"], (int, float))


def test_sync_label_dict(rng):
    """
    Legends are held within _legend_dict for which the key is a tuple of location and alignment.

    We need to ensure that the legend is updated in the dictionary when its location is changed.
    """
    data = rng.random((2, 100))
    fig, ax = uplt.subplots()
    ax.plot(*data, label="test")
    leg = ax.legend(loc="lower right")
    assert ("lower right", "center") in ax[0]._legend_dict, "Legend not found in dict"
    leg.set_loc("upper left")
    assert ("upper left", "center") in ax[
        0
    ]._legend_dict, "Legend not found in dict after update"
    assert leg is ax[0]._legend_dict[("upper left", "center")]
    assert ("lower right", "center") not in ax[
        0
    ]._legend_dict, "Old legend not removed from dict"
    uplt.close(fig)


def test_external_mode_defers_on_the_fly_legend():
    """
    External mode should defer on-the-fly legend creation until explicitly requested.
    """
    fig, ax = uplt.subplots()
    ax.set_external(True)
    (h,) = ax.plot([0, 1], label="a", legend="b")

    # No legend should have been created yet
    assert getattr(ax[0], "legend_", None) is None

    # Explicit legend creation should include the plotted label
    leg = ax.legend(h, loc="b")
    labels = [t.get_text() for t in leg.get_texts()]
    assert "a" in labels
    uplt.close(fig)


def test_external_mode_mixing_context_manager():
    """
    Mixing external and internal plotting on the same axes:
    - Inside ax.external(): on-the-fly legend is deferred
    - Outside: UltraPlot-native plotting resumes as normal
    - Final explicit ax.legend() consolidates both kinds of artists
    """
    fig, ax = uplt.subplots()

    with ax.external():
        (ext,) = ax.plot([0, 1], label="ext", legend="b")  # deferred

    (intr,) = ax.line([0, 1], label="int")  # normal UL behavior

    leg = ax.legend([ext, intr], loc="b")
    labels = {t.get_text() for t in leg.get_texts()}
    assert {"ext", "int"}.issubset(labels)
    uplt.close(fig)


def test_legend_entry_helpers():
    h1 = uplt.LegendEntry.line("Line", color="red8", linewidth=3)
    h2 = uplt.LegendEntry.marker("Marker", color="blue8", marker="s", markersize=8)

    assert h1.get_linestyle() != "none"
    assert h1.get_label() == "Line"
    assert h2.get_linestyle() == "None"
    assert h2.get_marker() == "s"
    assert h2.get_label() == "Marker"


def test_legend_entry_with_axes_legend():
    fig, ax = uplt.subplots()
    handles = [
        uplt.LegendEntry.line("Trend", color="green7", linewidth=2.5),
        uplt.LegendEntry.marker("Samples", color="orange7", marker="o", markersize=7),
    ]
    leg = ax.legend(handles=handles, loc="best")

    labels = [text.get_text() for text in leg.get_texts()]
    assert labels == ["Trend", "Samples"]
    lines = leg.get_lines()
    assert len(lines) == 2
    assert lines[0].get_linewidth() > 0
    assert lines[1].get_marker() == "o"
    uplt.close(fig)


def test_semantic_helpers_not_public_on_module():
    for name in ("cat_legend", "size_legend", "num_legend", "geo_legend"):
        assert not hasattr(uplt, name)


def test_geo_legend_helper_shapes():
    fig, ax = uplt.subplots()
    handles, labels = ax.geo_legend(
        [("Triangle", "triangle"), ("Hex", "hexagon")], add=False
    )
    assert labels == ["Triangle", "Hex"]
    assert len(handles) == 2
    assert all(isinstance(handle, mpatches.PathPatch) for handle in handles)
    uplt.close(fig)


def test_semantic_legend_rc_defaults():
    fig, axs = uplt.subplots(ncols=4, share=False)
    with uplt.rc.context(
        {
            "legend.cat.line": True,
            "legend.cat.marker": "s",
            "legend.cat.linewidth": 3.25,
            "legend.size.marker": "^",
            "legend.size.minsize": 8.0,
            "legend.num.n": 3,
            "legend.geo.facecolor": "red7",
            "legend.geo.edgecolor": "black",
            "legend.geo.fill": True,
        }
    ):
        leg = axs[0].cat_legend(["A"], loc="best")
        h = leg.legend_handles[0]
        assert h.get_marker() == "s"
        assert h.get_linewidth() == pytest.approx(3.25)

        leg = axs[1].size_legend([1.0], loc="best")
        h = leg.legend_handles[0]
        assert h.get_marker() == "^"
        assert h.get_markersize() >= 8.0

        leg = axs[2].num_legend(vmin=0, vmax=1, loc="best")
        assert len(leg.legend_handles) == 3

        leg = axs[3].geo_legend([("shape", "triangle")], loc="best")
        h = leg.legend_handles[0]
        assert isinstance(h, mpatches.PathPatch)
        assert np.allclose(h.get_facecolor(), mcolors.to_rgba("red7"))
    uplt.close(fig)


def test_semantic_legend_loc_shorthand():
    fig, ax = uplt.subplots()
    leg = ax.cat_legend(["A", "B"], loc="r")
    assert leg is not None
    assert [text.get_text() for text in leg.get_texts()] == ["A", "B"]
    uplt.close(fig)


def test_geo_legend_handlesize_scales_handle_box():
    fig, ax = uplt.subplots()
    leg = ax.geo_legend([("shape", "triangle")], loc="best", handlesize=2.0)
    assert leg.handlelength == pytest.approx(2.0 * uplt.rc["legend.handlelength"])
    assert leg.handleheight == pytest.approx(2.0 * uplt.rc["legend.handleheight"])

    with uplt.rc.context({"legend.geo.handlesize": 1.5}):
        leg = ax.geo_legend([("shape", "triangle")], loc="best")
        assert leg.handlelength == pytest.approx(1.5 * uplt.rc["legend.handlelength"])
        assert leg.handleheight == pytest.approx(1.5 * uplt.rc["legend.handleheight"])
    uplt.close(fig)


def test_geo_legend_helper_with_axes_legend(monkeypatch):
    sgeom = pytest.importorskip("shapely.geometry")
    from ultraplot import legend as plegend

    monkeypatch.setattr(
        plegend,
        "_resolve_country_geometry",
        lambda _, resolution="110m", include_far=False: sgeom.box(-1, -1, 1, 1),
    )
    fig, ax = uplt.subplots()
    leg = ax.geo_legend({"AUS": "country:AU", "NZL": "country:NZ"}, loc="best")
    assert [text.get_text() for text in leg.get_texts()] == ["AUS", "NZL"]
    uplt.close(fig)


def test_geo_legend_country_resolution_passthrough(monkeypatch):
    sgeom = pytest.importorskip("shapely.geometry")
    from ultraplot import legend as plegend

    calls = []

    def _fake_country(code, resolution="110m", include_far=False):
        calls.append((str(code).upper(), resolution, bool(include_far)))
        return sgeom.box(-1, -1, 1, 1)

    monkeypatch.setattr(plegend, "_resolve_country_geometry", _fake_country)

    fig, ax = uplt.subplots()
    ax.geo_legend([("NLD", "country:NLD")], country_reso="10m", add=False)
    assert calls == [("NLD", "10m", False)]

    calls.clear()
    with uplt.rc.context({"legend.geo.country_reso": "50m"}):
        ax.geo_legend([("NLD", "country:NLD")], add=False)
    assert calls == [("NLD", "50m", False)]

    calls.clear()
    ax.geo_legend([("NLD", "country:NLD")], country_territories=True, add=False)
    assert calls == [("NLD", "110m", True)]

    calls.clear()
    with uplt.rc.context({"legend.geo.country_territories": True}):
        ax.geo_legend([("NLD", "country:NLD")], add=False)
    assert calls == [("NLD", "110m", True)]
    uplt.close(fig)


def test_geo_legend_country_projection_passthrough(monkeypatch):
    sgeom = pytest.importorskip("shapely.geometry")
    from shapely import affinity
    from ultraplot import legend as plegend

    monkeypatch.setattr(
        plegend,
        "_resolve_country_geometry",
        lambda code, resolution="110m", include_far=False: sgeom.box(0, 0, 2, 1),
    )
    fig, ax = uplt.subplots()
    handles0, _ = ax.geo_legend([("NLD", "country:NLD")], add=False)
    handles1, _ = ax.geo_legend(
        [("NLD", "country:NLD")],
        country_proj=lambda geom: affinity.scale(
            geom, xfact=2.0, yfact=1.0, origin=(0, 0)
        ),
        add=False,
    )
    w0 = np.ptp(handles0[0].get_path().vertices[:, 0])
    w1 = np.ptp(handles1[0].get_path().vertices[:, 0])
    assert w1 > w0

    handles2, _ = ax.geo_legend(
        [("NLD", "country:NLD")],
        add=False,
        country_proj="platecarree",
    )
    assert isinstance(handles2[0], mpatches.PathPatch)

    # Per-entry overrides via 3-tuples
    handles3, labels3 = ax.geo_legend(
        [
            ("Base", "country:NLD"),
            (
                "Wide",
                "country:NLD",
                {
                    "country_proj": lambda geom: affinity.scale(
                        geom, xfact=2.0, yfact=1.0, origin=(0, 0)
                    )
                },
            ),
            ("StringProj", "country:NLD", "platecarree"),
        ],
        add=False,
    )
    assert labels3 == ["Base", "Wide", "StringProj"]
    w_base = np.ptp(handles3[0].get_path().vertices[:, 0])
    w_wide = np.ptp(handles3[1].get_path().vertices[:, 0])
    assert w_wide > w_base
    uplt.close(fig)


def test_country_geometry_uses_dominant_component():
    sgeom = pytest.importorskip("shapely.geometry")
    from ultraplot import legend as plegend

    big = sgeom.box(4.0, 51.0, 7.0, 54.0)
    tiny_far = sgeom.box(-69.0, 12.0, -68.8, 12.2)
    geometry = sgeom.MultiPolygon([big, tiny_far])
    dominant = plegend._country_geometry_for_legend(geometry)
    assert dominant.equals(big)


def test_country_geometry_keeps_nearby_islands():
    sgeom = pytest.importorskip("shapely.geometry")
    from ultraplot import legend as plegend

    mainland = sgeom.box(4.0, 51.0, 7.0, 54.0)
    nearby_island = sgeom.box(5.0, 54.2, 5.2, 54.35)
    far_island = sgeom.box(-69.0, 12.0, -68.8, 12.2)
    geometry = sgeom.MultiPolygon([mainland, nearby_island, far_island])

    reduced = plegend._country_geometry_for_legend(geometry)
    geoms = list(getattr(reduced, "geoms", [reduced]))
    assert any(part.equals(mainland) for part in geoms)
    assert any(part.equals(nearby_island) for part in geoms)
    assert not any(part.equals(far_island) for part in geoms)


def test_country_geometry_can_include_far_territories():
    sgeom = pytest.importorskip("shapely.geometry")
    from ultraplot import legend as plegend

    mainland = sgeom.box(4.0, 51.0, 7.0, 54.0)
    far_island = sgeom.box(-69.0, 12.0, -68.8, 12.2)
    geometry = sgeom.MultiPolygon([mainland, far_island])
    kept = plegend._country_geometry_for_legend(geometry, include_far=True)
    geoms = list(getattr(kept, "geoms", [kept]))
    assert any(part.equals(mainland) for part in geoms)
    assert any(part.equals(far_island) for part in geoms)


def test_geo_axes_add_geometries_auto_legend():
    ccrs = pytest.importorskip("cartopy.crs")
    sgeom = pytest.importorskip("shapely.geometry")

    fig, ax = uplt.subplots(proj="cyl")
    ax.add_geometries(
        [sgeom.box(-20, -10, 20, 10)],
        ccrs.PlateCarree(),
        facecolor="blue7",
        edgecolor="blue9",
        label="Region",
    )
    leg = ax.legend(loc="best")
    labels = [text.get_text() for text in leg.get_texts()]
    assert "Region" in labels
    assert len(leg.legend_handles) == 1
    assert isinstance(leg.legend_handles[0], mpatches.PathPatch)
    uplt.close(fig)


@pytest.mark.mpl_image_compare
def test_semantic_legends_showcase_smoke(monkeypatch):
    """
    End-to-end smoke test showing semantic legend helpers in one figure:
    categorical, size, numeric-color, and geometry (generic + country shorthands).
    """
    sgeom = pytest.importorskip("shapely.geometry")
    from ultraplot import legend as plegend

    # Prefer real Natural Earth country geometries if available. In offline CI,
    # fall back to deterministic local geometries while still exercising shorthand.
    country_entries = [("Australia", "country:AU"), ("New Zealand", "country:NZ")]
    uses_real_countries = True
    try:
        fig_tmp, ax_tmp = uplt.subplots()
        ax_tmp.geo_legend(
            country_entries, edgecolor="black", facecolor="none", add=False
        )
        uplt.close(fig_tmp)
    except ValueError:
        uses_real_countries = False
        country_geoms = {
            "AU": sgeom.box(110, -45, 155, -10),
            "NZ": sgeom.box(166, -48, 179, -34),
        }

        def _fake_country(code):
            key = str(code).upper()
            if key not in country_geoms:
                raise ValueError(f"Unknown shorthand in test: {code!r}")
            return country_geoms[key]

        monkeypatch.setattr(plegend, "_resolve_country_geometry", _fake_country)

    fig, axs = uplt.subplots(ncols=2, nrows=2, share=False)

    leg = axs[0].cat_legend(
        ["A", "B", "C"],
        colors={"A": "red7", "B": "green7", "C": "blue7"},
        markers={"A": "o", "B": "s", "C": "^"},
        loc="best",
        title="cat_legend",
    )
    assert [text.get_text() for text in leg.get_texts()] == ["A", "B", "C"]

    leg = axs[1].size_legend(
        [10, 50, 200], color="gray6", loc="best", title="size_legend"
    )
    assert [text.get_text() for text in leg.get_texts()] == ["10", "50", "200"]

    leg = axs[2].num_legend(
        vmin=0.0,
        vmax=1.0,
        n=4,
        cmap="viridis",
        fmt="{:.2f}",
        loc="best",
        title="num_legend",
    )
    assert len(leg.legend_handles) == 4
    assert all(isinstance(handle, mpatches.Patch) for handle in leg.legend_handles)

    handles, labels = axs[3].geo_legend(
        [
            ("Triangle", "triangle"),
            ("Hexagon", "hexagon"),
            *country_entries,
        ],
        edgecolor="black",
        facecolor="none",
        add=False,
    )
    leg = axs[3].legend(handles, labels, loc="best", title="geo_legend")
    legend_labels = [text.get_text() for text in leg.get_texts()]
    assert set(legend_labels) == set(labels)
    assert len(legend_labels) == len(labels)
    assert all(isinstance(handle, mpatches.PathPatch) for handle in leg.legend_handles)
    if uses_real_countries:
        # Real shorthand resolution succeeded (no monkeypatched fallback).
        assert {"Australia", "New Zealand"}.issubset(set(legend_labels))
    return fig


def test_pie_legend_uses_wedge_handles():
    fig, ax = uplt.subplots()
    wedges, _ = ax.pie([30, 70], labels=["a", "b"])
    leg = ax.legend(wedges, ["a", "b"], loc="best")
    handles = leg.legend_handles
    assert len(handles) == 2
    assert all(isinstance(handle, mpatches.Wedge) for handle in handles)
    uplt.close(fig)


def test_pie_legend_handler_map_override():
    fig, ax = uplt.subplots()
    wedges, _ = ax.pie([30, 70], labels=["a", "b"])
    leg = ax.legend(
        wedges,
        ["a", "b"],
        loc="best",
        handler_map={mpatches.Wedge: mhandler.HandlerPatch()},
    )
    handles = leg.legend_handles
    assert len(handles) == 2
    assert all(isinstance(handle, mpatches.Rectangle) for handle in handles)
    uplt.close(fig)


def test_external_mode_toggle_enables_auto():
    """
    Toggling external mode back off should resume on-the-fly guide creation.
    """
    fig, ax = uplt.subplots()

    ax.set_external(True)
    (ha,) = ax.plot([0, 1], label="a", legend="b")
    assert getattr(ax[0], "legend_", None) is None  # deferred

    ax.set_external(False)
    (hb,) = ax.plot([0, 1], label="b", legend="b")
    # Now legend is queued for creation; verify it is registered in the outer legend dict
    assert ("bottom", "center") in ax[0]._legend_dict

    # Ensure final legend contains both entries
    leg = ax.legend([ha, hb], loc="b")
    labels = {t.get_text() for t in leg.get_texts()}
    assert {"a", "b"}.issubset(labels)
    uplt.close(fig)


def test_synthetic_handles_filtered():
    """
    Synthetic-tagged helper artists must be ignored by legend parsing even when
    explicitly passed as handles.
    """
    fig, ax = uplt.subplots()
    (h1,) = ax.plot([0, 1], label="visible")
    (h2,) = ax.plot([1, 0], label="helper")
    # Mark helper as synthetic; it should be filtered out from legend entries
    setattr(h2, "_ultraplot_synthetic", True)

    leg = ax.legend([h1, h2], loc="best")
    labels = [t.get_text() for t in leg.get_texts()]
    assert "visible" in labels
    assert "helper" not in labels
    uplt.close(fig)


def test_fill_between_included_in_legend():
    """
    Legitimate fill_between/area handles must appear in legends (regression for
    previously skipped FillBetweenPolyCollection).
    """
    fig, ax = uplt.subplots()
    x = np.arange(5)
    y1 = np.zeros(5)
    y2 = np.ones(5)
    ax.fill_between(x, y1, y2, label="band")

    leg = ax.legend(loc="best")
    labels = [t.get_text() for t in leg.get_texts()]
    assert "band" in labels
    uplt.close(fig)


def test_legend_span_bottom():
    """Test bottom legend with span parameter."""

    fig, axs = uplt.subplots(nrows=2, ncols=3)
    axs[0, 0].plot([], [], label="test")

    # Legend below row 1, spanning columns 1-2
    leg = fig.legend(ax=axs[0, :], span=(1, 2), loc="bottom")

    # Verify legend was created
    assert leg is not None


def test_legend_span_top():
    """Test top legend with span parameter."""

    fig, axs = uplt.subplots(nrows=2, ncols=3)
    axs[0, 0].plot([], [], label="test")

    # Legend above row 2, spanning columns 2-3
    leg = fig.legend(ax=axs[1, :], cols=(2, 3), loc="top")

    assert leg is not None


def test_legend_span_right():
    """Test right legend with rows parameter."""

    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    # Legend right of column 1, spanning rows 1-2
    leg = fig.legend(ax=axs[:, 0], rows=(1, 2), loc="right")

    assert leg is not None


def test_legend_span_left():
    """Test left legend with rows parameter."""

    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    # Legend left of column 2, spanning rows 2-3
    leg = fig.legend(ax=axs[:, 1], rows=(2, 3), loc="left")

    assert leg is not None


def test_legend_span_validation_left_with_cols_error():
    """Test that LEFT legend raises error with cols parameter."""

    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    with pytest.raises(ValueError, match="left.*vertical.*use 'rows='.*not 'cols='"):
        fig.legend(ax=axs[0, 0], cols=(1, 2), loc="left")


def test_legend_span_validation_right_with_cols_error():
    """Test that RIGHT legend raises error with cols parameter."""
    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    with pytest.raises(ValueError, match="right.*vertical.*use 'rows='.*not 'cols='"):
        fig.legend(ax=axs[0, 0], cols=(1, 2), loc="right")


def test_legend_span_validation_top_with_rows_error():
    """Test that TOP legend raises error with rows parameter."""
    fig, axs = uplt.subplots(nrows=2, ncols=3)
    axs[0, 0].plot([], [], label="test")

    with pytest.raises(ValueError, match="top.*horizontal.*use 'cols='.*not 'rows='"):
        fig.legend(ax=axs[0, 0], rows=(1, 2), loc="top")


def test_legend_span_validation_bottom_with_rows_error():
    """Test that BOTTOM legend raises error with rows parameter."""
    fig, axs = uplt.subplots(nrows=2, ncols=3)
    axs[0, 0].plot([], [], label="test")

    with pytest.raises(
        ValueError, match="bottom.*horizontal.*use 'cols='.*not 'rows='"
    ):
        fig.legend(ax=axs[0, 0], rows=(1, 2), loc="bottom")


def test_legend_span_validation_left_with_span_warns():
    """Test that LEFT legend with span parameter issues warning."""
    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    with pytest.warns(match="left.*vertical.*prefer 'rows='"):
        leg = fig.legend(ax=axs[0, 0], span=(1, 2), loc="left")
        assert leg is not None


def test_legend_span_validation_right_with_span_warns():
    """Test that RIGHT legend with span parameter issues warning."""
    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    with pytest.warns(match="right.*vertical.*prefer 'rows='"):
        leg = fig.legend(ax=axs[0, 0], span=(1, 2), loc="right")
        assert leg is not None


def test_legend_array_without_span():
    """Test that legend on array without span preserves original behavior."""
    fig, axs = uplt.subplots(nrows=2, ncols=2)
    axs[0, 0].plot([], [], label="test")

    # Should create legend for all axes in the array
    leg = fig.legend(ax=axs[:], loc="right")
    assert leg is not None


def test_legend_array_with_span():
    """Test that legend on array with span uses first axis + span extent."""
    fig, axs = uplt.subplots(nrows=2, ncols=3)
    axs[0, 0].plot([], [], label="test")

    # Should use first axis position with span extent
    leg = fig.legend(ax=axs[0, :], span=(1, 2), loc="bottom")
    assert leg is not None


def test_legend_row_without_span():
    """Test that legend on row without span spans entire row."""
    fig, axs = uplt.subplots(nrows=2, ncols=3)
    axs[0, 0].plot([], [], label="test")

    # Should span all 3 columns
    leg = fig.legend(ax=axs[0, :], loc="bottom")
    assert leg is not None


def test_legend_column_without_span():
    """Test that legend on column without span spans entire column."""
    fig, axs = uplt.subplots(nrows=3, ncols=2)
    axs[0, 0].plot([], [], label="test")

    # Should span all 3 rows
    leg = fig.legend(ax=axs[:, 0], loc="right")
    assert leg is not None


def test_legend_multiple_sides_with_span():
    """Test multiple legends on different sides with span control."""
    fig, axs = uplt.subplots(nrows=3, ncols=3)
    axs.plot([0, 1], [0, 1], label="line")

    # Create legends on all 4 sides with different spans
    leg_bottom = fig.legend(ref=axs[0, 0], span=(1, 2), loc="bottom")
    leg_top = fig.legend(ref=axs[1, 0], span=(2, 3), loc="top")
    leg_right = fig.legend(ref=axs[0, 0], rows=(1, 2), loc="right")
    leg_left = fig.legend(ref=axs[0, 1], rows=(2, 3), loc="left")

    assert leg_bottom is not None
    assert leg_top is not None
    assert leg_right is not None
    assert leg_left is not None


def test_legend_auto_collect_handles_labels_with_span():
    """Test automatic collection of handles and labels from multiple axes with span parameters."""

    fig, axs = uplt.subplots(nrows=2, ncols=2)

    # Create different plots in each subplot with labels
    axs[0, 0].plot([0, 1], [0, 1], label="line1")
    axs[0, 1].plot([0, 1], [1, 0], label="line2")
    axs[1, 0].scatter([0.5], [0.5], label="point1")
    axs[1, 1].scatter([0.5], [0.5], label="point2")

    # Test automatic collection with span parameter (no explicit handles/labels)
    leg = fig.legend(ax=axs[0, :], span=(1, 2), loc="bottom")

    # Verify legend was created and contains all handles/labels from both axes
    assert leg is not None
    assert len(leg.get_texts()) == 2  # Should have 2 labels (line1, line2)

    # Test with rows parameter
    leg2 = fig.legend(ax=axs[:, 0], rows=(1, 2), loc="right")
    assert leg2 is not None
    assert len(leg2.get_texts()) == 2  # Should have 2 labels (line1, point1)


def test_legend_explicit_handles_labels_override_auto_collection():
    """Test that explicit handles/labels override auto-collection."""

    fig, axs = uplt.subplots(nrows=1, ncols=2)

    # Create plots with labels
    (h1,) = axs[0].plot([0, 1], [0, 1], label="auto_label1")
    (h2,) = axs[1].plot([0, 1], [1, 0], label="auto_label2")

    # Test with explicit handles/labels (should override auto-collection)
    custom_handles = [h1]
    custom_labels = ["custom_label"]
    leg = fig.legend(
        ax=axs, span=(1, 2), loc="bottom", handles=custom_handles, labels=custom_labels
    )

    # Verify legend uses explicit handles/labels, not auto-collected ones
    assert leg is not None
    assert len(leg.get_texts()) == 1
    assert leg.get_texts()[0].get_text() == "custom_label"


def test_legend_ref_argument():
    """Test using 'ref' to decouple legend location from content axes."""
    fig, axs = uplt.subplots(nrows=2, ncols=2)
    axs[0, 0].plot([], [], label="line1")  # Row 0
    axs[1, 0].plot([], [], label="line2")  # Row 1

    # Place legend below Row 0 (axs[0, :]) using content from Row 1 (axs[1, :])
    leg = fig.legend(ax=axs[1, :], ref=axs[0, :], loc="bottom")

    assert leg is not None

    # Should be a single legend because span is inferred from ref
    assert not isinstance(leg, tuple)

    texts = [t.get_text() for t in leg.get_texts()]
    assert "line2" in texts
    assert "line1" not in texts


def test_legend_ref_argument_no_ax():
    """Test using 'ref' where 'ax' is implied to be 'ref'."""
    fig, axs = uplt.subplots(nrows=1, ncols=1)
    axs[0].plot([], [], label="line1")

    # ref provided, ax=None. Should behave like ax=ref.
    leg = fig.legend(ref=axs[0], loc="bottom")
    assert leg is not None

    # Should be a single legend
    assert not isinstance(leg, tuple)

    texts = [t.get_text() for t in leg.get_texts()]
    assert "line1" in texts


def test_ref_with_explicit_handles():
    """Test using ref with explicit handles and labels."""
    fig, axs = uplt.subplots(ncols=2)
    h = axs[0].plot([0, 1], [0, 1], label="line")

    # Place legend below both axes (ref=axs) using explicit handle
    leg = fig.legend(handles=h, labels=["explicit"], ref=axs, loc="bottom")

    assert leg is not None
    texts = [t.get_text() for t in leg.get_texts()]
    assert texts == ["explicit"]


def test_ref_with_non_edge_location():
    """Test using ref with an inset location (should not infer span)."""
    fig, axs = uplt.subplots(ncols=2)
    axs[0].plot([0, 1], label="test")

    # ref=axs (list of 2).
    # 'upper left' is inset. Should fallback to first axis.
    leg = fig.legend(ref=axs, loc="upper left")

    assert leg is not None
    if isinstance(leg, tuple):
        leg = leg[0]
    # Should be associated with axs[0] (or a panel of it? Inset is child of axes)
    # leg.axes is the axes containing the legend. For inset, it's the parent axes?
    # No, legend itself is an artist. leg.axes should be axs[0].
    assert leg.axes is axs[0]


def test_ref_with_single_axis():
    """Test using ref with a single axis object."""
    fig, axs = uplt.subplots(ncols=2)
    axs[0].plot([0, 1], label="line")

    # ref=axs[1]. loc='bottom'.
    leg = fig.legend(ref=axs[1], ax=axs[0], loc="bottom")
    assert leg is not None


def test_ref_with_manual_axes_no_subplotspec():
    """Test using ref with axes that don't have subplotspec."""
    fig = uplt.figure()
    ax1 = fig.add_axes([0.1, 0.1, 0.4, 0.4])
    ax2 = fig.add_axes([0.5, 0.1, 0.4, 0.4])
    ax1.plot([0, 1], [0, 1], label="line")
    # ref=[ax1, ax2]. loc='upper right' (inset).
    leg = fig.legend(ref=[ax1, ax2], loc="upper right")
    assert leg is not None


def _decode_panel_span(panel_ax, axis):
    ss = panel_ax.get_subplotspec().get_topmost_subplotspec()
    r1, r2, c1, c2 = ss._get_rows_columns()
    gs = ss.get_gridspec()
    if axis == "rows":
        r1, r2 = gs._decode_indices(r1, r2, which="h")
        return int(r1), int(r2)
    if axis == "cols":
        c1, c2 = gs._decode_indices(c1, c2, which="w")
        return int(c1), int(c2)
    raise ValueError(f"Unknown axis {axis!r}.")


def _anchor_axis(ref):
    if np.iterable(ref) and not isinstance(ref, (str, UAxes)):
        return next(iter(ref))
    return ref


@pytest.mark.parametrize(
    "first_loc, first_ref, second_loc, second_ref, span_axis",
    [
        ("b", lambda axs: axs[0], "r", lambda axs: axs[:, 1], "rows"),
        ("r", lambda axs: axs[:, 2], "b", lambda axs: axs[1, :], "cols"),
        ("t", lambda axs: axs[2], "l", lambda axs: axs[:, 0], "rows"),
        ("l", lambda axs: axs[:, 0], "t", lambda axs: axs[1, :], "cols"),
    ],
)
def test_legend_span_inference_with_multi_panels(
    first_loc, first_ref, second_loc, second_ref, span_axis
):
    fig, axs = uplt.subplots(nrows=3, ncols=3)
    axs.plot([0, 1], [0, 1], label="line")

    fig.legend(ref=first_ref(axs), loc=first_loc)
    fig.legend(ref=second_ref(axs), loc=second_loc)

    side_map = {"l": "left", "r": "right", "t": "top", "b": "bottom"}
    anchor = _anchor_axis(second_ref(axs))
    panel_ax = anchor._panel_dict[side_map[second_loc]][-1]
    span = _decode_panel_span(panel_ax, span_axis)
    assert span == (0, 2)


def test_legend_best_axis_selection_right_left():
    fig, axs = uplt.subplots(nrows=1, ncols=3)
    axs.plot([0, 1], [0, 1], label="line")
    ref = [axs[0, 0], axs[0, 2]]

    fig.legend(ref=ref, loc="r", rows=1)
    assert len(axs[0, 2]._panel_dict["right"]) == 1
    assert len(axs[0, 0]._panel_dict["right"]) == 0

    fig.legend(ref=ref, loc="l", rows=1)
    assert len(axs[0, 0]._panel_dict["left"]) == 1
    assert len(axs[0, 2]._panel_dict["left"]) == 0


def test_legend_best_axis_selection_top_bottom():
    fig, axs = uplt.subplots(nrows=2, ncols=1)
    axs.plot([0, 1], [0, 1], label="line")
    ref = [axs[0, 0], axs[1, 0]]

    fig.legend(ref=ref, loc="t", cols=1)
    assert len(axs[0, 0]._panel_dict["top"]) == 1
    assert len(axs[1, 0]._panel_dict["top"]) == 0

    fig.legend(ref=ref, loc="b", cols=1)
    assert len(axs[1, 0]._panel_dict["bottom"]) == 1
    assert len(axs[0, 0]._panel_dict["bottom"]) == 0


def test_legend_span_decode_fallback(monkeypatch):
    fig, axs = uplt.subplots(nrows=2, ncols=2)
    axs.plot([0, 1], [0, 1], label="line")
    ref = axs[:, 0]

    gs = axs[0, 0].get_subplotspec().get_topmost_subplotspec().get_gridspec()

    def _raise_decode(*args, **kwargs):
        raise ValueError("forced")

    monkeypatch.setattr(gs, "_decode_indices", _raise_decode)
    leg = fig.legend(ref=ref, loc="r")
    assert leg is not None


def test_legend_span_inference_skips_invalid_ref_axes():
    class DummyNoSpec:
        pass

    class DummyNullSpec:
        def get_subplotspec(self):
            return None

    fig, axs = uplt.subplots(nrows=1, ncols=2)
    axs[0].plot([0, 1], [0, 1], label="line")
    ref = [DummyNoSpec(), DummyNullSpec(), axs[0]]

    leg = fig.legend(ax=axs[0], ref=ref, loc="r")
    assert leg is not None
    assert len(axs[0]._panel_dict["right"]) == 1


def test_legend_best_axis_fallback_with_inset_loc():
    fig, axs = uplt.subplots(nrows=1, ncols=2)
    axs.plot([0, 1], [0, 1], label="line")

    leg = fig.legend(ref=axs, loc="upper left", rows=1)
    assert leg is not None


def test_legend_best_axis_fallback_empty_iterable_ref():
    class LegendProxy:
        def __init__(self, ax):
            self._ax = ax

        def __iter__(self):
            return iter(())

        def legend(self, *args, **kwargs):
            return self._ax.legend(*args, **kwargs)

    fig, ax = uplt.subplots()
    ax.plot([0, 1], [0, 1], label="line")
    proxy = LegendProxy(ax)

    leg = fig.legend(ref=proxy, loc="upper left", rows=1)
    assert leg is not None
