"""Area-proportional, squarified treemaps using native Matplotlib artists."""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterator, Mapping, Sequence
from dataclasses import dataclass
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
    value: float
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
        getattr(sizes, "ndim", None) == 1 and hasattr(sizes, "items")
    ):
        if labels is not None:
            raise ValueError("Mapping and Series inputs already supply their labels.")
        result = []
        # Series is duck-typed so pandas remains an optional dependency.
        for key, value in cast(Mapping[Hashable, Any], sizes).items():
            child_path = (*path, key)
            if isinstance(value, Mapping):
                children = _nodes(cast(TreemapHierarchy, value), path=child_path)
                total = math.fsum(child.value for child in children)
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
        elif isinstance(labels, str) or len(labels) != len(values):
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
    weights = [node.value / scale for node in ordered]
    total = math.fsum(weights)
    areas = [weight / total * width * height for weight in weights]
    result: list[tuple[_Node, Bounds]] = []

    def worst(row: list[tuple[_Node, float]], side: float) -> float:
        total = math.fsum(area for _, area in row)
        smallest = min(area for _, area in row)
        largest = max(area for _, area in row)
        return max(
            side * side * largest / total**2, total**2 / (side * side * smallest)
        )

    def place(row: list[tuple[_Node, float]], bounds: Bounds) -> Bounds:
        x, y, width, height = bounds
        area = math.fsum(size for _, size in row)
        vertical = width >= height
        strip = area / min(width, height)
        offset = y if vertical else x
        for node, size in row:
            length = size / strip
            box = (x, offset, strip, length) if vertical else (offset, y, length, strip)
            result.append((node, box))
            offset += length
        return (
            (x + strip, y, max(0, width - strip), height)
            if vertical
            else (x, y + strip, width, max(0, height - strip))
        )

    row: list[tuple[_Node, float]] = []
    for node, area in zip(ordered, areas):
        candidate = [*row, (node, area)]
        if row and worst(candidate, min(width, height)) > worst(
            row, min(width, height)
        ):
            x, y, width, height = place(row, (x, y, width, height))
            row = []
        row.append((node, area))
    if row:
        place(row, (x, y, width, height))
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
    if color is not None and cmap is not None:
        raise ValueError("Use either color or cmap, not both.")
    leaves = [leaf for node in nodes for leaf in node.leaves()]
    values = np.array([node.value for node in leaves])
    mappable: mcm.ScalarMappable | None = None
    colors: NDArray[np.float64] | None = None
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
        colors = mcolors.to_rgba_array(color)
        if len(colors) not in (1, len(leaves)):
            raise ValueError(
                "color must be a single color or one color per nonzero leaf."
            )
    elif norm is not None or vmin is not None or vmax is not None:
        raise ValueError("norm, vmin, and vmax require cmap.")
    cycle = constructor.Cycle(rc["cycle"]).by_key()["color"]

    style = _style("patch", "patch", kwargs)
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
    tiles: dict[int, tuple[Bounds, NDArray[np.float64]]] = {}

    def layout(
        branch: Sequence[_Node], bounds: Bounds, base_color: TreemapColor | None = None
    ) -> None:
        for index, (node, box) in enumerate(_squarify(branch, bounds)):
            hue = base_color if base_color is not None else cycle[index % len(cycle)]
            if node.children:
                box = _inset(box, group_pad)
                x, y, width, height = box
                group_style: dict[str, Any] = {"facecolor": hue, **parent_style}
                patch = Rectangle((x, y), width, height, **group_style)
                ax.add_patch(patch)
                result["groups"].append(patch)
                inner = _inset(box, group_pad)
                header = min(0.05 * rect[3], inner[3] * 0.18) if group_labels else 0
                if group_labels:
                    label = ax.text(
                        inner[0],
                        inner[1] + inner[3] - header / 2,
                        node.label,
                        **group_text_style,
                    )
                    label.set_clip_path(patch)
                    result["group_texts"].append(label)
                layout(node.children, (*inner[:3], inner[3] - header), hue)
            else:
                rgb = np.array(mcolors.to_rgb(hue))
                blend = 0.10 + 0.12 * (index % 4) if base_color is not None else 0
                tiles[id(node)] = _inset(box, pad), rgb * (1 - blend) + blend

    layout(nodes, rect)
    # Draw leaves in input order; only layout needs size sorting.
    for index, (node, label) in enumerate(zip(leaves, labels)):
        (x, y, width, height), default_color = tiles[id(node)]
        rgba = default_color if colors is None else colors[index % len(colors)]
        leaf_style: dict[str, Any] = {"facecolor": rgba, **style}
        patch = Rectangle((x, y), width, height, **leaf_style)
        ax.add_patch(patch)
        text = None
        if label:
            options = dict(text_style)
            if isinstance(options["color"], str) and options["color"].lower() == "auto":
                luminance = np.dot(patch.get_facecolor()[:3], [0.2126, 0.7152, 0.0722])
                options["color"] = "#18212b" if luminance > 0.5 else "white"
            text = ax.text(x + width / 2, y + height / 2, label, **options)
            text.set_clip_path(patch)
        result["patches"].append(patch)
        result["texts"].append(text)
    ax.set_xlim(rect[0], rect[0] + rect[2])
    ax.set_ylim(rect[1], rect[1] + rect[3])
    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()
    return result
