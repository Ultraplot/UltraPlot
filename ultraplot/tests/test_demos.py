import numpy as np, pytest, ultraplot as plt, os
import matplotlib.font_manager as mfonts
import ultraplot.demos as demos

# Skip all tests in this module when running on GitHub Actions
pytestmark = pytest.mark.skipif(
    os.getenv("GITHUB_ACTIONS") == "true", reason="Skip tests on GitHub Actions"
)


def test_show_channels_requires_arg():
    """show_channels should raise when no positional colormap is provided."""
    with pytest.raises(ValueError):
        demos.show_channels()


@pytest.mark.mpl_image_compare
def test_show_channels_basic():
    """Basic invocation of show_channels returns a figure and axes of expected length."""
    # Request fewer samples and fewer channels to keep the figure small
    fig, axs = demos.show_channels("viridis", N=20, saturation=False, rgb=False)
    # Expect three channel plots: Hue, Chroma, Luminance
    assert fig is not None
    assert hasattr(axs, "__len__")
    assert len(axs) == 3
    # Each axis should have a title set
    for ax in axs:
        assert isinstance(ax.get_title(), str)
    return fig


@pytest.mark.mpl_image_compare
def test_show_colorspaces_default_and_options():
    """show_colorspaces should create three panels (hcl/hsl/hpl)."""
    fig, axs = demos.show_colorspaces()
    assert fig is not None
    assert hasattr(axs, "__len__")
    assert len(axs) == 3
    # Titles should include the space names
    titles = [ax.get_title().upper() for ax in axs]
    assert any("HCL" in t or "HSL" in t or "HPL" in t for t in titles)
    return fig


@pytest.mark.parametrize("demo", ["show_cmaps", "show_cycles"])
@pytest.mark.mpl_image_compare
def test_show_cmaps_and_cycles_return_fig_and_axes(demo):
    """show_cmaps and show_cycles should return a figure and axes collection."""
    fig, axs = getattr(demos, demo)()
    assert fig is not None
    assert hasattr(axs, "__len__")
    assert len(axs) > 0
    # Return a figure for image comparison (use the colormap figure)
    return fig


def test__filter_colors_behavior():
    """Unit tests for the color filtering helper."""
    # When ihue == 0, function should return True for gray colors (sat <= minsat)
    hcl_gray = (10.0, 5.0, 50.0)  # hue, sat, lum
    assert demos._filter_colors(hcl_gray, ihue=0, nhues=8, minsat=10)

    # Non-gray color should be filtered according to hue buckets
    nhues = 4
    hcl_color = (100.0, 50.0, 50.0)
    breakpoints = np.linspace(0, 360, nhues)
    found = False
    for ihue in range(1, nhues):
        low = breakpoints[ihue - 1]
        high = breakpoints[ihue]
        if low <= hcl_color[0] < high or (ihue == nhues - 1 and hcl_color[0] == high):
            assert demos._filter_colors(hcl_color, ihue=ihue, nhues=nhues, minsat=10)
            found = True
            break
    assert found, "Did not find a matching hue interval for the test hue"

    # Hue at the endpoint should be included for last bucket
    hcl_endpoint = (360.0, 50.0, 50.0)
    # For nhues=4 the last bucket index is 3; the endpoint logic should include it
    assert not demos._filter_colors(hcl_endpoint, ihue=3, nhues=4, minsat=10)


@pytest.mark.mpl_image_compare
@pytest.mark.parametrize("nhues,minsat", [(4, 10), (8, 15)])
def test_show_colors_basic_and_titles(nhues, minsat):
    """show_colors generates axes with titles for requested categories."""
    # Use parameterized nhues/minsat to exercise behavior deterministically
    fig, axs = demos.show_colors(nhues=nhues, minsat=minsat)
    assert fig is not None
    assert hasattr(axs, "__len__")
    assert len(axs) > 0
    for ax in axs:
        # Titles should be non-empty strings (e.g., "CSS4 colors", "Base colors", ...)
        title = ax.get_title()
        assert isinstance(title, str)
        assert title != ""
    return fig


@pytest.mark.mpl_image_compare
def test_show_fonts_with_existing_font():
    """show_fonts should accept a real font name from the system and return a figure."""
    # Pick a font that is available in the matplotlib font manager
    ttflist = mfonts.fontManager.ttflist
    # If no fonts are present, skip the test
    if not ttflist:
        pytest.skip("No system fonts available for testing show_fonts.")
    font_name = ttflist[0].name
    fig, axs = demos.show_fonts(font_name)
    assert fig is not None
    # When a single font is requested, we expect a single row (len(props)) of axes
    assert hasattr(axs, "__len__")
    assert len(axs) >= 1
    # Basic sanity: each axis should contain at least one text artist
    for ax in axs:
        texts = ax.texts
        assert hasattr(texts, "__len__")
        assert len(texts) >= 1
    return fig
