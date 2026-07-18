"""Tests for the shared style docstrings in ``ultraplot.internals.docstring``."""

import ultraplot as uplt
from ultraplot.internals import docstring


def test_style_snippets_lead_with_canonical_name() -> None:
    # The shared style fields should lead with the canonical parameter name and
    # relegate synonyms to a trailing "Aliases:" note, rather than opening the
    # numpydoc field with a pile of alias names.
    line = docstring._snippet_manager["artist.line"]
    assert line.lstrip().startswith("linewidth : unit-spec")
    assert "Aliases: ``lw``, ``linewidths``." in line
    assert "The color of the line(s)" in line
    assert "Aliases: ``c``, ``colors``." in line
    # The old alias-pile header must be gone.
    assert "lw, linewidth, linewidths :" not in line


def test_collection_snippets_lead_with_registry_canonical_names() -> None:
    for name in ("artist.collection_pcolor", "artist.collection_contour"):
        snippet = docstring._snippet_manager[name]
        assert snippet.lstrip().startswith("linewidths : unit-spec")
        assert "\nlinestyles : str" in snippet
        assert "\nedgecolors : color-spec" in snippet
        assert "Aliases: ``lw``, ``linewidth``." in snippet
        assert "Aliases: ``ls``, ``linestyle``." in snippet
        assert "Aliases: ``ec``, ``edgecolor``." in snippet


def test_contour_alpha_alias_typo_fixed() -> None:
    # Previously the contour snippet listed ``a, alpha, alpha`` (duplicate typo).
    contour = docstring._snippet_manager["artist.collection_contour"]
    assert "``a``, ``alphas``." in contour
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
    assert "Aliases: ``lw``" in doc
    assert "%(artist" not in doc


def test_geo_format_folds_alias_entries() -> None:
    # The geo format docstring folded its standalone "Aliases for ..." blocks
    # into trailing notes on the canonical locator entries.
    geo = docstring._snippet_manager["geo.format"]
    assert "Aliases for" not in geo
    assert "lonlocator, latlocator : locator-spec" in geo
    assert "Aliases: ``lonlines`` and ``latlines``, respectively." in geo
    assert (
        "Aliases: ``lonminorlines_kw`` and ``latminorlines_kw``, respectively." in geo
    )
