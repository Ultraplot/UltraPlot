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


def test_taylor_projection_labels_and_defaults():
    fig, axs = uplt.subplots(proj="taylor")
    ax = axs[0]

    assert ax._name == "taylor"
    ax.format(xlabel="STD X", ylabel="STD Y")
    fig.canvas.draw()

    assert ax.get_xlabel() == "STD X"
    assert ax.get_ylabel() == "STD Y"
    assert not ax.xaxis.label.get_visible()
    assert not ax.yaxis.label.get_visible()
    assert ax._taylor_xlabel_artist.get_text() == "STD X"
    assert ax._taylor_ylabel_artist.get_text() == "STD Y"
    assert ax._taylor_corrlabel_artist.get_text() == "Correlation"
    assert np.allclose(np.rad2deg(ax.get_xlim()), (0.0, 90.0))
    assert ax.get_rlabel_position() == pytest.approx(135.0)
    assert [label.get_text() for label in ax.get_xticklabels()] == [
        "1.00",
        "0.95",
        "0.90",
        "0.80",
        "0.60",
        "0.40",
        "0.20",
        "0.00",
    ]


def test_taylor_projection_thetaunit_deg():
    fig, axs = uplt.subplots(proj="taylor")
    ax = axs[0]
    ax.format(thetaunit="deg")
    fig.canvas.draw()

    labels = [label.get_text() for label in ax.get_xticklabels() if label.get_text()]
    assert labels
    assert any("°" in label for label in labels)


def test_taylor_projection_via_figure_format_dispatch():
    fig, axs = uplt.subplots(ncols=2, proj="taylor")
    axs.format(xlabel="Common X", ylabel="Common Y")
    for ax in axs:
        assert ax.get_xlabel() == "Common X"
        assert ax.get_ylabel() == "Common Y"


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
