"""Tests for the shared style docstrings in ``ultraplot.internals.docstring``."""

import ultraplot as uplt
from ultraplot.internals import docstring


def test_style_snippets_lead_with_canonical_name() -> None:
    # Shared style fields only show canonical names. Compatibility spellings are
    # documented centrally in docs/aliases.rst.
    line = docstring._snippet_manager["artist.line"]
    assert line.lstrip().startswith("linewidth : unit-spec")
    assert "The color of the line(s)" in line
    assert "Aliases:" not in line
    # The old alias-pile header must be gone.
    assert "lw, linewidth, linewidths :" not in line


def test_collection_snippets_use_only_registry_canonical_names() -> None:
    for name in ("artist.collection_pcolor", "artist.collection_contour"):
        snippet = docstring._snippet_manager[name]
        assert snippet.lstrip().startswith("linewidths : unit-spec")
        assert "\nlinestyles : str" in snippet
        assert "\nedgecolors : color-spec" in snippet
        assert "Aliases:" not in snippet


def test_contour_alpha_alias_typo_fixed() -> None:
    # Previously the contour snippet listed ``a, alpha, alpha`` (duplicate typo).
    contour = docstring._snippet_manager["artist.collection_contour"]
    assert "Aliases:" not in contour
    assert "a, alpha, alpha" not in contour


def test_patch_edgecolor_placeholder_still_fills() -> None:
    # The patch snippet keeps its ``{edgecolor}`` placeholder for the later
    # ``.format(...)`` call; both registered variants must resolve it.
    assert "default: 'none'" in docstring._snippet_manager["artist.patch"]
    assert "default: 'black'" in docstring._snippet_manager["artist.patch_black"]


def test_method_docstring_fully_substituted() -> None:
    # A plotting method that pulls in %(artist.line)s must render without any
    # leftover unfilled snippet markers.
    doc = uplt.axes.PlotAxes.line.__doc__ or ""
    assert "linewidth : unit-spec" in doc
    assert "Aliases:" not in doc
    assert "%(artist" not in doc


def test_geo_format_uses_only_canonical_entries() -> None:
    # Compatibility spellings live in the generated alias reference instead of
    # competing with canonical parameters in each function's primary docs.
    geo = docstring._snippet_manager["geo.format"]
    assert "Aliases for" not in geo
    assert "lonlocator, latlocator : locator-spec" in geo
    assert "lonlines" not in geo
    assert "latlines" not in geo
