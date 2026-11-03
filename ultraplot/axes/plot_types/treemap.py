"""Area-proportional, squarified treemaps using native Matplotlib artists."""

from collections.abc import Mapping
from dataclasses import dataclass
import math

import matplotlib.cm as mcm
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle
import numpy as np

from ... import constructor
from ...config import rc
from ...internals import _pop_props


@dataclass
class _Node:
    label: str
    value: float
    path: tuple
    children: tuple = ()


def _nodes(sizes, labels=None, path=()):
    """Validate the complete hierarchy before adding any artists."""
    if isinstance(sizes, Mapping) or (
        getattr(sizes, "ndim", None) == 1 and hasattr(sizes, "items")
    ):
        if labels is not None:
            raise ValueError("Mapping and Series inputs already supply their labels.")
        result = []
        for key, value in sizes.items():
            child_path = (*path, key)
            if isinstance(value, Mapping):
                children = _nodes(value, path=child_path)
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


def _value(value):
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("sizes must contain finite, nonnegative numbers.") from exc
    if not math.isfinite(value) or value < 0:
        raise ValueError("sizes must contain finite, nonnegative numbers.")
    return value


def _squarify(nodes, rect):
    """Tile a rectangle with compact strips, retaining each node's identity."""
    x, y, width, height = rect
    ordered = sorted((node for node in nodes if node.value > 0), key=lambda n: -n.value)
    scale = max(node.value for node in ordered)
    weights = [node.value / scale for node in ordered]
    total = math.fsum(weights)
    areas = [weight / total * width * height for weight in weights]
    result = []

    def worst(row, side):
        total = math.fsum(area for _, area in row)
        smallest = min(area for _, area in row)
        largest = max(area for _, area in row)
        return max(
            side * side * largest / total**2, total**2 / (side * side * smallest)
        )

    def place(row, x, y, width, height):
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

    row = []
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


def _inset(rect, pad):
    x, y, width, height = rect
    inset = min(pad / 2, width * 0.2, height * 0.2)
    return x + inset, y + inset, width - 2 * inset, height - 2 * inset


def treemap(
    ax,
    sizes,
    labels=None,
    *,
    color=None,
    cmap=None,
    norm=None,
    vmin=None,
    vmax=None,
    rect=(0, 0, 1, 1),
    pad=0.008,
    group_pad=0.018,
    group_labels=True,
    show_values=False,
    value_format="{:g}",
    text_kw=None,
    group_kw=None,
    **kwargs,
):
    if not ax.transData.is_affine:
        raise ValueError("treemap requires Cartesian axes with linear scales.")
    nodes = _nodes(sizes, labels)
    rect = np.asarray(rect, dtype=float)
    if rect.shape != (4,) or not np.all(np.isfinite(rect)) or np.any(rect[2:] <= 0):
        raise ValueError("rect must be (x, y, width, height) with positive dimensions.")
    if not np.isfinite(pad) or pad < 0 or not np.isfinite(group_pad) or group_pad < 0:
        raise ValueError("pad and group_pad must be finite and nonnegative.")
    if color is not None and cmap is not None:
        raise ValueError("Use either color or cmap, not both.")
    if not callable(value_format) and not isinstance(value_format, str):
        raise ValueError("value_format must be a format string or callable.")

    leaves = []

    def collect(branch):
        for node in branch:
            if node.children:
                collect(node.children)
            elif node.value > 0:
                leaves.append(node)

    collect(nodes)
    values = np.array([node.value for node in leaves])
    mappable = None
    colors = {}
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

    style = dict(kwargs)
    style.update(_pop_props(style, "patch"))
    style.setdefault("edgecolor", "white")
    style.setdefault("linewidth", 0.6)
    parent_style = dict(group_kw or {})
    parent_style.update(_pop_props(parent_style, "patch"))
    parent_style.setdefault("edgecolor", "white")
    parent_style.setdefault("linewidth", 1.2)
    text_style = dict(text_kw or {})
    text_style.setdefault("fontsize", 9)
    text_style.setdefault("ha", "center")
    text_style.setdefault("va", "center")
    text_style.setdefault("clip_on", True)

    # Format all values before drawing so a bad formatter leaves the axes untouched.
    formatted = {}
    if show_values:
        for node in leaves:
            formatted[id(node)] = str(
                value_format(node.value)
                if callable(value_format)
                else value_format.format(node.value)
            )

    result = {
        "patches": [],
        "texts": [],
        "groups": [],
        "group_texts": [],
        "paths": [],
        "values": [],
        "mappable": mappable,
    }
    drawn = {}

    def draw(branch, bounds, base_color=None):
        for index, (node, box) in enumerate(_squarify(branch, bounds)):
            hue = base_color if base_color is not None else cycle[index % len(cycle)]
            if node.children:
                box = _inset(box, group_pad)
                x, y, width, height = box
                group_style = {"facecolor": hue, "alpha": 0.12, **parent_style}
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
                        fontsize=10,
                        fontweight="bold",
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
                patch = Rectangle((x, y), width, height, **{"facecolor": rgba, **style})
                ax.add_patch(patch)
                text = node.label
                if show_values:
                    text = "\n".join(filter(None, [text, formatted[id(node)]]))
                artist = None
                if text:
                    luminance = np.dot(
                        patch.get_facecolor()[:3], [0.2126, 0.7152, 0.0722]
                    )
                    options = {
                        "color": "#18212b" if luminance > 0.5 else "white",
                        **text_style,
                    }
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
