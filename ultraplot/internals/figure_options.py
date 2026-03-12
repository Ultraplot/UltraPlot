#!/usr/bin/env python3
"""
Helpers for parsing Figure constructor options.
"""

from dataclasses import dataclass

import numpy as np

from ..config import rc, rc_matplotlib
from ..utils import units
from . import _not_none, warnings


@dataclass(frozen=True)
class FigureSizeOptions:
    refnum: int
    refaspect: object
    refwidth: object
    refheight: object
    figwidth: object
    figheight: object
    interactive_warning: bool = False


@dataclass(frozen=True)
class FigureShareOptions:
    sharex: int
    sharey: int
    sharex_auto: bool
    sharey_auto: bool


@dataclass(frozen=True)
class FigureSpanAlignOptions:
    spanx: bool
    spany: bool
    alignx: bool
    aligny: bool


def resolve_size_options(
    *,
    refnum=None,
    ref=None,
    refaspect=None,
    aspect=None,
    refwidth=None,
    refheight=None,
    axwidth=None,
    axheight=None,
    figwidth=None,
    figheight=None,
    width=None,
    height=None,
    journal=None,
    journal_size_resolver=None,
    backend_name=None,
    warn_interactive_enabled=False,
):
    """
    Resolve figure sizing aliases, defaults, and interactive-backend fallbacks.
    """
    refnum = _not_none(refnum=refnum, ref=ref, default=1)
    refaspect = _not_none(refaspect=refaspect, aspect=aspect)
    refwidth = _not_none(refwidth=refwidth, axwidth=axwidth)
    refheight = _not_none(refheight=refheight, axheight=axheight)
    figwidth = _not_none(figwidth=figwidth, width=width)
    figheight = _not_none(figheight=figheight, height=height)

    _warn_size_conflicts(
        journal=journal,
        figwidth=figwidth,
        figheight=figheight,
        refwidth=refwidth,
        refheight=refheight,
        journal_size_resolver=journal_size_resolver,
    )
    if journal is not None and journal_size_resolver is not None:
        jwidth, jheight = journal_size_resolver(journal)
        figwidth = _not_none(jwidth, figwidth)
        figheight = _not_none(jheight, figheight)

    if figwidth is not None and refwidth is not None:
        refwidth = None
    if figheight is not None and refheight is not None:
        refheight = None
    if (
        figwidth is None
        and figheight is None
        and refwidth is None
        and refheight is None
    ):
        refwidth = rc["subplots.refwidth"]
    if np.iterable(refaspect):
        refaspect = refaspect[0] / refaspect[1]

    interactive_warning = False
    backend_name = _not_none(backend_name, "").lower()
    interactive = "nbagg" in backend_name or "ipympl" in backend_name
    if interactive and (figwidth is None or figheight is None):
        figsize = rc["figure.figsize"]
        figwidth = _not_none(figwidth, figsize[0])
        figheight = _not_none(figheight, figsize[1])
        refwidth = refheight = None
        interactive_warning = bool(warn_interactive_enabled)

    return FigureSizeOptions(
        refnum=refnum,
        refaspect=refaspect,
        refwidth=units(refwidth, "in"),
        refheight=units(refheight, "in"),
        figwidth=units(figwidth, "in"),
        figheight=units(figheight, "in"),
        interactive_warning=interactive_warning,
    )


def build_gridspec_params(**params):
    """
    Build and validate scalar gridspec spacing parameters.
    """
    for key, value in tuple(params.items()):
        if not isinstance(value, str) and np.iterable(value) and len(value) > 1:
            raise ValueError(
                f"Invalid gridspec parameter {key}={value!r}. Space parameters "
                "passed to Figure() must be scalar. For vector spaces use "
                "GridSpec() or pass space parameters to subplots()."
            )
    return params


def resolve_tight_active(
    kwargs,
    *,
    tight=None,
    space_message="",
    tight_message="",
):
    """
    Normalize native Matplotlib layout kwargs and return the active tight flag.
    """
    pars = kwargs.pop("subplotpars", None)
    if pars is not None:
        warnings._warn_ultraplot(f"Ignoring subplotpars={pars!r}. " + space_message)
    if kwargs.pop("tight_layout", None):
        warnings._warn_ultraplot("Ignoring tight_layout=True. " + tight_message)
    if kwargs.pop("constrained_layout", None):
        warnings._warn_ultraplot("Ignoring constrained_layout=True. " + tight_message)
    if rc_matplotlib.get("figure.autolayout", False):
        warnings._warn_ultraplot(
            "Setting rc['figure.autolayout'] to False. " + tight_message
        )
    if rc_matplotlib.get("figure.constrained_layout.use", False):
        warnings._warn_ultraplot(
            "Setting rc['figure.constrained_layout.use'] to False. " + tight_message
        )
    try:
        rc_matplotlib["figure.autolayout"] = False
    except KeyError:
        pass
    try:
        rc_matplotlib["figure.constrained_layout.use"] = False
    except KeyError:
        pass
    return _not_none(tight, rc["subplots.tight"])


def resolve_share_options(
    *,
    sharex=None,
    sharey=None,
    share=None,
    share_message="",
):
    """
    Normalize figure-wide share settings and auto-share flags.
    """
    translate = {"labels": 1, "labs": 1, "limits": 2, "lims": 2, "all": 4}
    sharex = _not_none(sharex, share, rc["subplots.share"])
    sharey = _not_none(sharey, share, rc["subplots.share"])

    def _normalize_share(value):
        auto = isinstance(value, str) and value.lower() == "auto"
        if auto:
            return 3, True
        value = 3 if value is True else translate.get(value, value)
        if value not in range(5):
            raise ValueError(f"Invalid sharing value {value!r}. " + share_message)
        return int(value), False

    sharex, sharex_auto = _normalize_share(sharex)
    sharey, sharey_auto = _normalize_share(sharey)
    return FigureShareOptions(
        sharex=int(sharex),
        sharey=int(sharey),
        sharex_auto=bool(sharex_auto),
        sharey_auto=bool(sharey_auto),
    )


def resolve_span_align_options(
    *,
    sharex,
    sharey,
    spanx=None,
    spany=None,
    span=None,
    alignx=None,
    aligny=None,
    align=None,
):
    """
    Normalize span and alignment flags derived from share settings.
    """
    spanx = _not_none(spanx, span, False if not sharex else None, rc["subplots.span"])
    spany = _not_none(spany, span, False if not sharey else None, rc["subplots.span"])
    if spanx and (alignx or align):
        warnings._warn_ultraplot('"alignx" has no effect when spanx=True.')
    if spany and (aligny or align):
        warnings._warn_ultraplot('"aligny" has no effect when spany=True.')
    alignx = _not_none(alignx, align, rc["subplots.align"])
    aligny = _not_none(aligny, align, rc["subplots.align"])
    return FigureSpanAlignOptions(
        spanx=bool(spanx),
        spany=bool(spany),
        alignx=bool(alignx),
        aligny=bool(aligny),
    )


def _warn_size_conflicts(
    *,
    journal=None,
    figwidth=None,
    figheight=None,
    refwidth=None,
    refheight=None,
    journal_size_resolver=None,
):
    messages = []
    if journal is not None and journal_size_resolver is not None:
        jwidth, jheight = journal_size_resolver(journal)
        if jwidth is not None and figwidth is not None:
            messages.append(("journal", journal, "figwidth", figwidth))
        if jheight is not None and figheight is not None:
            messages.append(("journal", journal, "figheight", figheight))
    if figwidth is not None and refwidth is not None:
        messages.append(("figwidth", figwidth, "refwidth", refwidth))
    if figheight is not None and refheight is not None:
        messages.append(("figheight", figheight, "refheight", refheight))
    for key1, val1, key2, val2 in messages:
        warnings._warn_ultraplot(
            f"Got conflicting figure size arguments {key1}={val1!r} and "
            f"{key2}={val2!r}. Ignoring {key2!r}."
        )
