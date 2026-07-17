#!/usr/bin/env python3
"""
Keyword-argument and alias resolution utilities.

These helpers centralize how ultraplot resolves keyword aliases, folds synonym
keywords into canonical names, and pops parameters/properties out of ``**kwargs``.
They live in their own module (rather than the ``internals`` grab-bag) because
they form a single cohesive concern and are imported throughout the package.
"""

import functools
import inspect

from . import warnings

__all__ = [
    "_not_none",
    "_alias_kwargs",
    "_alias_maps",
    "_get_aliases",
    "_kwargs_to_args",
    "_pop_kwargs",
    "_pop_params",
    "_pop_props",
]


def _not_none(*args, default=None, **kwargs):
    """
    Return the first non-``None`` value. This is used with keyword arg aliases and
    for setting default values. Use `kwargs` to issue warnings when multiple passed.
    """
    first = default
    if args and kwargs:
        raise ValueError("_not_none can only be used with args or kwargs.")
    elif args:
        for arg in args:
            if arg is not None:
                first = arg
                break
    elif kwargs:
        for name, arg in list(kwargs.items()):
            if arg is not None:
                first = arg
                break
        kwargs = {name: arg for name, arg in kwargs.items() if arg is not None}
        if len(kwargs) > 1:
            warnings._warn_ultraplot(
                f"Got conflicting or duplicate keyword arguments: {kwargs}. "
                "Using the first keyword argument."
            )
    return first


def _alias_kwargs(**aliases):
    """
    Fold keyword-argument aliases into their canonical names before a call.

    Each keyword maps a canonical parameter name to a tuple of accepted synonyms,
    e.g. ``@_alias_kwargs(figwidth=("width",), refnum=("ref",))``. A synonym passed
    by the caller is renamed to its canonical name. Passing a canonical together
    with a synonym (or two synonyms) warns and keeps the canonical / first value,
    matching the precedence and warning of `_not_none`. This replaces the repetitive
    ``x = _not_none(x=x, y=y)`` boilerplate at the top of aliased functions.

    This handles keyword aliases only: a canonical argument passed *positionally*
    is not deduplicated against its synonyms, and a synonym must not shadow a
    different real parameter of the wrapped function.
    """
    # Map each synonym to its canonical name; synonyms are tried in declared order
    # so the first non-``None`` one wins, exactly like `_not_none`.
    lookup = {syn: canon for canon, syns in aliases.items() for syn in syns}

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for syn, canon in lookup.items():
                if syn not in kwargs:
                    continue
                value = kwargs.pop(syn)
                if value is None:
                    continue
                if kwargs.get(canon) is None:
                    kwargs[canon] = value
                else:
                    # ``canon`` already holds an earlier value (from the canonical
                    # keyword or a prior synonym); keep it and drop this synonym.
                    warnings._warn_ultraplot(
                        f"Got conflicting or duplicate values for {canon!r} "
                        f"(ignoring alias {syn!r}). Using the first value."
                    )
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Style aliases. We use this rather than matplotlib's normalize_kwargs and _alias_maps.
# NOTE: We add aliases 'edgewidth' and 'fillcolor' for patch edges and faces
# NOTE: Alias cannot appear as key or else _translate_kwargs will overwrite with None!
_alias_maps = {
    "rgba": {
        "red": ("r",),
        "green": ("g",),
        "blue": ("b",),
        "alpha": ("a",),
    },
    "hsla": {
        "hue": ("h",),
        "saturation": ("s", "c", "chroma"),
        "luminance": ("l",),
        "alpha": ("a",),
    },
    "patch": {
        "alpha": (
            "a",
            "alphas",
            "fa",
            "facealpha",
            "facealphas",
            "fillalpha",
            "fillalphas",
        ),  # noqa: E501
        "color": ("c", "colors"),
        "edgecolor": ("ec", "edgecolors"),
        "facecolor": ("fc", "facecolors", "fillcolor", "fillcolors"),
        "hatch": ("h", "hatching"),
        "linestyle": ("ls", "linestyles"),
        "linewidth": ("lw", "linewidths", "ew", "edgewidth", "edgewidths"),
        "zorder": ("z", "zorders"),
    },
    "line": {  # copied from lines.py but expanded to include plurals
        "alpha": ("a", "alphas"),
        "color": ("c", "colors"),
        "dashes": ("d", "dash"),
        "drawstyle": ("ds", "drawstyles"),
        "fillstyle": ("fs", "fillstyles", "mfs", "markerfillstyle", "markerfillstyles"),
        "linestyle": ("ls", "linestyles"),
        "linewidth": ("lw", "linewidths"),
        "marker": ("m", "markers"),
        "markersize": ("s", "ms", "markersizes"),  # WARNING: no 'sizes' here for barb
        "markeredgewidth": ("ew", "edgewidth", "edgewidths", "mew", "markeredgewidths"),
        "markeredgecolor": ("ec", "edgecolor", "edgecolors", "mec", "markeredgecolors"),
        "markerfacecolor": (
            "fc",
            "facecolor",
            "facecolors",
            "fillcolor",
            "fillcolors",
            "mc",
            "markercolor",
            "markercolors",
            "mfc",
            "markerfacecolors",
        ),
        "zorder": ("z", "zorders"),
    },
    "collection": {  # WARNING: face color ignored for line collections
        "alpha": ("a", "alphas"),  # WARNING: collections and contours use singular!
        "colors": ("c", "color"),
        "edgecolors": ("ec", "edgecolor", "mec", "markeredgecolor", "markeredgecolors"),
        "facecolors": (
            "fc",
            "facecolor",
            "fillcolor",
            "fillcolors",
            "mc",
            "markercolor",
            "markercolors",
            "mfc",
            "markerfacecolor",
            "markerfacecolors",  # noqa: E501
        ),
        "linestyles": ("ls", "linestyle"),
        "linewidths": (
            "lw",
            "linewidth",
            "ew",
            "edgewidth",
            "edgewidths",
            "mew",
            "markeredgewidth",
            "markeredgewidths",
        ),  # noqa: E501
        "marker": ("m", "markers"),
        "sizes": ("s", "ms", "markersize", "markersizes"),
        "zorder": ("z", "zorders"),
    },
    "text": {
        "color": ("c", "fontcolor"),  # NOTE: see text.py source code
        "fontfamily": ("family", "name", "fontname"),
        "fontsize": ("size",),
        "fontstretch": ("stretch",),
        "fontstyle": ("style",),
        "fontvariant": ("variant",),
        "fontweight": ("weight",),
        "fontproperties": ("fp", "font", "font_properties"),
        "zorder": ("z", "zorders"),
    },
}


_INTERNAL_POP_PARAMS = frozenset(
    {
        "default_cmap",
        "default_discrete",
        "inbounds",
        "plot_contours",
        "plot_lines",
        "skip_autolev",
        "to_centers",
    }
)


@functools.lru_cache(maxsize=256)
def _signature_cached(func):
    """
    Cache inspect.signature lookups for hot utility paths.
    """
    return inspect.signature(func)


def _get_signature(func):
    """
    Return a signature, normalizing bound methods to their underlying function.
    """
    key = getattr(func, "__func__", func)
    try:
        return _signature_cached(key)
    except TypeError:
        # Some callable objects may be unhashable for lru_cache keys.
        return inspect.signature(func)


def _get_aliases(category, *keys):
    """
    Get all available aliases.
    """
    aliases = []
    for key in keys:
        aliases.append(key)
        aliases.extend(_alias_maps[category][key])
    return tuple(aliases)


def _kwargs_to_args(options, *args, allow_extra=False, **kwargs):
    """
    Translate keyword arguments to positional arguments. Permit omitted
    arguments so that plotting functions can infer values.
    """
    nargs, nopts = len(args), len(options)
    if nargs > nopts and not allow_extra:
        raise ValueError(f"Expected up to {nopts} positional arguments. Got {nargs}.")
    args = list(args)  # WARNING: Axes.text() expects return type of list
    args.extend(None for _ in range(nopts - nargs))  # fill missing args
    for idx, keys in enumerate(options):
        if isinstance(keys, str):
            keys = (keys,)
        opts = {}
        if args[idx] is not None:  # positional args have first priority
            opts[keys[0] + "_positional"] = args[idx]
        for key in keys:  # keyword args
            opts[key] = kwargs.pop(key, None)
        args[idx] = _not_none(**opts)  # may reassign None
    return args, kwargs


def _pop_kwargs(kwargs, *keys, **aliases):
    """
    Pop the input properties and return them in a new dictionary.
    """
    output = {}
    aliases.update({key: () for key in keys})
    for key, aliases in aliases.items():
        aliases = (aliases,) if isinstance(aliases, str) else aliases
        opts = {key: kwargs.pop(key, None) for key in (key, *aliases)}
        value = _not_none(**opts)
        if value is not None:
            output[key] = value
    return output


def _pop_params(kwargs, *funcs, ignore_internal=False):
    """
    Pop parameters of the input functions or methods.
    """
    output = {}
    for func in funcs:
        if isinstance(func, inspect.Signature):
            sig = func
        elif callable(func):
            sig = _get_signature(func)
        elif func is None:
            continue
        else:
            raise RuntimeError(f"Internal error. Invalid function {func!r}.")
        for key in sig.parameters:
            value = kwargs.pop(key, None)
            if ignore_internal and key in _INTERNAL_POP_PARAMS:
                continue
            if value is not None:
                output[key] = value
    return output


def _pop_props(input, *categories, prefix=None, ignore=None, skip=None):
    """
    Pop the registered properties and return them in a new dictionary.
    """
    output = {}
    skip = skip or ()
    ignore = ignore or ()
    if isinstance(skip, str):  # e.g. 'sizes' for barbs() input
        skip = (skip,)
    if isinstance(ignore, str):  # e.g. 'marker' to ignore marker properties
        ignore = (ignore,)
    prefix = prefix or ""  # e.g. 'box' for boxlw, boxlinewidth, etc.
    for category in categories:
        for key, aliases in _alias_maps[category].items():
            if isinstance(aliases, str):
                aliases = (aliases,)
            opts = {
                prefix + alias: input.pop(prefix + alias, None)
                for alias in (key, *aliases)
                if alias not in skip
            }
            prop = _not_none(**opts)
            if prop is None:
                continue
            if any(string in key for string in ignore):
                warnings._warn_ultraplot(f"Ignoring property {key}={prop!r}.")
                continue
            if isinstance(prop, str):  # ad-hoc unit conversion
                if key in ("fontsize",):
                    from ..utils import _fontsize_to_pt

                    prop = _fontsize_to_pt(prop)
                if key in ("linewidth", "linewidths", "markersize"):
                    from ..utils import units

                    prop = units(prop, "pt")
            output[key] = prop
    return output
