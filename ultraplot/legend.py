from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable, Optional, Tuple, Union

import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.text as mtext
import numpy as np
from matplotlib import cm as mcm
from matplotlib import colors as mcolors
from matplotlib import lines as mlines
from matplotlib import legend as mlegend
from matplotlib import legend_handler as mhandler

from .config import rc
from .internals import _not_none, _pop_props, guides, rcsetup
from .utils import _fontsize_to_pt, units

from .config import rc
from .internals import _not_none, _pop_props, guides, rcsetup
from .utils import _fontsize_to_pt, units

try:
    from typing import override
except ImportError:
    from typing_extensions import override

try:  # optional cartopy-dependent geometry support
    import cartopy.crs as ccrs
    from cartopy.io import shapereader as cshapereader
    from cartopy.mpl.feature_artist import FeatureArtist as _CartopyFeatureArtist
    from cartopy.mpl.path import shapely_to_path as _cartopy_shapely_to_path
except Exception:
    ccrs = None
    cshapereader = None
    _CartopyFeatureArtist = None
    _cartopy_shapely_to_path = None

try:  # optional shapely support for direct geometry legend handles
    from shapely.geometry.base import BaseGeometry as _ShapelyBaseGeometry
    from shapely.ops import unary_union as _shapely_unary_union
except Exception:
    _ShapelyBaseGeometry = None
    _shapely_unary_union = None

__all__ = [
    "Legend",
    "LegendEntry",
    "GeometryEntry",
]


def _wedge_legend_patch(
    legend,
    orig_handle,
    xdescent,
    ydescent,
    width,
    height,
    fontsize,
):
    """
    Draw wedge-shaped legend keys for pie wedge handles.
    """
    center = (-xdescent + width * 0.5, -ydescent + height * 0.5)
    radius = 0.5 * min(width, height)
    theta1 = float(getattr(orig_handle, "theta1", 0.0))
    theta2 = float(getattr(orig_handle, "theta2", 300.0))
    if theta2 == theta1:
        theta2 = theta1 + 300.0
    return mpatches.Wedge(center, radius, theta1=theta1, theta2=theta2)


class LegendEntry(mlines.Line2D):
    """
    Convenience artist for custom legend entries.

    This is a lightweight wrapper around `matplotlib.lines.Line2D` that
    initializes with empty data so it can be passed directly to
    `Axes.legend()` or `Figure.legend()` handles.
    """

    def __init__(
        self,
        label=None,
        *,
        color=None,
        line=True,
        marker=None,
        linestyle="-",
        linewidth=2,
        markersize=6,
        markerfacecolor=None,
        markeredgecolor=None,
        markeredgewidth=None,
        alpha=None,
        **kwargs,
    ):
        marker = "o" if marker is None and not line else marker
        linestyle = "none" if not line else linestyle
        if markerfacecolor is None and color is not None:
            markerfacecolor = color
        if markeredgecolor is None and color is not None:
            markeredgecolor = color
        super().__init__(
            [],
            [],
            label=label,
            color=color,
            marker=marker,
            linestyle=linestyle,
            linewidth=linewidth,
            markersize=markersize,
            markerfacecolor=markerfacecolor,
            markeredgecolor=markeredgecolor,
            markeredgewidth=markeredgewidth,
            alpha=alpha,
            **kwargs,
        )

    @classmethod
    def line(cls, label=None, **kwargs):
        """
        Build a line-style legend entry.
        """
        return cls(label=label, line=True, **kwargs)

    @classmethod
    def marker(cls, label=None, marker="o", **kwargs):
        """
        Build a marker-style legend entry.
        """
        return cls(label=label, line=False, marker=marker, **kwargs)


_GEOMETRY_SHAPE_PATHS = {
    "circle": mpath.Path.unit_circle(),
    "square": mpath.Path.unit_rectangle(),
    "triangle": mpath.Path.unit_regular_polygon(3),
    "diamond": mpath.Path.unit_regular_polygon(4),
    "pentagon": mpath.Path.unit_regular_polygon(5),
    "hexagon": mpath.Path.unit_regular_polygon(6),
    "star": mpath.Path.unit_regular_star(5),
}
_GEOMETRY_SHAPE_ALIASES = {
    "box": "square",
    "rect": "square",
    "rectangle": "square",
    "tri": "triangle",
    "pent": "pentagon",
    "hex": "hexagon",
}
_DEFAULT_GEO_JOINSTYLE = "bevel"


def _normalize_shape_name(value: str) -> str:
    """
    Normalize geometry shape shorthand names.
    """
    key = str(value).strip().lower().replace("_", "").replace("-", "").replace(" ", "")
    return _GEOMETRY_SHAPE_ALIASES.get(key, key)


def _normalize_country_resolution(resolution: str) -> str:
    """
    Normalize Natural Earth shorthand resolution.
    """
    value = str(resolution).strip().lower()
    if value in {"10", "10m"}:
        return "10m"
    if value in {"50", "50m"}:
        return "50m"
    if value in {"110", "110m"}:
        return "110m"
    raise ValueError(
        f"Invalid country resolution {resolution!r}. "
        "Use one of: '10m', '50m', '110m'."
    )


def _country_geometry_for_legend(geometry: Any, *, include_far: bool = False) -> Any:
    """
    Reduce multi-part country geometry for readability while preserving local islands.

    This avoids tiny legend glyphs for countries with distant overseas territories
    (e.g., Netherlands in Natural Earth datasets), but tries to keep nearby islands.
    """
    if include_far:
        return geometry
    geoms = getattr(geometry, "geoms", None)
    if geoms is None:
        return geometry
    parts = []
    for part in geoms:
        area = float(getattr(part, "area", 0.0) or 0.0)
        if area > 0:
            parts.append((area, part))
    if not parts:
        return geometry
    dominant = max(parts, key=lambda item: item[0])[1]

    # Preserve local components near the dominant polygon (e.g. nearby coastal islands)
    # while dropping very distant territories that make legend glyphs too tiny.
    minx, miny, maxx, maxy = dominant.bounds
    span = max(maxx - minx, maxy - miny, 1e-6)
    neighborhood = dominant.buffer(1.5 * span)
    keep = [part for _, part in parts if part.intersects(neighborhood)]
    if not keep:
        return dominant
    if len(keep) == 1:
        return keep[0]
    if _shapely_unary_union is None:
        return dominant
    try:
        return _shapely_unary_union(keep)
    except Exception:
        return dominant


def _resolve_country_projection(country_proj: Any) -> Any:
    """
    Resolve shorthand strings to cartopy projections for country legend geometries.
    """
    if country_proj is None:
        return None
    if callable(country_proj) and not hasattr(country_proj, "project_geometry"):
        return country_proj
    if hasattr(country_proj, "project_geometry"):
        return country_proj
    if isinstance(country_proj, str):
        if ccrs is None:
            raise ValueError(
                "country_proj requires cartopy. Install cartopy or pass a callable."
            )
        key = (
            country_proj.strip()
            .lower()
            .replace("_", "")
            .replace("-", "")
            .replace(" ", "")
        )
        mapping = {
            "platecarree": ccrs.PlateCarree,
            "pc": ccrs.PlateCarree,
            "mercator": ccrs.Mercator,
            "robinson": ccrs.Robinson,
            "mollweide": ccrs.Mollweide,
            "equalearth": ccrs.EqualEarth,
            "orthographic": ccrs.Orthographic,
        }
        if key not in mapping:
            raise ValueError(
                f"Unknown country_proj {country_proj!r}. "
                "Use a cartopy CRS, callable, or one of: "
                + ", ".join(sorted(mapping))
                + "."
            )
        # Orthographic needs center lon/lat.
        if key == "orthographic":
            return mapping[key](0, 0)
        return mapping[key]()
    raise ValueError(
        "country_proj must be None, a cartopy CRS, a projection name string, or "
        "a callable accepting and returning a geometry."
    )


def _project_geometry_for_legend(geometry: Any, country_proj: Any) -> Any:
    """
    Project geometry for legend rendering when requested.
    """
    projection = _resolve_country_projection(country_proj)
    if projection is None:
        return geometry
    if callable(projection) and not hasattr(projection, "project_geometry"):
        out = projection(geometry)
        if out is None:
            raise ValueError("country_proj callable returned None geometry.")
        return out
    if ccrs is None:
        raise ValueError(
            "country_proj cartopy projection requested but cartopy missing."
        )
    try:
        return projection.project_geometry(geometry, src_crs=ccrs.PlateCarree())
    except TypeError:
        return projection.project_geometry(geometry, ccrs.PlateCarree())


@lru_cache(maxsize=256)
def _resolve_country_geometry(
    code: str, resolution: str = "110m", include_far: bool = False
):
    """
    Resolve a country shorthand code (e.g., ``AU`` or ``AUS``) to a geometry.
    """
    if cshapereader is None:
        raise ValueError(
            "Country shorthand requires cartopy's shapereader support. "
            "Pass a shapely geometry directly instead."
        )
    key = str(code).strip().upper()
    if not key:
        raise ValueError("Country shorthand cannot be empty.")
    resolution = _normalize_country_resolution(resolution)
    try:
        path = cshapereader.natural_earth(
            resolution=resolution,
            category="cultural",
            name="admin_0_countries",
        )
        reader = cshapereader.Reader(path)
    except Exception as exc:
        raise ValueError(
            "Unable to load Natural Earth country geometries for shorthand parsing. "
            "This usually means cartopy data is not available offline yet. "
            "Pass a shapely geometry directly (e.g. from GeoPandas), or pre-download "
            "the Natural Earth dataset."
        ) from exc

    fields = (
        "ADM0_A3",
        "ISO_A3",
        "ISO_A3_EH",
        "SOV_A3",
        "SU_A3",
        "GU_A3",
        "BRK_A3",
        "ADM0_A3_US",
        "ISO_A2",
        "ISO_A2_EH",
        "ABBREV",
        "NAME",
        "NAME_LONG",
        "ADMIN",
    )
    for record in reader.records():
        attrs = record.attributes or {}
        values = {str(attrs.get(field, "")).strip().upper() for field in fields}
        values.discard("")
        if key in values:
            return _country_geometry_for_legend(
                record.geometry, include_far=include_far
            )
    raise ValueError(f"Unknown country shorthand {code!r}.")


def _geometry_to_path(
    geometry: Any,
    *,
    country_reso: str = "110m",
    country_territories: bool = False,
    country_proj: Any = None,
) -> mpath.Path:
    """
    Convert geometry/path shorthand input to a matplotlib path.
    """
    if isinstance(geometry, mpath.Path):
        return geometry
    if isinstance(geometry, str):
        spec = geometry.strip()
        shape = _normalize_shape_name(spec)
        if shape in _GEOMETRY_SHAPE_PATHS:
            return _GEOMETRY_SHAPE_PATHS[shape]
        if spec.lower().startswith("country:"):
            geometry = _resolve_country_geometry(
                spec.split(":", 1)[1],
                country_reso,
                include_far=country_territories,
            )
            geometry = _project_geometry_for_legend(geometry, country_proj)
        elif spec.isalpha() and len(spec) in (2, 3):
            geometry = _resolve_country_geometry(
                spec,
                country_reso,
                include_far=country_territories,
            )
            geometry = _project_geometry_for_legend(geometry, country_proj)
        else:
            options = ", ".join(sorted(_GEOMETRY_SHAPE_PATHS))
            raise ValueError(
                f"Unknown geometry shorthand {geometry!r}. "
                f"Use a shapely geometry, country code, or one of: {options}."
            )
    if hasattr(geometry, "geom_type") and _cartopy_shapely_to_path is not None:
        return _cartopy_shapely_to_path(geometry)
    raise TypeError(
        "Geometry must be a matplotlib Path, shapely geometry, geometry shorthand, "
        "or country shorthand."
    )


def _fit_path_to_handlebox(
    path: mpath.Path,
    *,
    xdescent: float,
    ydescent: float,
    width: float,
    height: float,
    pad: float = 0.08,
) -> mpath.Path:
    """
    Normalize an arbitrary path into the legend-handle box.
    """
    verts = np.array(path.vertices, copy=True, dtype=float)
    finite = np.isfinite(verts).all(axis=1)
    if not finite.any():
        return mpath.Path.unit_rectangle()
    xmin, ymin = verts[finite].min(axis=0)
    xmax, ymax = verts[finite].max(axis=0)
    dx = max(float(xmax - xmin), 1e-12)
    dy = max(float(ymax - ymin), 1e-12)
    px = max(width * pad, 0.0)
    py = max(height * pad, 0.0)
    span_x = max(width - 2 * px, 1e-12)
    span_y = max(height - 2 * py, 1e-12)
    scale = min(span_x / dx, span_y / dy)
    cx = -xdescent + width * 0.5
    cy = -ydescent + height * 0.5
    verts[finite, 0] = (verts[finite, 0] - (xmin + xmax) * 0.5) * scale + cx
    verts[finite, 1] = (verts[finite, 1] - (ymin + ymax) * 0.5) * scale + cy
    return mpath.Path(
        verts, None if path.codes is None else np.array(path.codes, copy=True)
    )


def _feature_geometry_path(handle: Any) -> Optional[mpath.Path]:
    """
    Extract the first geometry path from a cartopy feature artist.
    """
    feature = getattr(handle, "_feature", None)
    if feature is None or _cartopy_shapely_to_path is None:
        return None
    geoms = getattr(feature, "geometries", None)
    if geoms is None:
        return None
    try:
        iterator = iter(geoms())
    except Exception:
        return None
    try:
        geometry = next(iterator)
    except StopIteration:
        return None
    try:
        return _cartopy_shapely_to_path(geometry)
    except Exception:
        return None


def _first_scalar(value: Any, default: Any = None) -> Any:
    """
    Return first scalar from lists/arrays used by collection-style artists.
    """
    if value is None:
        return default
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return default
        if value.ndim == 0:
            return value.item()
        if value.ndim >= 2:
            item = value[0]
        else:
            item = value
        if isinstance(item, np.ndarray) and item.size == 1:
            return item.item()
        return item
    if isinstance(value, (list, tuple)):
        if not value:
            return default
        item = value[0]
        if isinstance(item, np.ndarray) and item.size == 1:
            return item.item()
        return item
    return value


def _patch_joinstyle(value: Any, default: str = _DEFAULT_GEO_JOINSTYLE) -> str:
    """
    Resolve patch joinstyle from artist methods/kwargs with a sensible default.
    """
    getter = getattr(value, "get_joinstyle", None)
    if callable(getter):
        try:
            joinstyle = getter()
        except Exception:
            joinstyle = None
        if joinstyle:
            return joinstyle
    kwargs = getattr(value, "_kwargs", None)
    if isinstance(kwargs, dict):
        for key in ("joinstyle", "solid_joinstyle", "linejoin"):
            joinstyle = kwargs.get(key, None)
            if joinstyle:
                return joinstyle
    return default


def _feature_legend_patch(
    legend,
    orig_handle,
    xdescent,
    ydescent,
    width,
    height,
    fontsize,
):
    """
    Draw a normalized geometry path for cartopy feature artists.
    """
    path = _feature_geometry_path(orig_handle)
    if path is None:
        path = mpath.Path.unit_rectangle()
    path = _fit_path_to_handlebox(
        path,
        xdescent=xdescent,
        ydescent=ydescent,
        width=width,
        height=height,
    )
    return mpatches.PathPatch(path, joinstyle=_DEFAULT_GEO_JOINSTYLE)


def _shapely_geometry_patch(
    legend,
    orig_handle,
    xdescent,
    ydescent,
    width,
    height,
    fontsize,
):
    """
    Draw shapely geometry handles in legend boxes.
    """
    if _cartopy_shapely_to_path is None:
        path = mpath.Path.unit_rectangle()
    else:
        try:
            path = _cartopy_shapely_to_path(orig_handle)
        except Exception:
            path = mpath.Path.unit_rectangle()
    path = _fit_path_to_handlebox(
        path,
        xdescent=xdescent,
        ydescent=ydescent,
        width=width,
        height=height,
    )
    return mpatches.PathPatch(path, joinstyle=_DEFAULT_GEO_JOINSTYLE)


def _geometry_entry_patch(
    legend,
    orig_handle,
    xdescent,
    ydescent,
    width,
    height,
    fontsize,
):
    """
    Draw a geometry entry path inside the legend-handle box.
    """
    path = _fit_path_to_handlebox(
        orig_handle.get_path(),
        xdescent=xdescent,
        ydescent=ydescent,
        width=width,
        height=height,
    )
    return mpatches.PathPatch(path, joinstyle=_DEFAULT_GEO_JOINSTYLE)


class _FeatureArtistLegendHandler(mhandler.HandlerPatch):
    """
    Legend handler for cartopy FeatureArtist instances.
    """

    def __init__(self):
        super().__init__(patch_func=_feature_legend_patch)

    def update_prop(self, legend_handle, orig_handle, legend):
        facecolor = _first_scalar(
            (
                orig_handle.get_facecolor()
                if hasattr(orig_handle, "get_facecolor")
                else None
            ),
            default="none",
        )
        edgecolor = _first_scalar(
            (
                orig_handle.get_edgecolor()
                if hasattr(orig_handle, "get_edgecolor")
                else None
            ),
            default="none",
        )
        linewidth = _first_scalar(
            (
                orig_handle.get_linewidth()
                if hasattr(orig_handle, "get_linewidth")
                else None
            ),
            default=0.0,
        )
        legend_handle.set_facecolor(facecolor)
        legend_handle.set_edgecolor(edgecolor)
        legend_handle.set_linewidth(linewidth)
        legend_handle.set_joinstyle(_patch_joinstyle(orig_handle))
        if hasattr(orig_handle, "get_alpha"):
            legend_handle.set_alpha(orig_handle.get_alpha())
        legend._set_artist_props(legend_handle)
        legend_handle.set_clip_box(None)
        legend_handle.set_clip_path(None)


class _ShapelyGeometryLegendHandler(mhandler.HandlerPatch):
    """
    Legend handler for raw shapely geometries.
    """

    def __init__(self):
        super().__init__(patch_func=_shapely_geometry_patch)

    def update_prop(self, legend_handle, orig_handle, legend):
        # No style information is stored on shapely geometry objects.
        legend_handle.set_joinstyle(_DEFAULT_GEO_JOINSTYLE)
        legend._set_artist_props(legend_handle)
        legend_handle.set_clip_box(None)
        legend_handle.set_clip_path(None)


class _GeometryEntryLegendHandler(mhandler.HandlerPatch):
    """
    Legend handler for `GeometryEntry` custom handles.
    """

    def __init__(self):
        super().__init__(patch_func=_geometry_entry_patch)

    def update_prop(self, legend_handle, orig_handle, legend):
        super().update_prop(legend_handle, orig_handle, legend)
        legend_handle.set_joinstyle(_patch_joinstyle(orig_handle))
        legend_handle.set_clip_box(None)
        legend_handle.set_clip_path(None)


class GeometryEntry(mpatches.PathPatch):
    """
    Convenience geometry legend entry.

    Parameters
    ----------
    geometry
        Geometry shorthand (e.g. ``'triangle'`` or ``'country:AU'``),
        shapely geometry, or `matplotlib.path.Path`.
    """

    def __init__(
        self,
        geometry: Any = "square",
        *,
        country_reso: str = "110m",
        country_territories: bool = False,
        country_proj: Any = None,
        label: Optional[str] = None,
        facecolor: Any = "none",
        edgecolor: Any = "0.25",
        linewidth: float = 1.0,
        joinstyle: str = _DEFAULT_GEO_JOINSTYLE,
        alpha: Optional[float] = None,
        fill: Optional[bool] = None,
        **kwargs: Any,
    ):
        path = _geometry_to_path(
            geometry,
            country_reso=country_reso,
            country_territories=country_territories,
            country_proj=country_proj,
        )
        if fill is None:
            fill = facecolor not in (None, "none")
        super().__init__(
            path=path,
            label=label,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=linewidth,
            joinstyle=joinstyle,
            alpha=alpha,
            fill=fill,
            **kwargs,
        )
        self._ultraplot_geometry = geometry


def _geometry_default_label(geometry: Any, index: int) -> str:
    """
    Derive default labels for geo legend entries.
    """
    if isinstance(geometry, str):
        return geometry
    return f"Entry {index + 1}"


def _geo_legend_entries(
    entries: Iterable[Any] | dict[Any, Any],
    labels: Optional[Iterable[Any]] = None,
    *,
    country_reso: str = "110m",
    country_territories: bool = False,
    country_proj: Any = None,
    facecolor: Any = "none",
    edgecolor: Any = "0.25",
    linewidth: float = 1.0,
    alpha: Optional[float] = None,
    fill: Optional[bool] = None,
):
    """
    Build geometry semantic legend handles and labels.

    Notes
    -----
    `entries` may be:
    - mapping of ``label -> geometry``
    - sequence of ``(label, geometry)`` or ``(label, geometry, options)`` tuples
      where ``options`` is either a projection spec or a dict of per-entry
      `GeometryEntry` keyword overrides (e.g., `country_proj`, `country_reso`)
    - sequence of geometries with explicit `labels`
    """
    entry_options = None
    if isinstance(entries, dict):
        label_list = [str(label) for label in entries]
        geometry_list = list(entries.values())
        entry_options = [{} for _ in geometry_list]
    else:
        entries = list(entries)
        if labels is None and all(
            isinstance(entry, tuple) and len(entry) in (2, 3) for entry in entries
        ):
            label_list = []
            geometry_list = []
            entry_options = []
            for entry in entries:
                if len(entry) == 2:
                    label, geometry = entry
                    options = {}
                else:
                    label, geometry, options = entry
                    if options is None:
                        options = {}
                    elif isinstance(options, dict):
                        options = dict(options)
                    else:
                        # Convenience shorthand for per-entry projection only.
                        options = {"country_proj": options}
                label_list.append(str(label))
                geometry_list.append(geometry)
                entry_options.append(options)
        else:
            geometry_list = list(entries)
            entry_options = [{} for _ in geometry_list]
            if labels is None:
                label_list = [
                    _geometry_default_label(geometry, idx)
                    for idx, geometry in enumerate(geometry_list)
                ]
            else:
                label_list = [str(label) for label in labels]
    if len(label_list) != len(geometry_list):
        raise ValueError(
            "Labels and geometry entries must have the same length. "
            f"Got {len(label_list)} labels and {len(geometry_list)} entries."
        )
    handles = []
    for geometry, label, options in zip(geometry_list, label_list, entry_options):
        geo_kwargs = {
            "country_reso": country_reso,
            "country_territories": country_territories,
            "country_proj": country_proj,
            "facecolor": facecolor,
            "edgecolor": edgecolor,
            "linewidth": linewidth,
            "alpha": alpha,
            "fill": fill,
        }
        geo_kwargs.update(options or {})
        handles.append(GeometryEntry(geometry, label=label, **geo_kwargs))
    return handles, label_list


def _style_lookup(style, key, index, default=None):
    """
    Resolve style values from scalar, mapping, or sequence inputs.
    """
    if style is None:
        return default
    if isinstance(style, dict):
        return style.get(key, default)
    if isinstance(style, str):
        return style
    try:
        values = list(style)
    except TypeError:
        return style
    if not values:
        return default
    return values[index % len(values)]


def _format_label(value, fmt):
    """
    Format legend labels from values.
    """
    if fmt is None:
        return f"{value:g}" if isinstance(value, (float, np.floating)) else str(value)
    if callable(fmt):
        return str(fmt(value))
    return fmt.format(value)


def _default_cycle_colors():
    """
    Return default color cycle entries.
    """
    try:
        import matplotlib as mpl

        colors = mpl.rcParams["axes.prop_cycle"].by_key().get("color", None)
    except Exception:
        colors = None
    return colors or ["C0"]


def _cat_legend_entries(
    categories: Iterable[Any],
    *,
    colors=None,
    markers="o",
    line: bool = False,
    linestyle: str = "-",
    linewidth: float = 2.0,
    markersize: float = 6.0,
    alpha=None,
    markeredgecolor=None,
    markeredgewidth=None,
):
    """
    Build categorical semantic legend handles and labels.
    """
    labels = list(dict.fromkeys(categories))
    palette = _default_cycle_colors()
    handles = []
    for idx, label in enumerate(labels):
        color = _style_lookup(colors, label, idx, default=palette[idx % len(palette)])
        marker = _style_lookup(markers, label, idx, default="o")
        if line and marker in (None, ""):
            marker = None
        handles.append(
            LegendEntry(
                label=str(label),
                color=color,
                line=line,
                marker=marker,
                linestyle=linestyle,
                linewidth=linewidth,
                markersize=markersize,
                markeredgecolor=markeredgecolor,
                markeredgewidth=markeredgewidth,
                alpha=alpha,
            )
        )
    return handles, [str(label) for label in labels]


def _size_legend_entries(
    levels: Iterable[float],
    *,
    color="0.35",
    marker: str = "o",
    area: bool = True,
    scale: float = 1.0,
    minsize: float = 3.0,
    fmt=None,
    alpha=None,
    markeredgecolor=None,
    markeredgewidth=None,
):
    """
    Build size semantic legend handles and labels.
    """
    values = np.asarray(list(levels), dtype=float)
    if values.size == 0:
        return [], []
    if area:
        ms = np.sqrt(np.clip(values, 0, None))
    else:
        ms = np.abs(values)
    ms = np.maximum(ms * scale, minsize)
    labels = [_format_label(value, fmt) for value in values]
    handles = [
        LegendEntry.marker(
            label=label,
            marker=marker,
            color=color,
            markersize=float(size),
            alpha=alpha,
            markeredgecolor=markeredgecolor,
            markeredgewidth=markeredgewidth,
        )
        for label, size in zip(labels, ms)
    ]
    return handles, labels


def _num_legend_entries(
    levels=None,
    *,
    vmin=None,
    vmax=None,
    n: int = 5,
    cmap="viridis",
    norm=None,
    fmt=None,
    edgecolor="none",
    linewidth: float = 0.0,
    alpha=None,
):
    """
    Build numeric-color semantic legend handles and labels.
    """
    if levels is None:
        if vmin is None or vmax is None:
            raise ValueError("Please provide levels or both vmin and vmax.")
        values = np.linspace(float(vmin), float(vmax), int(n))
    elif np.isscalar(levels) and isinstance(levels, (int, np.integer)):
        if vmin is None or vmax is None:
            raise ValueError("Please provide vmin and vmax when levels is an integer.")
        values = np.linspace(float(vmin), float(vmax), int(levels))
    else:
        values = np.asarray(list(levels), dtype=float)
    if values.size == 0:
        return [], []
    if norm is None:
        lo = float(np.nanmin(values) if vmin is None else vmin)
        hi = float(np.nanmax(values) if vmax is None else vmax)
        norm = mcolors.Normalize(vmin=lo, vmax=hi)
    try:
        import matplotlib as mpl

        cmap_obj = mpl.colormaps.get_cmap(cmap)
    except Exception:
        cmap_obj = mcm.get_cmap(cmap)
    labels = [_format_label(value, fmt) for value in values]
    handles = [
        mpatches.Patch(
            facecolor=cmap_obj(norm(float(value))),
            edgecolor=edgecolor,
            linewidth=linewidth,
            alpha=alpha,
            label=label,
        )
        for value, label in zip(values, labels)
    ]
    return handles, labels


ALIGN_OPTS = {
    None: {
        "center": "center",
        "left": "center left",
        "right": "center right",
        "top": "upper center",
        "bottom": "lower center",
    },
    "left": {
        "center": "center right",
        "left": "center right",
        "right": "center right",
        "top": "upper right",
        "bottom": "lower right",
    },
    "right": {
        "center": "center left",
        "left": "center left",
        "right": "center left",
        "top": "upper left",
        "bottom": "lower left",
    },
    "top": {
        "center": "lower center",
        "left": "lower left",
        "right": "lower right",
        "top": "lower center",
        "bottom": "lower center",
    },
    "bottom": {
        "center": "upper center",
        "left": "upper left",
        "right": "upper right",
        "top": "upper center",
        "bottom": "upper center",
    },
}

LegendKw = dict[str, Any]
LegendHandles = Any
LegendLabels = Any


@dataclass(frozen=True)
class _LegendInputs:
    handles: LegendHandles
    labels: LegendLabels
    loc: Any
    align: Any
    width: Any
    pad: Any
    space: Any
    frameon: bool
    ncol: Any
    order: str
    label: Any
    title: Any
    fontsize: float
    fontweight: Any
    fontcolor: Any
    titlefontsize: float
    titlefontweight: Any
    titlefontcolor: Any
    handle_kw: Any
    handler_map: Any
    span: Optional[Union[int, Tuple[int, int]]]
    row: Optional[int]
    col: Optional[int]
    rows: Optional[Union[int, Tuple[int, int]]]
    cols: Optional[Union[int, Tuple[int, int]]]
    kwargs: dict[str, Any]


class Legend(mlegend.Legend):
    # Soft wrapper of matplotlib legend's class.
    # Currently we only override the syncing of the location.
    # The user may change the location and the legend_dict should
    # be updated accordingly. This caused an issue where
    # a legend format was not behaving according to the docs
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def get_default_handler_map(cls):
        """
        Extend matplotlib defaults with a wedge handler for pie legends.
        """
        handler_map = dict(super().get_default_handler_map())
        handler_map.setdefault(
            GeometryEntry,
            _GeometryEntryLegendHandler(),
        )
        handler_map.setdefault(
            mpatches.Wedge,
            mhandler.HandlerPatch(patch_func=_wedge_legend_patch),
        )
        if _CartopyFeatureArtist is not None:
            handler_map.setdefault(_CartopyFeatureArtist, _FeatureArtistLegendHandler())
        if _ShapelyBaseGeometry is not None:
            handler_map.setdefault(
                _ShapelyBaseGeometry, _ShapelyGeometryLegendHandler()
            )
        return handler_map

    @override
    def set_loc(self, loc=None):
        # Sync location setting with the move
        old_loc = None
        if self.axes is not None:
            # Get old location which is a tuple of location and
            # legend type
            for k, v in self.axes._legend_dict.items():
                if v is self:
                    old_loc = k
                    break
        super().set_loc(loc)
        if old_loc is not None:
            value = self.axes._legend_dict.pop(old_loc, None)
            where, type = old_loc
            self.axes._legend_dict[(loc, type)] = value


def _normalize_em_kwargs(kwargs: dict[str, Any], *, fontsize: float) -> dict[str, Any]:
    """
    Convert legend-related em unit kwargs to absolute values in points.
    """
    for setting in rcsetup.EM_KEYS:
        pair = setting.split("legend.", 1)
        if len(pair) == 1:
            continue
        _, key = pair
        value = kwargs.pop(key, None)
        if isinstance(value, str):
            value = units(value, "em", fontsize=fontsize)
        if value is not None:
            kwargs[key] = value
    return kwargs


class UltraLegend:
    """
    Centralized legend builder for axes.
    """

    def __init__(self, axes):
        self.axes = axes

    @staticmethod
    def _validate_semantic_kwargs(method: str, kwargs: dict[str, Any]) -> None:
        """
        Prevent ambiguous legend kwargs for semantic legend helpers.
        """
        if "label" in kwargs:
            raise TypeError(
                f"{method}() does not accept the legend kwarg 'label'. "
                "Use title=... for the legend title."
            )
        if "labels" in kwargs:
            raise TypeError(
                f"{method}() does not accept the legend kwarg 'labels'. "
                "Semantic legend labels are derived from the helper inputs."
            )

    def catlegend(
        self,
        categories: Iterable[Any],
        *,
        colors=None,
        markers=None,
        line: Optional[bool] = None,
        linestyle=None,
        linewidth: Optional[float] = None,
        markersize: Optional[float] = None,
        alpha=None,
        markeredgecolor=None,
        markeredgewidth=None,
        add: bool = True,
        **legend_kwargs: Any,
    ):
        """
        Build categorical legend entries and optionally draw a legend.
        """
        line = _not_none(line, rc["legend.cat.line"])
        markers = _not_none(markers, rc["legend.cat.marker"])
        linestyle = _not_none(linestyle, rc["legend.cat.linestyle"])
        linewidth = _not_none(linewidth, rc["legend.cat.linewidth"])
        markersize = _not_none(markersize, rc["legend.cat.markersize"])
        alpha = _not_none(alpha, rc["legend.cat.alpha"])
        markeredgecolor = _not_none(markeredgecolor, rc["legend.cat.markeredgecolor"])
        markeredgewidth = _not_none(markeredgewidth, rc["legend.cat.markeredgewidth"])
        handles, labels = _cat_legend_entries(
            categories,
            colors=colors,
            markers=markers,
            line=line,
            linestyle=linestyle,
            linewidth=linewidth,
            markersize=markersize,
            alpha=alpha,
            markeredgecolor=markeredgecolor,
            markeredgewidth=markeredgewidth,
        )
        if not add:
            return handles, labels
        self._validate_semantic_kwargs("catlegend", legend_kwargs)
        # Route through Axes.legend so location shorthands (e.g. 'r', 'b')
        # and queued guide keyword handling behave exactly like the public API.
        return self.axes.legend(handles, labels, **legend_kwargs)

    def sizelegend(
        self,
        levels: Iterable[float],
        *,
        color=None,
        marker=None,
        area: Optional[bool] = None,
        scale: Optional[float] = None,
        minsize: Optional[float] = None,
        fmt=None,
        alpha=None,
        markeredgecolor=None,
        markeredgewidth=None,
        add: bool = True,
        **legend_kwargs: Any,
    ):
        """
        Build size legend entries and optionally draw a legend.
        """
        color = _not_none(color, rc["legend.size.color"])
        marker = _not_none(marker, rc["legend.size.marker"])
        area = _not_none(area, rc["legend.size.area"])
        scale = _not_none(scale, rc["legend.size.scale"])
        minsize = _not_none(minsize, rc["legend.size.minsize"])
        fmt = _not_none(fmt, rc["legend.size.format"])
        alpha = _not_none(alpha, rc["legend.size.alpha"])
        markeredgecolor = _not_none(markeredgecolor, rc["legend.size.markeredgecolor"])
        markeredgewidth = _not_none(markeredgewidth, rc["legend.size.markeredgewidth"])
        handles, labels = _size_legend_entries(
            levels,
            color=color,
            marker=marker,
            area=area,
            scale=scale,
            minsize=minsize,
            fmt=fmt,
            alpha=alpha,
            markeredgecolor=markeredgecolor,
            markeredgewidth=markeredgewidth,
        )
        if not add:
            return handles, labels
        self._validate_semantic_kwargs("sizelegend", legend_kwargs)
        return self.axes.legend(handles, labels, **legend_kwargs)

    def numlegend(
        self,
        levels=None,
        *,
        vmin=None,
        vmax=None,
        n: Optional[int] = None,
        cmap=None,
        norm=None,
        fmt=None,
        edgecolor=None,
        linewidth: Optional[float] = None,
        alpha=None,
        add: bool = True,
        **legend_kwargs: Any,
    ):
        """
        Build numeric-color legend entries and optionally draw a legend.
        """
        n = _not_none(n, rc["legend.num.n"])
        cmap = _not_none(cmap, rc["legend.num.cmap"])
        edgecolor = _not_none(edgecolor, rc["legend.num.edgecolor"])
        linewidth = _not_none(linewidth, rc["legend.num.linewidth"])
        alpha = _not_none(alpha, rc["legend.num.alpha"])
        fmt = _not_none(fmt, rc["legend.num.format"])
        handles, labels = _num_legend_entries(
            levels=levels,
            vmin=vmin,
            vmax=vmax,
            n=n,
            cmap=cmap,
            norm=norm,
            fmt=fmt,
            edgecolor=edgecolor,
            linewidth=linewidth,
            alpha=alpha,
        )
        if not add:
            return handles, labels
        self._validate_semantic_kwargs("numlegend", legend_kwargs)
        return self.axes.legend(handles, labels, **legend_kwargs)

    def geolegend(
        self,
        entries: Iterable[Any] | dict[Any, Any],
        labels: Optional[Iterable[Any]] = None,
        *,
        country_reso: Optional[str] = None,
        country_territories: Optional[bool] = None,
        country_proj: Any = None,
        handlesize: Optional[float] = None,
        facecolor: Any = None,
        edgecolor: Any = None,
        linewidth: Optional[float] = None,
        alpha: Optional[float] = None,
        fill: Optional[bool] = None,
        add: bool = True,
        **legend_kwargs: Any,
    ):
        """
        Build geometry legend entries and optionally draw a legend.
        """
        facecolor = _not_none(facecolor, rc["legend.geo.facecolor"])
        edgecolor = _not_none(edgecolor, rc["legend.geo.edgecolor"])
        linewidth = _not_none(linewidth, rc["legend.geo.linewidth"])
        alpha = _not_none(alpha, rc["legend.geo.alpha"])
        fill = _not_none(fill, rc["legend.geo.fill"])
        country_reso = _not_none(country_reso, rc["legend.geo.country_reso"])
        country_territories = _not_none(
            country_territories, rc["legend.geo.country_territories"]
        )
        country_proj = _not_none(country_proj, rc["legend.geo.country_proj"])
        handlesize = _not_none(handlesize, rc["legend.geo.handlesize"])
        handles, labels = _geo_legend_entries(
            entries,
            labels=labels,
            country_reso=country_reso,
            country_territories=country_territories,
            country_proj=country_proj,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=linewidth,
            alpha=alpha,
            fill=fill,
        )
        if not add:
            return handles, labels
        self._validate_semantic_kwargs("geolegend", legend_kwargs)
        if handlesize is not None:
            handlesize = float(handlesize)
            if handlesize <= 0:
                raise ValueError("geolegend handlesize must be positive.")
            if "handlelength" not in legend_kwargs:
                legend_kwargs["handlelength"] = rc["legend.handlelength"] * handlesize
            if "handleheight" not in legend_kwargs:
                legend_kwargs["handleheight"] = rc["legend.handleheight"] * handlesize
        return self.axes.legend(handles, labels, **legend_kwargs)

    @staticmethod
    def _align_map() -> dict[Optional[str], dict[str, str]]:
        """
        Mapping between panel side + align and matplotlib legend loc strings.
        """
        return ALIGN_OPTS

    def _resolve_inputs(
        self,
        handles=None,
        labels=None,
        *,
        loc=None,
        align=None,
        width=None,
        pad=None,
        space=None,
        frame=None,
        frameon=None,
        ncol=None,
        ncols=None,
        alphabetize=False,
        center=None,
        order=None,
        label=None,
        title=None,
        fontsize=None,
        fontweight=None,
        fontcolor=None,
        titlefontsize=None,
        titlefontweight=None,
        titlefontcolor=None,
        handle_kw=None,
        handler_map=None,
        span: Optional[Union[int, Tuple[int, int]]] = None,
        row: Optional[int] = None,
        col: Optional[int] = None,
        rows: Optional[Union[int, Tuple[int, int]]] = None,
        cols: Optional[Union[int, Tuple[int, int]]] = None,
        **kwargs: Any,
    ):
        """
        Normalize inputs, apply rc defaults, and convert units.
        """
        ncol = _not_none(ncols=ncols, ncol=ncol)
        order = _not_none(order, "C")
        frameon = _not_none(frame=frame, frameon=frameon, default=rc["legend.frameon"])
        fontsize = _not_none(fontsize, rc["legend.fontsize"])
        titlefontsize = _not_none(
            title_fontsize=kwargs.pop("title_fontsize", None),
            titlefontsize=titlefontsize,
            default=rc["legend.title_fontsize"],
        )
        fontsize = _fontsize_to_pt(fontsize)
        titlefontsize = _fontsize_to_pt(titlefontsize)
        if order not in ("F", "C"):
            raise ValueError(
                f"Invalid order {order!r}. Please choose from "
                "'C' (row-major, default) or 'F' (column-major)."
            )

        # Convert relevant keys to em-widths
        kwargs = _normalize_em_kwargs(kwargs, fontsize=fontsize)
        return _LegendInputs(
            handles=handles,
            labels=labels,
            loc=loc,
            align=align,
            width=width,
            pad=pad,
            space=space,
            frameon=frameon,
            ncol=ncol,
            order=order,
            label=label,
            title=title,
            fontsize=fontsize,
            fontweight=fontweight,
            fontcolor=fontcolor,
            titlefontsize=titlefontsize,
            titlefontweight=titlefontweight,
            titlefontcolor=titlefontcolor,
            handle_kw=handle_kw,
            handler_map=handler_map,
            span=span,
            row=row,
            col=col,
            rows=rows,
            cols=cols,
            kwargs=kwargs,
        )

    def _resolve_axes_layout(self, inputs: _LegendInputs):
        """
        Determine the legend axes and layout-related kwargs.
        """
        ax = self.axes
        if inputs.loc in ("fill", "left", "right", "top", "bottom"):
            lax = ax._add_guide_panel(
                inputs.loc,
                inputs.align,
                width=inputs.width,
                space=inputs.space,
                pad=inputs.pad,
                span=inputs.span,
                row=inputs.row,
                col=inputs.col,
                rows=inputs.rows,
                cols=inputs.cols,
            )
            kwargs = dict(inputs.kwargs)
            kwargs.setdefault("borderaxespad", 0)
            if not inputs.frameon:
                kwargs.setdefault("borderpad", 0)
            try:
                kwargs["loc"] = self._align_map()[lax._panel_side][inputs.align]
            except KeyError as exc:
                raise ValueError(
                    f"Invalid align={inputs.align!r} for legend loc={inputs.loc!r}."
                ) from exc
        else:
            lax = ax
            kwargs = dict(inputs.kwargs)
            pad = kwargs.pop("borderaxespad", inputs.pad)
            kwargs["loc"] = inputs.loc  # simply pass to legend
            kwargs["borderaxespad"] = units(pad, "em", fontsize=inputs.fontsize)
        return lax, kwargs

    def _resolve_style_kwargs(
        self,
        *,
        lax,
        fontcolor,
        fontweight,
        handle_kw,
        kwargs,
    ):
        """
        Parse frame settings and build per-element style kwargs.
        """
        kw_frame, kwargs = lax._parse_frame("legend", **kwargs)
        kw_text = {}
        if fontcolor is not None:
            kw_text["color"] = fontcolor
        if fontweight is not None:
            kw_text["weight"] = fontweight
        kw_handle = _pop_props(kwargs, "line")
        kw_handle.setdefault("solid_capstyle", "butt")
        kw_handle.update(handle_kw or {})
        return kw_frame, kw_text, kw_handle, kwargs

    def _build_legends(
        self,
        *,
        lax,
        inputs: _LegendInputs,
        center,
        alphabetize,
        kw_frame,
        kwargs,
    ):
        pairs, multi = lax._parse_legend_handles(
            inputs.handles,
            inputs.labels,
            ncol=inputs.ncol,
            order=inputs.order,
            center=center,
            alphabetize=alphabetize,
            handler_map=inputs.handler_map,
        )
        title = _not_none(label=inputs.label, title=inputs.title)
        kwargs.update(
            {
                "title": title,
                "frameon": inputs.frameon,
                "fontsize": inputs.fontsize,
                "handler_map": inputs.handler_map,
                "title_fontsize": inputs.titlefontsize,
            }
        )
        if multi:
            objs = lax._parse_legend_centered(pairs, kw_frame=kw_frame, **kwargs)
        else:
            kwargs.update({key: kw_frame.pop(key) for key in ("shadow", "fancybox")})
            objs = [
                lax._parse_legend_aligned(
                    pairs, ncol=inputs.ncol, order=inputs.order, **kwargs
                )
            ]
            objs[0].legendPatch.update(kw_frame)
        for obj in objs:
            if hasattr(lax, "legend_") and lax.legend_ is None:
                lax.legend_ = obj
            else:
                lax.add_artist(obj)
        return objs

    def _apply_handle_styles(self, objs, *, kw_text, kw_handle):
        """
        Apply per-handle styling overrides to legend artists.
        """
        for obj in objs:
            obj.set_clip_on(False)
            box = getattr(obj, "_legend_handle_box", None)
            for child in guides._iter_children(box):
                if isinstance(child, mtext.Text):
                    kw = kw_text
                else:
                    kw = {
                        key: val
                        for key, val in kw_handle.items()
                        if hasattr(child, "set_" + key)
                    }
                    if hasattr(child, "set_sizes") and "markersize" in kw_handle:
                        kw["sizes"] = np.atleast_1d(kw_handle["markersize"])
                child.update(kw)

    def _finalize(self, objs, *, loc, align):
        """
        Register legend for guide tracking and return the public object.
        """
        ax = self.axes
        if isinstance(objs[0], mpatches.FancyBboxPatch):
            objs = objs[1:]
        obj = objs[0] if len(objs) == 1 else tuple(objs)
        ax._register_guide("legend", obj, (loc, align))
        return obj

    def add(
        self,
        handles=None,
        labels=None,
        *,
        loc=None,
        align=None,
        width=None,
        pad=None,
        space=None,
        frame=None,
        frameon=None,
        ncol=None,
        ncols=None,
        alphabetize=False,
        center=None,
        order=None,
        label=None,
        title=None,
        fontsize=None,
        fontweight=None,
        fontcolor=None,
        titlefontsize=None,
        titlefontweight=None,
        titlefontcolor=None,
        handle_kw=None,
        handler_map=None,
        span: Optional[Union[int, Tuple[int, int]]] = None,
        row: Optional[int] = None,
        col: Optional[int] = None,
        rows: Optional[Union[int, Tuple[int, int]]] = None,
        cols: Optional[Union[int, Tuple[int, int]]] = None,
        **kwargs,
    ):
        """
        The driver function for adding axes legends.
        """
        inputs = self._resolve_inputs(
            handles,
            labels,
            loc=loc,
            align=align,
            width=width,
            pad=pad,
            space=space,
            frame=frame,
            frameon=frameon,
            ncol=ncol,
            ncols=ncols,
            alphabetize=alphabetize,
            center=center,
            order=order,
            label=label,
            title=title,
            fontsize=fontsize,
            fontweight=fontweight,
            fontcolor=fontcolor,
            titlefontsize=titlefontsize,
            titlefontweight=titlefontweight,
            titlefontcolor=titlefontcolor,
            handle_kw=handle_kw,
            handler_map=handler_map,
            span=span,
            row=row,
            col=col,
            rows=rows,
            cols=cols,
            **kwargs,
        )

        lax, kwargs = self._resolve_axes_layout(inputs)

        kw_frame, kw_text, kw_handle, kwargs = self._resolve_style_kwargs(
            lax=lax,
            fontcolor=inputs.fontcolor,
            fontweight=inputs.fontweight,
            handle_kw=inputs.handle_kw,
            kwargs=kwargs,
        )

        objs = self._build_legends(
            lax=lax,
            inputs=inputs,
            center=center,
            alphabetize=alphabetize,
            kw_frame=kw_frame,
            kwargs=kwargs,
        )

        self._apply_handle_styles(objs, kw_text=kw_text, kw_handle=kw_handle)
        return self._finalize(objs, loc=inputs.loc, align=inputs.align)
