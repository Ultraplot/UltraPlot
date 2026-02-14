#!/usr/bin/env python3
"""
Utilities for global configuration.
"""

import functools
import re
from collections.abc import MutableMapping
from numbers import Integral, Real

import matplotlib as mpl
import matplotlib.rcsetup as msetup
import numpy as np
from cycler import Cycler
from matplotlib import RcParams
from matplotlib import rcParamsDefault as _rc_matplotlib_native
from matplotlib.colors import Colormap
from matplotlib.font_manager import font_scalings

if hasattr(mpl, "_fontconfig_pattern"):
    from matplotlib._fontconfig_pattern import parse_fontconfig_pattern
else:
    from matplotlib.fontconfig_pattern import parse_fontconfig_pattern

from . import (
    ic,  # noqa: F401
    warnings,
)
from .rc import (
    build_settings_rc_table,
    get_rc_removed,
    get_rc_renamed,
)
from .versions import _version_mpl

# Regex for "probable" unregistered named colors. Try to retain warning message for
# colors that were most likely a failed literal string evaluation during startup.
REGEX_NAMED_COLOR = re.compile(r"\A[a-zA-Z0-9:_ -]*\Z")

# Configurable validation settings
# NOTE: These are set to True inside __init__.py
# NOTE: We really cannot delay creation of 'rc' until after registration because
# colormap creation depends on rc['cmap.lut'] and rc['cmap.listedthresh'].
# And anyway to revoke that dependence would require other uglier kludges.
VALIDATE_REGISTERED_CMAPS = False
VALIDATE_REGISTERED_COLORS = False

# Initial synced properties
# NOTE: Important that LINEWIDTH is less than matplotlib default of 0.8.
# In general want axes lines to look about as thick as text.
# NOTE: Important that default values are equivalent to the *validated* values
# used in the RcParams dictionaries. Otherwise _user_settings() detects changes.
# NOTE: We *could* just leave some settings empty and leave it up to Configurator
# to sync them when ultraplot is imported... but also sync them here so that we can
# simply compare any Configurator state to these dictionaries and use save() to
# save only the settings changed by the user.
BLACK = "black"
CYCLE = "colorblind"
CMAPCYC = "twilight"
CMAPDIV = "BuRd"
CMAPSEQ = "Fire"
CMAPCAT = "colorblind10"
DIVERGING = "div"
FRAMEALPHA = 0.8  # legend and colorbar
FONTNAME = "sans-serif"
FONTSIZE = 9.0
GRIDALPHA = 0.1
GRIDBELOW = "line"
GRIDPAD = 3.0
GRIDRATIO = 0.5  # differentiated from major by half size reduction
GRIDSTYLE = "-"
LABELPAD = 4.0  # default is 4.0, previously was 3.0
LARGESIZE = "med-large"
LINEWIDTH = 0.6
MARGIN = 0.05
MATHTEXT = False
SMALLSIZE = "medium"
TICKDIR = "out"
TICKLEN = 4.0
TICKLENRATIO = 0.5  # very noticeable length reduction
TICKMINOR = True
TICKPAD = 2.0
TICKWIDTHRATIO = 0.8  # very slight width reduction
TITLEPAD = 5.0  # default is 6.0, previously was 3.0
WHITE = "white"
ZLINES = 2  # default zorder for lines
ZPATCHES = 1

# Preset legend locations and aliases
LEGEND_LOCS = {
    "fill": "fill",
    "inset": "best",
    "i": "best",
    0: "best",
    1: "upper right",
    2: "upper left",
    3: "lower left",
    4: "lower right",
    5: "center left",
    6: "center right",
    7: "lower center",
    8: "upper center",
    9: "center",
    "l": "left",
    "r": "right",
    "b": "bottom",
    "t": "top",
    "c": "center",
    "ur": "upper right",
    "ul": "upper left",
    "ll": "lower left",
    "lr": "lower right",
    "cr": "center right",
    "cl": "center left",
    "uc": "upper center",
    "lc": "lower center",
    "ol": "outer left",
    "or": "outer right",
}
for _loc in tuple(LEGEND_LOCS.values()):
    if _loc not in LEGEND_LOCS:
        LEGEND_LOCS[_loc] = _loc  # identity assignments
TEXT_LOCS = {
    key: val
    for key, val in LEGEND_LOCS.items()
    if val
    in (
        "left",
        "center",
        "right",
        "upper left",
        "upper center",
        "upper right",
        "lower left",
        "lower center",
        "lower right",
        "outer left",
        "outer right",
    )
}
COLORBAR_LOCS = {
    key: val
    for key, val in LEGEND_LOCS.items()
    if val
    in (
        "fill",
        "best",
        "left",
        "right",
        "top",
        "bottom",
        "upper left",
        "upper right",
        "lower left",
        "lower right",
    )
}
PANEL_LOCS = {
    key: val
    for key, val in LEGEND_LOCS.items()
    if val in ("left", "right", "top", "bottom")
}
ALIGN_LOCS = {
    key: val
    for key, val in LEGEND_LOCS.items()
    if isinstance(key, str)
    and val
    in (
        "left",
        "right",
        "top",
        "bottom",
        "center",
    )
}

# Matplotlib setting categories
EM_KEYS = (  # em-width units
    "legend.borderpad",
    "legend.labelspacing",
    "legend.handlelength",
    "legend.handleheight",
    "legend.handletextpad",
    "legend.borderaxespad",
    "legend.columnspacing",
)
PT_KEYS = (
    "font.size",  # special case
    "xtick.major.size",
    "xtick.minor.size",
    "ytick.major.size",
    "ytick.minor.size",
    "xtick.major.pad",
    "xtick.minor.pad",
    "ytick.major.pad",
    "ytick.minor.pad",
    "xtick.major.width",
    "xtick.minor.width",
    "ytick.major.width",
    "ytick.minor.width",
    "axes.labelpad",
    "axes.titlepad",
    "axes.linewidth",
    "grid.linewidth",
    "patch.linewidth",
    "hatch.linewidth",
    "lines.linewidth",
    "contour.linewidth",
)
FONT_KEYS = set()  # dynamically add to this below


def _get_default_param(key):
    """
    Get the default parameter from one of three places. This is used for
    the :rc: role when compiling docs and when saving ultraplotrc files.
    """
    sentinel = object()
    for dict_ in (
        _rc_ultraplot_default,
        _rc_matplotlib_default,  # imposed defaults
        _rc_matplotlib_native,  # native defaults
    ):
        value = dict_.get(key, sentinel)
        if value is not sentinel:
            return value
    raise KeyError(f"Invalid key {key!r}.")


def _validate_abc(value):
    """
    Validate a-b-c setting.
    """
    try:
        if np.iterable(value):
            return all(map(_validate_bool, value))
        else:
            return _validate_bool(value)
    except ValueError:
        pass
    if isinstance(value, str):
        if "a" in value.lower():
            return value
    else:
        if all(isinstance(_, str) for _ in value):
            return tuple(value)
    raise ValueError(
        "A-b-c setting must be string containing 'a' or 'A' or sequence of strings."
    )


def _validate_belongs(*options):
    """
    Return a validator ensuring the item belongs in the list.
    """

    def _validate_belongs(value):  # noqa: E306
        for opt in options:
            if isinstance(value, str) and isinstance(opt, str):
                if value.lower() == opt.lower():  # noqa: E501
                    return opt
            elif value is True or value is False or value is None:
                if value is opt:
                    return opt
            elif value == opt:
                return opt
        raise ValueError(
            f"Invalid value {value!r}. Options are: "
            + ", ".join(map(repr, options))
            + "."
        )

    return _validate_belongs


_CFTIME_RESOLUTIONS = (
    "SECONDLY",
    "MINUTELY",
    "HOURLY",
    "DAILY",
    "MONTHLY",
    "YEARLY",
)


def _validate_cftime_resolution_format(units: dict) -> dict:
    if not isinstance(units, dict):
        raise ValueError("Cftime units expects a dict")

    for resolution, format_ in units.items():
        unit = _validate_cftime_resolution(resolution)

    # Delegate format parsing to cftime
    _rc_ultraplot_default["cftime.time_resolution_format"].update(units)
    return _rc_ultraplot_default["cftime.time_resolution_format"]


def _validate_cftime_resolution(unit: str) -> str:
    if not isinstance(unit, str):
        raise TypeError("Time unit cftime is expecting str")
    if unit in _CFTIME_RESOLUTIONS:
        return unit
    msg = f"Unit not understood. Got {unit} expected one of: {_CFTIME_RESOLUTIONS}"
    raise ValueError(msg)


def _validate_cmap(subtype, cycle=False):
    """
    Validate the colormap or cycle. Possibly skip name registration check
    and assign the colormap name rather than a colormap instance.
    """

    def _validate_cmap(value):

        name = value
        if isinstance(value, str):
            if VALIDATE_REGISTERED_CMAPS:
                from ..colors import _get_cmap_subtype

                _get_cmap_subtype(name, subtype)  # may trigger useful error message
            return name
        elif isinstance(value, Colormap):
            name = getattr(value, "name", None)
            if isinstance(name, str):
                from ..colors import _cmap_database  # avoid circular imports

                _cmap_database.register(value, name=name)
                return name
        elif cycle:
            from ..constructor import Cycle

            if isinstance(value, Cycler):
                return Cycle(value)
            elif np.iterable(value):
                return Cycle(value)
        raise ValueError(f"Invalid colormap or color cycle name {name!r}.")

    return _validate_cmap


def _validate_color(value, alternative=None):
    """
    Validate the color. Possibly skip name registration check.
    """
    if alternative and isinstance(value, str) and value.lower() == alternative:
        return value
    try:
        return msetup.validate_color(value)
    except ValueError:
        if (
            VALIDATE_REGISTERED_COLORS
            or not isinstance(value, str)
            or not REGEX_NAMED_COLOR.match(value)
        ):
            raise ValueError(f"{value!r} is not a valid color arg.") from None
        return value
    except Exception as error:
        raise error


def _validate_bool_or_iterable(value):
    if isinstance(value, bool):
        return _validate_bool(value)
    elif np.isiterable(value):
        return value
    raise ValueError(f"{value!r} is not a valid bool or iterable of node labels.")


def _validate_bool_or_string(value):
    if isinstance(value, bool):
        return _validate_bool(value)
    if isinstance(value, str):
        return _validate_string(value)
    raise ValueError(f"{value!r} is not a valid bool or string.")


def _validate_fontprops(s):
    """
    Parse font property with support for ``'regular'`` placeholder.
    """
    b = s.startswith("regular")
    if b:
        s = s.replace("regular", "sans", 1)
    parse_fontconfig_pattern(s)
    if b:
        s = s.replace("sans", "regular", 1)
    return s


def _validate_fontsize(value):
    """
    Validate font size with new scalings and permitting other units.
    """
    if value is None and None in font_scalings:  # has it always been this way?
        return
    if isinstance(value, str):
        value = value.lower()
        if value in font_scalings:
            return value
    try:
        return _validate_pt(value)  # note None is also a valid font size!
    except ValueError:
        pass
    raise ValueError(
        f"Invalid font size {value!r}. Can be points or one of the "
        "preset scalings: " + ", ".join(map(repr, font_scalings)) + "."
    )


def _validate_labels(labels, lon=True):
    """
    Convert labels argument to length-4 boolean array.
    """
    if labels is None:
        return [None] * 4
    which = "lon" if lon else "lat"
    if isinstance(labels, str):
        labels = (labels,)
    array = np.atleast_1d(labels).tolist()
    if all(isinstance(_, str) for _ in array):
        bool_ = [False] * 4
        opts = ("left", "right", "bottom", "top")
        for string in array:
            if string in opts:
                string = string[0]
            elif set(string) - set("lrbt"):
                raise ValueError(
                    f"Invalid {which}label string {string!r}. Must be one of "
                    + ", ".join(map(repr, opts))
                    + " or a string of single-letter characters like 'lr'."
                )
            for char in string:
                bool_["lrbt".index(char)] = True
        array = bool_
    if len(array) == 1:
        array.append(False)  # default is to label bottom or left
    if len(array) == 2:
        if lon:
            array = [False, False, *array]
        else:
            array = [*array, False, False]
    if len(array) != 4 or any(isinstance(_, str) for _ in array):
        raise ValueError(f"Invalid {which}label spec: {labels}.")
    return array


def _validate_or_none(validator):
    """
    Allow none otherwise pass to the input validator.
    """

    @functools.wraps(validator)
    def _validate_or_none(value):
        if value is None:
            return
        if isinstance(value, str) and value.lower() == "none":
            return
        return validator(value)

    _validate_or_none.__name__ = validator.__name__ + "_or_none"
    return _validate_or_none


def _validate_float_or_iterable(value):
    try:
        return _validate_float(value)
    except Exception:
        if np.isiterable(value) and not isinstance(value, (str, bytes)):
            return tuple(_validate_float(item) for item in value)
    raise ValueError(f"{value!r} is not a valid float or iterable of floats.")


def _validate_string_or_iterable(value):
    if isinstance(value, str):
        return _validate_string(value)
    if np.isiterable(value) and not isinstance(value, (str, bytes)):
        values = tuple(value)
        if all(isinstance(item, str) for item in values):
            return values
    raise ValueError(f"{value!r} is not a valid string or iterable of strings.")


def _validate_rotation(value):
    """
    Valid rotation arguments.
    """
    if isinstance(value, str) and value.lower() in ("horizontal", "vertical"):
        return value
    return _validate_float(value)


def _validate_units(dest):
    """
    Validate the input using the units function.
    """

    def _validate_units(value):
        if isinstance(value, str):
            from ..utils import units  # avoid circular imports

            value = units(value, dest)  # validation happens here
        return _validate_float(value)

    return _validate_units


def _validate_float_or_auto(value):
    if value == "auto":
        return value
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Value must be a float or 'auto', got {value!r}")


def _validate_tuple_int_2(value):
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return tuple(_validate_int(item) for item in value)
    raise ValueError(f"Value must be a tuple/list of 2 ints, got {value!r}")


def _validate_tuple_float_2(value):
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return tuple(_validate_float(item) for item in value)
    raise ValueError(f"Value must be a tuple/list of 2 floats, got {value!r}")


def _rst_table():
    """
    Return the setting names and descriptions in an RST-style table.
    """
    # Initial stuff
    colspace = 2  # spaces between each column
    descrips = tuple(descrip for (_, _, descrip) in _rc_ultraplot_table.values())
    keylen = len(max((*_rc_ultraplot_table, "Key"), key=len)) + 4  # literal backticks
    vallen = len(max((*descrips, "Description"), key=len))
    divider = "=" * keylen + " " * colspace + "=" * vallen + "\n"
    header = "Key" + " " * (keylen - 3 + colspace) + "Description\n"

    # Build table
    string = divider + header + divider
    for key, (_, _, descrip) in _rc_ultraplot_table.items():
        spaces = " " * (keylen - (len(key) + 4) + colspace)
        string += f"``{key}``{spaces}{descrip}\n"

    string = string + divider
    return ".. rst-class:: ultraplot-rctable\n\n" + string.strip()


def _to_string(value):
    """
    Translate setting to a string suitable for saving.
    """
    # NOTE: Never safe hex strings with leading '#'. In both matplotlibrc
    # and ultraplotrc this will be read as comment character.
    if value is None or isinstance(value, (str, bool, Integral)):
        value = str(value)
        if value[:1] == "#":  # i.e. a HEX string
            value = value[1:]
    elif isinstance(value, Real):
        value = str(round(value, 6))  # truncate decimals
    elif isinstance(value, Cycler):
        value = repr(value)  # special case!
    elif isinstance(value, (list, tuple, np.ndarray)):
        value = ", ".join(map(_to_string, value))  # sexy recursion
    elif isinstance(value, dict):
        # Convert dict to YAML-style inline format: {key1: val1, key2: val2}
        items = ", ".join(f"{k}: {_to_string(v)}" for k, v in value.items())
        value = "{" + items + "}"
    else:
        value = None
    return value


def _yaml_table(rcdict, comment=True, description=False):
    """
    Return the settings as a nicely tabulated YAML-style table.
    """
    prefix = "# " if comment else ""
    data = []
    for key, args in rcdict.items():
        # Optionally append description
        includes_descrip = isinstance(args, tuple) and len(args) == 3
        if not description:
            descrip = ""
            value = args[0] if includes_descrip else args
        elif includes_descrip:
            value, validator, descrip = args
            descrip = "# " + descrip  # skip the validator
        else:
            raise ValueError(f"Unexpected input {key}={args!r}.")

        # Translate object to string
        value = _to_string(value)
        if value is not None:
            data.append((key, value, descrip))
        else:
            warnings._warn_ultraplot(
                f"Failed to write rc setting {key} = {value!r}. Must be None, bool, "
                "string, int, float, a list or tuple thereof, or a property cycler."
            )

    # Generate string
    string = ""
    keylen = len(max(rcdict, key=len))
    vallen = len(max((tup[1] for tup in data), key=len))
    for key, value, descrip in data:
        space1 = " " * (keylen - len(key) + 1)
        space2 = " " * (vallen - len(value) + 2) if descrip else ""
        string += f"{prefix}{key}:{space1}{value}{space2}{descrip}\n"

    return string.strip()


class _RcParams(MutableMapping, dict):
    """
    A simple dictionary with locked inputs and validated assignments.
    """

    # NOTE: By omitting __delitem__ in MutableMapping we effectively
    # disable mutability. Also disables deleting items with pop().
    def __init__(self, source, validate):
        self._validate = validate
        for key, value in source.items():
            self.__setitem__(key, value)  # trigger validation

    def __repr__(self):
        return RcParams.__repr__(self)

    def __str__(self):
        return RcParams.__repr__(self)

    def __len__(self):
        return dict.__len__(self)

    def __iter__(self):
        # NOTE: ultraplot doesn't add deprecated args to dictionary so
        # we don't have to suppress warning messages here.
        yield from sorted(dict.__iter__(self))

    def __getitem__(self, key):
        key, _ = self._check_key(key)
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        key, value = self._check_key(key, value)
        if key not in self._validate:
            raise KeyError(f"Invalid rc key {key!r}.")
        try:
            value = self._validate[key](value)
        except (ValueError, TypeError) as error:
            raise ValueError(f"Key {key}: {error}") from None
        if key is not None:
            dict.__setitem__(self, key, value)

    @staticmethod
    def _check_key(key, value=None):
        # NOTE: If we assigned from the Configurator then the deprecated key will
        # still propagate to the same 'children' as the new key.
        # NOTE: This also translates values for special cases of renamed keys.
        # Currently the special cases are 'basemap' and 'cartopy.autoextent'.
        if key in _rc_renamed:
            key_new, version = _rc_renamed[key]
            warnings._warn_ultraplot(
                f"The rc setting {key!r} was deprecated in version {version} and may be "  # noqa: E501
                f"removed in {warnings.next_release()}. Please use {key_new!r} instead."  # noqa: E501
            )
            if key == "basemap":  # special case
                value = ("cartopy", "basemap")[int(bool(value))]
            if key == "cartopy.autoextent":
                value = ("globe", "auto")[int(bool(value))]
            key = key_new
        if key in _rc_removed:
            info, version = _rc_removed[key]
            raise KeyError(
                f"The rc setting {key!r} was removed in version {version}."
                + (info and " " + info)
            )
        return key, value

    def copy(self):
        source = {key: dict.__getitem__(self, key) for key in self}
        return _RcParams(source, self._validate)


# Borrow validators from matplotlib and construct some new ones
# WARNING: Instead of validate_fontweight matplotlib used validate_string
# until version 3.1.2. So use that as backup here.
# WARNING: We create custom 'or none' validators since their
# availability seems less consistent across matplotlib versions.
_validate_pt = _validate_units("pt")
_validate_em = _validate_units("em")
_validate_in = _validate_units("in")
_validate_bool = msetup.validate_bool
_validate_int = msetup.validate_int
_validate_float = msetup.validate_float
_validate_string = msetup.validate_string
_validate_fontname = msetup.validate_stringlist  # same as 'font.family'
_validate_fontweight = getattr(msetup, "validate_fontweight", _validate_string)

# Special style validators
# See: https://matplotlib.org/stable/api/_as_gen/matplotlib.patches.FancyBboxPatch.html
_validate_boxstyle = _validate_belongs(
    "square",
    "circle",
    "round",
    "round4",
    "sawtooth",
    "roundtooth",
)
_validate_joinstyle = _validate_belongs("miter", "round", "bevel")
if hasattr(msetup, "_validate_linestyle"):  # fancy validation including dashes
    _validate_linestyle = msetup._validate_linestyle
else:  # no dashes allowed then but no big deal
    _validate_linestyle = _validate_belongs(
        "-",
        ":",
        "--",
        "-.",
        "solid",
        "dashed",
        "dashdot",
        "dotted",
        "none",
        " ",
        "",
    )

# Patch existing matplotlib validators.
# NOTE: validate_fontsizelist is unused in recent matplotlib versions and
# validate_colorlist is only used with prop cycle eval (which we don't care about)
font_scalings["med"] = 1.0  # consistent shorthand
font_scalings["med-small"] = 0.9  # add scaling
font_scalings["med-large"] = 1.1  # add scaling
if not hasattr(RcParams, "validate"):  # not mission critical so skip
    warnings._warn_ultraplot("Failed to update matplotlib rcParams validators.")
else:

    def _validator_accepts(validator, value):
        try:
            validator(value)
            return True
        except Exception:
            return False

    _validate = RcParams.validate
    _validate["image.cmap"] = _validate_cmap("continuous")
    _validate["legend.loc"] = _validate_belongs(*LEGEND_LOCS)
    for _key, _validator in _validate.items():
        if _validator is getattr(msetup, "validate_fontsize", None):  # should exist
            FONT_KEYS.add(_key)
            _validate[_key] = _validate_fontsize
        if _validator is getattr(msetup, "validate_fontsize_None", None):
            FONT_KEYS.add(_key)
            _validate[_key] = _validate_or_none(_validate_fontsize)
        if _validator is getattr(msetup, "validate_font_properties", None):
            _validate[_key] = _validate_fontprops
        if _validator is getattr(msetup, "validate_color", None):  # should exist
            _validate[_key] = _validate_color
        if _validator is getattr(msetup, "validate_color_or_auto", None):
            _validate[_key] = functools.partial(_validate_color, alternative="auto")
        if _validator is getattr(msetup, "validate_color_or_inherit", None):
            _validate[_key] = functools.partial(_validate_color, alternative="inherit")
        # Matplotlib may wrap fontsize validators in callable objects instead of
        # exposing validate_fontsize directly. Detect these by behavior so custom
        # shorthands like "med-large" remain valid regardless of import order.
        if (
            _key.endswith("size")
            and _key not in FONT_KEYS
            and _validator_accepts(_validator, "large")
            and not _validator_accepts(_validator, "med-large")
        ):
            FONT_KEYS.add(_key)
            if _validator_accepts(_validator, None):
                _validate[_key] = _validate_or_none(_validate_fontsize)
            else:
                _validate[_key] = _validate_fontsize
    for _keys, _validator_replace in ((EM_KEYS, _validate_em), (PT_KEYS, _validate_pt)):
        for _key in _keys:
            _validator = _validate.get(_key, None)
            if _validator is None:
                continue
            if _validator is msetup.validate_float:
                _validate[_key] = _validator_replace
            if _validator is getattr(msetup, "validate_float_or_None"):
                _validate[_key] = _validate_or_none(_validator_replace)


# ultraplot overrides of matplotlib default style
# WARNING: Critical to include every parameter here that can be changed by a
# "meta" setting so that _get_default_param returns the value imposed by *ultraplot*
# and so that "changed" settings detected by Configurator.save are correct.
_rc_matplotlib_default = {
    "axes.axisbelow": GRIDBELOW,
    "axes.formatter.use_mathtext": MATHTEXT,
    "axes.grid": True,  # enable lightweight transparent grid by default
    "axes.grid.which": "major",
    "axes.edgecolor": BLACK,
    "axes.labelcolor": BLACK,
    "axes.labelpad": LABELPAD,  # more compact
    "axes.labelsize": SMALLSIZE,
    "axes.labelweight": "normal",
    "axes.linewidth": LINEWIDTH,
    "axes.titlepad": TITLEPAD,  # more compact
    "axes.titlesize": LARGESIZE,
    "axes.titleweight": "normal",
    "axes.xmargin": MARGIN,
    "axes.ymargin": MARGIN,
    "errorbar.capsize": 3.0,
    "figure.autolayout": False,
    "figure.figsize": (4.0, 4.0),  # for interactife backends
    "figure.dpi": 100,
    "figure.facecolor": "#f4f4f4",  # similar to MATLAB interface
    "figure.titlesize": LARGESIZE,
    "figure.titleweight": "bold",  # differentiate from axes titles
    "font.serif": [
        "TeX Gyre Schola",  # Century lookalike
        "TeX Gyre Bonum",  # Bookman lookalike
        "TeX Gyre Termes",  # Times New Roman lookalike
        "TeX Gyre Pagella",  # Palatino lookalike
        "DejaVu Serif",
        "Bitstream Vera Serif",
        "Computer Modern Roman",
        "Bookman",
        "Century Schoolbook L",
        "Charter",
        "ITC Bookman",
        "New Century Schoolbook",
        "Nimbus Roman No9 L",
        "Noto Serif",
        "Palatino",
        "Source Serif Pro",
        "Times New Roman",
        "Times",
        "Utopia",
        "serif",
    ],
    "font.sans-serif": [
        "TeX Gyre Heros",  # Helvetica lookalike
        "DejaVu Sans",
        "Bitstream Vera Sans",
        "Computer Modern Sans Serif",
        "Arial",
        "Avenir",
        "Fira Math",
        "Fira Sans",
        "Frutiger",
        "Geneva",
        "Gill Sans",
        "Helvetica",
        "Lucid",
        "Lucida Grande",
        "Myriad Pro",
        "Noto Sans",
        "Roboto",
        "Source Sans Pro",
        "Tahoma",
        "Trebuchet MS",
        "Ubuntu",
        "Univers",
        "Verdana",
        "sans-serif",
    ],
    "font.cursive": [
        "TeX Gyre Chorus",  # Chancery lookalike
        "Apple Chancery",
        "Felipa",
        "Sand",
        "Script MT",
        "Textile",
        "Zapf Chancery",
        "cursive",
    ],
    "font.fantasy": [
        "TeX Gyre Adventor",  # Avant Garde lookalike
        "Avant Garde",
        "Charcoal",
        "Chicago",
        "Comic Sans MS",
        "Futura",
        "Humor Sans",
        "Impact",
        "Optima",
        "Western",
        "xkcd",
        "fantasy",
    ],
    "font.monospace": [
        "TeX Gyre Cursor",  # Courier lookalike
        "DejaVu Sans Mono",
        "Bitstream Vera Sans Mono",
        "Computer Modern Typewriter",
        "Andale Mono",
        "Courier New",
        "Courier",
        "Fixed",
        "Nimbus Mono L",
        "Terminal",
        "monospace",
    ],
    "font.family": FONTNAME,
    "font.size": FONTSIZE,
    "grid.alpha": GRIDALPHA,  # lightweight unobtrusive gridlines
    "grid.color": BLACK,  # lightweight unobtrusive gridlines
    "grid.linestyle": GRIDSTYLE,
    "grid.linewidth": LINEWIDTH,
    "hatch.color": BLACK,
    "hatch.linewidth": LINEWIDTH,
    "image.cmap": CMAPSEQ,
    "image.interpolation": "none",
    "lines.linestyle": "-",
    "lines.linewidth": 1.5,
    "lines.markersize": 6.0,
    "legend.borderaxespad": 0,  # i.e. flush against edge
    "legend.borderpad": 0.5,  # a bit more roomy
    "legend.columnspacing": 1.5,  # a bit more compact (see handletextpad)
    "legend.edgecolor": BLACK,
    "legend.facecolor": WHITE,
    "legend.fancybox": False,  # i.e. BboxStyle 'square' not 'round'
    "legend.fontsize": SMALLSIZE,
    "legend.framealpha": FRAMEALPHA,
    "legend.handleheight": 1.0,  # default is 0.7
    "legend.handlelength": 2.0,  # default is 2.0
    "legend.handletextpad": 0.5,  # a bit more compact (see columnspacing)
    "mathtext.default": "it",
    "mathtext.fontset": "custom",
    "mathtext.bf": "regular:bold",  # custom settings implemented above
    "mathtext.cal": "cursive",
    "mathtext.it": "regular:italic",
    "mathtext.rm": "regular",
    "mathtext.sf": "regular",
    "mathtext.tt": "monospace",
    "patch.linewidth": LINEWIDTH,
    "savefig.bbox": None,  # do not use 'tight'
    "savefig.directory": "",  # use the working directory
    "savefig.dpi": 1000,  # use academic journal recommendation
    "savefig.facecolor": WHITE,  # use white instead of 'auto'
    "savefig.format": "pdf",  # use vector graphics
    "savefig.transparent": False,
    "xtick.color": BLACK,
    "xtick.direction": TICKDIR,
    "xtick.labelsize": SMALLSIZE,
    "xtick.major.pad": TICKPAD,
    "xtick.major.size": TICKLEN,
    "xtick.major.width": LINEWIDTH,
    "xtick.minor.pad": TICKPAD,
    "xtick.minor.size": TICKLEN * TICKLENRATIO,
    "xtick.minor.width": LINEWIDTH * TICKWIDTHRATIO,
    "xtick.minor.visible": TICKMINOR,
    "ytick.color": BLACK,
    "ytick.direction": TICKDIR,
    "ytick.labelsize": SMALLSIZE,
    "ytick.major.pad": TICKPAD,
    "ytick.major.size": TICKLEN,
    "ytick.major.width": LINEWIDTH,
    "ytick.minor.pad": TICKPAD,
    "ytick.minor.size": TICKLEN * TICKLENRATIO,
    "ytick.minor.width": LINEWIDTH * TICKWIDTHRATIO,
    "ytick.minor.visible": TICKMINOR,
}
if "mathtext.fallback" in _rc_matplotlib_native:
    _rc_matplotlib_default["mathtext.fallback"] = "stixsans"

# ultraplot pseudo-setting defaults, validators, and descriptions
# NOTE: Cannot have different a-b-c and title paddings because they are both controlled
# by matplotlib's _title_offset_trans transform and want to keep them aligned anyway.
_addendum_rotation = " Must be 'vertical', 'horizontal', or a float indicating degrees."
_addendum_em = " Interpreted by `~ultraplot.utils.units`. Numeric units are em-widths."
_addendum_in = " Interpreted by `~ultraplot.utils.units`. Numeric units are inches."
_addendum_pt = " Interpreted by `~ultraplot.utils.units`. Numeric units are points."
_addendum_font = (
    " Must be a :ref:`relative font size <font_table>` or unit string "
    "interpreted by `~ultraplot.utils.units`. Numeric units are points."
)
_rc_ultraplot_table = build_settings_rc_table(globals())

# Child settings. Changing the parent changes all the children, but
# changing any of the children does not change the parent.
_rc_children = {
    "font.smallsize": (  # the 'small' fonts
        "tick.labelsize",
        "xtick.labelsize",
        "ytick.labelsize",
        "axes.labelsize",
        "legend.fontsize",
        "grid.labelsize",
    ),
    "font.largesize": (  # the 'large' fonts
        "abc.size",
        "figure.titlesize",
        "suptitle.size",
        "axes.titlesize",
        "title.size",
        "leftlabel.size",
        "toplabel.size",
        "rightlabel.size",
        "bottomlabel.size",
    ),
    "meta.color": (  # change the 'color' of an axes
        "axes.edgecolor",
        "axes.labelcolor",
        "legend.edgecolor",
        "colorbar.edgecolor",
        "tick.labelcolor",
        "hatch.color",
        "xtick.color",
        "ytick.color",
    ),
    "meta.width": (  # change the tick and frame line width
        "axes.linewidth",
        "tick.width",
        "tick.linewidth",
        "xtick.major.width",
        "ytick.major.width",
        "grid.width",
        "grid.linewidth",
    ),
    "axes.margin": ("axes.xmargin", "axes.ymargin"),
    "grid.color": ("gridminor.color", "grid.labelcolor"),
    "grid.alpha": ("gridminor.alpha",),
    "grid.linewidth": ("gridminor.linewidth",),
    "grid.linestyle": ("gridminor.linestyle",),
    "tick.color": ("xtick.color", "ytick.color"),
    "tick.dir": ("xtick.direction", "ytick.direction"),
    "tick.len": ("xtick.major.size", "ytick.major.size"),
    "tick.minor": ("xtick.minor.visible", "ytick.minor.visible"),
    "tick.pad": (
        "xtick.major.pad",
        "xtick.minor.pad",
        "ytick.major.pad",
        "ytick.minor.pad",
    ),  # noqa: E501
    "tick.width": ("xtick.major.width", "ytick.major.width"),
    "tick.labelsize": ("xtick.labelsize", "ytick.labelsize"),
}

# Recently added settings. Update these only if the version is recent enough
# NOTE: We don't make 'title.color' a child of 'axes.titlecolor' because
# the latter can take on the value 'auto' and can't handle that right now.
if _version_mpl >= "3.2":
    _rc_matplotlib_default["axes.titlecolor"] = BLACK
    _rc_children["title.color"] = ("axes.titlecolor",)
if _version_mpl >= "3.4":
    _rc_matplotlib_default["xtick.labelcolor"] = BLACK
    _rc_matplotlib_default["ytick.labelcolor"] = BLACK
    _rc_children["tick.labelcolor"] = ("xtick.labelcolor", "ytick.labelcolor")
    _rc_children["grid.labelcolor"] = ("xtick.labelcolor", "ytick.labelcolor")
    _rc_children["meta.color"] += ("xtick.labelcolor", "ytick.labelcolor")

# Setting synonyms. Changing one setting changes the other. Also account for existing
# children. Most of these are aliased due to ultraplot settings overlapping with
# existing matplotlib settings.
_rc_synonyms = (
    ("cmap", "image.cmap", "cmap.sequential"),
    ("cmap.lut", "image.lut"),
    ("font.name", "font.family"),
    ("font.small", "font.smallsize"),
    ("font.large", "font.largesize"),
    ("formatter.limits", "axes.formatter.limits"),
    ("formatter.use_locale", "axes.formatter.use_locale"),
    ("formatter.use_mathtext", "axes.formatter.use_mathtext"),
    ("formatter.min_exponent", "axes.formatter.min_exponent"),
    ("formatter.use_offset", "axes.formatter.useoffset"),
    ("formatter.offset_threshold", "axes.formatter.offset_threshold"),
    ("grid.below", "axes.axisbelow"),
    ("grid.labelpad", "grid.pad"),
    ("grid.linewidth", "grid.width"),
    ("grid.linestyle", "grid.style"),
    ("gridminor.linewidth", "gridminor.width"),
    ("gridminor.linestyle", "gridminor.style"),
    ("label.color", "axes.labelcolor"),
    ("label.pad", "axes.labelpad"),
    ("label.size", "axes.labelsize"),
    ("label.weight", "axes.labelweight"),
    ("margin", "axes.margin"),
    ("meta.width", "meta.linewidth"),
    ("meta.color", "meta.edgecolor"),
    ("tick.labelpad", "tick.pad"),
    ("tick.labelsize", "grid.labelsize"),
    ("tick.labelcolor", "grid.labelcolor"),
    ("tick.labelweight", "grid.labelweight"),
    ("tick.linewidth", "tick.width"),
    ("title.pad", "axes.titlepad"),
    ("title.size", "axes.titlesize"),
    ("title.weight", "axes.titleweight"),
)
for _keys in _rc_synonyms:
    for _key in _keys:
        _set = {_ for k in _keys for _ in {k, *_rc_children.get(k, ())}} - {_key}
        _rc_children[_key] = tuple(sorted(_set))

# Previously removed settings.
# NOTE: Initial idea was to defer deprecation warnings in Configurator to the
# subsequent RcParams indexing. However this turned out be complicated, because
# would have to detect deprecated keys in _get_item_dicts blocks, and need to
# validate values before e.g. applying 'tick.lenratio'. So the renamed parameters
# do not have to be added as _rc_children, since Configurator translates before
# retrieving the list of children in _get_item_dicts.
_rc_removed = get_rc_removed()
_rc_renamed = get_rc_renamed()

# Validate the default settings dictionaries using a custom ultraplot _RcParams
# and the original matplotlib RcParams. Also surreptitiously add ultraplot
# font settings to the font keys list (beoolean below always evalutes to True)
# font keys list whlie initializing.
_rc_ultraplot_default = {
    key: value for key, (value, _, _) in _rc_ultraplot_table.items()
}
_rc_ultraplot_validate = {
    key: validator
    for key, (_, validator, _) in _rc_ultraplot_table.items()
    if not (validator is _validate_fontsize and FONT_KEYS.add(key))
}
_rc_ultraplot_default = _RcParams(_rc_ultraplot_default, _rc_ultraplot_validate)
_rc_matplotlib_default = RcParams(_rc_matplotlib_default)

# Important joint matplotlib ultraplot constants
# NOTE: The 'nodots' dictionary should include removed and renamed settings
_rc_categories = {
    ".".join(name.split(".")[: i + 1])
    for dict_ in (_rc_ultraplot_default, _rc_matplotlib_native)
    for name in dict_
    for i in range(len(name.split(".")) - 1)
}
_rc_nodots = {
    name.replace(".", ""): name
    for dict_ in (
        _rc_ultraplot_default,
        _rc_matplotlib_native,
        _rc_renamed,
        _rc_removed,
    )
    for name in dict_.keys()
}
