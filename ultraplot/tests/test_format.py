#!/usr/bin/env python3
"""
Test format and rc behavior.
"""

import locale, numpy as np, ultraplot as uplt, pytest
import warnings


def test_format_is_the_only_entry_point():
    """Axes classes define and compose the public format method directly."""
    from ultraplot.axes import (
        Axes,
        CartesianAxes,
        ExternalAxesContainer,
        GeoAxes,
        PolarAxes,
        TaylorAxes,
    )

    for cls in (
        Axes,
        CartesianAxes,
        ExternalAxesContainer,
        GeoAxes,
        PolarAxes,
        TaylorAxes,
    ):
        assert "format" in cls.__dict__
        assert not hasattr(cls, "_format_impl")
        assert cls.format.__name__ == "format"
        assert cls.format.__qualname__ == f"{cls.__qualname__}.format"

    fig, axs = uplt.subplots()
    axs[0].format(title="Public format")
    assert axs[0].get_title() == "Public format"


def test_super_format_uses_exact_base_implementation():
    """A base-qualified call cannot bypass sharing through dynamic dispatch."""
    from ultraplot.axes import CartesianAxes

    fig, axs = uplt.subplots(nrows=2, share=True)
    before = fig.get_axis_sharing()

    with pytest.raises(TypeError, match="Unexpected keyword"):
        super(CartesianAxes, axs[0]).format(xlim=(2, 3))

    assert fig.get_axis_sharing() == before
    assert axs[0].get_xlim() == (0, 1)
    assert axs[1].get_xlim() == (0, 1)


def test_nested_format_uses_one_sharing_transaction(monkeypatch):
    """Projection inheritance composes format without repeating sharing updates."""
    fig, axs = uplt.subplots(proj="taylor")
    calls = []
    update = axs[0]._update_format_sharing

    def record(keys):
        calls.append(keys)
        return update(keys)

    monkeypatch.setattr(axs[0], "_update_format_sharing", record)
    axs[0].format(title="Taylor diagram")

    assert len(calls) == 1


# def test_colormap_assign():
#     """
#     Test below line is possible and naming schemes.
#     """
#     uplt.rc["image.cmap"] = uplt.Colormap("phase", shift=180, left=0.2)
#     assert uplt.rc["cmap"] == uplt.rc["cmap.sequential"] == "_Phase_copy_s"
#     uplt.rc["image.cmap"] = uplt.Colormap("magma", reverse=True, right=0.8)
#     assert uplt.rc["image.cmap"] == uplt.rc["cmap.sequential"] == "_magma_copy_r"


@pytest.mark.skip(reason="This is failing on github but not locally")
def test_ignored_keywords():
    """
    Test ignored keywords and functions.
    """
    with warnings.catch_warnings(record=True) as record:
        fig, ax = uplt.subplots(
            gridspec_kw={"left": 3},
            subplot_kw={"proj": "cart"},
            subplotpars={"left": 0.2},
        )
    # only capture ultraplot warnings not general mpl warnings, e.g. deprecation warnings
    record = [r for r in record if "UltraPlotWarning" in str(r)]
    assert len(record) == 3
    with warnings.catch_warnings(record=True) as record:
        fig.subplots_adjust(left=0.2)
    assert len(record) == 1


@pytest.mark.mpl_image_compare
def test_init_format():
    """
    Test application of format args on initialization.
    """
    fig, axs = uplt.subplots(
        ncols=2,
        xlim=(0, 10),
        xlabel="xlabel",
        abc=True,
        title="Subplot title",
        collabels=["Column 1", "Column 2"],
        suptitle="Figure title",
    )
    axs[0].format(hatch="xxx", hatchcolor="k", facecolor="blue3")
    return fig


@pytest.mark.mpl_image_compare
def test_patch_format():
    """
    Test application of patch args on initialization.
    """
    fig = uplt.figure(suptitle="Super title", share=0)
    fig.subplot(
        121, proj="cyl", labels=True, land=True, latlines=20, abcloc="l", abc="[A]"
    )
    fig.subplot(
        122,
        facecolor="gray1",
        color="red",
        titleloc="l",
        title="Hello",
        abcloc="l",
        abc="[A]",
        xticks=0.1,
        yformatter="scalar",
    )
    return fig


@pytest.mark.mpl_image_compare
def test_multi_formatting(rng):
    """
    Support formatting in multiple projections.
    """
    # Mix Cartesian with a projection
    fig, axs = uplt.subplots(ncols=2, proj=("cart", "cyl"), share=0)
    axs[0].pcolormesh(rng.random((5, 5)))

    # Warning is raised based on projection. Cart does not have lonlim, latllim or labels
    with pytest.warns(uplt.warnings.UltraPlotWarning):
        fig.format(
            land=1,
            labels=1,
            lonlim=(0, 90),
            latlim=(0, 90),
            xlim=(0, 10),
            ylim=(0, 10),
        )
        axs[:1].format(
            land=1,
            labels=1,
            lonlim=(0, 90),
            latlim=(0, 90),
            xlim=(0, 10),
            ylim=(0, 10),
        )
    return fig


@pytest.mark.mpl_image_compare
def test_inner_title_zorder():
    """
    Test prominence of contour labels and whatnot.
    """
    fig, ax = uplt.subplots()
    ax.format(
        title="TITLE", titleloc="upper center", titleweight="bold", titlesize="xx-large"
    )
    ax.format(xlim=(0, 1), ylim=(0, 1))
    ax.text(
        0.5,
        0.95,
        "text",
        ha="center",
        va="top",
        color="red",
        weight="bold",
        size="xx-large",
    )
    x = [[0.4, 0.6]] * 2
    y = z = [[0.9, 0.9], [1.0, 1.0]]
    ax.contour(
        x,
        y,
        z,
        color="k",
        labels=True,
        levels=None,
        labels_kw={"color": "blue", "weight": "bold", "size": "xx-large"},
    )
    return fig


def test_transfer_label_preserves_dest_font_properties():
    """
    Test that repeated _transfer_label calls do not overwrite dest's updated font properties.
    """
    import matplotlib.pyplot as plt
    from ultraplot.internals.labels import _transfer_label

    fig, ax = plt.subplots()
    src = ax.text(0.1, 0.5, "Source", fontsize=10, fontweight="bold", color="red")
    dest = ax.text(0.9, 0.5, "Dest", fontsize=12, fontweight="normal", color="blue")

    # First transfer: dest gets src's font properties
    _transfer_label(src, dest)
    assert dest.get_fontsize() == 10
    assert dest.get_fontweight() == "bold"
    assert dest.get_text() == "Source"

    # Change dest's font size
    dest.set_fontsize(20)

    # Second transfer: dest's font size should be preserved
    src.set_text("New Source")
    _transfer_label(src, dest)
    assert dest.get_fontsize() == 20  # Should not be overwritten by src
    assert dest.get_fontweight() == "bold"  # Still from src originally
    assert dest.get_text() == "New Source"


@pytest.mark.mpl_image_compare
def test_font_adjustments():
    """
    Test font name application. Somewhat hard to do.
    """
    fig, axs = uplt.subplots(ncols=2)
    axs.format(
        abc="A.",
        fontsize=15,
        fontname="Fira Math",
        xlabel="xlabel",
        ylabel="ylabel",
        title="Title",
        figtitle="Figure title",
        collabels=["Column 1", "Column 2"],
    )
    return fig


@pytest.mark.mpl_image_compare
def test_axes_colors():
    """
    Test behavior of passing color to format.
    """
    fig, axs = uplt.subplots(
        ncols=3,
        nrows=2,
        share=False,
        proj=("cyl", "cart", "polar", "cyl", "cart", "polar"),
        wratios=(2, 2, 1),
    )
    axs[:, 0].format(labels=True)
    axs[:3].format(edgecolor="red", gridlabelsize="med-large", gridlabelweight="bold")
    axs[:3].format(color="red")  # without this just colors the edge
    axs[1].format(xticklabelcolor="gray")
    # axs[2].format(ticklabelcolor='red')
    axs[1].format(tickcolor="blue")
    axs[3:].format(color="red")  # ensure propagates
    # axs[-1].format(gridlabelcolor='green')  # should work
    return fig


@pytest.mark.parametrize("loc", ["en_US.UTF-8"])
@pytest.mark.mpl_image_compare
def test_locale_formatting(loc):
    """
    Ensure locale formatting works. Also zerotrim should account
    for non-period decimal separators.
    """
    # dealing with read the docs
    original_locale = locale.getlocale()
    try:
        try:
            locale.setlocale(locale.LC_ALL, loc)
        except locale.Error:
            pytest.skip(f"Locale {loc} not available on this system")

        # Your test code that is sensitive to the locale settings
        assert locale.getlocale() == (loc.split(".")[0], loc.split(".")[1])

        with uplt.rc.context(
            {"formatter.use_locale": True, "formatter.zerotrim": True}
        ):
            fig, ax = uplt.subplots()
            ticks = uplt.arange(-1, 1, 0.1)
            ax.format(ylim=(min(ticks), max(ticks)), yticks=ticks)
        return fig
    finally:
        # Always reset to the original locale
        locale.setlocale(locale.LC_ALL, original_locale)


@pytest.mark.mpl_image_compare
def test_bounds_ticks():
    """
    Test spine bounds and location. Previously applied `fixticks`
    automatically but no longer the case.
    """
    fig, ax = uplt.subplots()
    # ax.format(xlim=(-10, 10))
    ax.format(xloc="top")
    ax.format(xlim=(-10, 15), xbounds=(0, 10))
    return fig


@pytest.mark.mpl_image_compare
def test_cutoff_ticks():
    """
    Test spine cutoff ticks.
    """
    fig, ax = uplt.subplots()
    # ax.format(xlim=(-10, 10))
    ax.format(xlim=(-10, 10), xscale=("cutoff", 0, 2), xloc="top", fixticks=True)
    ax.axvspan(0, 100, facecolor="k", alpha=0.1)
    return fig


@pytest.mark.mpl_image_compare
def test_spine_side(rng):
    """
    Test automatic spine selection when passing `xspineloc` or `yspineloc`.
    """
    fig, ax = uplt.subplots()
    ax.plot(uplt.arange(-5, 5), (10 * rng.random((11, 5)) - 5).cumsum(axis=0))
    ax.format(xloc="bottom", yloc="zero")
    ax.alty(loc="right")
    return fig


@pytest.mark.mpl_image_compare
def test_spine_offset():
    """
    Test offset axes.
    """
    fig, ax = uplt.subplots()
    ax.format(xloc="none")  # test none instead of neither
    ax.alty(loc=("axes", -0.2), color="red")
    # ax.alty(loc=('axes', 1.2), color='blue')
    ax.alty(loc=("axes", -0.4), color="blue")
    ax.alty(loc=("axes", 1.1), color="green")
    return fig


@pytest.mark.mpl_image_compare
def test_tick_direction():
    """
    Test tick direction arguments.
    """
    fig, axs = uplt.subplots(ncols=2)
    axs[0].format(tickdir="in")
    axs[1].format(xtickdirection="inout", ytickdir="out")  # rc setting should be used?
    return fig


@pytest.mark.mpl_image_compare
def test_tick_length():
    """
    Test tick length args. Ensure ratios can be applied successively.
    """
    fig, ax = uplt.subplots()
    ax.format(yticklen=100)
    ax.format(xticklen=50, yticklenratio=0.1)
    return fig


@pytest.mark.mpl_image_compare
def test_tick_width():
    """
    Test tick width args. Ensure ratios can be applied successively, setting
    width to `zero` adjusts length for label padding, and ticks can appear
    without spines if requested.
    """
    fig, axs = uplt.subplots(ncols=2, nrows=2, share=False)
    ax = axs[0]
    ax.format(linewidth=2, ticklen=20, xtickwidthratio=1)
    ax.format(ytickwidthratio=0.3)
    ax = axs[1]
    ax.format(axeslinewidth=0, ticklen=20, tickwidth=2)  # should permit ticks
    ax = axs[2]
    ax.format(tickwidth=0, ticklen=50)  # should set length to zero
    ax = axs[3]
    ax.format(linewidth=0, ticklen=20, tickwidth="5em")  # should override linewidth
    return fig


@pytest.mark.mpl_image_compare
def test_tick_labels(rng):
    """
    Test default and overwriting properties of auto tick labels.
    """
    import pandas as pd

    data = rng.random((5, 3))
    data = pd.DataFrame(data, index=["foo", "bar", "baz", "bat", "bot"])
    fig, axs = uplt.subplots(abc="A.", abcloc="ul", ncols=2, refwidth=3, span=False)
    for i, ax in enumerate(axs):
        data.index.name = "label"
        if i == 1:
            ax.format(xformatter="null")  # overrides result
        ax.bar(data, autoformat=True)
        if i == 0:
            data.index = ["abc", "def", "ghi", "jkl", "mno"]
            data.index.name = "foobar"  # label should be updated
        ax.bar(-data, autoformat=True)
    return fig


@pytest.mark.mpl_image_compare
def test_label_settings():
    """
    Test label colors and ensure color change does not erase labels.
    """
    fig, ax = uplt.subplots()
    ax.format(xlabel="xlabel", ylabel="ylabel")
    ax.format(labelcolor="red")
    return fig


def test_format_distributes_axis_label_sequences_and_reduces_sharing():
    """Per-axes labels retain shared limits but override label sharing."""
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=True)
    axs.format(
        title=["First", "Second", "Third", "Fourth"],
        xlabel=["First x", "Second x", "Third x", "Fourth x"],
        ylabel=["First y", "Second y", "Third y", "Fourth y"],
    )
    fig.canvas.draw()

    assert [ax.get_title() for ax in axs] == ["First", "Second", "Third", "Fourth"]
    assert [ax.get_xlabel() for ax in axs] == [
        "First x",
        "Second x",
        "Third x",
        "Fourth x",
    ]
    assert [ax.get_ylabel() for ax in axs] == [
        "First y",
        "Second y",
        "Third y",
        "Fourth y",
    ]
    assert fig._sharex_limits and fig._sharey_limits
    assert not fig._sharex_labels and not fig._sharey_labels
    assert all(ax.xaxis.label.get_visible() for ax in axs)
    assert all(ax.yaxis.label.get_visible() for ax in axs)
    axs[0].set_xlim(1, 2)
    axs[0].set_ylim(3, 4)
    assert axs[2].get_xlim() == (1, 2)
    assert axs[1].get_ylim() == (3, 4)


def test_format_short_title_sequence_formats_prefix():
    """Short title sequences format the first axes and leave the rest alone."""
    fig, axs = uplt.subplots(ncols=4)
    axs[2].format(title="Existing")
    axs[3].format(title="Existing")
    axs.format(title=["First", "Second"])

    assert [ax.get_title() for ax in axs] == [
        "First",
        "Second",
        "Existing",
        "Existing",
    ]


def test_orthogonal_axis_sharing_controls():
    """Limits can be shared while axis-title and tick-label sharing stay off."""
    fig, axs = uplt.subplots(
        nrows=2,
        share=0,
        sharexlimits=True,
        sharexlabels=False,
        sharexticklabels=False,
    )
    axs.format(xlabel=["Upper x", "Lower x"])
    fig.canvas.draw()

    assert fig._sharex == 2
    assert fig._sharex_limits
    assert not fig._sharex_labels
    assert not fig._sharex_ticklabels
    assert [ax.get_xlabel() for ax in axs] == ["Upper x", "Lower x"]
    axs[0].set_xlim(1, 2)
    assert axs[1].get_xlim() == (1, 2)


def test_format_axes_mapping_uses_one_based_selectors():
    """Axes mappings format selected axes and preserve native style dictionaries."""
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=True)
    axs.format(
        title={1: "First", (3, 4): "Last"},
        xlabel={2: "Second x"},
        ylim={1: (0, 2), 4: (0, 4)},
        title_kw={"color": "red"},
        labelcolor={1: "blue"},
    )

    assert [ax.get_title() for ax in axs] == ["First", "", "Last", "Last"]
    assert [ax.get_xlabel() for ax in axs] == ["", "Second x", "", ""]
    assert axs[0].get_ylim() == (0, 2)
    assert axs[3].get_ylim() == (0, 4)
    assert axs[0]._title_dict[axs[0]._title_loc].get_color() == "red"
    assert axs[0].xaxis.label.get_color() == "blue"
    assert axs[0].yaxis.label.get_color() == "blue"
    assert axs[1].xaxis.label.get_color() != "blue"
    assert not fig._sharex_labels
    assert not fig._sharey_labels
    assert not fig._sharey_limits
    assert fig._sharey == 0


def test_figure_format_subset_scalar_label_creates_shared_group():
    """Direct figure subset formatting shares one label across the subset."""
    fig, axs = uplt.subplots(nrows=3, share=True, span=False)

    fig.format(axs=axs[:2], xlabel="Subset x")
    fig.canvas.draw()

    assert all(ax.get_xlabel().strip() == "" for ax in axs[:2])
    assert any(label.get_text() == "Subset x" for label in fig._supxlabel_dict.values())
    assert fig._sharex_labels


@pytest.mark.parametrize(
    ("projection", "key"),
    ((None, "lonlim"), ("cyl", "xlim")),
)
def test_unsupported_sparse_mapping_preserves_sharing(projection, key):
    """Ignored projection-specific mappings cannot change sharing state."""
    kwargs = {} if projection is None else {"proj": projection}
    fig, axs = uplt.subplots(nrows=2, share=True, **kwargs)
    before = fig.get_axis_sharing()

    with pytest.warns(uplt.warnings.UltraPlotWarning, match="Ignoring unused"):
        fig.format(**{key: {1: (0, 1)}})

    assert fig.get_axis_sharing() == before


@pytest.mark.parametrize(
    ("projection", "key"),
    ((None, "lonlim"), ("cyl", "xlim")),
)
def test_unsupported_direct_format_preserves_sharing(projection, key):
    """Projection-specific filtering also applies to direct axes calls."""
    kwargs = {} if projection is None else {"proj": projection}
    fig, axs = uplt.subplots(nrows=2, share=True, **kwargs)
    before = fig.get_axis_sharing()

    with pytest.raises(TypeError):
        axs[0].format(**{key: (0, 1)})

    assert fig.get_axis_sharing() == before


def test_mixed_projection_subset_only_considers_supported_targets():
    """An unsupported selected axis cannot detach another projection's group."""
    fig, axs = uplt.subplots(nrows=3, proj=(None, "cyl", "cyl"), share=True)
    before = fig.get_axis_sharing("x")

    fig.format(axs=axs[:2], xlim=(2, 3))

    assert axs[0].get_xlim() == (2, 3)
    assert fig.get_axis_sharing("x") == before
    assert axs[1].get_shared_x_axes().joined(axs[1], axs[2])


@pytest.mark.parametrize("syntax", ("direct", "mapping", "sequence"))
def test_invalid_limit_preserves_sharing(syntax):
    """Validation precedes every sharing state transition."""
    fig, axs = uplt.subplots(nrows=2, share=True)
    before = fig.get_axis_sharing()

    with pytest.raises(ValueError, match="Must be 2-tuple"):
        if syntax == "direct":
            axs[0].format(xlim=(0, 1, 2))
        elif syntax == "mapping":
            fig.format(xlim={1: (0, 1, 2)})
        else:
            fig.format(xlim=((0, 1), (0, 1, 2)))

    assert fig.get_axis_sharing() == before


@pytest.mark.parametrize("syntax", ("direct", "figure"))
def test_failed_scale_format_restores_sharing(syntax):
    """Projection errors roll back sharing policy and topology."""
    fig, axs = uplt.subplots(nrows=2, share=True)
    before = fig.get_axis_sharing()

    with pytest.raises(ValueError):
        if syntax == "direct":
            axs[0].format(xscale="definitely-not-a-scale")
        else:
            fig.format(axs=axs[:1], xscale="definitely-not-a-scale")

    assert fig.get_axis_sharing() == before
    assert axs[0].get_shared_x_axes().joined(axs[0], axs[1])


def test_local_label_in_singleton_direction_preserves_sharing_state():
    """A local label only reduces a direction with actual shared siblings."""
    fig, axs = uplt.subplots(ncols=2, share=True)
    before = fig.get_axis_sharing("x")

    axs[0].format(xlabel="Local x")

    assert fig.get_axis_sharing("x") == before
    assert axs[0].get_xlabel() == "Local x"


def test_indexed_format_updates_axis_sharing():
    """Formatting one axes updates sharing like a sparse figure-level mapping."""
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=True)
    axs[0].format(ylabel="Local y")

    assert not fig._sharey_labels
    assert fig._sharey_limits
    axs[0].set_ylim(1, 2)
    assert axs[1].get_ylim() == (1, 2)
    axs[0].format(ylim=(3, 4))
    assert not fig._sharey_limits
    assert not fig._sharey_ticklabels
    assert fig._sharey == 0
    assert axs[0].get_ylim() == (3, 4)
    assert axs[1].get_ylim() == (1, 2)


def test_indexed_limit_format_restores_interior_ticklabels():
    """Local limits restore tick labels previously hidden by global sharing."""
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=True)
    fig.canvas.draw()
    assert not axs[0]._is_ticklabel_on("labelbottom")

    axs[2].format(xlim=(-1, 0))
    fig.canvas.draw()

    assert axs[0]._is_ticklabel_on("labelbottom")
    assert fig._sharex == 1
    assert axs[0].get_xlim() == (0, 1)
    assert axs[2].get_xlim() == (-1, 0)
    assert 1 in axs[0].get_xticks()
    assert "1" in [label.get_text() for label in axs[0].get_xticklabels()]


def test_indexed_formatter_restores_interior_ticklabels():
    """Local formatters restore labels hidden by sharing on every mpl version."""
    fig, axs = uplt.subplots(nrows=2, share=True)
    fig.canvas.draw()
    assert not axs[0]._is_ticklabel_on("labelbottom")

    axs[1].format(xformatter="null")
    fig.canvas.draw()

    assert axs[0]._is_ticklabel_on("labelbottom")
    assert axs[1]._is_ticklabel_on("labelbottom")
    assert all(not label.get_text() for label in axs[1].get_xticklabels())


def test_indexed_unshared_direction_preserves_figure_sharing():
    """Local formatting only reduces a direction with actual shared siblings."""
    fig, axs = uplt.subplots(ncols=2, share=True)
    before = fig.get_axis_sharing("x")

    axs[1].format(xformatter="null")

    assert fig.get_axis_sharing("x") == before
    assert len(axs[1].get_shared_x_axes().get_siblings(axs[1])) == 1


def test_indexed_ylim_restores_interior_ticklabels():
    """The ticker-detachment behavior is symmetric for y axes."""
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=True)
    fig.canvas.draw()
    assert not axs[1]._is_ticklabel_on("labelleft")

    axs[1].format(ylim=(-1, 0))
    fig.canvas.draw()

    assert fig._sharey == 1
    assert axs[1]._is_ticklabel_on("labelleft")
    assert axs[0].get_ylim() == (0, 1)
    assert axs[1].get_ylim() == (-1, 0)
    assert 1 in axs[0].get_yticks()
    assert "1" in [label.get_text() for label in axs[0].get_yticklabels()]


@pytest.mark.parametrize("which", ("x", "y"))
def test_unshared_tickers_are_independent_and_bound_to_owner(which):
    """Detached tickers must not retain another axes as their data source."""
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=True)
    axs[2 if which == "x" else 1].format(**{f"{which}lim": (-1, 0)})

    tickers = [getattr(ax, f"{which}axis").major for ax in axs]
    assert len({id(ticker) for ticker in tickers}) == len(axs)
    for ax, ticker in zip(axs, tickers):
        axis = getattr(ax, f"{which}axis")
        assert ticker.locator.axis is axis
        assert ticker.formatter.axis is axis


def test_local_limits_remain_independent_after_repeated_updates():
    """Later limit updates cannot leak after an indexed format call detaches axes."""
    fig, axs = uplt.subplots(nrows=2, share=True)
    axs[1].format(xlim=(-1, 0))
    axs[0].set_xlim(2, 3)
    assert axs[0].get_xlim() == (2, 3)
    assert axs[1].get_xlim() == (-1, 0)

    axs[1].set_xlim(-3, -2)
    assert axs[0].get_xlim() == (2, 3)
    assert axs[1].get_xlim() == (-3, -2)


def test_sparse_limit_mapping_detaches_tickers_for_every_axes():
    """Sparse dict formatting gives selected and unselected axes valid locators."""
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=True)
    axs.format(xlim={3: (-1, 0)})
    fig.canvas.draw()

    assert fig._sharex == 1
    assert [ax.get_xlim() for ax in axs] == [(0, 1), (0, 1), (-1, 0), (0, 1)]
    assert 1 in axs[0].get_xticks()
    assert -1 in axs[2].get_xticks()
    assert all(ax.xaxis.major.locator.axis is ax.xaxis for ax in axs)


def test_limit_sequence_gives_every_axes_an_independent_ticker():
    """Each item in a limit sequence gets an independently evaluated ticker."""
    limits = [(0, 1), (1, 2), (2, 3), (3, 4)]
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=True)
    axs.format(xlim=limits)
    fig.canvas.draw()

    for ax, lim in zip(axs, limits):
        assert ax.get_xlim() == lim
        assert np.isclose(ax.get_xticks(), lim[0]).any()
        assert np.isclose(ax.get_xticks(), lim[1]).any()
        assert ax.xaxis.major.locator.axis is ax.xaxis


def test_sharing_level_tracks_each_indexed_component_transition():
    """The numeric level follows the highest active orthogonal component."""
    fig, axs = uplt.subplots(nrows=2, share=True)
    axs[0].format(xlabel="Local x")
    assert fig._sharex == 3
    assert not fig._sharex_labels

    axs[0].format(xticklabelloc="bottom")
    assert fig._sharex == 2
    assert not fig._sharex_ticklabels

    axs[0].format(xlim=(-1, 0))
    assert fig._sharex == 0
    assert not fig._sharex_limits


def test_explicit_ticklabel_location_survives_later_limit_detach():
    """Restoring shared tick labels must preserve an explicit local opt-out."""
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=True)
    fig.canvas.draw()
    axs[1].format(xticklabelloc="neither")
    axs[2].format(xlim=(-1, 0))
    fig.canvas.draw()

    assert axs[0]._is_ticklabel_on("labelbottom")
    assert not axs[1]._is_ticklabel_on("labelbottom")
    assert not axs[1]._is_ticklabel_on("labeltop")


def test_indexed_tick_location_only_disables_ticklabel_sharing():
    """Local tick-label placement retains shared numeric limits."""
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=True)
    fig.canvas.draw()

    axs[0].format(xticklabelloc="bottom")
    fig.canvas.draw()

    assert fig._sharex_limits
    assert not fig._sharex_ticklabels
    assert fig._sharex == 2
    assert axs[0]._is_ticklabel_on("labelbottom")
    axs[0].set_xlim(2, 3)
    assert axs[2].get_xlim() == (2, 3)


def test_singleton_grid_format_updates_axis_sharing():
    """A one-item grid slice has the same sharing semantics as direct indexing."""
    fig, axs = uplt.subplots(nrows=2, share=True)
    axs[:1].format(xlim=(2, 3), ylabel="Local y")

    assert not fig._sharex_limits
    # These vertically stacked axes do not participate in a y-sharing group,
    # so a local ylabel does not contradict the nominal y-sharing setting.
    assert fig._sharey_labels
    assert axs[0].get_ylabel() == "Local y"
    assert axs[0].get_xlim() == (2, 3)
    assert axs[1].get_xlim() != (2, 3)


@pytest.mark.parametrize(
    ("key", "limits", "shared_attr", "unaffected_attr", "getter", "sibling"),
    (
        (
            "xlim",
            [(0, 1), (0, 2), (0, 3), (0, 4)],
            "_sharex",
            "_sharey",
            "get_xlim",
            2,
        ),
        (
            "ylim",
            [(0, 5), (0, 6), (0, 7), (0, 8)],
            "_sharey",
            "_sharex",
            "get_ylim",
            1,
        ),
    ),
)
def test_format_distributes_limit_sequences_and_unshares(
    key, limits, shared_attr, unaffected_attr, getter, sibling
):
    """Per-axes limits disable sharing only in the corresponding direction."""
    fig, axs = uplt.subplots(nrows=2, ncols=2, share=True)
    axs.format(**{key: limits})
    fig.canvas.draw()

    assert getattr(fig, shared_attr) == 1
    assert getattr(fig, unaffected_attr) == 3
    assert not getattr(fig, f"{shared_attr}_limits")
    assert not getattr(fig, f"{shared_attr}_ticklabels")
    assert getattr(fig, f"{shared_attr}_labels")
    assert getattr(fig, f"{unaffected_attr}_limits")
    assert [getattr(ax, getter)() for ax in axs] == limits
    shared = getattr(axs[0], f"get_shared_{key[0]}_axes")()
    assert not shared.joined(axs[0], axs[sibling])


def test_colormap_parsing():
    """Test colormaps merging"""
    reds = uplt.colormaps.get_cmap("reds")
    blues = uplt.colormaps.get_cmap("blues")

    # helper function to test specific values in the colormaps
    # threshold is used due to rounding errors
    def test_range(
        a: uplt.Colormap,
        b: uplt.Colormap,
        threshold=1e-10,
        ranges=[0.0, 1.0],
    ):
        for i in ranges:
            if not np.allclose(a(i), b(i)):
                raise ValueError(f"Colormaps differ !")

    # Test if the colormaps are the same
    test_range(uplt.Colormap("blues"), blues)
    test_range(uplt.Colormap("reds"), reds)
    # For joint colormaps, the lower value should be the lower of the first cmap and the highest should be the highest of the second cmap
    test_range(uplt.Colormap("blues", "reds"), reds, ranges=[1.0])
    # Note: the ranges should not match either of the original colormaps
    with pytest.raises(ValueError):
        test_range(uplt.Colormap("blues", "reds"), reds)


def test_input_parsing_cycle():
    """
    Test the potential inputs to cycle
    """
    # The first argument is a string or an iterable of strings
    with pytest.raises(ValueError):
        cycle = uplt.Cycle(None)

    # Empty should also be handled
    cycle = uplt.Cycle()

    # Test singular string
    cycle = uplt.Cycle("Blues")
    target = uplt.colormaps.get_cmap("blues")
    first_color = cycle.get_next()["color"]
    first_color = uplt.colors.to_rgba(first_color)
    assert np.allclose(first_color, target(0))

    # Test composition
    cycle = uplt.Cycle("Blues", "Reds", N=2)
    lower_half = uplt.colormaps.get_cmap("blues")
    upper_half = uplt.colormaps.get_cmap("reds")
    first_color = uplt.colors.to_rgba(cycle.get_next()["color"])
    last_color = uplt.colors.to_rgba(cycle.get_next()["color"])
    assert np.allclose(first_color, lower_half(0.0))
    assert np.allclose(last_color, upper_half(1.0))


def test_scaler():
    # Test a ultraplot scaler and a matplotlib native scaler; should not race errors
    fig, ax = uplt.subplots(ncols=2, share=0)
    ax[0].set_yscale("mercator")
    ax[1].set_yscale("asinh")
    uplt.close(fig)


@pytest.mark.mpl_image_compare
def test_outer_labels():
    """
    Produces a plot where the abc loc is in top left or top right of a plot. Padding can be used for finer adjustment if necessary.
    """
    fig, ax = uplt.subplots(ncols=2)
    ax[0].format(
        abc="a.",
        abcloc="ol",
        title="testing",
    )
    ax[1].format(
        abc="a.",
        abcloc="outer right",
        title="testing",
        abcpad=-0.25,
    )
    return fig


def test_abc_padding():
    """
    Test the specific calculation for ABC padding in title positioning.
    """
    fig, ax = uplt.subplots()

    # Set up test scenario
    ax.set_title("Test Title")
    ax.format(
        title="Testing",
        abc="a.",
        abcloc="or",
    )
    # Get initial position
    initial_abc_x = ax.axes._title_dict["abc"].get_position()[0]

    # Pad the position and check the offset
    padding_value = 12

    ax.format(
        title="Testing",
        abc="a.",
        abcloc="or",
        abcpad=padding_value,
    )
    fig.canvas.draw()

    # Verify the new position
    new_abc_x = ax.axes._title_dict["abc"].get_position()[0]

    # Assert position has changed
    assert new_abc_x != initial_abc_x, "ABC padding didn't affect position"

    # Reset padding and position
    ax.format(
        title="Testing",
        abc="a.",
        abcloc="or",
        abcpad=0,
    )
    fig.canvas.draw()
    reference_position = ax.axes._title_dict["abc"].get_position()[0]

    # Apply padding again
    ax.format(
        title="Testing",
        abc="a.",
        abcloc="or",
        abcpad=padding_value,
    )
    # Verify the exact offset matches our expectation
    actual_offset = ax.axes._title_dict["abc"].get_position()[0] - reference_position
    diff = actual_offset - ax.axes._abc_pad  # Note pad is signed!
    assert np.allclose(diff, -padding_value), "ABC padding offset calculation incorrect"
    uplt.close(fig)


@pytest.mark.mpl_image_compare
def test_unequal_abc_padding():
    """Check if labels are pushed out based on the largest labl length"""
    fig, ax = uplt.subplots(ncols=2, nrows=2, share=0)
    ax[0, 0].set_yscale("asinh")
    ax[1, 0].set_yscale("mercator")
    ax[1, 1].set_yscale("logit")
    ax.format(abc="a.", abcloc="ol")
    return fig


def test_abc_with_labels():
    """
    This test should check the "normal" conditions in which the yaxis has labels and the location for abc is adjusted for the outer labels (left or right)
    """
    fig, ax = uplt.subplots()
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(["one", "two", "three"])
    ax.format(abc="a.", abcloc="ol")
    uplt.close(fig)


def test_abc_number():
    """
    Test handling of `abc` with lists of labels that exceed or match the number of axes.
    """
    # The keyword `abc` can take on lists, if the lists exceeds the number of the axes
    with pytest.raises(ValueError):
        fig, ax = uplt.subplots(ncols=3)
        ax.format(abc=["a", "bb"])
    # This should work fine
    fig, ax = uplt.subplots(ncols=2)
    ax.format(abc=["a", "b"])
    uplt.close(fig)


def test_loc_positions():
    """
    Test all locations the abc labels can be in
    """
    from ultraplot.internals.rcsetup import TEXT_LOCS

    fig, ax = uplt.subplots()
    ax.set_title(
        "Dummy title"
    )  # trigger sync with abc to ensure they both move correctly
    for loc in TEXT_LOCS:
        ax.format(abc="a.", abcloc=loc)
    uplt.close(fig)


@pytest.mark.parametrize("angle", [0, 45, 89, 63, 90])
def test_axis_label_anchor(angle):
    """
    Check if the rotation of the xticklabels is correctly handle by xrotation and yrotation
    """
    fig, ax = uplt.subplots(ncols=2)
    ax[0].format(xrotation=angle, yrotation=angle)

    # Need fixed ticks for it to work (set locator explicitly)
    ax[1].set_xticks(ax[1].get_xticks())
    ax[1].set_yticks(ax[1].get_yticks())

    kw = dict()
    if angle in (0, 90, -90):
        kw["ha"] = "right"
    ax[1].set_xticklabels(
        ax[1].get_xticklabels(), rotation=angle, rotation_mode="anchor", **kw
    )
    ax[1].set_yticklabels(
        ax[1].get_yticklabels(), rotation=angle, rotation_mode="anchor", **kw
    )

    # Ticks should be in the same position
    for tick1, tick2 in zip(ax[0].get_xticklabels(), ax[1].get_xticklabels()):
        assert tick1.get_rotation() == angle
        assert tick2.get_rotation() == angle
        assert tick1.get_position()[0] == tick2.get_position()[0]
        assert tick1.get_position()[1] == tick2.get_position()[1]

    for tick1, tick2 in zip(ax[0].get_yticklabels(), ax[1].get_yticklabels()):
        assert tick1.get_rotation() == angle
        assert tick2.get_rotation() == angle
        assert tick1.get_position()[0] == tick2.get_position()[0]
        assert tick1.get_position()[1] == tick2.get_position()[1]
