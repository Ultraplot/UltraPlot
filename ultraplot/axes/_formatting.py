#!/usr/bin/env python3
"""
Shared metadata for axis formatting keyword routing and persistence.
"""

import inspect

_AXIS_STYLE_FIELD_TEMPLATES = {
    "color": ("{axis}color", "color"),
    "linewidth": ("{axis}linewidth", "linewidth"),
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


def _dedupe(items):
    return tuple(dict.fromkeys(items))


GENERIC_AXIS_FORMAT_KEYS = _dedupe(
    name
    for names in _AXIS_STYLE_FIELD_TEMPLATES.values()
    for name in names
    if "{axis}" not in name
)


CARTESIAN_PARENT_FILTER_KEYS = GENERIC_AXIS_FORMAT_KEYS + (
    "label_kw",
    "scale_kw",
    "locator_kw",
    "formatter_kw",
    "minorlocator_kw",
)


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
