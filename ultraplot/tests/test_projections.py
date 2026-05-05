#!/usr/bin/env python3
"""
Test projection features.
"""

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np, warnings
import ultraplot as uplt
import pytest


@pytest.mark.mpl_image_compare
def test_aspect_ratios():
    """
    Test aspect ratio adjustments.
    """
    fig, axs = uplt.subplots(ncols=2)
    axs[0].format(aspect=1.5)
    fig, axs = uplt.subplots(ncols=2, proj=("cart", "cyl"), aspect=2)
    axs[0].set_aspect(1)
    return fig


if uplt.internals._version_mpl <= "3.2":

    @pytest.mark.mpl_image_compare
    def test_basemap_labels():
        """
        Add basemap labels.
        """
        fig, axs = uplt.subplots(ncols=2, proj="robin", refwidth=3, basemap=True)
        axs.format(coast=True, labels="rt")
        return fig


@pytest.mark.mpl_image_compare
def test_cartopy_labels():
    """
    Add cartopy labels.
    """
    fig, axs = uplt.subplots(ncols=2, proj="robin", refwidth=3)
    axs.format(coast=True, labels=True)
    axs[0].format(inlinelabels=True)
    axs[1].format(rotatelabels=True)
    return fig


def test_cartopy_labels_not_shared_for_non_rectilinear():
    """
    Non-rectilinear cartopy axes should keep independent gridliner labels.
    """
    fig, axs = uplt.subplots(ncols=2, proj="robin", refwidth=3)
    axs.format(coast=True, labels=True)
    fig.canvas.draw()

    assert axs[0]._is_ticklabel_on("labelleft")
    assert axs[1]._is_ticklabel_on("labelleft")


def test_cartopy_cyl_projection_is_rectilinear():
    fig, axs = uplt.subplots(ncols=1, proj="cyl")
    assert axs[0]._is_rectilinear()


@pytest.mark.mpl_image_compare
def test_cartopy_contours(rng):
    """
    Test bug with cartopy contours. Sometimes results in global coverage
    with single color sometimes not.
    """
    N = 10
    fig = plt.figure(figsize=(5, 2.5))
    ax = fig.add_subplot(projection=ccrs.Mollweide())
    ax.coastlines()
    x = np.linspace(-180, 180, N)
    y = np.linspace(-90, 90, N)
    z = rng.random((N, N)) * 10 - 5
    m = ax.contourf(
        x,
        y,
        z,
        transform=ccrs.PlateCarree(),
        cmap="RdBu_r",
        vmin=-5,
        vmax=5,
    )
    fig.colorbar(m, ax=ax)
    fig = uplt.figure()
    ax = fig.add_subplot(projection=uplt.Mollweide(), extent="auto")
    ax.coastlines()
    N = 10
    m = ax.contourf(
        np.linspace(0, 180, N),
        np.linspace(0, 90, N)[1::2],
        rng.random((N // 2, N)) * 10 + 5,
        cmap="BuRd",
        transform=uplt.PlateCarree(),
        edgefix=False,
    )
    fig.colorbar(m, ax=ax)
    return fig


@pytest.mark.mpl_image_compare
def test_cartopy_manual():
    """
    Test alternative workflow without classes.
    """
    fig = uplt.figure()
    proj = uplt.Proj("npstere")
    # fig.add_axes([0.1, 0.1, 0.9, 0.9], proj='geo', map_projection=proj)
    fig.add_subplot(111, proj="geo", land=True, map_projection=proj)
    return fig


@pytest.mark.mpl_image_compare
def test_three_axes():
    """
    Test basic 3D axes here.
    """
    with uplt.rc.context({"tick.minor": False}):
        fig, ax = uplt.subplots(proj="3d", outerpad=3)
    return fig


@pytest.mark.mpl_image_compare
def test_projection_dicts():
    """
    Test projection dictionaries.
    """
    fig = uplt.figure(refnum=1)
    a = [[1, 0], [1, 4], [2, 4], [2, 4], [3, 4], [3, 0]]
    fig.subplots(a, proj={1: "cyl", 2: "cart", 3: "cart", 4: "cart"})
    return fig


@pytest.mark.mpl_image_compare
def test_polar_projections():
    """
    Rigorously test polar features here.
    """
    fig, ax = uplt.subplots(proj="polar")
    ax.format(
        rlabelpos=45,
        thetadir=-1,
        thetalines=90,
        thetalim=(0, 270),
        theta0="N",
        r0=0,
        rlim=(0.5, 1),
        rlines=0.25,
    )
    return fig


def test_polar_format_labels():
    """
    ax.format(xlabel=..., ylabel=...) must forward to set_xlabel/set_ylabel.
    """
    fig, ax = uplt.subplots(proj="polar")
    ax.format(xlabel="xlabel", ylabel="ylabel")
    assert ax.get_xlabel() == "xlabel"
    assert ax.get_ylabel() == "ylabel"


def test_polar_format_thetalabel_rlabel():
    """
    `thetalabel` and `rlabel` both create CurvedText artists.
    `thetalabel` follows the outer arc at r=rmax.
    `rlabel` follows the radial spoke at rlabel_position, spanning rmin→rmax.
    """
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(
        thetalim=(0, 90),
        rlim=(0, 1),
        thetalabel="thetalabel",
        rlabel="rlabel",
    )
    assert ax._thetalabel_artist is not None
    assert ax._rlabel_artist is not None
    assert ax._thetalabel_artist.get_text() == "thetalabel"
    assert ax._rlabel_artist.get_text() == "rlabel"
    # thetalabel: CurvedText arc at r >= rmax (offset for tick clearance),
    # centered on midpoint, 80% of span.
    tx, ty = ax._thetalabel_artist.get_curve()
    assert np.allclose(ty, ty[0])
    assert ty[0] >= ax.get_rmax()
    mid = 0.5 * (0.0 + 90.0)
    half_span = 0.5 * 90.0 * 0.8
    assert np.isclose(np.rad2deg(tx[0]), mid - half_span)
    assert np.isclose(np.rad2deg(tx[-1]), mid + half_span)
    # rlabel: CurvedText along spoke at thetamin (sector default), rmin→rmax
    rx, ry = ax._rlabel_artist.get_curve()
    assert np.allclose(np.rad2deg(rx), 0.0)  # thetamin for (0, 90) sector
    assert np.isclose(ry[0], ax.get_rmin())
    assert np.isclose(ry[-1], ax.get_rmax())


def test_polar_format_thetalabel_full_circle():
    """`thetalabel` on a full-range polar axes centers on theta=0."""
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(thetalabel="thetalabel")
    tx, _ = ax._thetalabel_artist.get_curve()
    mid_deg = np.rad2deg(0.5 * (tx[0] + tx[-1]))
    assert np.isclose(mid_deg % 360, 0.0)


def test_polar_format_thetalabel_clear():
    """Passing thetalabel='' clears an existing label."""
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(thetalabel="x")
    ax.format(thetalabel="")
    assert ax._thetalabel_artist.get_text() == ""


def test_polar_format_thetalabelloc():
    """`thetalabelloc=<deg>` overrides the default midpoint center."""
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(thetalim=(0, 90), thetalabel="thetalabel", thetalabelloc=30)
    tx, _ = ax._thetalabel_artist.get_curve()
    mid_deg = np.rad2deg(0.5 * (tx[0] + tx[-1]))
    assert np.isclose(mid_deg, 30.0)


def test_polar_thetalabel_stays_radially_outside_under_theta_transform():
    """The thetalabel offset must stay radially outward after theta transforms."""
    fig, axs = uplt.subplots(ncols=2, proj="polar")
    for ax, kwargs in zip(
        axs,
        ({}, {"theta0": "N", "thetadir": -1}),
    ):
        ax.format(
            thetalim=(0, 180),
            rlim=(0.2, 1),
            thetalabel="thetalabel",
            thetalabelloc=135,
            **kwargs,
        )
    fig.canvas.draw()
    for ax in axs:
        tx, ty = ax._thetalabel_artist.get_curve()
        idx = len(tx) // 2
        base = ax.transData.transform((tx[idx], ax.get_rmax()))
        disp = ax._thetalabel_artist.get_transform().transform((tx[idx], ty[idx]))
        outward = ax.transData.transform((tx[idx], ax.get_rmax() + 1.0)) - base
        offset = disp - base
        assert np.dot(offset, outward) > 0


def test_polar_annular_labels_draw_without_nan_positions():
    """Annular polar labels must resolve finite character positions after draw."""
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(
        thetalim=(30, 120),
        rlim=(0.4, 1.2),
        thetalabel="Annular sector",
        rlabel="rlabel",
    )
    fig.canvas.draw()
    for artist in (ax._thetalabel_artist, ax._rlabel_artist):
        positions = [
            np.asarray(text.get_position(), dtype=float)
            for char, text in artist._characters
            if char.strip()
        ]
        assert positions
        assert all(np.all(np.isfinite(position)) for position in positions)


def test_polar_format_wrapped_sector_uses_directed_interval():
    """Wrapped sectors must use the directed theta interval, not sorted extrema."""
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(thetalim=(300, 60), rlim=(0, 1), thetalabel="thetalabel", rlabel="rlabel")
    tx, _ = ax._thetalabel_artist.get_curve()
    mid_deg = np.rad2deg(0.5 * (tx[0] + tx[-1])) % 360
    assert np.isclose(mid_deg, 0.0)
    rx, _ = ax._rlabel_artist.get_curve()
    assert np.allclose(np.rad2deg(rx) % 360, 300.0)
    ax.format(rlabelloc="left")
    rx, _ = ax._rlabel_artist.get_curve()
    assert np.allclose(np.rad2deg(rx) % 360, 60.0)


def test_polar_format_rlabelloc_full_circle_flips_offset():
    """On a full circle, `rlabelloc='left'` flips the perpendicular offset."""
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(rlabel="rlabel", rlabelloc="right")
    fig.canvas.draw()
    rpos_deg = ax.get_rlabel_position()
    rmid = 0.5 * (ax.get_rmin() + ax.get_rmax())
    test_point = (np.deg2rad(rpos_deg), rmid)
    right_base_disp = ax.transData.transform(test_point)
    right_disp = ax._rlabel_artist.get_transform().transform(test_point)
    ax.format(rlabelloc="left")
    fig.canvas.draw()
    left_base_disp = ax.transData.transform(test_point)
    left_disp = ax._rlabel_artist.get_transform().transform(test_point)
    right_off = right_disp - right_base_disp
    left_off = left_disp - left_base_disp
    assert np.allclose(right_off, -left_off)
    assert not np.allclose(right_off, 0)


def test_polar_format_rlabelloc_sector_selects_spoke():
    """On a sector, `rlabelloc='right'` anchors to thetamin and `'left'` to thetamax."""
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(thetalim=(0, 90), rlabel="rlabel", rlabelloc="right")
    rx_right, _ = ax._rlabel_artist.get_curve()
    assert np.allclose(np.rad2deg(rx_right), 0.0)  # thetamin spoke
    ax.format(rlabelloc="left")
    rx_left, _ = ax._rlabel_artist.get_curve()
    assert np.allclose(np.rad2deg(rx_left), 90.0)  # thetamax spoke


def test_polar_format_rlabelloc_sector_stays_outside_under_theta_transform():
    """Sector-default `rlabelloc` must stay outside after theta transforms."""
    fig, axs = uplt.subplots(ncols=2, proj="polar")
    for ax, loc in zip(axs, ("right", "left")):
        ax.format(
            thetalim=(0, 180),
            rlim=(0, 1),
            theta0="N",
            thetadir=-1,
            rlabel="rlabel",
            rlabelloc=loc,
        )
    fig.canvas.draw()
    for ax, rpos_deg, inside_deg in zip(axs, (0.0, 180.0), (1.0, 179.0)):
        rmid = 0.5 * (ax.get_rmin() + ax.get_rmax())
        point = (np.deg2rad(rpos_deg), rmid)
        base_disp = ax.transData.transform(point)
        rlabel_disp = ax._rlabel_artist.get_transform().transform(point)
        inside_disp = ax.transData.transform((np.deg2rad(inside_deg), rmid))
        off = rlabel_disp - base_disp
        inside = inside_disp - base_disp
        assert np.dot(off, inside) < 0


def test_polar_format_loc_persists_across_format_calls():
    """
    A subsequent `format()` call without `thetalabelloc`/`rlabelloc`/`rlabelpos`
    must not reset the previously-applied values. Regression test for trailing
    `axs.format(suptitle=...)`-style calls.
    """
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(
        thetalim=(0, 90),
        thetalabel="t",
        thetalabelloc=30,
        rlabel="r",
        rlabelloc="left",
    )
    tx0, _ = ax._thetalabel_artist.get_curve()
    rx0, _ = ax._rlabel_artist.get_curve()
    # Trailing generic format() call — must preserve the previous loc/pos.
    ax.format(title="anything")
    tx1, _ = ax._thetalabel_artist.get_curve()
    rx1, _ = ax._rlabel_artist.get_curve()
    assert np.isclose(np.rad2deg(0.5 * (tx1[0] + tx1[-1])), 30.0)
    assert np.allclose(np.rad2deg(rx1), 90.0)
    # Geometry is recomputed but anchors stay put.
    assert np.allclose(
        np.rad2deg(0.5 * (tx0[0] + tx0[-1])), np.rad2deg(0.5 * (tx1[0] + tx1[-1]))
    )
    assert np.allclose(rx0, rx1)


def test_polar_format_rlabelpos_sector_auto_outside():
    """`rlabelpos=thetamax` on a sector offsets *outside* the wedge."""
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(thetalim=(0, 180), rlim=(0, 1), rlabel="rlabel", rlabelpos=180)
    fig.canvas.draw()
    rmid = 0.5 * (ax.get_rmin() + ax.get_rmax())
    test_point = (np.deg2rad(180.0), rmid)
    base_disp = ax.transData.transform(test_point)
    rlabel_disp = ax._rlabel_artist.get_transform().transform(test_point)
    off = rlabel_disp - base_disp
    # Spoke at theta=180 lies along the −x axis; the upper half-disk is +y, so
    # outside-the-wedge means the perpendicular offset must be in −y.
    assert off[1] < 0


def test_polar_rlabel_offset_stays_perpendicular_under_theta_transform():
    """The rlabel offset must stay perpendicular to the spoke after theta transforms."""
    fig, axs = uplt.subplots(ncols=2, proj="polar")
    for ax, kwargs in zip(
        axs,
        ({}, {"theta0": "N", "thetadir": -1}),
    ):
        ax.format(thetalim=(0, 180), rlim=(0.2, 1), rlabel="rlabel", rlabelpos=135, **kwargs)
    fig.canvas.draw()
    for ax in axs:
        rmid = 0.5 * (ax.get_rmin() + ax.get_rmax())
        point = (np.deg2rad(135.0), rmid)
        base = ax.transData.transform(point)
        disp = ax._rlabel_artist.get_transform().transform(point)
        offset = disp - base
        tangent = ax.transData.transform((np.deg2rad(135.0), ax.get_rmax())) - ax.transData.transform(
            (np.deg2rad(135.0), ax.get_rmin())
        )
        tangent /= np.linalg.norm(tangent)
        assert np.isclose(np.dot(offset, tangent), 0.0, atol=1e-6)


def test_polar_rlabel_refresh_tracks_tick_params():
    """Refreshing the rlabel must honor later tick-param changes."""
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(thetalim=(0, 180), rlim=(0.2, 1), rlabel="rlabel")
    fig.canvas.draw()
    rpos_deg = ax.get_rlabel_position()
    rmid = 0.5 * (ax.get_rmin() + ax.get_rmax())
    point = (np.deg2rad(rpos_deg), rmid)
    base = ax.transData.transform(point)
    disp0 = ax._rlabel_artist.get_transform().transform(point)
    off0 = np.linalg.norm(disp0 - base)
    ax.tick_params(axis="y", which="major", pad=30, labelsize=20)
    fig.canvas.draw()
    disp1 = ax._rlabel_artist.get_transform().transform(point)
    off1 = np.linalg.norm(disp1 - base)
    assert off1 > off0


def test_polar_labels_refresh_after_plot_draw():
    """Polar-aware label geometry must refresh when later plotting changes draw state."""
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(
        thetalim=(0, 90),
        rlim=(0, 2),
        thetalabel="thetalabel",
        rlabel="rlabel",
    )
    tx0, ty0 = ax._thetalabel_artist.get_curve()
    rx0, ry0 = ax._rlabel_artist.get_curve()
    ax.plot(np.linspace(0, 2 * np.pi, 200), np.linspace(0, 100, 200))
    fig.canvas.draw()
    tx1, ty1 = ax._thetalabel_artist.get_curve()
    rx1, ry1 = ax._rlabel_artist.get_curve()
    assert np.allclose(np.rad2deg(rx1), 0.0)
    assert np.isclose(ry1[0], ax.get_rmin())
    assert np.isclose(ry1[-1], ax.get_rmax())
    assert np.allclose(ty1, ty1[0])
    assert ty1[0] >= ax.get_rmax()
    assert not np.allclose(ty0, ty1) or not np.allclose(ry0, ry1) or not np.allclose(tx0, tx1)


def test_polar_labels_refresh_for_tightbbox():
    """Polar-aware labels must also refresh during tight-bbox queries."""
    fig, axs = uplt.subplots(proj="polar")
    ax = axs[0]
    ax.format(thetalim=(0, 90), rlim=(0, 1), thetalabel="thetalabel", rlabel="rlabel")
    fig.canvas.draw()
    tx0, ty0 = ax._thetalabel_artist.get_curve()
    rx0, ry0 = ax._rlabel_artist.get_curve()
    ax.set_rmax(3)
    ax.get_tightbbox(fig.canvas.get_renderer())
    tx1, ty1 = ax._thetalabel_artist.get_curve()
    rx1, ry1 = ax._rlabel_artist.get_curve()
    assert np.allclose(np.rad2deg(rx1), 0.0)
    assert np.isclose(ry1[-1], ax.get_rmax())
    assert np.allclose(ty1, ty1[0])
    assert ty1[0] >= ax.get_rmax()
    assert not np.allclose(ty0, ty1) or not np.allclose(ry0, ry1) or not np.allclose(tx0, tx1)


def test_sharing_axes():
    """
    Test sharing axes for GeoAxes
    """

    with warnings.catch_warnings(record=True) as record:
        # For rectilinear plots all axes can be shared
        fig, ax = uplt.subplots(ncols=3, nrows=3, share="all", proj="cyl")
        ax.format(
            land=True,
            lonlim=(-10, 10),  # make small to plot quicker
            latlim=(-10, 10),
        )
        lims = [ax[0].get_xlim(), ax[0].get_ylim()]
        for axi in ax[1:]:
            test_lims = [axi.get_xlim(), axi.get_ylim()]
            for this, other in zip(lims, test_lims):
                L = np.linalg.norm(np.array(this) - np.array(other))
                assert np.allclose(L, 0)
    # Should not emit any warnings
    assert len(record) == 0


def test_sharing_axes_different_projections():
    """
    Test sharing axes for GeoAxes
    """

    projs = ("cyl", "merc", "merc")
    with pytest.warns(uplt.internals.UltraPlotWarning) as record:
        fig, ax = uplt.subplots(ncols=1, nrows=3, share="all", proj=projs)
    assert len(record) == 1  # should only warn once
    ax.format(
        land=True,
        lonlim=(-10, 10),  # make small to plot quicker
        latlim=(-10, 10),
    )
    # The incompatible cylindrical subplot should stay isolated, while the two
    # compatible Mercator subplots can still share with each other.
    assert ax[0]._sharex is None
    assert ax[0]._sharey is None
    assert ax[1]._sharey is None
    assert ax[2]._sharey is None
    assert len(list(ax[0]._shared_axes["x"].get_siblings(ax[0]))) == 1
    assert len(list(ax[1]._shared_axes["x"].get_siblings(ax[1]))) == 2
    assert len(list(ax[2]._shared_axes["x"].get_siblings(ax[2]))) == 2

    cyl_lims = [ax[0].get_xlim(), ax[0].get_ylim()]
    merc_lims = [ax[1].get_xlim(), ax[1].get_ylim()]
    for this, other in zip(cyl_lims, merc_lims):
        delta = np.linalg.norm(np.array(this) - np.array(other))
        assert not np.allclose(delta, 0)

    for this, other in zip(merc_lims, [ax[2].get_xlim(), ax[2].get_ylim()]):
        delta = np.linalg.norm(np.array(this) - np.array(other))
        assert np.allclose(delta, 0)
