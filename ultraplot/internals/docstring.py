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
from typing import Any, Callable, TypeVar, cast, overload

from . import ic  # noqa: F401

_F = TypeVar("_F", bound=Callable[..., Any])
_T = TypeVar("_T")


def _obfuscate_kwargs(func: _F) -> _F:
    """
    Mark keyword arguments as compact in generated API documentation.
    """
    return _obfuscate_signature(func, lambda **kwargs: None)


def _obfuscate_params(func: _F) -> _F:
    """
    Mark all parameters as compact in generated API documentation.
    """
    return _obfuscate_signature(func, lambda *args, **kwargs: None)


def _obfuscate_signature(func: _F, dummy: Callable[..., Any]) -> _F:
    """
    Mark a misleading or incomplete signature as compact in generated docs.

    The callable's actual signature remains available to Python and language
    servers; Sphinx reads the marker below when rendering API headings.
    """
    # Keep the compact signature available to documentation tooling without
    # changing the callable's runtime signature. Sphinx uses this marker to
    # avoid filling API headings with inherited or dynamically routed options.
    setattr(func, "__ultraplot_doc_signature__", str(inspect.signature(dummy)))
    return func


def _concatenate_inherited(
    func: _F, prepend_summary: bool = False
) -> _F:
    """
    Concatenate docstrings from a matplotlib axes method with a ultraplot
    axes method and mark its generated-documentation signature as compact.
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
    # Keep generated API headings compact to avoid showing partial call signatures.
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
        "legend": "ultraplot.legend",
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

    @overload
    def __call__(self, obj: str) -> str: ...

    @overload
    def __call__(self, obj: _T) -> _T: ...

    def __call__(self, obj: _T | str) -> _T | str:
        """
        Add snippets to the string or object using ``%(name)s`` substitution. Here
        ``%(name)s`` is used rather than ``.format`` to support invalid identifiers.
        """
        if isinstance(obj, str):
            obj %= self  # add snippets to a string
        else:
            documented = cast(Any, obj)
            documented.__doc__ = inspect.getdoc(documented)  # also dedents the docstring
            if documented.__doc__:
                documented.__doc__ %= self  # insert snippets after dedent
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
def _aliases_note(*names):
    """
    Render a compact ``Aliases: ...`` note for a style parameter. The canonical
    name leads the numpydoc field; the common documented synonyms go here so the
    parameter reads cleanly instead of opening with a pile of alias names.
    """
    return "Aliases: " + ", ".join(f"``{name}``" for name in names) + "."


_line_docstring = f"""
linewidth : unit-spec, default: :rc:`lines.linewidth`
    The width of the line(s). {_aliases_note("lw", "linewidths")}
    %(units.pt)s
linestyle : str, default: :rc:`lines.linestyle`
    The style of the line(s). {_aliases_note("ls", "linestyles")}
color : color-spec, optional
    The color of the line(s). The property `cycle` is used by default. {_aliases_note("c", "colors")}
alpha : float, optional
    The opacity of the line(s). Inferred from `color` by default. {_aliases_note("a", "alphas")}
"""
_patch_docstring = f"""
linewidth : unit-spec, default: :rc:`patch.linewidth`
    The edge width of the patch(es). {_aliases_note("lw", "linewidths")}
    %(units.pt)s
linestyle : str, default: '-'
    The edge style of the patch(es). {_aliases_note("ls", "linestyles")}
edgecolor : color-spec, default: '{{edgecolor}}'
    The edge color of the patch(es). {_aliases_note("ec", "edgecolors")}
facecolor : color-spec, optional
    The face color of the patch(es). The property `cycle` is used by default. {_aliases_note("fc", "facecolors", "fillcolor", "fillcolors")}
alpha : float, optional
    The opacity of the patch(es). Inferred from `facecolor` and `edgecolor` by default. {_aliases_note("a", "alphas")}
"""
_pcolor_collection_docstring = f"""
linewidths : unit-spec, default: 0.3
    The width of lines between grid boxes. {_aliases_note("lw", "linewidth")}
    %(units.pt)s
linestyles : str, default: '-'
    The style of lines between grid boxes. {_aliases_note("ls", "linestyle")}
edgecolors : color-spec, default: 'k'
    The color of lines between grid boxes. {_aliases_note("ec", "edgecolor")}
alpha : float, optional
    The opacity of the grid boxes. Inferred from `cmap` by default. {_aliases_note("a", "alphas")}
"""
_contour_collection_docstring = f"""
linewidths : unit-spec, default: 0.3 or :rc:`lines.linewidth`
    The width of the line contours. Default is ``0.3`` when adding to filled contours
    or :rc:`lines.linewidth` otherwise. {_aliases_note("lw", "linewidth")} %(units.pt)s
linestyles : str, default: '-' or :rc:`contour.negative_linestyle`
    The style of the line contours. Default is ``'-'`` for positive contours and
    :rcraw:`contour.negative_linestyle` for negative contours. {_aliases_note("ls", "linestyle")}
edgecolors : color-spec, default: 'k' or inferred
    The color of the line contours. Default is ``'k'`` when adding to filled contours
    or inferred from `color` or `cmap` otherwise. {_aliases_note("ec", "edgecolor")}
alpha : float, optional
    The opacity of the contours. Inferred from `edgecolors` by default. {_aliases_note("a", "alphas")}
"""
_text_docstring = f"""
fontfamily : str, optional
    The font typeface name (e.g., ``'Fira Math'``) or font family name (e.g.,
    ``'serif'``). Matplotlib falls back to the system default if not found. {_aliases_note("family", "name", "fontname")}
fontsize : unit-spec or str, optional
    The font size. {_aliases_note("size")} %(units.pt)s
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
