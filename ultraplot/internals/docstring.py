#!/usr/bin/env python3
"""
Utilities for modifying ultraplot docstrings.
"""

# WARNING: To check every docstring in the package for
# unfilled snippets simply use the following code:
# >>> import ultraplot as uplt
# ... seen = set()
# ... def _iter_doc(objs):
# ...     if objs in seen:
# ...         return
# ...     seen.add(objs)
# ...     for attr in dir(objs):
# ...         obj = getattr(objs, attr, None)
# ...         if callable(obj) and hasattr(obj, '__doc__'):
# ...             if obj in seen:
# ...                 continue
# ...             seen.add(obj)
# ...             if obj.__doc__ and '%(' in obj.__doc__:
# ...                 yield obj.__name__
# ...             yield from _iter_doc(obj)
# ... print(*_iter_doc(uplt))
import inspect
import re

from . import ic  # noqa: F401


def _obfuscate_kwargs(func):
    """
    Obfuscate keyword args.
    """
    return _obfuscate_signature(func, lambda **kwargs: None)


def _obfuscate_params(func):
    """
    Obfuscate all parameters.
    """
    return _obfuscate_signature(func, lambda *args, **kwargs: None)


def _obfuscate_signature(func, dummy):
    """
    Obfuscate a misleading or incomplete call signature.
    Instead users should inspect the parameter table.
    """
    # Obfuscate signature by converting to *args **kwargs. Note this does
    # not change behavior of function! Copy parameters from a dummy function
    # because I'm too lazy to figure out inspect.Parameters API
    # See: https://stackoverflow.com/a/33112180/4970632
    sig = inspect.signature(func)
    sig_repl = inspect.signature(dummy)
    func.__signature__ = sig.replace(parameters=tuple(sig_repl.parameters.values()))
    return func


def _concatenate_inherited(func, prepend_summary=False):
    """
    Concatenate docstrings from a matplotlib axes method with a ultraplot
    axes method and obfuscate the call signature.
    """
    import matplotlib.axes as maxes
    import matplotlib.figure as mfigure
    from matplotlib import rcParams as rc_matplotlib

    # Get matplotlib axes func
    # NOTE: Do not bother inheriting from cartopy GeoAxes. Cartopy completely
    # truncates the matplotlib docstrings (which is kind of not great).
    qual = func.__qualname__
    if "Axes" in qual:
        cls = maxes.Axes
    elif "Figure" in qual:
        cls = mfigure.Figure
    else:
        raise ValueError(f"Unexpected method {qual!r}. Must be Axes or Figure method.")
    doc = inspect.getdoc(func) or ""  # also dedents
    func_orig = getattr(cls, func.__name__, None)
    doc_orig = inspect.getdoc(func_orig)
    if not doc_orig:  # should never happen
        return func

    # Optionally prepend the function summary
    # Concatenate docstrings only if this is not generated for website
    regex = re.search(r"\.( | *\n|\Z)", doc_orig)
    if regex and prepend_summary:
        doc = doc_orig[: regex.start() + 1] + "\n\n" + doc
    if not rc_matplotlib["docstring.hardcopy"]:
        doc = f"""
=====================
ultraplot documentation
=====================

{doc}

========================
Matplotlib documentation
========================

{doc_orig}
"""

    # Return docstring
    # NOTE: Also obfuscate parameters to avoid partial coverage of call signatures
    func.__doc__ = inspect.cleandoc(doc)
    func = _obfuscate_params(func)
    return func


class _SnippetManager(dict):
    """
    A simple database for handling documentation snippets.
    """

    _lazy_modules = {
        "axes": "ultraplot.axes.base",
        "cartesian": "ultraplot.axes.cartesian",
        "polar": "ultraplot.axes.polar",
        "geo": "ultraplot.axes.geo",
        "plot": "ultraplot.axes.plot",
        "figure": "ultraplot.figure",
        "gridspec": "ultraplot.gridspec",
        "ticker": "ultraplot.ticker",
        "proj": "ultraplot.proj",
        "colors": "ultraplot.colors",
        "utils": "ultraplot.utils",
        "config": "ultraplot.config",
        "demos": "ultraplot.demos",
        "rc": "ultraplot.axes.base",
    }

    def __missing__(self, key):
        """
        Attempt to import modules that populate missing snippet keys.
        """
        prefix = key.split(".", 1)[0]
        module_name = self._lazy_modules.get(prefix)
        if module_name:
            __import__(module_name)
        if key in self:
            return dict.__getitem__(self, key)
        raise KeyError(key)

    def __call__(self, obj):
        """
        Add snippets to the string or object using ``%(name)s`` substitution. Here
        ``%(name)s`` is used rather than ``.format`` to support invalid identifiers.
        """
        if isinstance(obj, str):
            obj %= self  # add snippets to a string
        else:
            obj.__doc__ = inspect.getdoc(obj)  # also dedents the docstring
            if obj.__doc__:
                obj.__doc__ %= self  # insert snippets after dedent
        return obj

    def __setitem__(self, key, value):
        """
        Populate input strings with other snippets and strip newlines. Developers
        should take care to import modules in the correct order.
        """
        value = self(value)
        value = value.strip("\n")
        super().__setitem__(key, value)


# Initiate snippets database
_snippet_manager = _SnippetManager()

# Unit docstrings
# NOTE: Try to fit this into a single line. Cannot break up with newline as that will
# mess up docstring indentation since this is placed in indented param lines.
_units_docstring = (
    "If float, units are {units}. If string, interpreted by `~ultraplot.utils.units`."
)
_snippet_manager["units.pt"] = _units_docstring.format(units="points")
_snippet_manager["units.in"] = _units_docstring.format(units="inches")
_snippet_manager["units.em"] = _units_docstring.format(units="em-widths")

# Style docstrings
# NOTE: These are needed in a few different places
_line_docstring = """
lw, linewidth, linewidths : unit-spec, default: :rc:`lines.linewidth`
    The width of the line(s).
    %(units.pt)s
ls, linestyle, linestyles : str, default: :rc:`lines.linestyle`
    The style of the line(s).
c, color, colors : color-spec, optional
    The color of the line(s). The property `cycle` is used by default.
a, alpha, alphas : float, optional
    The opacity of the line(s). Inferred from `color` by default.
"""
_patch_docstring = """
lw, linewidth, linewidths : unit-spec, default: :rc:`patch.linewidth`
    The edge width of the patch(es).
    %(units.pt)s
ls, linestyle, linestyles : str, default: '-'
    The edge style of the patch(es).
ec, edgecolor, edgecolors : color-spec, default: '{edgecolor}'
    The edge color of the patch(es).
fc, facecolor, facecolors, fillcolor, fillcolors : color-spec, optional
    The face color of the patch(es). The property `cycle` is used by default.
a, alpha, alphas : float, optional
    The opacity of the patch(es). Inferred from `facecolor` and `edgecolor` by default.
"""
_pcolor_collection_docstring = """
lw, linewidth, linewidths : unit-spec, default: 0.3
    The width of lines between grid boxes.
    %(units.pt)s
ls, linestyle, linestyles : str, default: '-'
    The style of lines between grid boxes.
ec, edgecolor, edgecolors : color-spec, default: 'k'
    The color of lines between grid boxes.
a, alpha, alphas : float, optional
    The opacity of the grid boxes. Inferred from `cmap` by default.
"""
_contour_collection_docstring = """
lw, linewidth, linewidths : unit-spec, default: 0.3 or :rc:`lines.linewidth`
    The width of the line contours. Default is ``0.3`` when adding to filled contours
    or :rc:`lines.linewidth` otherwise. %(units.pt)s
ls, linestyle, linestyles : str, default: '-' or :rc:`contour.negative_linestyle`
    The style of the line contours. Default is ``'-'`` for positive contours and
    :rcraw:`contour.negative_linestyle` for negative contours.
ec, edgecolor, edgecolors : color-spec, default: 'k' or inferred
    The color of the line contours. Default is ``'k'`` when adding to filled contours
    or inferred from `color` or `cmap` otherwise.
a, alpha, alpha : float, optional
    The opacity of the contours. Inferred from `edgecolor` by default.
"""
_text_docstring = """
name, fontname, family, fontfamily : str, optional
    The font typeface name (e.g., ``'Fira Math'``) or font family name (e.g.,
    ``'serif'``). Matplotlib falls back to the system default if not found.
size, fontsize : unit-spec or str, optional
    The font size. %(units.pt)s
    This can also be a string indicating some scaling relative to
    :rcraw:`font.size`. The sizes and scalings are shown below. The
    scalings ``'med'``, ``'med-small'``, and ``'med-large'`` are
    added by ultraplot while the rest are native matplotlib sizes.

    .. _font_table:

    ==========================  =====
    Size                        Scale
    ==========================  =====
    ``'xx-small'``              0.579
    ``'x-small'``               0.694
    ``'small'``, ``'smaller'``  0.833
    ``'med-small'``             0.9
    ``'med'``, ``'medium'``     1.0
    ``'med-large'``             1.1
    ``'large'``, ``'larger'``   1.2
    ``'x-large'``               1.440
    ``'xx-large'``              1.728
    ``'larger'``                1.2
    ==========================  =====

"""
_snippet_manager["artist.line"] = _line_docstring
_snippet_manager["artist.text"] = _text_docstring
_snippet_manager["artist.patch"] = _patch_docstring.format(edgecolor="none")
_snippet_manager["artist.patch_black"] = _patch_docstring.format(edgecolor="black")
_snippet_manager["artist.collection_pcolor"] = _pcolor_collection_docstring
_snippet_manager["artist.collection_contour"] = _contour_collection_docstring
