import warnings
from unittest import mock

import numpy as np
import pytest

import ultraplot as uplt


@pytest.mark.mpl_image_compare
def test_geographic_single_projection():
    fig = uplt.figure(refwidth=3)
    axs = fig.subplots(nrows=2, proj="robin", proj_kw={"lon_0": 180})
    axs.format(
        suptitle="Figure with single projection",
        land=True,
        latlines=30,
        lonlines=60,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_geographic_multiple_projections():
    fig = uplt.figure(share=0)
    # Add projections
    gs = uplt.GridSpec(ncols=2, nrows=3, hratios=(1, 1, 1.4))
    for i, proj in enumerate(("cyl", "hammer", "npstere")):
        ax1 = fig.subplot(gs[i, 0], proj=proj, basemap=True)  # basemap
        ax2 = fig.subplot(gs[i, 1], proj=proj)  # cartopy

    # Format projections
    fig.format(
        land=True,
        suptitle="Figure with several projections",
        toplabels=("Basemap projections", "Cartopy projections"),
        toplabelweight="normal",
        latlines=30,
        lonlines=60,
        lonlabels="b",
        latlabels="r",  # or lonlabels=True, labels=True, etc.
    )
    fig.subplotgrid[-2:].format(
        latlines=20,
        lonlines=30,
        labels=True,
    )  # dense gridlines for polar plots
    uplt.rc.reset()
    return fig


@pytest.mark.mpl_image_compare
def test_drawing_in_projection_without_globe(rng):
    # Fake data with unusual longitude seam location and without coverage over poles
    offset = -40
    lon = uplt.arange(offset, 360 + offset - 1, 60)
    lat = uplt.arange(-60, 60 + 1, 30)
    data = rng.random((len(lat), len(lon)))

    globe = False
    string = "with" if globe else "without"
    gs = uplt.GridSpec(nrows=2, ncols=2)
    fig = uplt.figure(refwidth=2.5)
    for i, ss in enumerate(gs):
        ax = fig.subplot(ss, proj="kav7", basemap=(i % 2))
        cmap = ("sunset", "sunrise")[i % 2]
        if i > 1:
            ax.pcolor(lon, lat, data, cmap=cmap, globe=globe, extend="both")
        else:
            m = ax.contourf(lon, lat, data, cmap=cmap, globe=globe, extend="both")
            fig.colorbar(m, loc="b", span=i + 1, label="values", extendsize="1.7em")
    fig.format(
        suptitle=f"Geophysical data {string} global coverage",
        toplabels=("Cartopy example", "Basemap example"),
        leftlabels=("Filled contours", "Grid boxes"),
        toplabelweight="normal",
        leftlabelweight="normal",
        coast=True,
        lonlines=90,
        abc="A.",
        abcloc="ul",
        abcborder=False,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_drawing_in_projection_with_globe(rng):
    # Fake data with unusual longitude seam location and without coverage over poles
    offset = -40
    lon = uplt.arange(offset, 360 + offset - 1, 60)
    lat = uplt.arange(-60, 60 + 1, 30)
    data = rng.random((len(lat), len(lon)))

    globe = True
    string = "with" if globe else "without"
    gs = uplt.GridSpec(nrows=2, ncols=2)
    fig = uplt.figure(refwidth=2.5)
    for i, ss in enumerate(gs):
        ax = fig.subplot(ss, proj="kav7", basemap=(i % 2))
        cmap = ("sunset", "sunrise")[i % 2]
        if i > 1:
            ax.pcolor(lon, lat, data, cmap=cmap, globe=globe, extend="both")
        else:
            m = ax.contourf(lon, lat, data, cmap=cmap, globe=globe, extend="both")
            fig.colorbar(m, loc="b", span=i + 1, label="values", extendsize="1.7em")
    fig.format(
        suptitle=f"Geophysical data {string} global coverage",
        toplabels=("Cartopy example", "Basemap example"),
        leftlabels=("Filled contours", "Grid boxes"),
        toplabelweight="normal",
        leftlabelweight="normal",
        coast=True,
        lonlines=90,
        abc="A.",
        abcloc="ul",
        abcborder=False,
    )
    return fig


@pytest.mark.mpl_image_compare
def test_geoticks():

    lonlim = (-140, 60)
    latlim = (-10, 50)
    basemap_projection = uplt.Proj(
        "cyl",
        lonlim=lonlim,
        latlim=latlim,
        backend="basemap",
    )
    fig, ax = uplt.subplots(
        ncols=3,
        proj=(
            "cyl",  # cartopy
            "cyl",  # cartopy
            basemap_projection,  # basemap
        ),
        share=0,
    )
    settings = dict(land=True, labels=True, lonlines=20, latlines=20)
    # Shows sensible "default"; uses cartopy backend to show the grid lines with ticks
    ax[0].format(
        lonlim=lonlim,
        latlim=latlim,
        **settings,
    )

    # Add lateral ticks only
    ax[1].format(
        latticklen=True,
        gridminor=True,
        lonlim=lonlim,
        latlim=latlim,
        **settings,
    )

    ax[2].format(
        latticklen=5.0,
        lonticklen=2.0,
        grid=False,
        gridminor=False,
        **settings,
    )
    return fig


def test_geoticks_input_handling(recwarn):
    fig, ax = uplt.subplots(proj="aeqd")
    # Should warn that about non-rectilinear projection.
    with pytest.warns(uplt.warnings.UltraPlotWarning):
        ax.format(lonticklen=True)
    # When set to None the latticks are not added.
    # No warnings should be raised.
    ax.format(lonticklen=None)
    assert len(recwarn) == 0
    # Can parse a string
    ax.format(lonticklen="1em")


def test_geoticks_label_shorthand_lb_no_warning(recwarn):
    fig, ax = uplt.subplots(proj="cyl")
    ax.format(land=True, lonlines=30, latlines=30, labels="lb")
    assert len(recwarn) == 0
    assert ax[0].xaxis.get_ticks_position() == "bottom"
    assert ax[0].yaxis.get_ticks_position() == "left"
    uplt.close(fig)


def test_toggle_ticks_supports_bool_and_sequence_specs():
    fig, ax = uplt.subplots(proj="cyl")
    geo = ax[0]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", uplt.warnings.UltraPlotWarning)
        geo._toggle_ticks(True, "x")
        assert geo.xaxis.get_ticks_position() == "bottom"
        geo._toggle_ticks((True, True), "x")
        assert geo.xaxis.get_ticks_position() in ("both", "default")
        geo._toggle_ticks(("left", "bottom"), "x")
        assert geo.xaxis.get_ticks_position() == "bottom"

        geo._toggle_ticks(True, "y")
        assert geo.yaxis.get_ticks_position() == "left"
        geo._toggle_ticks((True, True), "y")
        assert geo.yaxis.get_ticks_position() in ("both", "default")
        geo._toggle_ticks(("left", "bottom"), "y")
        assert geo.yaxis.get_ticks_position() == "left"

    assert not caught
    uplt.close(fig)


@pytest.mark.parametrize(
    ("layout", "lonlabels", "latlabels"),
    [
        ([1, 2], "tb", "lr"),
        ([1, 2], "r", "t"),
        ([[1, 2, 3], [4, 5, 3]], "t", "lr"),
    ],
)
@pytest.mark.mpl_image_compare
def test_geoticks_shared(layout, lonlabels, latlabels):
    fig, ax = uplt.subplots(layout, proj="cyl", share="all")
    ax.format(
        latlim=(0, 10),  # smaller rangers are quicker
        lonlim=(0, 10),
        lonlines=10,
        latlines=10,
        land=True,  # enable land
        labels=True,  # enable tick labels
        latticklen=True,  # show ticks
        lonticklen=True,  # show ticks
        grid=True,
        gridminor=False,
        lonlabels=lonlabels,
        latlabels=latlabels,
    )
    return fig


def test_geoticks_shared_non_rectilinear():
    with pytest.warns(uplt.warnings.UltraPlotWarning):
        fig, ax = uplt.subplots(ncols=2, proj="aeqd", share="all")
        ax.format(
            land=True,
            labels=True,
            lonlabels="all",
            latlabels="all",
        )
        fig.canvas.draw()  # draw is necessary to invoke the warning
    uplt.close(fig)


def test_lon0_shifts():
    """
    Check if a shift with lon0 actually shifts the
    view port labels and ticks
    """
    # Note for small enough shifts, e.g. +- 10 we are
    # still showing zero due to the formatting logic
    fig, ax = uplt.subplots(proj="cyl", proj_kw=dict(lon_0=90))
    ax.format(land=True, labels=True)
    locator = ax[0]._lonaxis.get_major_locator()
    formatter = ax[0]._lonaxis.get_major_formatter()
    locs = locator()
    formatted_ticks = np.array([formatter(x) for x in locs])
    for loc, format in zip(locs, formatted_ticks):
        # Get normalized coordinates
        loc = (loc + 180) % 360 - 180
        # Check if the labels are matching the location
        # abs is taken due to north-west
        str_loc = str(abs(int(loc)))
        n = len(str_loc)
        assert str_loc == format[:n], f"Epxected: {str_loc}, got: {format[:n]}"
    assert locs[0] != 0  # we should not be a 0 anymore
    uplt.close(fig)


@pytest.mark.parametrize(
    "layout, expectations",
    [
        (
            # layout 1: 3x3 grid with unique IDs
            [
                [1, 2, 3],
                [4, 5, 6],
                [7, 8, 9],
            ],
            # expectations: per element ID (1-9), four booleans: [top, right, bottom, left]
            [
                [True, False, False, True],  # 1
                [True, False, False, False],  # 2
                [True, False, True, False],  # 3
                [False, False, False, True],  # 4
                [False, False, False, False],  # 5
                [False, False, True, False],  # 6
                [False, True, False, True],  # 7
                [False, True, False, False],  # 8
                [False, True, True, False],  # 9
            ],
        ),
        (
            # layout 2: shared IDs (merged subplots?)
            [
                [1, 2, 0],
                [1, 2, 5],
                [3, 4, 5],
                [3, 4, 0],
            ],
            # expectations for IDs 1–5: [top, right, bottom, left]
            [
                [True, False, False, True],  # 1
                [True, False, True, False],  # 2
                [False, True, False, True],  # 3
                [False, True, True, False],  # 4
                [True, True, True, True],  # 5
            ],
        ),
    ],
)
def test_sharing_cartopy(layout, expectations):
    def are_labels_on(ax, which=["top", "bottom", "right", "left"]) -> tuple[bool]:
        gl = ax.gridlines_major

        on = [False, False, False, False]
        for idx, labeler in enumerate(which):
            if getattr(gl, f"{labeler}_labels"):
                on[idx] = True
        return on

    settings = dict(land=True, ocean=True, labels="both")
    fig, ax = uplt.subplots(layout, share="all", proj="cyl")
    ax.format(**settings)
    fig.canvas.draw()  # needed for sharing labels
    for axi in ax:
        state = are_labels_on(axi)
        expectation = expectations[axi.number - 1]
        for i, j in zip(state, expectation):
            assert i == j
    uplt.close(fig)


def test_toggle_gridliner_labels():
    """
    Test whether we can toggle the labels on or off
    """
    # Cartopy backend
    fig, ax = uplt.subplots(proj="cyl", backend="cartopy")
    ax[0]._toggle_gridliner_labels(labelleft=False, labelbottom=False)
    gl = ax[0].gridlines_major

    assert gl.left_labels == False
    assert gl.right_labels == False
    assert gl.top_labels == False
    assert gl.bottom_labels == False
    ax[0]._toggle_gridliner_labels(labeltop=True)
    assert gl.top_labels == True
    uplt.close(fig)

    # Basemap backend
    fig, ax = uplt.subplots(proj="cyl", backend="basemap")
    ax.format(land=True, labels="both")  # need this otherwise no labels are printed
    ax[0]._toggle_gridliner_labels(
        labelleft=False,
        labelbottom=False,
        labelright=False,
        labeltop=False,
    )
    gl = ax[0].gridlines_major

    # All label are off
    for gli in gl:
        for _, (line, labels) in gli.items():
            for label in labels:
                assert label.get_visible() == False

    # Should be off
    ax[0]._toggle_gridliner_labels(labeltop=True)
    # Gridliner labels are not added for the top (and I guess right for GeoAxes).
    # Need to figure out how this is set in matplotlib
    dir_labels = ax[0]._get_gridliner_labels(
        left=True, right=True, top=True, bottom=True
    )
    for dir, labels in dir_labels.items():
        expectation = False
        if dir in "top":
            expectation = True
        for label in labels:
            assert label.get_visible() == expectation
    uplt.close(fig)


def test_geo_panel_group_respects_figure_share():
    """
    Ensure that panel-only configurations do not promote sharing when figure-level
    sharing is disabled, and do promote when figure-level sharing is enabled for GeoAxes.
    """
    # Right-only panels with share=False should NOT mark y panel-group
    fig, ax = uplt.subplots(nrows=2, proj="cyl", share=False)
    ax[0].panel("right")
    fig.canvas.draw()
    assert ax[0]._panel_sharey_group is False

    # Right-only panels with share='labels' SHOULD mark y panel-group
    fig2, ax2 = uplt.subplots(nrows=2, proj="cyl", share="labels")
    ax2[0].panel("right")
    fig2.canvas.draw()
    assert ax2[0]._panel_sharey_group is True

    # Top-only panels with share=False should NOT mark x panel-group
    fig3, ax3 = uplt.subplots(ncols=2, proj="cyl", share=False)
    ax3[0].panel("top")
    fig3.canvas.draw()
    assert ax3[0]._panel_sharex_group is False

    # Top-only panels with share='labels' SHOULD mark x panel-group
    fig4, ax4 = uplt.subplots(ncols=2, proj="cyl", share="labels")
    ax4[0].panel("top")
    fig4.canvas.draw()
    assert ax4[0]._panel_sharex_group is True


def test_geo_panel_share_flag_controls_membership():
    """
    Panels created with share=False should not join panel share groups even when
    the figure has sharing enabled, for GeoAxes as well.
    """
    # Y panels: right-only with panel share=False
    fig, ax = uplt.subplots(nrows=2, proj="cyl", share="labels")
    ax[0].panel("right", share=False)
    fig.canvas.draw()
    assert ax[0]._panel_sharey_group is False

    # X panels: top-only with panel share=False
    fig2, ax2 = uplt.subplots(ncols=2, proj="cyl", share="labels")
    ax2[0].panel("top", share=False)
    fig2.canvas.draw()
    assert ax2[0]._panel_sharex_group is False


def test_geo_subset_share_xlabels_override():
    fig, ax = uplt.subplots(ncols=2, nrows=2, proj="cyl", share="labels", span=False)
    # GeoAxes.format does not accept xlabel/ylabel; set labels directly.
    ax[0, 0].set_xlabel("Top-left X")
    ax[0, 1].set_xlabel("Top-right X")
    bottom = ax[1, :]
    bottom[0].set_xlabel("Bottom-row X")
    bottom.format(share_xlabels=list(bottom))

    fig.canvas.draw()

    assert not ax[0, 0].xaxis.get_label().get_visible()
    assert not ax[0, 1].xaxis.get_label().get_visible()
    assert bottom[0].get_xlabel().strip() == ""
    assert bottom[1].get_xlabel().strip() == ""
    assert any(lab.get_text() == "Bottom-row X" for lab in fig._supxlabel_dict.values())

    uplt.close(fig)


def test_geo_subset_share_xlabels_implicit():
    fig, ax = uplt.subplots(ncols=2, nrows=2, proj="cyl", share="labels", span=False)
    ax[0, 0].set_xlabel("Top-left X")
    ax[0, 1].set_xlabel("Top-right X")
    bottom = ax[1, :]
    bottom[0].set_xlabel("Bottom-row X")
    bottom.share_labels(axis="x")

    fig.canvas.draw()

    assert not ax[0, 0].xaxis.get_label().get_visible()
    assert not ax[0, 1].xaxis.get_label().get_visible()
    assert bottom[0].get_xlabel().strip() == ""
    assert bottom[1].get_xlabel().strip() == ""
    assert any(lab.get_text() == "Bottom-row X" for lab in fig._supxlabel_dict.values())

    uplt.close(fig)


def test_geo_non_rectilinear_right_panel_forces_no_share_and_warns():
    """
    Non-rectilinear Geo projections should not allow panel sharing; adding a right panel
    should warn and force panel share=False, and not promote the main axes to y panel group.
    """
    fig, ax = uplt.subplots(nrows=1, proj="aeqd", share="labels")
    with pytest.warns(uplt.warnings.UltraPlotWarning):
        pax = ax[0].panel("right")  # should warn and force share=False internally
    fig.canvas.draw()
    assert ax[0]._panel_sharey_group is False
    assert pax._panel_share is False


def test_geo_non_rectilinear_top_panel_forces_no_share_and_warns():
    """
    Non-rectilinear Geo projections should not allow panel sharing; adding a top panel
    should warn and force panel share=False, and not promote the main axes to x panel group.
    """
    fig, ax = uplt.subplots(ncols=1, proj="aeqd", share="labels")
    with pytest.warns(uplt.warnings.UltraPlotWarning):
        pax = ax[0].panel("top")  # should warn and force share=False internally
    fig.canvas.draw()
    assert ax[0]._panel_sharex_group is False
    assert pax._panel_share is False


def test_sharing_geo_limits():
    """
    Test that we can share limits on GeoAxes
    """
    fig, ax = uplt.subplots(
        ncols=2,
        proj="cyl",
        share=False,
    )
    expectation = dict(
        lonlim=(-10, 10),
        latlim=(-13, 15),
    )
    ax.format(land=True)
    ax[0].format(**expectation)

    before_lon = ax[1]._lonaxis.get_view_interval()
    before_lat = ax[1]._lataxis.get_view_interval()

    # Need to set this otherwise will be skipped
    fig._sharey = 3
    ax[0]._sharey_setup(ax[1])  # manually call setup
    ax[0]._sharey_limits(ax[1])  # manually call sharing limits
    # Limits should now be shored for lat but not for lon
    after_lat = ax[1]._lataxis.get_view_interval()

    # We are sharing y which is the latitude axis
    assert all(
        [np.allclose(i, j, atol=1e-6) for i, j in zip(expectation["latlim"], after_lat)]
    )
    # We are not sharing longitude yet
    assert all(
        [
            not np.allclose(i, j)
            for i, j in zip(expectation["lonlim"], ax[1]._lonaxis.get_view_interval())
        ]
    )

    ax[0]._sharex_setup(ax[1])
    ax[0]._sharex_limits(ax[1])
    after_lon = ax[1]._lonaxis.get_view_interval()

    assert all([not np.allclose(i, j) for i, j in zip(before_lon, after_lon)])
    assert all(
        [np.allclose(i, j, atol=1e-6) for i, j in zip(after_lon, expectation["lonlim"])]
    )
    uplt.close(fig)


def test_copy_locator_props():
    """
    When sharing axes the locator properties need
    to move as well.
    """

    fig, ax = uplt.subplots(ncols=2, proj="cyl", share=0)

    g1 = ax[0]._lonaxis
    g2 = ax[1]._lonaxis
    props = [
        "isDefault_majloc",
        "isDefault_minloc",
        "isDefault_majfmt",
    ]
    for prop in props:
        assert hasattr(g1, prop)
        assert hasattr(g2, prop)
        setattr(g1, prop, False)
        setattr(g2, prop, True)

    # The copy happens when the properties between g1 and g2 differ. Note this copies from g1 to g2.
    g1._copy_locator_properties(g2)
    for prop in props:
        assert getattr(g1, prop) == False
        assert getattr(g1, prop) == getattr(g2, prop)


def test_turn_off_tick_labels_basemap():
    """
    Check if we can toggle the labels off for GeoAxes
    with a basemap backend.
    """
    fig, ax = uplt.subplots(proj="cyl", backend="basemap")
    ax.format(labels="both")
    locators = ax[0].gridlines_major

    def test_if_labels_are(is_on, locator):
        from matplotlib import text as mtext

        for loc, objects in locator.items():
            for object in objects:
                if isinstance(object, list) and len(objects) > 0:
                    object = object[0]
                if isinstance(object, mtext.Text):
                    assert object.get_visible() == is_on

    # Check if the labels are on
    for locator in locators:
        test_if_labels_are(is_on=True, locator=locator)

    # Turn off both the labels
    for locator in locators:
        ax[0]._turnoff_tick_labels(locator)

    # Check if  are off
    for locator in locators:
        test_if_labels_are(is_on=False, locator=locator)
    uplt.close(fig)


def test_get_gridliner_labels_cartopy():
    from itertools import product

    fig, ax = uplt.subplots(proj="cyl", backend="cartopy")
    ax.format(labels="both")
    bools = [True, False]

    for bottom, top, left, right in product(bools, bools, bools, bools):
        ax[0]._toggle_gridliner_labels(
            labelleft=left,
            labelright=right,
            labeltop=top,
            labelbottom=bottom,
        )
        fig.canvas.draw()  # need draw to retrieve the labels
        labels = ax[0]._get_gridliner_labels(
            bottom=bottom,
            top=top,
            left=left,
            right=right,
        )
        for dir, is_on in zip(
            "bottom top left right".split(), [bottom, top, left, right]
        ):
            if is_on:
                assert len(labels.get(dir, [])) > 0
            else:
                assert len(labels.get(dir, [])) == 0
    uplt.close(fig)


def test_get_gridliner_labels_basemap():
    fig, ax = uplt.subplots(proj="cyl", backend="basemap")
    ax.format(labels="both", lonlines=30, latlines=30)
    fig.canvas.draw()  # ensure labels are positioned
    labels = ax[0]._get_gridliner_labels(bottom=True, top=True, left=True, right=True)
    assert labels.get("bottom")
    assert labels.get("top")
    assert labels.get("left")
    assert labels.get("right")
    uplt.close(fig)


def test_toggle_gridliner_labels_basemap():
    fig, ax = uplt.subplots(proj="cyl", backend="basemap")
    ax[0].format(labels="both", lonlines=30, latlines=30)
    fig.canvas.draw()

    ax[0]._toggle_gridliner_labels(
        labelbottom=False,
        labeltop=True,
        labelleft=True,
        labelright=True,
    )
    labels = ax[0]._get_gridliner_labels(bottom=True, top=True, left=True, right=True)
    assert labels.get("bottom")
    assert labels.get("top")
    assert labels.get("left")
    assert labels.get("right")
    assert all(not label.get_visible() for label in labels["bottom"])
    assert any(label.get_visible() for label in labels["top"])
    assert any(label.get_visible() for label in labels["left"])
    assert any(label.get_visible() for label in labels["right"])
    uplt.close(fig)


@pytest.mark.parametrize("backend", ["cartopy", "basemap"])
def test_tick_params_updates_gridliner(backend):
    fig, ax = uplt.subplots(proj="cyl", backend=backend)
    ax[0].format(lonlines=30, latlines=30, labels=True, grid=True)
    ax[0].tick_params(
        labelcolor="red",
        labelsize=8,
        labelrotation=15,
        pad=6,
        colors="blue",
        width=1.5,
        labelbottom=False,
        labelleft=False,
    )

    assert not ax[0]._is_ticklabel_on("labelbottom")
    assert not ax[0]._is_ticklabel_on("labelleft")

    if ax[0]._name == "cartopy":
        gl = ax[0].gridlines_major
        assert gl.collection_kwargs.get("color") == "blue"
        assert gl.collection_kwargs.get("linewidth") == 1.5
        assert gl.xlabel_style.get("color") == "red"
        assert gl.ylabel_style.get("color") == "red"
        assert gl.xlabel_style.get("fontsize") == 8
        assert gl.ylabel_style.get("fontsize") == 8
        assert gl.xlabel_style.get("rotation") == 15
        assert gl.ylabel_style.get("rotation") == 15
        if hasattr(gl, "xpadding"):
            assert gl.xpadding == 6
        if hasattr(gl, "ypadding"):
            assert gl.ypadding == 6
    else:  # basemap
        from matplotlib import colors as mcolors
        from matplotlib import text as mtext

        lonlines, latlines = ax[0].gridlines_major
        label_colors = []
        label_sizes = []
        label_rotations = []
        line_colors = []
        line_widths = []
        for grid in (lonlines, latlines):
            for _, (lines, labels) in grid.items():
                for line in lines:
                    if hasattr(line, "get_color"):
                        line_colors.append(mcolors.to_rgba(line.get_color()))
                    if hasattr(line, "get_linewidth"):
                        line_widths.append(line.get_linewidth())
                for label in labels:
                    if isinstance(label, mtext.Text):
                        label_colors.append(mcolors.to_rgba(label.get_color()))
                        label_sizes.append(label.get_fontsize())
                        label_rotations.append(label.get_rotation())
        expected_label_color = mcolors.to_rgba("red")
        expected_line_color = mcolors.to_rgba("blue")
        assert label_colors and all(c == expected_label_color for c in label_colors)
        assert label_sizes and all(np.isclose(s, 8) for s in label_sizes)
        assert label_rotations and all(np.isclose(r, 15) for r in label_rotations)
        assert line_colors and all(c == expected_line_color for c in line_colors)
        assert line_widths and all(np.isclose(w, 1.5) for w in line_widths)

    uplt.close(fig)


@pytest.mark.parametrize("backend", ["cartopy", "basemap"])
def test_gridliner_adapter_refresh(backend):
    fig, ax = uplt.subplots(proj="cyl", backend=backend)
    ax[0].format(lonlines=30, latlines=30, labels=True)
    assert ax[0]._gridliner_adapter("major", create=False) is not None

    ax[0]._gridliner_adapters.pop("major", None)
    assert ax[0]._gridliner_adapter("major", create=False) is None
    _ = ax[0].gridlines_major
    assert ax[0]._gridliner_adapter("major", create=False) is not None
    uplt.close(fig)


@pytest.mark.parametrize("backend", ["cartopy", "basemap"])
def test_gridliner_tick_positions(backend):
    fig, ax = uplt.subplots(proj="cyl", backend=backend)
    ax[0].format(lonlines=30, latlines=30, labels=True, grid=True)
    fig.canvas.draw()
    lon_positions = ax[0]._gridliner_tick_positions("x", which="major")
    lat_positions = ax[0]._gridliner_tick_positions("y", which="major")
    assert len(lon_positions) > 0
    assert len(lat_positions) > 0

    if ax[0]._name == "cartopy":
        expected_lon = ax[0]._get_lonticklocs()
        expected_lat = ax[0]._get_latticklocs()
        assert np.allclose(lon_positions, expected_lon)
        assert np.allclose(lat_positions, expected_lat)
    else:  # basemap
        lonlines, latlines = ax[0].gridlines_major
        expected_lon = np.sort(np.asarray(list(lonlines.keys())))
        expected_lat = np.sort(np.asarray(list(latlines.keys())))
        assert np.allclose(np.sort(lon_positions), expected_lon)
        assert np.allclose(np.sort(lat_positions), expected_lat)

    uplt.close(fig)


@pytest.mark.parametrize("level", [0, 1, 2, 3, 4])
def test_sharing_levels(level):
    """
    We can share limits or labels.
    We check if we can do both for the GeoAxes.
    """
    # We can share labels, limits, scale or all
    # For labels we share the axis labels but nothing else
    # Limits shares both labels and ticks
    # Scale (= True) will also share the scale
    # All does all the ticks across all plots
    # (not necessarily on same line)
    #
    # Succinctly this means that for
    # - share = 0: no sharing takes place, each
    # axis have their tick labels and data limits are their
    # own
    # - share = 1: x and y labels are shared but nothing else
    # - share = 2: ticks are shared  but still are shown
    # - share = 3: ticks are shared and turned of for the ticks
    # facing towards the "inside"
    # - share = 4: ticks are shared, and the data limits are the same

    x = np.array([0, 10])
    y = np.array([0, 10])
    lonlim = latlim = np.array((-10, 10))

    def assert_views_are_sharing(ax):
        # We are testing a 2x2 grid here
        match ax.number - 1:
            # Note ax.number is idx + 1
            case 0:
                targets = [1, 2]
                sharing_x = [False, True]
                sharing_y = [True, False]
            case 1:
                targets = [0, 3]
                sharing_x = [False, True]
                sharing_y = [True, False]
            case 2:
                targets = [0, 3]
                sharing_x = [True, False]
                sharing_y = [False, True]
            case 3:
                targets = [1, 2]
                sharing_x = [True, False]
                sharing_y = [False, True]
        lonview = ax._lonaxis.get_view_interval()
        latview = ax._lataxis.get_view_interval()
        for target, share_x, share_y in zip(targets, sharing_x, sharing_y):
            other = ax.figure.axes[target]
            target_lon = other._lonaxis.get_view_interval()
            target_lat = other._lataxis.get_view_interval()

            l1 = np.linalg.norm(
                np.asarray(lonview) - np.asarray(target_lon),
            )
            l2 = np.linalg.norm(
                np.asarray(latview) - np.asarray(target_lat),
            )
            level = ax.figure._sharex
            if level <= 1:
                share_x = share_y = False
            assert np.allclose(l1, 0) == share_x
            assert np.allclose(l2, 0) == share_y

    fig, ax = uplt.subplots(ncols=2, nrows=2, proj="cyl", share=level)
    ax.format(labels="both")
    for axi in ax:
        axi.format(
            lonlim=lonlim * axi.number,
            latlim=latlim * axi.number,
        )

    fig.canvas.draw()
    for idx, axi in enumerate(ax):
        axi.plot(x * (idx + 1), y * (idx + 1))

    # All the labels should be on
    for axi in ax:

        s = sum(
            [
                1 if axi._is_ticklabel_on(side) else 0
                for side in "labeltop labelbottom labelleft labelright".split()
            ]
        )

        assert_views_are_sharing(axi)
        # When we share the labels but not the limits,
        # we expect all ticks to be on
        if level > 2:
            assert s == 2
        else:
            assert s == 4
    uplt.close(fig)


@pytest.mark.mpl_image_compare
def test_cartesian_and_geo(rng):
    """
    Test that axis sharing does not prevent
    running Cartesian based plot functions
    """

    fig, ax = uplt.subplots(
        ncols=2,
        proj="cyl",
        share=True,
    )
    original_toggler = ax[0]._toggle_gridliner_labels
    with mock.patch.object(
        ax[0],
        "_toggle_gridliner_labels",
        autospec=True,
        side_effect=original_toggler,
    ) as mocked:
        # Make small range to speed up plotting
        ax.format(land=True, lonlim=(-10, 10), latlim=(-10, 10))
        ax[0].pcolormesh(rng.random((10, 10)))
        ax[1].scatter(*rng.random((2, 100)))
        fig.canvas.draw()
        assert (
            mocked.call_count >= 2
        )  # needs to be called at least twice; one for each axis
    return fig


def test_rasterize_feature():
    fig, ax = uplt.subplots(proj="cyl")
    ax.format(
        land=True,
        landrasterized=True,
        ocean=True,
        oceanrasterized=True,
        rivers=True,
        riversrasterized=True,
        borders=True,
        bordersrasterized=True,
    )
    for feature in "land ocean rivers borders".split():
        feat = getattr(ax[0], f"_{feature}_feature")
        assert feat._kwargs["rasterized"]
    uplt.close(fig)


def test_check_tricontourf():
    """
    Ensure that tricontour functions are getting
    the transform for GeoAxes.
    """
    import cartopy.crs as ccrs

    lon0 = 90
    lon = np.linspace(-180, 180, 10)
    lat = np.linspace(-90, 90, 10)
    lon2d, lat2d = np.meshgrid(lon, lat)

    data = np.sin(3 * np.radians(lat2d)) * np.cos(2 * np.radians(lon2d))
    # Place a box with constant values in order to have a visual reference
    mask_box = (lon2d >= 0) & (lon2d <= 20) & (lat2d >= 0) & (lat2d <= 20)
    data[mask_box] = 1.5

    lon, lat, data = map(np.ravel, (lon2d, lat2d, data))

    fig, ax = uplt.subplots(proj="cyl", proj_kw={"lon0": lon0})
    original_func = ax[0]._call_native
    with mock.patch.object(
        ax[0],
        "_call_native",
        autospec=True,
        side_effect=original_func,
    ) as mocked:
        for func in "tricontour tricontourf".split():
            getattr(ax[0], func)(lon, lat, data)
        assert "transform" in mocked.call_args.kwargs
        assert isinstance(mocked.call_args.kwargs["transform"], ccrs.PlateCarree)
    uplt.close(fig)


def test_panels_geo():
    fig, ax = uplt.subplots(proj="cyl")
    ax.format(labels=True)
    dirs = "top bottom right left".split()
    for dir in dirs:
        pax = ax.panel_axes(dir)
    fig.canvas.draw()
    pax = ax[0]._panel_dict["left"][-1]
    assert pax._is_ticklabel_on("labelleft")  # should not error
    assert not pax._is_ticklabel_on("labelright")
    assert not pax._is_ticklabel_on("labeltop")
    assert pax._is_ticklabel_on("labelbottom")

    pax = ax[0]._panel_dict["top"][-1]
    assert pax._is_ticklabel_on("labelleft")  # should not error
    assert not pax._is_ticklabel_on("labelright")
    assert not pax._is_ticklabel_on("labeltop")
    assert not pax._is_ticklabel_on("labelbottom")

    pax = ax[0]._panel_dict["bottom"][-1]
    assert pax._is_ticklabel_on("labelleft")  # should not error
    assert not pax._is_ticklabel_on("labelright")
    assert not pax._is_ticklabel_on("labeltop")
    assert pax._is_ticklabel_on("labelbottom")

    pax = ax[0]._panel_dict["right"][-1]
    assert not pax._is_ticklabel_on("labelleft")  # should not error
    assert not pax._is_ticklabel_on("labelright")
    assert not pax._is_ticklabel_on("labeltop")
    assert pax._is_ticklabel_on("labelbottom")

    for dir in dirs:
        not ax[0]._is_ticklabel_on(f"label{dir}")

    fig.canvas.draw()
    uplt.close(fig)


@pytest.mark.mpl_image_compare
def test_geo_with_panels(rng):
    """
    We are allowed to add panels in GeoPlots
    """
    # Define coordinates
    lat = np.linspace(-90, 90, 180)
    lon = np.linspace(-180, 180, 360)
    time = np.arange(2000, 2005)
    lon_grid, lat_grid = np.meshgrid(lon, lat)

    # Zoomed region elevation (Asia region)
    lat_zoom = np.linspace(0, 60, 60)
    lon_zoom = np.linspace(60, 180, 120)
    lz, lz_grid = np.meshgrid(lon_zoom, lat_zoom)

    elevation = (
        2000 * np.exp(-((lz - 90) ** 2 + (lz_grid - 30) ** 2) / 400)
        + 1000 * np.exp(-((lz - 120) ** 2 + (lz_grid - 45) ** 2) / 225)
        + rng.normal(0, 100, lz.shape)
    )
    elevation = np.clip(elevation, 0, 4000)

    fig, ax = uplt.subplots(nrows=2, proj="cyl")
    ax.format(latlabels="r")  # by default right-side latitude labels are off
    pax = ax.panel("r")
    z = elevation.sum()
    pax[0].barh(lat_zoom, elevation.sum(axis=1))
    pax[1].barh(lat_zoom - 30, elevation.sum(axis=1))
    ax[0].pcolormesh(
        lon_zoom,
        lat_zoom,
        elevation,
        cmap="bilbao",
        colorbar="t",
        colorbar_kw=dict(
            align="l",
            length=0.5,
        ),
    )
    ax[1].pcolormesh(
        lon_zoom,
        lat_zoom - 30,
        elevation,
        cmap="glacial",
        colorbar="t",
        colorbar_kw=dict(
            align="r",
            length=0.5,
        ),
    )
    ax.format(oceancolor="blue", coast=True)
    return fig


@pytest.mark.mpl_image_compare
def test_inset_axes_geographic():
    fig, ax = uplt.subplots(proj="cyl")
    ax.format(labels=True)

    e = [126, 30, 8.8, 10]
    ix = ax.inset_axes(
        e,
        zoom=True,
        zoom_kw={"fc": "r", "ec": "b"},
        transform="data",
    )
    ix.format(
        lonlim=(100, 110),
        latlim=(20, 30),
    )
    return fig


def test_tick_toggler():
    fig, ax = uplt.subplots(proj="cyl")
    for pos in "left right top bottom".split():
        if pos in "left right".split():
            ax.format(latlabels=pos)
        else:
            ax.format(lonlabels=pos)
        ax.set_title(f"Toggle {pos} labels")
        # Check if the labels are on
        # For cartopy backend labelleft can contain
        # False or x or y
        label = f"label{pos}"
        assert ax[0]._is_ticklabel_on(label) != False
        ax[0]._toggle_gridliner_labels(**{label: False})
        assert ax[0]._is_ticklabel_on(label) != True
    uplt.close(fig)


@pytest.mark.mpl_image_compare
def test_sharing_cartopy_with_colorbar(rng):

    def are_labels_on(ax, which=("top", "bottom", "right", "left")) -> tuple[bool]:
        gl = ax.gridlines_major

        on = [False, False, False, False]
        for idx, labeler in enumerate(which):
            if getattr(gl, f"{labeler}_labels"):
                on[idx] = True
        return on

    fig, ax = uplt.subplots(
        ncols=3,
        nrows=3,
        proj="cyl",
        share="all",
    )

    data = rng.random((10, 10))
    h = ax.imshow(data)[0]
    ax.format(land=True, labels="both")  # need this otherwise no labels are printed
    fig.colorbar(h, loc="r")
    fig.canvas.draw()  # needed to  invoke axis sharing

    expectations = (
        [True, False, False, True],
        [True, False, False, False],
        [True, False, True, False],
        [False, False, False, True],
        [False, False, False, False],
        [False, False, True, False],
        [False, True, False, True],
        [False, True, False, False],
        [False, True, True, False],
    )
    for axi in ax:
        state = are_labels_on(axi)
        expectation = expectations[axi.number - 1]
        for i, j in zip(state, expectation):
            assert i == j
    return fig


def test_consistent_range():
    """
    Check if the extent of the axes is consistent
    after setting ticklen. Ticklen uses a MaxNlocator which
    changes the extent of the axes -- we are resetting
    it now explicitly.
    """

    lonlim = np.array((10, 20))
    latlim = np.array((10, 20))
    fig, ax = uplt.subplots(ncols=2, proj="cyl", share=False)

    ax.format(
        lonlim=(10, 20),
        latlim=latlim,
        lonlines=2,
        latlines=2,
        lonlabels="both",
        latlabels="both",
    )
    # Now change ticklen of ax[1], cause extent change
    ax[1].format(ticklen=1)
    for a in ax:
        lonview = np.array(a._lonaxis.get_view_interval())
        latview = np.array(a._lataxis.get_view_interval())

        assert np.allclose(lonview, lonlim, atol=1e-6)
        assert np.allclose(latview, latlim, atol=1e-6)


@pytest.mark.mpl_image_compare
def test_dms_used_for_mercator():
    """
    Test that DMS is used for Mercator projection
    """
    limit = (0.6, 113.25)
    fig, ax = uplt.subplots(ncols=2, proj=("cyl", "merc"), share=0)
    ax.format(land=True, labels=True, lonlocator=limit)
    ax.format(land=True, labels=True, lonlocator=limit)
    import matplotlib.ticker as mticker

    expectations = (
        "0°36′E",
        "113°15′E",
    )

    for expectation, tick in zip(expectations, limit):
        a = ax[0].gridlines_major.xformatter(tick)
        b = ax[1].gridlines_major.xformatter(tick)
        assert a == expectation
        assert b == expectation
    return fig


@pytest.mark.mpl_image_compare
def test_imshow_with_and_without_transform(rng):
    data = rng.random((100, 100))
    fig, ax = uplt.subplots(ncols=3, proj="lcc", share=0)
    ax.format(land=True, labels=True)
    ax[:2].format(
        latlim=(-10, 10),
        lonlim=(-10, 10),
    )
    ax[0].imshow(data, transform=ax[0].projection)
    ax[1].imshow(data, transform=None)
    ax[2].imshow(data, transform=uplt.axes.geo.ccrs.PlateCarree())
    ax.format(title=["LCC", "No transform", "PlateCarree"])
    return fig


@pytest.mark.mpl_image_compare
def test_grid_indexing_formatting(rng):
    """
    Check if subplotgrid is correctly selecting
    the subplots based on non-shared axis formatting
    """
    # See https://github.com/Ultraplot/UltraPlot/issues/356
    lon = np.arange(0, 360, 10)
    lat = np.arange(-60, 60 + 1, 10)
    data = rng.random((len(lat), len(lon)))

    fig, axs = uplt.subplots(nrows=3, ncols=2, proj="cyl", share=0)
    axs.format(coast=True)

    for ax in axs:
        m = ax.pcolor(lon, lat, data)
        ax.colorbar(m)

    axs[-1, :].format(lonlabels=True)
    axs[:, 0].format(latlabels=True)
    return fig


@pytest.mark.parametrize(
    "backend",
    [
        "cartopy",
        "basemap",
    ],
)
def test_label_rotation(backend):
    """
    Test label rotation parameters for both Cartopy and Basemap backends.
    Tests labelrotation, lonlabelrotation, and latlabelrotation parameters.
    """
    fig, axs = uplt.subplots(ncols=2, proj="cyl", backend=backend, share=0)

    # Test 1: labelrotation applies to both axes
    axs[0].format(
        title="Both rotated 45°",
        lonlabels="b",
        latlabels="l",
        labelrotation=45,
        lonlines=30,
        latlines=30,
    )

    # Test 2: Different rotations for lon and lat
    axs[1].format(
        title="Lon: 90°, Lat: 0°",
        lonlabels="b",
        latlabels="l",
        lonlabelrotation=90,
        latlabelrotation=0,
        lonlines=30,
        latlines=30,
    )

    # Verify that rotation was applied based on actual backend
    if axs[0]._name == "cartopy":
        # For Cartopy, check gridliner xlabel_style and ylabel_style
        gl0 = axs[0].gridlines_major
        assert gl0.xlabel_style.get("rotation") == 45
        assert gl0.ylabel_style.get("rotation") == 45

        gl1 = axs[1].gridlines_major
        assert gl1.xlabel_style.get("rotation") == 90
        assert gl1.ylabel_style.get("rotation") == 0

    else:  # basemap
        # For Basemap, check Text object rotation
        from matplotlib import text as mtext

        def get_text_rotations(gridlines_dict):
            """Extract rotation angles from Text objects in gridlines."""
            rotations = []
            for line_dict in gridlines_dict.values():
                for obj_list in line_dict:
                    for obj in obj_list:
                        if isinstance(obj, mtext.Text):
                            rotations.append(obj.get_rotation())
            return rotations

        # Check first axes (both 45°)
        lonlines_0, latlines_0 = axs[0].gridlines_major
        lon_rotations_0 = get_text_rotations(lonlines_0)
        lat_rotations_0 = get_text_rotations(latlines_0)
        if lon_rotations_0:  # Only check if labels exist
            assert all(r == 45 for r in lon_rotations_0)
        if lat_rotations_0:
            assert all(r == 45 for r in lat_rotations_0)

        # Check second axes (lon: 90°, lat: 0°)
        lonlines_1, latlines_1 = axs[1].gridlines_major
        lon_rotations_1 = get_text_rotations(lonlines_1)
        lat_rotations_1 = get_text_rotations(latlines_1)
        if lon_rotations_1:
            assert all(r == 90 for r in lon_rotations_1)
        if lat_rotations_1:
            assert all(r == 0 for r in lat_rotations_1)

    uplt.close(fig)


@pytest.mark.parametrize("backend", ["cartopy", "basemap"])
def test_label_rotation_precedence(backend):
    """
    Test that specific rotation parameters take precedence over general labelrotation.
    """
    fig, ax = uplt.subplots(proj="cyl", backend=backend)

    # lonlabelrotation should override labelrotation for lon axis
    # latlabelrotation not specified, so should use labelrotation
    ax.format(
        lonlabels="b",
        latlabels="l",
        labelrotation=30,
        lonlabelrotation=60,  # This should override for lon
        lonlines=30,
        latlines=30,
    )

    if ax[0]._name == "cartopy":
        gl = ax[0].gridlines_major
        assert gl.xlabel_style.get("rotation") == 60  # Override value
        assert gl.ylabel_style.get("rotation") == 30  # Fallback value
    else:  # basemap
        from matplotlib import text as mtext

        def get_text_rotations(gridlines_dict):
            rotations = []
            for line_dict in gridlines_dict.values():
                for obj_list in line_dict:
                    for obj in obj_list:
                        if isinstance(obj, mtext.Text):
                            rotations.append(obj.get_rotation())
            return rotations

        lonlines, latlines = ax[0].gridlines_major
        lon_rotations = get_text_rotations(lonlines)
        lat_rotations = get_text_rotations(latlines)

        if lon_rotations:
            assert all(r == 60 for r in lon_rotations)
        if lat_rotations:
            assert all(r == 30 for r in lat_rotations)

    uplt.close(fig)


def test_label_rotation_backward_compatibility():
    """
    Test that existing code without rotation parameters still works.
    """
    fig, ax = uplt.subplots(proj="cyl")

    # Should work without any rotation parameters
    ax.format(
        lonlabels="b",
        latlabels="l",
        lonlines=30,
        latlines=30,
    )

    # Verify no rotation was applied (should be default or None)
    gl = ax[0]._gridlines_major
    # If rotation key doesn't exist or is None/0, that's expected
    lon_rotation = gl.xlabel_style.get("rotation")
    lat_rotation = gl.ylabel_style.get("rotation")

    # Default rotation should be None or 0 (no rotation)
    assert lon_rotation is None or lon_rotation == 0
    assert lat_rotation is None or lat_rotation == 0

    uplt.close(fig)


@pytest.mark.parametrize("rotation_angle", [0, 45, 90, -30, 180])
def test_label_rotation_angles(rotation_angle):
    """
    Test various rotation angles to ensure they're applied correctly.
    """
    fig, ax = uplt.subplots(proj="cyl")

    ax.format(
        lonlabels="b",
        latlabels="l",
        labelrotation=rotation_angle,
        lonlines=60,
        latlines=30,
    )

    gl = ax[0]._gridlines_major
    assert gl.xlabel_style.get("rotation") == rotation_angle
    assert gl.ylabel_style.get("rotation") == rotation_angle

    uplt.close(fig)


@pytest.mark.parametrize("backend", ["cartopy", "basemap"])
def test_label_rotation_only_lon(backend):
    """
    Test rotation applied only to longitude labels.
    """
    fig, ax = uplt.subplots(proj="cyl", backend=backend)

    # Only rotate longitude labels
    ax.format(
        lonlabels="b",
        latlabels="l",
        lonlabelrotation=45,
        lonlines=30,
        latlines=30,
    )

    if ax[0]._name == "cartopy":
        gl = ax[0].gridlines_major
        assert gl.xlabel_style.get("rotation") == 45
        assert gl.ylabel_style.get("rotation") is None
    else:  # basemap
        from matplotlib import text as mtext

        def get_text_rotations(gridlines_dict):
            rotations = []
            for line_dict in gridlines_dict.values():
                for obj_list in line_dict:
                    for obj in obj_list:
                        if isinstance(obj, mtext.Text):
                            rotations.append(obj.get_rotation())
            return rotations

        lonlines, latlines = ax[0].gridlines_major
        lon_rotations = get_text_rotations(lonlines)
        lat_rotations = get_text_rotations(latlines)

        if lon_rotations:
            assert all(r == 45 for r in lon_rotations)
        if lat_rotations:
            # Default rotation should be 0
            assert all(r == 0 for r in lat_rotations)

    uplt.close(fig)


@pytest.mark.parametrize("backend", ["cartopy", "basemap"])
def test_label_rotation_only_lat(backend):
    """
    Test rotation applied only to latitude labels.
    """
    fig, ax = uplt.subplots(proj="cyl", backend=backend)

    # Only rotate latitude labels
    ax.format(
        lonlabels="b",
        latlabels="l",
        latlabelrotation=60,
        lonlines=30,
        latlines=30,
    )

    if ax[0]._name == "cartopy":
        gl = ax[0].gridlines_major
        assert gl.xlabel_style.get("rotation") is None
        assert gl.ylabel_style.get("rotation") == 60
    else:  # basemap
        from matplotlib import text as mtext

        def get_text_rotations(gridlines_dict):
            rotations = []
            for line_dict in gridlines_dict.values():
                for obj_list in line_dict:
                    for obj in obj_list:
                        if isinstance(obj, mtext.Text):
                            rotations.append(obj.get_rotation())
            return rotations

        lonlines, latlines = ax[0].gridlines_major
        lon_rotations = get_text_rotations(lonlines)
        lat_rotations = get_text_rotations(latlines)

        if lon_rotations:
            # Default rotation should be 0
            assert all(r == 0 for r in lon_rotations)
        if lat_rotations:
            assert all(r == 60 for r in lat_rotations)

    uplt.close(fig)


def test_label_rotation_with_different_projections():
    """
    Test label rotation with various projections.
    """
    projections = ["cyl", "robin", "moll"]

    for proj in projections:
        fig, ax = uplt.subplots(proj=proj)

        ax.format(
            lonlabels="b",
            latlabels="l",
            labelrotation=30,
            lonlines=60,
            latlines=30,
        )

        # For cartopy, verify rotation was set
        if ax[0]._name == "cartopy":
            gl = ax[0]._gridlines_major
            if gl is not None:  # Some projections might not support gridlines
                assert gl.xlabel_style.get("rotation") == 30
                assert gl.ylabel_style.get("rotation") == 30

        uplt.close(fig)


@pytest.mark.parametrize("backend", ["cartopy", "basemap"])
def test_label_rotation_with_format_options(backend):
    """
    Test label rotation combined with other format options.
    """
    fig, ax = uplt.subplots(proj="cyl", backend=backend)

    # Combine rotation with other formatting
    ax.format(
        lonlabels="b",
        latlabels="l",
        lonlabelrotation=45,
        latlabelrotation=30,
        lonlines=30,
        latlines=30,
        coast=True,
        land=True,
    )

    # Verify rotation was applied
    if ax[0]._name == "cartopy":
        gl = ax[0].gridlines_major
        assert gl.xlabel_style.get("rotation") == 45
        assert gl.ylabel_style.get("rotation") == 30
    else:  # basemap
        from matplotlib import text as mtext

        def get_text_rotations(gridlines_dict):
            rotations = []
            for line_dict in gridlines_dict.values():
                for obj_list in line_dict:
                    for obj in obj_list:
                        if isinstance(obj, mtext.Text):
                            rotations.append(obj.get_rotation())
            return rotations

        lonlines, latlines = ax[0].gridlines_major
        lon_rotations = get_text_rotations(lonlines)
        lat_rotations = get_text_rotations(latlines)

        if lon_rotations:
            assert all(r == 45 for r in lon_rotations)
        if lat_rotations:
            assert all(r == 30 for r in lat_rotations)

    uplt.close(fig)


def test_label_rotation_none_values():
    """
    Test that None values for rotation work correctly.
    """
    fig, ax = uplt.subplots(proj="cyl")

    # Explicitly set None for rotations
    ax.format(
        lonlabels="b",
        latlabels="l",
        lonlabelrotation=None,
        latlabelrotation=None,
        lonlines=30,
        latlines=30,
    )

    gl = ax[0]._gridlines_major
    # None should result in no rotation being set
    lon_rotation = gl.xlabel_style.get("rotation")
    lat_rotation = gl.ylabel_style.get("rotation")

    assert lon_rotation is None or lon_rotation == 0
    assert lat_rotation is None or lat_rotation == 0

    uplt.close(fig)


@pytest.mark.parametrize("backend", ["cartopy", "basemap"])
def test_label_rotation_update_existing(backend):
    """
    Test updating rotation on axes that already have labels.
    """
    fig, ax = uplt.subplots(proj="cyl", backend=backend)

    # First format without rotation
    ax.format(
        lonlabels="b",
        latlabels="l",
        lonlines=30,
        latlines=30,
    )

    # Then update with rotation
    ax.format(
        lonlabelrotation=45,
        latlabelrotation=90,
    )

    # Verify rotation was applied
    if ax[0]._name == "cartopy":
        gl = ax[0].gridlines_major
        assert gl.xlabel_style.get("rotation") == 45
        assert gl.ylabel_style.get("rotation") == 90
    else:  # basemap
        from matplotlib import text as mtext

        def get_text_rotations(gridlines_dict):
            rotations = []
            for line_dict in gridlines_dict.values():
                for obj_list in line_dict:
                    for obj in obj_list:
                        if isinstance(obj, mtext.Text):
                            rotations.append(obj.get_rotation())
            return rotations

        lonlines, latlines = ax[0].gridlines_major
        lon_rotations = get_text_rotations(lonlines)
        lat_rotations = get_text_rotations(latlines)

        if lon_rotations:
            assert all(r == 45 for r in lon_rotations)
        if lat_rotations:
            assert all(r == 90 for r in lat_rotations)

    uplt.close(fig)


def test_label_rotation_negative_angles():
    """
    Test various negative rotation angles.
    """
    fig, ax = uplt.subplots(proj="cyl")

    negative_angles = [-15, -45, -90, -120, -180]

    for angle in negative_angles:
        ax.format(
            lonlabels="b",
            latlabels="l",
            labelrotation=angle,
            lonlines=60,
            latlines=30,
        )

        gl = ax[0]._gridlines_major
        assert gl.xlabel_style.get("rotation") == angle
        assert gl.ylabel_style.get("rotation") == angle

    uplt.close(fig)


def _check_boundary_labels(ax, expected_lon_labels, expected_lat_labels):
    """Helper to check that specific labels are created and visible."""
    gl = ax._gridlines_major
    assert gl is not None, "Gridliner should exist"

    # Check xlim/ylim are defined on the gridliner
    assert hasattr(gl, "xlim") and hasattr(gl, "ylim")

    # Check longitude labels - only verify the visible ones match expected
    lon_texts = [
        label.get_text() for label in gl.bottom_label_artists if label.get_visible()
    ]
    assert len(lon_texts) == len(expected_lon_labels), (
        f"Should have {len(expected_lon_labels)} visible longitude labels, "
        f"got {len(lon_texts)}: {lon_texts}"
    )
    for expected in expected_lon_labels:
        assert any(
            expected in text for text in lon_texts
        ), f"{expected} label should be visible, got: {lon_texts}"

    # Check latitude labels - only verify the visible ones match expected
    lat_texts = [
        label.get_text() for label in gl.left_label_artists if label.get_visible()
    ]
    assert len(lat_texts) == len(expected_lat_labels), (
        f"Should have {len(expected_lat_labels)} visible latitude labels, "
        f"got {len(lat_texts)}: {lat_texts}"
    )
    for expected in expected_lat_labels:
        assert any(
            expected in text for text in lat_texts
        ), f"{expected} label should be visible, got: {lat_texts}"


def test_boundary_labels_positive_longitude():
    """
    Test that interior labels remain visible with positive longitude limits.
    """
    fig, ax = uplt.subplots(proj="pcarree")
    ax.format(
        lonlim=(120, 130),
        latlim=(10, 20),
        lonlocator=[120, 125, 130],
        latlocator=[10, 15, 20],
        labels=True,
        grid=False,
    )
    fig.canvas.draw()
    _check_boundary_labels(ax[0], ["125°E"], ["15°N"])
    uplt.close(fig)


def test_boundary_labels_negative_longitude():
    """
    Test that interior labels remain visible with negative longitude limits.
    """
    fig, ax = uplt.subplots(proj="pcarree")
    ax.format(
        lonlim=(-120, -60),
        latlim=(20, 50),
        lonlocator=[-120, -90, -60],
        latlocator=[20, 35, 50],
        labels=True,
        grid=False,
    )
    fig.canvas.draw()
    _check_boundary_labels(
        ax[0],
        ["90°W"],
        ["35°N"],
    )
    uplt.close(fig)


def test_boundary_labels_view_intervals():
    """
    Test that view intervals match requested limits after setting lonlim/latlim.
    """
    fig, ax = uplt.subplots(proj="pcarree")
    ax.format(lonlim=(0, 60), latlim=(-20, 40), lonlines=30, latlines=20, labels=True)
    loninterval = ax[0]._lonaxis.get_view_interval()
    latinterval = ax[0]._lataxis.get_view_interval()
    assert abs(loninterval[0] - 0) < 1 and abs(loninterval[1] - 60) < 1
    assert abs(latinterval[0] - (-20)) < 1 and abs(latinterval[1] - 40) < 1
    uplt.close(fig)


def test_labels_preserved_with_ticklen():
    """
    Ensure ticklen updates do not disable top/right gridline labels.
    """
    fig, ax = uplt.subplots(proj="cyl")
    ax.format(lonlim=(0, 10), latlim=(0, 10), labels="both", lonlines=2, latlines=2)
    assert ax.gridlines_major.top_labels
    assert ax.gridlines_major.right_labels

    ax.format(ticklen=1, labels="both")
    assert ax.gridlines_major.top_labels
    assert ax.gridlines_major.right_labels
