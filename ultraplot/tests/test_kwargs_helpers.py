"""Tests for the keyword-argument / alias helpers in ``ultraplot.internals.kwargs``."""

import warnings

import pytest

from ultraplot import internals
from ultraplot.internals import guides
from ultraplot.internals import kwargs as ikwargs


def test_kwargs_helpers_reexported_from_package() -> None:
    # Moving the helpers into internals/kwargs.py must not change the import
    # surface: the package still re-exports the same objects.
    for name in (
        "_not_none",
        "_alias_kwargs",
        "_alias_registry",
        "_canonicalize_kwargs",
        "_format_alias_reference",
        "_figure_format_alias_scopes",
        "_format_alias_scopes",
        "_alias_maps",
        "_get_aliases",
        "_kwargs_to_args",
        "_pop_kwargs",
        "_pop_params",
        "_pop_props",
    ):
        assert getattr(internals, name) is getattr(ikwargs, name)


def test_not_none_first_non_none() -> None:
    assert ikwargs._not_none(None, None, 3, 4) == 3
    assert ikwargs._not_none(default=7) == 7
    assert ikwargs._not_none(a=None, b=5) == 5


def test_not_none_warns_on_conflicting_kwargs() -> None:
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        value = ikwargs._not_none(a=1, b=2)
    assert value == 1  # first non-None wins
    assert any("conflicting" in str(w.message).lower() for w in record)


def test_alias_kwargs_folds_synonym_to_canonical() -> None:
    @ikwargs._alias_kwargs(figwidth=("width",), refnum=("ref",))
    def func(*, refnum=1, figwidth=None, **kwargs):
        return refnum, figwidth, kwargs

    assert func() == (1, None, {})  # signature defaults untouched
    assert func(width=5) == (1, 5, {})  # synonym folded to canonical
    assert func(ref=2, figwidth=3) == (2, 3, {})  # mix of alias + canonical
    assert func(other=9) == (1, None, {"other": 9})  # unrelated kwargs pass through


def test_alias_kwargs_none_synonym_defers_to_default() -> None:
    @ikwargs._alias_kwargs(figwidth=("width",))
    def func(*, figwidth=42):
        return figwidth

    # Explicitly passing the synonym as None must not override the default.
    assert func(width=None) == 42


def test_alias_kwargs_conflict_raises() -> None:
    @ikwargs._alias_kwargs(figwidth=("width",))
    def func(*, figwidth=None):
        return figwidth

    with pytest.raises(TypeError, match="aliases"):
        func(figwidth=1, width=2)


def test_alias_kwargs_multiple_synonyms_raise() -> None:
    @ikwargs._alias_kwargs(saturation=("s", "c", "chroma"))
    def func(*, saturation=None):
        return saturation

    assert func(chroma=0.5) == 0.5
    with pytest.raises(TypeError, match="aliases"):
        func(s=0.1, chroma=0.9)


def test_registry_scope_translates_without_mutating_input() -> None:
    kwargs = {"xticks": [1, 2], "color": "red"}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = ikwargs._canonicalize_kwargs("cartesian.format", kwargs)
    assert kwargs == {"xticks": [1, 2], "color": "red"}
    assert result == {"xlocator": [1, 2], "color": "red"}


def test_registry_translates_explicit_format_keys() -> None:
    kwargs = {"xticks": [1, 2], "_explicit_format_keys": {"xticks"}}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = ikwargs._canonicalize_kwargs("cartesian.format", kwargs)
    assert result["_explicit_format_keys"] == {"xlocator"}


def test_ambiguous_alias_uses_call_context() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        axes = ikwargs._canonicalize_kwargs(
            ikwargs._format_alias_scopes, {"rlabels": 5}
        )
        figure = ikwargs._canonicalize_kwargs(
            ikwargs._figure_format_alias_scopes, {"rlabels": ["right"]}
        )
    assert axes == {"rformatter": 5}
    assert figure == {"rightlabels": ["right"]}


def test_alias_kwargs_combines_registered_scopes() -> None:
    @ikwargs._alias_kwargs(("plot.statistics", "plot.boxplot"))
    def func(*, means=None, medians=None, fill=None):
        return means, medians, fill

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert func(showmeans=True) == (True, None, None)
        assert func(filled=True) == (None, None, True)
    assert func._ultraplot_alias_scopes == ("plot.statistics", "plot.boxplot")
    assert func._ultraplot_aliases["fill"] == ("filled",)


def test_alias_kwargs_rejects_inline_aliases_with_registered_scopes() -> None:
    with pytest.raises(TypeError, match="Inline aliases"):
        ikwargs._alias_kwargs(("plot.statistics", "plot.boxplot"), old="new")


def test_alias_reference_is_generated_from_registry() -> None:
    reference = ikwargs._format_alias_reference()
    assert "Function keyword aliases" in reference
    assert "Artist property aliases" in reference
    assert "Dotless rc aliases" in reference
    assert "cartesian.format" in reference
    assert "xticks" in reference
    assert "xlocator" in reference


def test_guide_defaults_do_not_duplicate_accepted_aliases() -> None:
    kwargs = {"length": 0.5, "minorlocator": "minor"}
    guides._update_kw(kwargs, overwrite=False, shrink=1.0, minorticks=True)
    assert kwargs == {"length": 0.5, "minorlocator": "minor"}
