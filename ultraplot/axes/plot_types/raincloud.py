"""Composition of half violins, observations, and boxplots."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from numbers import Number
from typing import TYPE_CHECKING, Any, Literal

from numpy.typing import ArrayLike, NDArray

import numpy as np
import matplotlib.artist as martist
import matplotlib.collections as mcollections
import matplotlib.colors as mcolors

from ... import _sharing as psharing, colors as pcolors
from ...config import rc
from ...internals import _canonicalize_kwargs, _not_none, _pop_props, inputs, warnings

if TYPE_CHECKING:
    from ..plot import PlotAxes


def _resolve_color(color: Any) -> Any:
    """Match the (colormap, index) colour shorthand of other plot methods."""
    if (
        isinstance(color, tuple)
        and len(color) == 2
        and isinstance(color[0], (str, mcolors.Colormap))
        and isinstance(color[1], Number)
    ):
        cmap, index = color
        return mcolors.to_hex(
            pcolors._cmap_database.get_cmap(cmap)(index), keep_alpha=True
        )
    return color


def _component_style(
    options: Mapping[str, Any] | None, category: str
) -> dict[str, Any]:
    """Resolve artist aliases before applying raincloud's component defaults."""
    style = dict(options or {})
    style.update(_pop_props(style, category))
    for key in (
        "color",
        "facecolor",
        "edgecolor",
        "colors",
        "facecolors",
        "edgecolors",
    ):
        if key in style:
            style[key] = _resolve_color(style[key])
    if category == "patch":
        # Box/violin wrappers style faces and edges separately rather than
        # accepting the generic Patch colour argument themselves.
        color = style.pop("color", None)
        if color is not None:
            style.setdefault("facecolor", color)
            style.setdefault("edgecolor", color)
    return style


def _filter_point_style(
    style: Mapping[str, Any], valid: NDArray[np.bool_]
) -> dict[str, Any]:
    """Keep per-observation scatter properties aligned with cleaned values."""
    style = dict(style)
    for key in (
        "sizes",
        "size",
        "colors",
        "facecolors",
        "edgecolors",
        "linewidths",
        "alpha",
    ):
        if key not in style:
            continue
        value = style[key]
        if key in ("colors", "facecolors", "edgecolors") and mcolors.is_color_like(
            value
        ):
            continue
        array = np.asarray(value)
        if array.ndim and array.shape[0] == valid.size:
            style[key] = array[valid]
    return style


def _group_options(style: Mapping[str, Any], index: int, count: int) -> dict[str, Any]:
    """Select native box/violin options that contain one value per group."""
    style = dict(style)
    for key in ("widths", "capwidths"):
        value = style.get(key)
        if np.ndim(value) == 1 and len(value) == count:
            style[key] = value[index]
    quantiles = style.get("quantiles")
    if quantiles is not None and len(quantiles) == count and np.ndim(quantiles[0]):
        style["quantiles"] = quantiles[index]
    return style


@dataclass(frozen=True)
class _RaincloudOptions:
    """Validated layout and component controls."""

    vert: bool
    side: Literal["low", "high"]
    direction: int
    jitter: float
    offset: float
    cloud: bool
    rain: bool
    box: bool
    seed: int | np.random.Generator | None


@dataclass(frozen=True)
class _RaincloudData:
    """Cleaned observations, original masks, and group metadata."""

    values: list[NDArray[np.float64]]
    masks: list[NDArray[np.bool_]]
    positions: NDArray[np.float64]
    labels: Sequence[Any] | None
    group_title: str | None
    value_title: str | None


def _resolve_options(
    orientation: Literal["vertical", "horizontal"] | None,
    side: Literal["low", "high"] | None,
    jitter: float | None,
    offset: float | None,
    cloud: bool | None,
    rain: bool | None,
    box: bool | None,
    seed: int | np.random.Generator | None,
) -> _RaincloudOptions:
    """Resolve rc defaults and validate options before creating artists."""
    orientation = _not_none(orientation, rc["raincloud.orientation"])
    side = _not_none(side, rc["raincloud.side"])
    jitter = _not_none(jitter, rc["raincloud.jitter"])
    offset = _not_none(offset, rc["raincloud.offset"])
    cloud = _not_none(cloud, rc["raincloud.cloud"])
    rain = _not_none(rain, rc["raincloud.rain"])
    box = _not_none(box, rc["raincloud.box"])
    seed = _not_none(seed, rc["raincloud.seed"])
    if orientation not in ("vertical", "horizontal"):
        raise ValueError("orientation must be 'vertical' or 'horizontal'")
    if side not in ("low", "high"):
        raise ValueError("side must be 'low' or 'high'")
    for name, value in (("jitter", jitter), ("offset", offset)):
        if not np.isscalar(value) or not np.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be a finite non-negative number")
    if not any((cloud, rain, box)):
        raise ValueError("At least one of cloud, rain, or box must be enabled")
    return _RaincloudOptions(
        vert=orientation == "vertical",
        side=side,
        direction=1 if side == "high" else -1,
        jitter=jitter,
        offset=offset,
        cloud=cloud,
        rain=rain,
        box=box,
        seed=seed,
    )


def _infer_metadata(
    data: Any, labels: Sequence[Any] | None, autoformat: bool | None
) -> tuple[Any, Sequence[Any] | None, str | None, str | None]:
    """Extract labelled-array metadata without overriding explicit labels."""
    autoformat = _not_none(autoformat, rc["autoformat"])
    group_title = value_title = None
    if not isinstance(data, (list, tuple)):
        metadata = inputs._to_duck_array(data)
        if autoformat:
            value_title = inputs._meta_title(metadata)
            if metadata.ndim == 2:
                inferred = inputs._meta_labels(metadata, axis=1, always=False)
                if inferred is not None:
                    group_title = inputs._meta_title(inferred)
                    if labels is None:
                        labels = inputs._to_numpy_array(inferred).tolist()
        data = inputs._to_numpy_array(metadata, strip_units=True)
    return data, labels, group_title, value_title


def _split_distributions(data: Any) -> Iterable[ArrayLike]:
    """Use array columns or sequence elements as individual distributions."""
    if isinstance(data, (list, tuple)):
        return data if data and np.ndim(data[0]) else [data]
    values = np.ma.asarray(data)
    if values.ndim == 1:
        return (
            values
            if values.dtype == object and any(np.ndim(value) for value in values)
            else [values]
        )
    if values.ndim == 2:
        return values.T
    raise ValueError("data must be one- or two-dimensional")


def _prepare_data(
    data: Any,
    positions: ArrayLike | None,
    labels: Sequence[Any] | None,
    autoformat: bool | None,
) -> _RaincloudData:
    """Clean observations and validate group labels and positions."""
    data, labels, group_title, value_title = _infer_metadata(data, labels, autoformat)
    cleaned: list[NDArray[np.float64]] = []
    masks: list[NDArray[np.bool_]] = []
    for values in _split_distributions(data):
        if np.ndim(values) != 1:
            raise ValueError("Each distribution must be one-dimensional")
        values = np.ma.masked_invalid(np.ma.asarray(values, dtype=float))
        masks.append(~np.ma.getmaskarray(values))
        cleaned.append(values.compressed())
    n = len(cleaned)
    if not n or not any(values.size for values in cleaned):
        raise ValueError("No finite observations to plot")
    if labels is not None and (isinstance(labels, str) or len(labels) != n):
        raise ValueError("Number of labels must match number of distributions")
    positions = (
        np.arange(n, dtype=float)
        if positions is None
        else np.asarray(positions, dtype=float)
    )
    if positions.shape != (n,) or not np.all(np.isfinite(positions)):
        raise ValueError("positions must contain one finite value per distribution")
    if np.unique(positions).size != n:
        raise ValueError("positions must be distinct")
    return _RaincloudData(cleaned, masks, positions, labels, group_title, value_title)


def _prepare_styles(
    cloud_kw: Mapping[str, Any] | None,
    rain_kw: Mapping[str, Any] | None,
    box_kw: Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    """Normalize component aliases and reject options owned by the layout."""
    styles = {
        "cloud": _component_style(cloud_kw, "patch"),
        "rain": _component_style(rain_kw, "collection"),
        "box": _canonicalize_kwargs("plot.boxplot", _component_style(box_kw, "patch")),
    }
    reserved = {
        "positions",
        "orientation",
        "vert",
        "side",
        "labels",
        "tick_labels",
        "manage_ticks",
        "data",
        "cycle",
        "cycle_kw",
    }
    for name, style in styles.items():
        conflicts = reserved.intersection(style)
        if conflicts:
            raise ValueError(
                f"{name}_kw cannot override layout options: {sorted(conflicts)}"
            )
    return styles


def _group_colors(
    ax: PlotAxes,
    count: int,
    color: Any,
    cycle: Any,
    cycle_kw: Mapping[str, Any] | None,
) -> list[Any]:
    """Assign one cycle colour to all components of each group."""
    ax._parse_cycle(count, cycle=cycle, cycle_kw=cycle_kw)
    color = _resolve_color(color)
    return [
        color if color is not None else ax._get_patches_for_fill.get_next_color()
        for _ in range(count)
    ]


def _draw_cloud(
    ax: PlotAxes,
    values: NDArray[np.float64],
    position: float,
    color: Any,
    options: _RaincloudOptions,
    style: Mapping[str, Any],
) -> tuple[mcollections.PolyCollection, list[martist.Artist]]:
    """Draw one half violin and collect any optional summary artists."""
    kw = {"widths": rc["raincloud.cloud.width"], **style}
    props = _pop_props(kw, "patch")
    props.setdefault("alpha", rc["raincloud.cloud.alpha"])
    before = set(ax.get_children())
    bodies = ax.violinplot(
        [position + options.direction * options.offset],
        values[:, None],
        vert=options.vert,
        side=options.side,
        fillcolor=color,
        **kw,
    )
    if isinstance(bodies, tuple):
        bodies = bodies[0]
    body = bodies[0]
    body.update(props)
    extras = [
        artist
        for artist in ax.get_children()
        if artist not in before and artist is not body
    ]
    return body, extras


def _draw_rain(
    ax: PlotAxes,
    values: NDArray[np.float64],
    position: float,
    color: Any,
    options: _RaincloudOptions,
    style: Mapping[str, Any],
    rng: np.random.Generator,
) -> mcollections.PathCollection:
    """Draw one group's observations using the shared jitter generator."""
    locations = (
        position
        - options.direction * options.offset
        + rng.uniform(-options.jitter, options.jitter, values.size)
    )
    kw = {
        "alpha": rc["raincloud.rain.alpha"],
        "linewidths": rc["raincloud.rain.linewidth"],
        **style,
    }
    if not any(key in kw for key in ("sizes", "size")):
        kw["sizes"] = rc["raincloud.rain.markersize"]
    if not any(key in kw for key in ("colors", "facecolors")):
        kw["colors"] = color
    coords = (locations, values) if options.vert else (values, locations)
    return ax.scatter(*coords, **kw)


def _draw_box(
    ax: PlotAxes,
    values: NDArray[np.float64],
    position: float,
    color: Any,
    options: _RaincloudOptions,
    style: Mapping[str, Any],
) -> dict[str, list[martist.Artist]]:
    """Draw one distribution's boxplot at its category centre."""
    kw = {
        "facecolor": color,
        "widths": rc["raincloud.box.width"],
        "fill": rc["raincloud.box.fill"],
        "showfliers": rc["raincloud.box.showfliers"],
        "zorder": rc["raincloud.box.zorder"],
        **style,
    }
    return ax.boxplot([position], values, vert=options.vert, manage_ticks=False, **kw)


def _legend_handle(artists: Mapping[str, list[Any]], index: int) -> martist.Artist:
    """Choose the first visible component as a group's legend representative."""
    for component in ("cloud", "rain"):
        if artists[component][index] is not None:
            return artists[component][index]
    group = artists["box"][index]
    return (group.get("patches") or group["boxes"] or group["medians"])[0]


def _draw_groups(
    ax: PlotAxes,
    samples: _RaincloudData,
    options: _RaincloudOptions,
    styles: Mapping[str, Mapping[str, Any]],
    colors: Sequence[Any],
    legend: bool | str | int | None,
) -> tuple[dict[str, list[Any]], list[martist.Artist]]:
    """Compose each group in input order and preserve slots for empty groups."""
    n = len(samples.values)
    artists: dict[str, list[Any]] = {
        key: [None] * n for key in ("cloud", "rain", "box")
    }
    handles: list[martist.Artist] = []
    rng = np.random.default_rng(options.seed)
    for i, (position, values, color) in enumerate(
        zip(samples.positions, samples.values, colors)
    ):
        if not values.size:
            warnings._warn_ultraplot(
                f"Distribution {i} has no finite observations, skipping"
            )
            continue
        if options.cloud:
            body, extras = _draw_cloud(
                ax,
                values,
                position,
                color,
                options,
                _group_options(styles["cloud"], i, n),
            )
            artists["cloud"][i] = body
            if extras:
                artists.setdefault("cloud_extras", [None] * n)[i] = extras
        if options.rain:
            artists["rain"][i] = _draw_rain(
                ax,
                values,
                position,
                color,
                options,
                _filter_point_style(styles["rain"], samples.masks[i]),
                rng,
            )
        if options.box:
            artists["box"][i] = _draw_box(
                ax,
                values,
                position,
                color,
                options,
                _group_options(styles["box"], i, n),
            )
        handle = _legend_handle(artists, i)
        if samples.labels is not None or legend:
            handle.set_label(
                str(samples.labels[i] if samples.labels is not None else position)
            )
        handles.append(handle)
    return artists, handles


def _format_axes(ax: PlotAxes, samples: _RaincloudData, vert: bool) -> None:
    """Set categorical ticks and inferred titles while preserving shared axes."""
    axis = ax.xaxis if vert else ax.yaxis
    axis.set_ticks(samples.positions)
    if samples.labels is not None:
        axis.set_ticklabels(samples.labels)
    value_axis = ax.yaxis if vert else ax.xaxis
    formatting = {}
    if samples.group_title and axis.isDefault_label:
        formatting["xlabel" if vert else "ylabel"] = samples.group_title
    if samples.value_title and value_axis.isDefault_label:
        formatting["ylabel" if vert else "xlabel"] = samples.value_title
    if formatting:
        with psharing.preserve_axis_sharing():
            ax.format(**formatting)


def _update_legend(
    ax: PlotAxes,
    handles: Sequence[martist.Artist],
    group_title: str | None,
    legend: bool | str | int | None,
    legend_kw: Mapping[str, Any] | None,
) -> None:
    """Queue one legend entry per nonempty group with its inferred title."""
    legend_kw = dict(legend_kw or {})
    if group_title:
        legend_kw.setdefault("title", group_title)
    ax._update_guide(handles, legend=legend, legend_kw=legend_kw)


def raincloud(
    ax: PlotAxes,
    data: Any,
    *,
    positions: ArrayLike | None = None,
    labels: Sequence[Any] | None = None,
    orientation: Literal["vertical", "horizontal"] | None = None,
    autoformat: bool | None = None,
    legend: bool | str | int | None = None,
    legend_kw: Mapping[str, Any] | None = None,
    side: Literal["low", "high"] | None = None,
    jitter: float | None = None,
    offset: float | None = None,
    cloud: bool | None = None,
    rain: bool | None = None,
    box: bool | None = None,
    seed: int | np.random.Generator | None = None,
    color: Any = None,
    cycle: Any = None,
    cycle_kw: Mapping[str, Any] | None = None,
    cloud_kw: Mapping[str, Any] | None = None,
    rain_kw: Mapping[str, Any] | None = None,
    box_kw: Mapping[str, Any] | None = None,
) -> dict[str, list[Any]]:
    """Draw the components of :meth:`PlotAxes.raincloud`."""
    options = _resolve_options(
        orientation=orientation,
        side=side,
        jitter=jitter,
        offset=offset,
        cloud=cloud,
        rain=rain,
        box=box,
        seed=seed,
    )
    samples = _prepare_data(data, positions, labels, autoformat)
    styles = _prepare_styles(cloud_kw, rain_kw, box_kw)
    colors = _group_colors(ax, len(samples.values), color, cycle, cycle_kw)
    artists, handles = _draw_groups(ax, samples, options, styles, colors, legend)
    _format_axes(ax, samples, options.vert)
    _update_legend(ax, handles, samples.group_title, legend, legend_kw)
    return artists
