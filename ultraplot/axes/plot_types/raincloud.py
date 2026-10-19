"""Composition of half violins, observations, and boxplots."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from numbers import Number
from typing import TYPE_CHECKING, Any, Literal

from numpy.typing import ArrayLike, NDArray

import numpy as np
import matplotlib.colors as mcolors

from ... import _sharing as psharing, colors as pcolors
from ...config import rc
from ...internals import _canonicalize_kwargs, _pop_props, inputs, warnings

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
    orientation = rc["raincloud.orientation"] if orientation is None else orientation
    side = rc["raincloud.side"] if side is None else side
    jitter = rc["raincloud.jitter"] if jitter is None else jitter
    offset = rc["raincloud.offset"] if offset is None else offset
    cloud = rc["raincloud.cloud"] if cloud is None else cloud
    rain = rc["raincloud.rain"] if rain is None else rain
    box = rc["raincloud.box"] if box is None else box
    seed = rc["raincloud.seed"] if seed is None else seed
    if orientation not in ("vertical", "horizontal"):
        raise ValueError("orientation must be 'vertical' or 'horizontal'")
    if side not in ("low", "high"):
        raise ValueError("side must be 'low' or 'high'")
    for name, value in (("jitter", jitter), ("offset", offset)):
        if not np.isscalar(value) or not np.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be a finite non-negative number")
    if not any((cloud, rain, box)):
        raise ValueError("At least one of cloud, rain, or box must be enabled")

    # Arrays and labelled tables use columns; sequences of vectors permit
    # unequal sample sizes, following Matplotlib's distribution convention.
    autoformat = rc["autoformat"] if autoformat is None else autoformat
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
    if isinstance(data, (list, tuple)):
        distributions = data if data and np.ndim(data[0]) else [data]
    else:
        values = np.ma.asarray(data)
        if values.ndim == 1:
            distributions = (
                values
                if values.dtype == object and any(np.ndim(value) for value in values)
                else [values]
            )
        elif values.ndim == 2:
            distributions = values.T
        else:
            raise ValueError("data must be one- or two-dimensional")
    cleaned, masks = [], []
    for values in distributions:
        if np.ndim(values) != 1:
            raise ValueError("Each distribution must be one-dimensional")
        values = np.ma.masked_invalid(np.ma.asarray(values, dtype=float))
        valid = ~np.ma.getmaskarray(values)
        masks.append(valid)
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

    # Layout belongs to this function; component dictionaries style the artists.
    styles = [
        _component_style(cloud_kw, "patch"),
        _component_style(rain_kw, "collection"),
        _canonicalize_kwargs("plot.boxplot", _component_style(box_kw, "patch")),
    ]
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
    for name, style in zip(("cloud_kw", "rain_kw", "box_kw"), styles):
        conflicts = reserved.intersection(style)
        if conflicts:
            raise ValueError(
                f"{name} cannot override layout options: {sorted(conflicts)}"
            )

    ax._parse_cycle(n, cycle=cycle, cycle_kw=cycle_kw)
    color = _resolve_color(color)
    colors = [
        color if color is not None else ax._get_patches_for_fill.get_next_color()
        for _ in range(n)
    ]
    rng = np.random.default_rng(seed)
    vert = orientation == "vertical"
    direction = 1 if side == "high" else -1
    artists = {key: [None] * n for key in ("cloud", "rain", "box")}
    handles = []

    for i, (position, values, group_color) in enumerate(
        zip(positions, cleaned, colors)
    ):
        if not values.size:
            warnings._warn_ultraplot(
                f"Distribution {i} has no finite observations, skipping"
            )
            continue
        if cloud:
            kw = {
                "widths": rc["raincloud.cloud.width"],
                **_group_options(styles[0], i, n),
            }
            props = _pop_props(kw, "patch")
            props.setdefault("alpha", rc["raincloud.cloud.alpha"])
            before = set(ax.get_children())
            bodies = ax.violinplot(
                [position + direction * offset],
                values[:, None],
                vert=vert,
                side=side,
                fillcolor=group_color,
                **kw,
            )
            if isinstance(bodies, tuple):
                bodies = bodies[0]
            artists["cloud"][i] = bodies[0]
            bodies[0].update(props)
            extras = [
                artist
                for artist in ax.get_children()
                if artist not in before and artist is not bodies[0]
            ]
            if extras:
                artists.setdefault("cloud_extras", [None] * n)[i] = extras
        if rain:
            locations = (
                position
                - direction * offset
                + rng.uniform(-jitter, jitter, values.size)
            )
            kw = {
                "alpha": rc["raincloud.rain.alpha"],
                "linewidths": rc["raincloud.rain.linewidth"],
                **_filter_point_style(styles[1], masks[i]),
            }
            if not any(key in kw for key in ("sizes", "size")):
                kw["sizes"] = rc["raincloud.rain.markersize"]
            if not any(key in kw for key in ("colors", "facecolors")):
                kw["colors"] = group_color
            coords = (locations, values) if vert else (values, locations)
            artists["rain"][i] = ax.scatter(*coords, **kw)
        if box:
            kw = {
                "facecolor": group_color,
                "widths": rc["raincloud.box.width"],
                "fill": rc["raincloud.box.fill"],
                "showfliers": rc["raincloud.box.showfliers"],
                "zorder": rc["raincloud.box.zorder"],
                **_group_options(styles[2], i, n),
            }
            artists["box"][i] = ax.boxplot(
                [position],
                values,
                vert=vert,
                manage_ticks=False,
                **kw,
            )
        if cloud:
            handle = artists["cloud"][i]
        elif rain:
            handle = artists["rain"][i]
        else:
            group = artists["box"][i]
            handle = (group.get("patches") or group["boxes"] or group["medians"])[0]
        if labels is not None or legend:
            handle.set_label(str(labels[i] if labels is not None else position))
        handles.append(handle)

    axis = ax.xaxis if vert else ax.yaxis
    axis.set_ticks(positions)
    if labels is not None:
        axis.set_ticklabels(labels)
    value_axis = ax.yaxis if vert else ax.xaxis
    formatting = {}
    if group_title and axis.isDefault_label:
        formatting["xlabel" if vert else "ylabel"] = group_title
    if value_title and value_axis.isDefault_label:
        formatting["ylabel" if vert else "xlabel"] = value_title
    if formatting:
        with psharing.preserve_axis_sharing():
            ax.format(**formatting)
    legend_kw = dict(legend_kw or {})
    if group_title:
        legend_kw.setdefault("title", group_title)
    ax._update_guide(handles, legend=legend, legend_kw=legend_kw)
    return artists
