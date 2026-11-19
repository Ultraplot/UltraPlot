"""Area-proportional, squarified treemaps using native Matplotlib artists."""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from copy import copy
from dataclasses import dataclass
from fractions import Fraction
import math
from typing import TYPE_CHECKING, Any, TypeAlias, TypedDict, Union, cast

import matplotlib.cm as mcm
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle
from matplotlib.text import Text
import numpy as np
from numpy.typing import ArrayLike, NDArray

from ... import constructor
from ...config import rc
from ...internals import _not_none, _pop_props
from ...internals.rcsetup import (
    _validate_nonnegative_float,
    _validate_treemap_format,
    _validate_treemap_rect,
)

if TYPE_CHECKING:
    from pandas import DataFrame, Series

    from ..plot import PlotAxes

Bounds: TypeAlias = tuple[float, float, float, float]
TreemapHierarchy: TypeAlias = Mapping[Hashable, Union[float, "TreemapHierarchy"]]
TreemapInput: TypeAlias = Union[ArrayLike, TreemapHierarchy, "Series"]
TreemapData: TypeAlias = Union[Mapping[str, Any], "DataFrame"]
TreemapColor: TypeAlias = (
    str | tuple[float, float, float] | tuple[float, float, float, float]
)
TreemapColors: TypeAlias = TreemapColor | Sequence[TreemapColor] | NDArray[Any]
ValueFormat: TypeAlias = str | Callable[[float], str]
NodePath: TypeAlias = tuple[Hashable, ...]


class TreemapResult(TypedDict):
    """Treemap artists and metadata, with leaves in their original input order."""

    patches: list[Rectangle]
    texts: list[Text | None]
    groups: list[Rectangle]
    group_texts: list[Text]
    paths: list[NodePath]
    values: list[float]
    mappable: mcm.ScalarMappable | None


@dataclass
class _Node:
    label: str
    value: float | Fraction
    path: NodePath
    children: tuple[_Node, ...] = ()

    def leaves(self) -> Iterator[_Node]:
        if self.children:
            for child in self.children:
                yield from child.leaves()
        elif self.value > 0:
            yield self


def _nodes(
    sizes: TreemapInput,
    labels: Sequence[Any] | None = None,
    path: NodePath = (),
) -> list[_Node]:
    """Validate the complete hierarchy before adding any artists."""
    if isinstance(sizes, Mapping) or (
        labels is None and getattr(sizes, "ndim", None) == 1 and hasattr(sizes, "items")
    ):
        if labels is not None:
            raise ValueError("Mapping inputs already supply their labels.")
        result = []
        # Series is duck-typed so pandas remains an optional dependency.
        for key, value in cast(Mapping[Hashable, Any], sizes).items():
            child_path = (*path, key)
            if isinstance(value, Mapping):
                children = _nodes(cast(TreemapHierarchy, value), path=child_path)
                try:
                    total = math.fsum(child.value for child in children)
                except OverflowError:
                    # Only group totals can exceed float range. Preserve leaf
                    # values for labels, formatting, and colormap normalization.
                    total = sum(Fraction(child.value) for child in children)
                result.append(_Node(str(key), total, child_path, tuple(children)))
            else:
                result.append(
                    _Node(str(key), _validate_nonnegative_float(value), child_path)
                )
    else:
        try:
            values = np.ma.asarray(sizes, dtype=float).filled(np.nan)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "sizes must be a one-dimensional numeric sequence."
            ) from exc
        if values.ndim != 1:
            raise ValueError("sizes must be a one-dimensional numeric sequence.")
        if labels is None:
            labels = [""] * len(values)
        elif isinstance(labels, str):
            labels = [labels] * len(values)
        if len(labels) != len(values):
            raise ValueError("labels must have the same length as sizes.")
        result = [
            _Node(str(label), _validate_nonnegative_float(value), (index,))
            for index, (value, label) in enumerate(zip(values, labels))
        ]
    if not result or not any(node.value > 0 for node in result):
        raise ValueError("sizes must contain at least one positive value.")
    return result


def _squarify(nodes: Sequence[_Node], rect: Bounds) -> list[tuple[_Node, Bounds]]:
    """Tile a rectangle with compact strips, retaining each node's identity."""
    x, y, width, height = rect
    ordered = sorted((node for node in nodes if node.value > 0), key=lambda n: -n.value)
    scale = max(node.value for node in ordered)
    if isinstance(scale, Fraction):
        weights = [float(Fraction(node.value) / scale) for node in ordered]
    else:
        weights = [node.value / scale for node in ordered]
    # Use fractions of the remaining rectangle so rounding in a large strip
    # cannot inflate the dimensions of a much smaller tile that follows it.
    remaining = [0.0] * (len(weights) + 1)
    for i in reversed(range(len(weights))):
        remaining[i] = remaining[i + 1] + weights[i]

    result: list[tuple[_Node, Bounds]] = []
    start = 0
    while start < len(ordered):
        vertical = width >= height
        long, short = (width, height) if vertical else (height, width)
        total = remaining[start]
        if total == 0 or short == 0:
            result.extend((node, (x, y, 0.0, 0.0)) for node in ordered[start:])
            break

        def worst(weight: float, smallest: float) -> float:
            strip = long * (weight / total)
            narrow = short * (smallest / weight)
            wide = short * (weights[start] / weight)
            return max(wide / strip, strip / narrow) if strip and narrow else math.inf

        end = start + 1
        weight = weights[start]
        score = worst(weight, weight)
        while end < len(ordered) and weights[end] > 0:
            candidate = weight + weights[end]
            next_score = worst(candidate, weights[end])
            if next_score > score:
                break
            weight, score = candidate, next_score
            end += 1

        strip = long * min(1.0, weight / total)
        offset = y if vertical else x
        for i in range(start, end):
            length = short * (weights[i] / weight)
            box = (x, offset, strip, length) if vertical else (offset, y, length, strip)
            result.append((ordered[i], box))
            offset += length
        if vertical:
            x += strip
            width = long * (remaining[end] / total)
        else:
            y += strip
            height = long * (remaining[end] / total)
        start = end
    return result


def _inset(rect: Bounds, pad: float) -> Bounds:
    x, y, width, height = rect
    inset = min(pad / 2, width * 0.2, height * 0.2)
    return x + inset, y + inset, width - 2 * inset, height - 2 * inset


def _style(
    category: str, kind: str, options: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Canonicalize aliases before explicit properties override rc defaults."""
    defaults = rc.category("treemap." + category)
    props = dict(options or {})
    props.update(_pop_props(props, kind))
    return {**_pop_props(defaults, kind), **props}


def _composite(foreground, background):
    rgb = np.asarray(foreground[:3])
    alpha = foreground[3]
    return rgb * alpha + background * (1 - alpha)


def _label_style(style, background):
    color = style["color"]
    if isinstance(color, str) and color.lower() == "auto":
        luminance = np.dot(background, [0.2126, 0.7152, 0.0722])
        return {**style, "color": "#18212b" if luminance > 0.5 else "white"}
    return style


@contextmanager
def _draw_transaction(ax):
    """Restore artists, data bounds, and cycle positions if a style fails."""
    existing = set(ax.get_children())
    bounds = ax.dataLim.frozen()
    ignore_limits = ax.ignore_existing_data_limits
    cycles = ax._active_cycle, copy(ax._get_lines), copy(ax._get_patches_for_fill)
    try:
        yield
    except Exception:
        for artist in reversed(ax.get_children()):
            if artist not in existing:
                if isinstance(artist, Text):
                    ax._register_align_text(artist, False)
                artist.remove()
        ax.dataLim.set(bounds)
        ax.dataLim.minpos[:] = bounds.minpos
        ax.ignore_existing_data_limits = ignore_limits
        ax._active_cycle, ax._get_lines, ax._get_patches_for_fill = cycles
        raise


def treemap(
    ax: PlotAxes,
    sizes: TreemapInput,
    labels: Sequence[Any] | None = None,
    *,
    color: TreemapColors | None = None,
    cmap: str | mcolors.Colormap | None = None,
    norm: mcolors.Normalize | None = None,
    vmin: float | None = None,
    vmax: float | None = None,
    rect: Bounds | None = None,
    pad: float | None = None,
    group_pad: float | None = None,
    group_labels: bool | None = None,
    show_values: bool | None = None,
    value_format: ValueFormat | None = None,
    text_kw: Mapping[str, Any] | None = None,
    group_kw: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> TreemapResult:
    """Resolve rc defaults and draw :meth:`PlotAxes.treemap`."""
    rect = _validate_treemap_rect(_not_none(rect, rc["treemap.rect"]))
    pad = _validate_nonnegative_float(_not_none(pad, rc["treemap.pad"]))
    group_pad = _validate_nonnegative_float(
        _not_none(group_pad, rc["treemap.group_pad"])
    )
    group_labels = cast(bool, _not_none(group_labels, rc["treemap.group_labels"]))
    show_values = cast(bool, _not_none(show_values, rc["treemap.show_values"]))
    value_format = _validate_treemap_format(
        _not_none(value_format, rc["treemap.value_format"])
    )
    if not ax.transData.is_affine:
        raise ValueError("treemap requires Cartesian axes with linear scales.")
    nodes = _nodes(sizes, labels)
    style = _style("patch", "patch", kwargs)
    color = _not_none(
        color=color,
        colors=style.pop("color", None),
        facecolor=style.pop("facecolor", None),
    )
    if color is not None and cmap is not None:
        raise ValueError("Use either color or cmap, not both.")
    leaves = [leaf for node in nodes for leaf in node.leaves()]
    values = np.array([node.value for node in leaves])
    mappable: mcm.ScalarMappable | None = None
    colors: NDArray[np.float64] | None = None
    if cmap is None and any(option is not None for option in (norm, vmin, vmax)):
        raise ValueError("norm, vmin, and vmax require cmap.")
    if cmap is not None:
        if norm is None:
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        elif vmin is not None or vmax is not None:
            raise ValueError("vmin/vmax cannot be combined with an explicit norm.")
        mappable = mcm.ScalarMappable(norm=norm, cmap=constructor.Colormap(cmap))
        mappable.set_array(values)
        mappable.autoscale_None()
        colors = mappable.to_rgba(values)
    elif color is not None:
        colors = mcolors.to_rgba_array([color] if isinstance(color, str) else color)
        if len(colors) == 0:
            raise ValueError("color must contain at least one color.")
    parent_style = _style("group", "patch", group_kw)
    text_style: dict[str, Any] = {
        "ha": "center",
        "va": "center",
        "clip_on": True,
        **_style("text", "text", text_kw),
    }
    group_text_style = _style("group.text", "text")
    group_text_style.update(ha="left", va="center", clip_on=True)

    # Format all values before drawing so a bad formatter leaves the axes untouched.
    labels = [node.label for node in leaves]
    if show_values:
        formatter = value_format if callable(value_format) else value_format.format
        labels = [
            "\n".join(filter(None, (node.label, str(formatter(node.value)))))
            for node in leaves
        ]

    result: TreemapResult = {
        "patches": [],
        "texts": [],
        "groups": [],
        "group_texts": [],
        "paths": [node.path for node in leaves],
        "values": values.tolist(),
        "mappable": mappable,
    }
    tiles: dict[int, tuple[Bounds, NDArray[np.float64], NDArray[np.float64]]] = {}

    def layout(
        branch: Sequence[_Node],
        bounds: Bounds,
        background: NDArray[np.float64],
        base_color: TreemapColor | None = None,
    ) -> None:
        # Sorting determines positions only. Assign colors in input order.
        boxes = {id(node): box for node, box in _squarify(branch, bounds)}
        for index, node in enumerate(node for node in branch if node.value > 0):
            box = boxes[id(node)]
            hue = base_color
            if hue is None:
                hue = (
                    ax._get_patches_for_fill.get_next_color()
                    if colors is None or node.children
                    else "none"
                )
            if node.children:
                box = _inset(box, group_pad)
                x, y, width, height = box
                group_style: dict[str, Any] = {"facecolor": hue, **parent_style}
                patch = Rectangle((x, y), width, height, **group_style)
                ax.add_patch(patch)
                result["groups"].append(patch)
                inner = _inset(box, group_pad)
                header = min(0.05 * rect[3], inner[3] * 0.18) if group_labels else 0
                group_background = _composite(patch.get_facecolor(), background)
                if group_labels:
                    label = ax.text(
                        inner[0],
                        inner[1] + inner[3] - header / 2,
                        node.label,
                        **_label_style(group_text_style, group_background),
                    )
                    label.set_clip_path(patch)
                    result["group_texts"].append(label)
                layout(
                    node.children,
                    (*inner[:3], inner[3] - header),
                    group_background,
                    hue,
                )
            else:
                rgba = np.array(mcolors.to_rgba(hue))
                blend = 0.10 + 0.12 * (index % 4) if base_color is not None else 0
                rgba[:3] = rgba[:3] * (1 - blend) + blend
                tiles[id(node)] = _inset(box, pad), rgba, background

    # The axes frame is hidden for treemaps, exposing the figure background.
    background = _composite(ax.figure.get_facecolor(), np.ones(3))
    with _draw_transaction(ax):
        style = ax._parse_cycle(sum(node.value > 0 for node in nodes), **style)
        layout(nodes, rect, background)
        # Draw leaves in input order; only layout needs size sorting.
        for index, (node, label) in enumerate(zip(leaves, labels)):
            (x, y, width, height), default_color, background = tiles[id(node)]
            rgba = default_color if colors is None else colors[index % len(colors)]
            leaf_style: dict[str, Any] = {"facecolor": rgba, **style}
            patch = Rectangle((x, y), width, height, **leaf_style)
            ax.add_patch(patch)
            text = None
            if label:
                options = _label_style(
                    text_style, _composite(patch.get_facecolor(), background)
                )
                text = ax.text(x + width / 2, y + height / 2, label, **options)
                text.set_clip_path(patch)
            result["patches"].append(patch)
            result["texts"].append(text)
    ax.set_xlim(rect[0], rect[0] + rect[2])
    ax.set_ylim(rect[1], rect[1] + rect[3])
    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()
    return result
