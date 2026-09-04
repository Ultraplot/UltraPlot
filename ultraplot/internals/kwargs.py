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
]


# Compatibility aliases are deliberately kept outside function signatures. The
# first-level keys describe the API context because the same shorthand can map to
# different canonical Matplotlib names (for example ``lw`` for a Line2D versus a
# Collection). This is data, rather than decorator arguments scattered throughout
# the package, so it can also drive the migration reference and error messages.
_alias_registry = {
    "figure.init": {
        "refnum": ("ref",),
        "refaspect": ("aspect",),
        "refwidth": ("axwidth",),
        "refheight": ("axheight",),
        "figwidth": ("width",),
        "figheight": ("height",),
    },
    "axes.format": {
        "lefttitle": ("ltitle",),
        "centertitle": ("ctitle",),
        "righttitle": ("rtitle",),
        "upperlefttitle": ("ultitle",),
        "uppercentertitle": ("uctitle",),
        "upperrighttitle": ("urtitle",),
        "lowerlefttitle": ("lltitle",),
        "lowercentertitle": ("lctitle",),
        "lowerrighttitle": ("lrtitle",),
    },
    "cartesian.format": {
        "xspineloc": ("xloc",),
        "yspineloc": ("yloc",),
        "xformatter": ("xticklabels",),
        "yformatter": ("yticklabels",),
        "xlocator": ("xticks",),
        "ylocator": ("yticks",),
        "xminorlocator": ("xminorticks",),
        "yminorlocator": ("yminorticks",),
    },
    "geo.format": {
        "lonlocator": ("lonlines",),
        "latlocator": ("latlines",),
        "lonminorlocator": ("lonminorlines",),
        "latminorlocator": ("latminorlines",),
        "lonlocator_kw": ("lonlines_kw",),
        "latlocator_kw": ("latlines_kw",),
        "lonminorlocator_kw": ("lonminorlines_kw",),
        "latminorlocator_kw": ("latminorlines_kw",),
    },
    "polar.format": {
        "thetalocator": ("thetalines",),
        "rlocator": ("rlines",),
        "thetaminorlocator": ("thetaminorlines",),
        "rminorlocator": ("rminorlines",),
        "thetaformatter": ("thetalabels",),
        "rformatter": ("rlabels",),
    },
    "taylor.format": {
        "corrlocator": ("corrlines", "corrticks"),
    },
    "figure.format": {
        "suptitle": ("figtitle",),
        "leftlabels": ("llabels", "rowlabels"),
        "rightlabels": ("rlabels",),
        "bottomlabels": ("blabels",),
        "toplabels": ("tlabels", "collabels"),
    },
    "colorbar": {
        "loc": ("location",),
        "drawedges": ("grid", "edges"),
        "shrink": ("length",),
        "label": ("title",),
        "labellocation": ("labelloc",),
        "ticks": ("locator",),
        "format": ("formatter", "ticklabels"),
        "minorticks": ("minorlocator",),
        "color": ("c",),
        "linewidth": ("lw",),
        "tickdirection": ("tickdir",),
        "frameon": ("frame",),
    },
    "legend": {
        "loc": ("location",),
        "ncols": ("ncol",),
        "frameon": ("frame",),
    },
    "gridspec": {
        "width_ratios": ("wratios",),
        "height_ratios": ("hratios",),
    },
    "subplot": {
        "projection": ("proj",),
        "projection_kw": ("proj_kw",),
    },
    "inset": {
        "projection": ("proj",),
    },
    "cycle": {
        "samples": ("N",),
    },
    "projection": {
        "lon0": ("lon_0",),
        "lat0": ("lat_0",),
    },
    "scale.log": {
        "base": ("basex", "basey"),
        "nonpos": ("nonposx", "nonposy"),
        "subs": ("subsx", "subsy"),
    },
    "scale.symlog": {
        "base": ("basex", "basey"),
        "linthresh": ("linthreshx", "linthreshy"),
        "linscale": ("linscalex", "linscaley"),
        "subs": ("subsx", "subsy"),
    },
    "plot.labels": {
        "formatter": ("fmt",),
    },
    "plot.text": {
        "color": ("c", "colors"),
        "fontsize": ("size",),
    },
    "plot.contour_labels": {
        "colors": ("c", "color"),
        "fontsize": ("size",),
    },
    "plot.error_bars": {
        "barstds": ("bars", "barstd"),
        "barpctiles": ("barpctile",),
        "boxstds": ("boxes", "boxstd"),
        "boxpctiles": ("boxpctile",),
    },
    "plot.error_shading": {
        "shadestds": ("shade", "shadestd"),
        "shadepctiles": ("shadepctile",),
        "fadestds": ("fade", "fadestd"),
        "fadepctiles": ("fadepctile",),
    },
    "plot.colormap": {
        "colors": ("c", "color"),
    },
    "plot.levels": {
        "levels": ("N",),
    },
    "plot.stacked": {
        "stacked": ("stack",),
    },
    "plot.statistics": {
        "means": ("mean",),
        "medians": ("median",),
    },
    "plot.boxplot": {
        "means": ("showmeans",),
        "fill": ("filled",),
    },
    "plot.violinplot": {
        "means": ("showmeans",),
        "medians": ("showmedians",),
    },
    "plot.hist": {
        "rwidth": ("width",),
        "stacked": ("stack",),
        "fill": ("filled",),
    },
    "plot.pie": {
        "labeldistance": ("labelpad",),
    },
}

_format_alias_scopes = (
    "axes.format",
    "cartesian.format",
    "geo.format",
    "polar.format",
    "taylor.format",
)
_figure_format_alias_scopes = ("figure.format", *_format_alias_scopes)


def _get_alias_groups(scope=None, aliases=None):
    """Return validated canonical-to-legacy alias groups."""
    if scope is not None and aliases:
        raise TypeError("Pass an alias registry scope or inline aliases, not both.")
    if scope is None:
        groups = aliases or {}
    else:
        try:
            groups = _alias_registry[scope]
        except KeyError:
            raise KeyError(f"Unknown alias registry scope {scope!r}.") from None
    return {
        canonical: (legacy,) if isinstance(legacy, str) else tuple(legacy)
        for canonical, legacy in groups.items()
    }


def _canonicalize_kwargs(
    scope, kwargs, *, aliases=None, provided=(), warn=False
):
    """
    Return a copy of *kwargs* with legacy names translated to canonical names.

    Only explicitly registered spellings are translated. Supplying two spellings
    for one parameter raises ``TypeError``, matching Matplotlib's alias handling.
    The input mapping is never mutated. Translation is intentionally silent during
    the compatibility stage; a later deprecation can opt into warnings with
    ``warn=True`` without changing call signatures or registry data.
    """
    if isinstance(scope, (tuple, list)):
        if aliases:
            raise TypeError("Inline aliases cannot be combined with multiple scopes.")
        output = dict(kwargs)
        for item in scope:
            output = _canonicalize_kwargs(
                item, output, provided=provided, warn=warn
            )
        return output
    groups = _get_alias_groups(scope, aliases)
    lookup = {
        legacy: canonical
        for canonical, legacy_names in groups.items()
        for legacy in legacy_names
    }
    output = dict(kwargs)
    explicit = output.get("_explicit_format_keys")
    if explicit is not None:
        output["_explicit_format_keys"] = {
            lookup.get(name, name) for name in explicit
        }
    seen = {
        canonical: canonical
        for canonical in groups
        if output.get(canonical) is not None
    }
    seen.update(
        {
            canonical: canonical
            for canonical in provided
            if canonical in groups and provided[canonical] is not None
        }
    )
    # Validate the entire call before translating anything so invalid calls do
    # not emit a partial sequence of migration warnings.
    for legacy, value in output.items():
        canonical = lookup.get(legacy)
        if canonical is None or value is None:
            continue
        if canonical in seen:
            raise TypeError(
                f"Got both {seen[canonical]!r} and {legacy!r}, which are aliases "
                f"for {canonical!r}."
            )
        seen[canonical] = legacy
    for legacy in tuple(output):
        canonical = lookup.get(legacy)
        if canonical is None:
            continue
        value = output.pop(legacy)
        # ``None`` is how pyplot and UltraPlot wrappers forward unspecified
        # options. Treat it as absent so it neither warns nor shadows defaults.
        if value is None:
            continue
        output[canonical] = value
        if warn:
            warnings._warn_ultraplot(
                f"Keyword {legacy!r} is deprecated; use {canonical!r} instead."
            )
    return output


def _format_alias_table(rows):
    """Format alias rows as a simple RST table."""
    rows = [("Context", "Accepted spelling", "Canonical spelling"), *rows]
    widths = [max(len(row[idx]) for row in rows) for idx in range(3)]
    rule = " ".join("=" * width for width in widths)
    lines = [rule]
    for idx, row in enumerate(rows):
        lines.append(
            " ".join(value.ljust(widths[col]) for col, value in enumerate(row)).rstrip()
        )
        if idx == 0:
            lines.append(rule)
    lines.append(rule)
    return "\n".join(lines)


def _format_alias_reference():
    """Return the registered compatibility aliases as grouped RST tables."""
    function_rows = []
    style_rows = []
    for scope, groups in _alias_registry.items():
        target = style_rows if scope.startswith("style.") else function_rows
        for canonical, aliases in groups.items():
            target.extend((scope, legacy, canonical) for legacy in aliases)

    # Dotted rc names cannot be Python identifiers, so UltraPlot historically
    # accepted dotless spellings in ``format()`` kwargs. Generate these mappings
    # from the rc registry instead of copying hundreds of entries by hand.
    from . import rcsetup

    rc_rows = [
        ("rc (dotless)", legacy, canonical)
        for legacy, canonical in sorted(rcsetup._rc_nodots.items())
        if legacy != canonical
    ]
    sections = (
        (
            "Function keyword aliases",
            "These mappings apply only in the listed call context.",
            function_rows,
        ),
        (
            "Artist property aliases",
            "These are Matplotlib-style shorthand properties accepted while styling artists.",
            style_rows,
        ),
        (
            "Dotless rc aliases",
            "Use the dotted canonical spelling through ``rc_kw`` when avoiding the accepted shorthand.",
            rc_rows,
        ),
    )
    rendered = [
        f"{title}\n{'-' * len(title)}\n\n{description}\n\n{_format_alias_table(rows)}"
        for title, description, rows in sections
    ]
    return "\n\n".join(rendered)


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


def _alias_kwargs(scope=None, **aliases):
    """
    Fold keyword-argument aliases into their canonical names before a call.

    Pass a registry scope, e.g. ``@_alias_kwargs("figure.init")``. Inline mappings
    remain available for small private helpers, but public compatibility aliases
    should live in `_alias_registry` so they can be documented and audited.

    This handles keyword aliases only. Canonical arguments passed positionally
    are included in duplicate detection, and a synonym must not shadow a
    different real parameter of the wrapped function.
    """
    if isinstance(scope, (tuple, list)):
        if aliases:
            raise TypeError("Inline aliases cannot be combined with multiple scopes.")
        groups = {}
        for item in scope:
            groups.update(_get_alias_groups(item))
    else:
        groups = _get_alias_groups(scope, aliases)

    def decorator(func):
        signature = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Bind positional arguments separately so ``func(value, alias=value)``
            # is diagnosed before the translated call reaches Python's binder.
            provided = signature.bind_partial(*args).arguments
            kwargs = _canonicalize_kwargs(
                scope,
                kwargs,
                aliases=groups if scope is None else None,
                provided=provided,
            )
            return func(*args, **kwargs)

        wrapper._ultraplot_alias_scopes = (
            tuple(scope)
            if isinstance(scope, (tuple, list))
            else (scope,) if scope is not None else ()
        )
        wrapper._ultraplot_aliases = dict(groups)
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

# Style aliases are consumed by ``_pop_props`` rather than decorators, but they
# belong to the same context-aware compatibility registry. Keeping the legacy
# ``_alias_maps`` name as a view avoids a broad internal migration while making
# the complete public mapping discoverable and documentable in one place.
_alias_registry.update(
    {f"style.{category}": groups for category, groups in _alias_maps.items()}
)


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
