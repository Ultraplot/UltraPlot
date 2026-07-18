"""Tests for the keyword-argument / alias helpers in ``ultraplot.internals.kwargs``."""

import warnings

from ultraplot import internals
from ultraplot.internals import kwargs as ikwargs


def test_kwargs_helpers_reexported_from_package() -> None:
    # Moving the helpers into internals/kwargs.py must not change the import
    # surface: the package still re-exports the same objects.
    for name in (
        "_not_none",
        "_alias_kwargs",
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


def test_alias_kwargs_conflict_keeps_canonical_and_warns() -> None:
    @ikwargs._alias_kwargs(figwidth=("width",))
    def func(*, figwidth=None):
        return figwidth

    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        value = func(figwidth=1, width=2)
    assert value == 1  # canonical wins, matching _not_none precedence
    assert any("conflicting" in str(w.message).lower() for w in record)


def test_alias_kwargs_multiple_synonyms_first_wins() -> None:
    @ikwargs._alias_kwargs(saturation=("s", "c", "chroma"))
    def func(*, saturation=None):
        return saturation

    assert func(chroma=0.5) == 0.5
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        # Two synonyms: the first one encountered in declaration order wins.
        assert func(s=0.1, chroma=0.9) == 0.1
