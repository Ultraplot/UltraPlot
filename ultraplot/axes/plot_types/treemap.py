"""Area-proportional, squarified treemaps using native Matplotlib artists."""

from __future__ import annotations

from collections.abc import Callable, Hashable, Mapping, Sequence
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
                result.append(_Node(str(key), _value(value), child_path))
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
            _Node(str(label), _value(value), (index,))
            for index, (value, label) in enumerate(zip(values, labels))
        ]
    if not result or not any(node.value > 0 for node in result):
        raise ValueError("sizes must contain at least one positive value.")
    return result


def _value(value: Any) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("sizes must contain finite, nonnegative numbers.") from exc
    if not math.isfinite(value) or value < 0:
        raise ValueError("sizes must contain finite, nonnegative numbers.")
    return value


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

    def place(
        row: list[tuple[_Node, float]],
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> Bounds:
        area = math.fsum(size for _, size in row)
        if width >= height:
            strip = area / height
            offset = y
            for node, size in row:
                length = size / strip
                result.append((node, (x, offset, strip, length)))
                offset += length
            return x + strip, y, max(0, width - strip), height
        strip = area / width
        offset = x
        for node, size in row:
            length = size / strip
            result.append((node, (offset, y, length, strip)))
            offset += length
        return x, y + strip, width, max(0, height - strip)

    row: list[tuple[_Node, float]] = []
    for node, area in zip(ordered, areas):
        candidate = [*row, (node, area)]
        if row and worst(candidate, min(width, height)) > worst(
            row, min(width, height)
        ):
            x, y, width, height = place(row, x, y, width, height)
            row = []
        row.append((node, area))
    if row:
        place(row, x, y, width, height)
    return result


def _inset(rect: Bounds, pad: float) -> Bounds:
    x, y, width, height = rect
    inset = min(pad / 2, width * 0.2, height * 0.2)
    return x + inset, y + inset, width - 2 * inset, height - 2 * inset


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
    rect = cast(Bounds, _not_none(rect, rc["treemap.rect"]))
    pad = cast(float, _not_none(pad, rc["treemap.pad"]))
    group_pad = cast(float, _not_none(group_pad, rc["treemap.group_pad"]))
    group_labels = cast(bool, _not_none(group_labels, rc["treemap.group_labels"]))
    show_values = cast(bool, _not_none(show_values, rc["treemap.show_values"]))
    value_format = cast(
        ValueFormat, _not_none(value_format, rc["treemap.value_format"])
    )
    if not ax.transData.is_affine:
        raise ValueError("treemap requires Cartesian axes with linear scales.")
    nodes = _nodes(sizes, labels)
    rect_array = np.asarray(rect, dtype=float)
    if (
        rect_array.shape != (4,)
        or not np.all(np.isfinite(rect_array))
        or np.any(rect_array[2:] <= 0)
    ):
        raise ValueError("rect must be (x, y, width, height) with positive dimensions.")
    rect = (
        float(rect_array[0]),
        float(rect_array[1]),
        float(rect_array[2]),
        float(rect_array[3]),
    )
    if not np.isfinite(pad) or pad < 0 or not np.isfinite(group_pad) or group_pad < 0:
        raise ValueError("pad and group_pad must be finite and nonnegative.")
    if color is not None and cmap is not None:
        raise ValueError("Use either color or cmap, not both.")
    if not callable(value_format) and not isinstance(value_format, str):
        raise ValueError("value_format must be a format string or callable.")

    leaves: list[_Node] = []

    def collect(branch: Sequence[_Node]) -> None:
        for node in branch:
            if node.children:
                collect(node.children)
            elif node.value > 0:
                leaves.append(node)

    collect(nodes)
    values = np.array([node.value for node in leaves])
    mappable: mcm.ScalarMappable | None = None
    colors: dict[int, NDArray[np.float64]] = {}
    if cmap is not None:
        if norm is None:
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        elif vmin is not None or vmax is not None:
            raise ValueError("vmin/vmax cannot be combined with an explicit norm.")
        mappable = mcm.ScalarMappable(norm=norm, cmap=constructor.Colormap(cmap))
        mappable.set_array(values)
        mappable.autoscale_None()
        colors = {
            id(node): rgba for node, rgba in zip(leaves, mappable.to_rgba(values))
        }
    elif color is not None:
        rgba = mcolors.to_rgba_array(color)
        if len(rgba) not in (1, len(leaves)):
            raise ValueError(
                "color must be a single color or one color per nonzero leaf."
            )
        colors = {id(node): rgba[i % len(rgba)] for i, node in enumerate(leaves)}
    elif norm is not None or vmin is not None or vmax is not None:
        raise ValueError("norm, vmin, and vmax require cmap.")
    cycle = constructor.Cycle(rc["cycle"]).by_key()["color"]

    style: dict[str, Any] = dict(kwargs)
    style.update(_pop_props(style, "patch"))
    style.setdefault("edgecolor", rc["treemap.patch.edgecolor"])
    style.setdefault("linewidth", rc["treemap.patch.linewidth"])
    parent_style: dict[str, Any] = dict(group_kw or {})
    parent_style.update(_pop_props(parent_style, "patch"))
    parent_style.setdefault("edgecolor", rc["treemap.group.edgecolor"])
    parent_style.setdefault("linewidth", rc["treemap.group.linewidth"])
    parent_style.setdefault("alpha", rc["treemap.group.alpha"])
    text_style: dict[str, Any] = dict(text_kw or {})
    text_style.update(_pop_props(text_style, "text"))
    text_style.setdefault("fontsize", rc["treemap.text.size"])
    text_style.setdefault("color", rc["treemap.text.color"])
    text_style.setdefault("ha", "center")
    text_style.setdefault("va", "center")
    text_style.setdefault("clip_on", True)

    # Format all values before drawing so a bad formatter leaves the axes untouched.
    formatted: dict[int, str] = {}
    if show_values:
        for node in leaves:
            formatted[id(node)] = str(
                value_format(node.value)
                if callable(value_format)
                else value_format.format(node.value)
            )

    result: TreemapResult = {
        "patches": [],
        "texts": [],
        "groups": [],
        "group_texts": [],
        "paths": [],
        "values": [],
        "mappable": mappable,
    }
    drawn: dict[int, tuple[Rectangle, Text | None]] = {}

    def draw(
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
                        fontsize=rc["treemap.group.text.size"],
                        fontweight=rc["treemap.group.text.weight"],
                        ha="left",
                        va="center",
                        clip_on=True,
                    )
                    label.set_clip_path(patch)
                    result["group_texts"].append(label)
                draw(node.children, (*inner[:3], inner[3] - header), hue)
            else:
                x, y, width, height = _inset(box, pad)
                rgba = colors.get(id(node))
                if rgba is None:
                    # Related leaves share a hue, with gentle categorical shades.
                    rgb = np.array(mcolors.to_rgb(hue))
                    blend = 0.10 + 0.12 * (index % 4) if base_color is not None else 0
                    rgba = rgb * (1 - blend) + blend
                leaf_style: dict[str, Any] = {"facecolor": rgba, **style}
                patch = Rectangle((x, y), width, height, **leaf_style)
                ax.add_patch(patch)
                text = node.label
                if show_values:
                    text = "\n".join(filter(None, [text, formatted[id(node)]]))
                artist = None
                if text:
                    luminance = np.dot(
                        patch.get_facecolor()[:3], [0.2126, 0.7152, 0.0722]
                    )
                    options = dict(text_style)
                    if (
                        isinstance(options["color"], str)
                        and options["color"].lower() == "auto"
                    ):
                        options["color"] = "#18212b" if luminance > 0.5 else "white"
                    artist = ax.text(x + width / 2, y + height / 2, text, **options)
                    artist.set_clip_path(patch)
                drawn[id(node)] = patch, artist

    draw(nodes, rect)
    # Public results retain input order even though the layout sorts by size.
    for node in leaves:
        patch, text = drawn[id(node)]
        result["patches"].append(patch)
        result["texts"].append(text)
        result["paths"].append(node.path)
        result["values"].append(node.value)
    ax.set_xlim(rect[0], rect[0] + rect[2])
    ax.set_ylim(rect[1], rect[1] + rect[3])
    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()
    return result
