#!/usr/bin/env python3
"""
Shared metadata for axis formatting keyword routing and persistence.
"""

import inspect

_GENERIC_AXIS_LABEL_FORMAT_KEYS = {
    "labelpad",
    "labelcolor",
    "labelsize",
    "labelweight",
}

AXIS_LABEL_FORMAT_KEYS = {
    axis: {
        f"{axis}label",
        f"{axis}labelloc",
        f"{axis}labelpad",
        f"{axis}labelcolor",
        f"{axis}labelsize",
        f"{axis}labelweight",
        f"{axis}label_kw",
    }
    | _GENERIC_AXIS_LABEL_FORMAT_KEYS
    for axis in "xy"
}
AXIS_SHARED_STATE_FORMAT_KEYS = {
    axis: {
        f"{axis}lim",
        f"{axis}min",
        f"{axis}max",
        f"{axis}scale",
        f"{axis}reverse",
        f"{axis}margin",
        f"{axis}formatter",
        f"{axis}ticklabels",
        f"{axis}ticks",
        f"{axis}locator",
        f"{axis}minorticks",
        f"{axis}minorlocator",
        f"{axis}tickrange",
        f"{axis}wraprange",
        f"{axis}scale_kw",
        f"{axis}locator_kw",
        f"{axis}formatter_kw",
        f"{axis}minorlocator_kw",
    }
    for axis in "xy"
}
AXIS_TICKLABEL_SHARING_FORMAT_KEYS = {
    axis: {
        f"{axis}loc",
        f"{axis}spineloc",
        f"{axis}tickloc",
        f"{axis}ticklabelloc",
    }
    for axis in "xy"
}

# Geographic axes use longitude as their x-like coordinate and latitude as
# their y-like coordinate. Keep these aliases in the shared classifier so
# sparse Figure.format() calls and direct GeoAxes.format() calls make the same
# sharing decision as their Cartesian counterparts.
AXIS_SHARED_STATE_FORMAT_KEYS["x"].update(
    {
        "extent",
        "lonlim",
        "lonlocator",
        "lonlines",
        "lonminorlocator",
        "lonminorlines",
        "lonformatter",
        "lonlocator_kw",
        "lonlines_kw",
        "lonminorlocator_kw",
        "lonminorlines_kw",
        "lonformatter_kw",
        "dms",
    }
)
AXIS_SHARED_STATE_FORMAT_KEYS["y"].update(
    {
        "extent",
        "latlim",
        "boundinglat",
        "latmax",
        "latlocator",
        "latlines",
        "latminorlocator",
        "latminorlines",
        "latformatter",
        "latlocator_kw",
        "latlines_kw",
        "latminorlocator_kw",
        "latminorlines_kw",
        "latformatter_kw",
        "dms",
    }
)
AXIS_TICKLABEL_SHARING_FORMAT_KEYS["x"].update(
    {"labels", "lonlabels", "loninline", "inlinelabels"}
)
AXIS_TICKLABEL_SHARING_FORMAT_KEYS["y"].update(
    {"labels", "latlabels", "latinline", "inlinelabels"}
)

_AXIS_STYLE_FIELD_TEMPLATES = {
    "color": (
        "{axis}color",
        "color",
        "{axis}ec",
        "ec",
        "{axis}edgecolor",
        "edgecolor",
        "axesec",
        "axesedgecolor",
    ),
    "linewidth": (
        "{axis}linewidth",
        "linewidth",
        "{axis}lw",
        "lw",
        "axeslw",
        "axeslinewidth",
    ),
    "rotation": ("{axis}rotation", "rotation"),
    "spineloc": ("{axis}spineloc", "{axis}loc"),
    "tickloc": ("{axis}tickloc",),
    "ticklabelloc": ("{axis}ticklabelloc",),
    "labelloc": ("{axis}labelloc",),
    "offsetloc": ("{axis}offsetloc",),
    "grid": ("{axis}grid",),
    "gridminor": ("{axis}gridminor",),
    "gridcolor": ("{axis}gridcolor", "gridcolor"),
    "tickdir": ("{axis}tickdir", "tickdir"),
    "tickcolor": ("{axis}tickcolor", "tickcolor"),
    "ticklen": ("{axis}ticklen", "ticklen"),
    "ticklenratio": ("{axis}ticklenratio", "ticklenratio"),
    "tickwidth": ("{axis}tickwidth", "tickwidth"),
    "tickwidthratio": ("{axis}tickwidthratio", "tickwidthratio"),
    "ticklabeldir": ("{axis}ticklabeldir", "ticklabeldir"),
    "ticklabelpad": ("{axis}ticklabelpad",),
    "ticklabelcolor": ("{axis}ticklabelcolor", "ticklabelcolor"),
    "ticklabelsize": ("{axis}ticklabelsize", "ticklabelsize"),
    "ticklabelweight": ("{axis}ticklabelweight", "ticklabelweight"),
    "labelpad": ("{axis}labelpad",),
    "labelcolor": ("{axis}labelcolor", "labelcolor"),
    "labelsize": ("{axis}labelsize", "labelsize"),
    "labelweight": ("{axis}labelweight", "labelweight"),
}

# These fields change only how existing geometry is painted. They do not change
# tick locations, text metrics, padding, or another layout input. Keep this list
# deliberately conservative: unknown fields must continue to invalidate layout.
_PAINT_ONLY_AXIS_STYLE_FIELDS = {
    "color",
    "linewidth",
    "grid",
    "gridminor",
    "gridcolor",
    "tickcolor",
    "tickwidth",
    "tickwidthratio",
    "ticklabelcolor",
    "labelcolor",
}


def _dedupe(items):
    return tuple(dict.fromkeys(items))


GENERIC_AXIS_FORMAT_KEYS = _dedupe(
    name
    for names in _AXIS_STYLE_FIELD_TEMPLATES.values()
    for name in names
    if "{axis}" not in name
)

PAINT_ONLY_AXIS_FORMAT_KEYS = frozenset(
    name.format(axis=axis)
    for field in _PAINT_ONLY_AXIS_STYLE_FIELDS
    for name in _AXIS_STYLE_FIELD_TEMPLATES[field]
    for axis in ("x", "y")
)


CARTESIAN_PARENT_FILTER_KEYS = GENERIC_AXIS_FORMAT_KEYS + (
    "label_kw",
    "scale_kw",
    "locator_kw",
    "formatter_kw",
    "minorlocator_kw",
)


def axis_format_requires_layout(keys):
    """
    Return whether explicit Cartesian formatting keys can affect layout.

    Unknown keys are treated as layout-affecting so new formatting options
    remain correct until they are deliberately classified.
    """
    keys = set(keys)
    keys.difference_update(
        {
            "_explicit_format_keys",
            "rc_kw",
            "rc_mode",
            "skip_axes",
            "skip_figure",
        }
    )
    return bool(keys - PAINT_ONLY_AXIS_FORMAT_KEYS)


def get_axis_style_fields(axis):
    """
    Return the parameter names used to store explicit style overrides.
    """
    return {
        field: tuple(name.format(axis=axis) for name in names)
        for field, names in _AXIS_STYLE_FIELD_TEMPLATES.items()
    }


def _signature_param_names(*funcs):
    names = []
    for func in funcs:
        if isinstance(func, inspect.Signature):
            sig = func
        elif callable(func):
            sig = inspect.signature(func)
        elif func is None:
            continue
        else:
            raise RuntimeError(f"Internal error. Invalid function {func!r}.")
        names.extend(sig.parameters)
    return set(names)


def pop_axis_format_kwargs(kwargs, *funcs):
    """
    Pop axis-format kwargs so they survive rc parsing.

    Returns
    -------
    tuple(dict, dict)
        The signature-defined keyword arguments and the generic alias keyword
        arguments that are not represented in the stored signatures.
    """
    signature_keys = _signature_param_names(*funcs)
    signature_kwargs = {}
    generic_kwargs = {}
    for key in tuple(kwargs):
        if key in GENERIC_AXIS_FORMAT_KEYS:
            generic_kwargs[key] = kwargs.pop(key)
        elif key in signature_keys:
            signature_kwargs[key] = kwargs.pop(key)
    return signature_kwargs, generic_kwargs
