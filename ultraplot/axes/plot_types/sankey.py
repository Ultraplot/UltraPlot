# Helper tools for layered sankey diagrams.
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from matplotlib import colors as mcolors
from matplotlib import patches as mpatches
from matplotlib import path as mpath


@dataclass
class SankeyDiagram:
    nodes: dict[Any, mpatches.Patch]
    flows: list[mpatches.PathPatch]
    labels: dict[Any, Any]
    layout: dict[str, Any]


def _tint(color: Any, amount: float) -> tuple[float, float, float]:
    """Return a lightened version of a base color."""
    r, g, b = mcolors.to_rgb(color)
    return (
        (1 - amount) * r + amount,
        (1 - amount) * g + amount,
        (1 - amount) * b + amount,
    )


def _normalize_nodes(
    nodes: Any, flows: Sequence[Mapping[str, Any]]
) -> tuple[dict[Any, dict[str, Any]], list[Any]]:
    """Normalize node definitions into a map and stable order list."""
    # Infer node order from the first occurrence in flows.
    if nodes is None:
        order = []
        seen = set()
        for flow in flows:
            for key in (flow["source"], flow["target"]):
                if key not in seen:
                    seen.add(key)
                    order.append(key)
        nodes = order

    # Normalize nodes to a dict keyed by node id.
    node_map = {}
    order = []
    if isinstance(nodes, dict):
        nodes = [{"id": key, **value} for key, value in nodes.items()]
    for node in nodes:
        if isinstance(node, dict):
            node_id = node.get("id", node.get("name"))
            if node_id is None:
                raise ValueError("Node dicts must include an 'id' or 'name'.")
            label = node.get("label", str(node_id))
            color = node.get("color", None)
        else:
            node_id = node
            label = str(node_id)
            color = None
        node_map[node_id] = {"id": node_id, "label": label, "color": color}
        order.append(node_id)
    return node_map, order


def _normalize_flows(flows: Any) -> list[dict[str, Any]]:
    """Normalize flow definitions into a list of dicts."""
    if flows is None:
        raise ValueError("Flows are required to draw a sankey diagram.")
    normalized = []
    for flow in flows:
        # Support dict flows or tuple-like flows.
        if isinstance(flow, dict):
            source = flow["source"]
            target = flow["target"]
            value = flow["value"]
            label = flow.get("label", None)
            color = flow.get("color", None)
        else:
            if len(flow) < 3:
                raise ValueError(
                    "Flow tuples must have at least (source, target, value)."
                )
            source, target, value = flow[:3]
            label = flow[3] if len(flow) > 3 else None
            color = flow[4] if len(flow) > 4 else None
        if value is None or value < 0:
            raise ValueError("Flow values must be non-negative.")
        if value == 0:
            continue
        # Store a consistent flow record for downstream layout/drawing.
        normalized.append(
            {
                "source": source,
                "target": target,
                "value": float(value),
                "label": label,
                "color": color,
                "group": flow.get("group", None) if isinstance(flow, dict) else None,
            }
        )
    if not normalized:
        raise ValueError("Flows must include at least one non-zero value.")
    return normalized


def _assign_layers(
    flows: Sequence[Mapping[str, Any]],
    nodes: Sequence[Any],
    layers: Mapping[Any, int] | None,
) -> dict[Any, int]:
    """Assign layer indices for nodes using a DAG topological pass."""
    if layers is not None:
        # Honor explicit layer assignments when provided.
        layer_map = dict(layers)
        missing = [node for node in nodes if node not in layer_map]
        if missing:
            raise ValueError(f"Missing layer assignments for nodes: {missing}")
        return layer_map

    # Build adjacency for a simple topological layer assignment.
    successors = {node: set() for node in nodes}
    predecessors = {node: set() for node in nodes}
    for flow in flows:
        source = flow["source"]
        target = flow["target"]
        successors[source].add(target)
        predecessors[target].add(source)

    layer_map = {node: 0 for node in nodes}
    indegree = {node: len(preds) for node, preds in predecessors.items()}
    queue = [node for node, deg in indegree.items() if deg == 0]
    visited = 0
    # Kahn's algorithm to assign layers from sources outward.
    while queue:
        node = queue.pop(0)
        visited += 1
        for succ in successors[node]:
            layer_map[succ] = max(layer_map[succ], layer_map[node] + 1)
            indegree[succ] -= 1
            if indegree[succ] == 0:
                queue.append(succ)
    if visited != len(nodes):
        raise ValueError("Sankey nodes must form a directed acyclic graph.")
    return layer_map


def _compute_layout(
    nodes: Sequence[Any],
    flows: Sequence[Mapping[str, Any]],
    *,
    node_pad: float,
    node_width: float,
    align: str,
    layers: Mapping[Any, int] | None,
    margin: float,
    layer_order: Sequence[int] | None = None,
) -> tuple[
    dict[str, Any],
    dict[Any, list[dict[str, Any]]],
    dict[Any, list[dict[str, Any]]],
    dict[Any, float],
]:
    """Compute node and flow layout geometry in axes-relative coordinates."""
    # Split flows into incoming/outgoing for node sizing.
    flow_in = {node: [] for node in nodes}
    flow_out = {node: [] for node in nodes}
    for flow in flows:
        flow_out[flow["source"]].append(flow)
        flow_in[flow["target"]].append(flow)

    node_value = {}
    for node in nodes:
        incoming = sum(flow["value"] for flow in flow_in[node])
        outgoing = sum(flow["value"] for flow in flow_out[node])
        # Nodes size to the larger of in/out totals.
        node_value[node] = max(incoming, outgoing)

    layer_map = _assign_layers(flows, nodes, layers)
    max_layer = max(layer_map.values()) if layer_map else 0
    if layer_order is None:
        layer_order = sorted(set(layer_map.values()))
    # Group nodes by layer in the desired order.
    grouped = {layer: [] for layer in layer_order}
    for node in nodes:
        grouped[layer_map[node]].append(node)

    height_available = 1.0 - 2 * margin
    layer_totals = []
    for layer, layer_nodes in grouped.items():
        total = sum(node_value[node] for node in layer_nodes)
        total += node_pad * max(len(layer_nodes) - 1, 0)
        layer_totals.append(total)
    scale = height_available / max(layer_totals) if layer_totals else 1.0

    # Lay out nodes within each layer using the same scale.
    layout = {"nodes": {}, "scale": scale, "layers": layer_map}
    for layer in layer_order:
        layer_nodes = grouped[layer]
        total = sum(node_value[node] for node in layer_nodes) * scale
        total += node_pad * max(len(layer_nodes) - 1, 0)
        if align == "top":
            start = margin + (height_available - total)
        elif align == "bottom":
            start = margin
        else:
            start = margin + (height_available - total) / 2
        y = start
        for node in layer_nodes:
            height = node_value[node] * scale
            layout["nodes"][node] = {
                "x": margin
                + (1.0 - 2 * margin - node_width) * (layer / max(max_layer, 1)),
                "y": y,
                "width": node_width,
                "height": height,
            }
            y += height + node_pad
    return layout, flow_in, flow_out, node_value


def _ribbon_path(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    thickness: float,
    curvature: float,
) -> mpath.Path:
    """Build a closed Bezier path for a ribbon segment."""
    dx = x1 - x0
    if dx <= 0:
        dx = max(thickness, 0.02)
    cx0 = x0 + dx * curvature
    cx1 = x1 - dx * curvature
    top0 = y0 + thickness / 2
    bot0 = y0 - thickness / 2
    top1 = y1 + thickness / 2
    bot1 = y1 - thickness / 2
    verts = [
        (x0, top0),
        (cx0, top0),
        (cx1, top1),
        (x1, top1),
        (x1, bot1),
        (cx1, bot1),
        (cx0, bot0),
        (x0, bot0),
        (x0, top0),
    ]
    codes = [
        mpath.Path.MOVETO,
        mpath.Path.CURVE4,
        mpath.Path.CURVE4,
        mpath.Path.CURVE4,
        mpath.Path.LINETO,
        mpath.Path.CURVE4,
        mpath.Path.CURVE4,
        mpath.Path.CURVE4,
        mpath.Path.CLOSEPOLY,
    ]
    return mpath.Path(verts, codes)


def _bezier_point(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    """Evaluate a cubic Bezier coordinate at t in [0, 1]."""
    u = 1 - t
    return (u**3) * p0 + 3 * (u**2) * t * p1 + 3 * u * (t**2) * p2 + (t**3) * p3


def _flow_label_point(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    thickness: float,
    curvature: float,
    frac: float,
) -> tuple[float, float]:
    """Return a point along the flow centerline for label placement."""
    dx = x1 - x0
    if dx <= 0:
        dx = max(thickness, 0.02)
    cx0 = x0 + dx * curvature
    cx1 = x1 - dx * curvature
    target_x = x0 + (x1 - x0) * frac
    if x1 == x0:
        t = frac
    else:
        lo, hi = 0.0, 1.0
        for _ in range(24):
            mid = (lo + hi) / 2
            mid_x = _bezier_point(x0, cx0, cx1, x1, mid)
            if mid_x < target_x:
                lo = mid
            else:
                hi = mid
        t = (lo + hi) / 2
    x = _bezier_point(x0, cx0, cx1, x1, t)
    y = _bezier_point(y0, y0, y1, y1, t)
    return x, y


def _apply_style(
    style: str | None,
    *,
    flow_cycle: Sequence[Any] | None,
    node_facecolor: Any,
    flow_alpha: float,
    flow_curvature: float,
    node_label_box: bool | Mapping[str, Any] | None,
    node_label_kw: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply a named style preset and merge overrides."""
    if style is None:
        return {
            "flow_cycle": flow_cycle,
            "node_facecolor": node_facecolor,
            "flow_alpha": flow_alpha,
            "flow_curvature": flow_curvature,
            "node_label_box": node_label_box,
            "node_label_kw": node_label_kw,
        }
    presets = {
        "budget": dict(
            node_facecolor="0.8",
            flow_alpha=0.85,
            flow_curvature=0.55,
            node_label_box=True,
            node_label_kw=dict(fontsize=9, color="0.2"),
        ),
        "pastel": dict(
            node_facecolor="0.88",
            flow_alpha=0.7,
            flow_curvature=0.6,
            node_label_box=True,
        ),
        "mono": dict(
            node_facecolor="0.7",
            flow_alpha=0.5,
            flow_curvature=0.45,
            node_label_box=False,
            flow_cycle=["0.55"],
        ),
    }
    if style not in presets:
        raise ValueError(f"Unknown sankey style {style!r}.")
    preset = presets[style]
    # Merge preset overrides with caller-provided defaults.
    return {
        "flow_cycle": preset.get("flow_cycle", flow_cycle),
        "node_facecolor": preset.get("node_facecolor", node_facecolor),
        "flow_alpha": preset.get("flow_alpha", flow_alpha),
        "flow_curvature": preset.get("flow_curvature", flow_curvature),
        "node_label_box": preset.get("node_label_box", node_label_box),
        "node_label_kw": {**preset.get("node_label_kw", {}), **node_label_kw},
    }


def _apply_flow_other(
    flows: list[dict[str, Any]], flow_other: float | None, other_label: str
) -> list[dict[str, Any]]:
    """Aggregate small flows into a single 'Other' target per source."""
    if flow_other is None:
        return flows
    # Collapse small values per source into an "Other" flow.
    other_sums = {}
    filtered = []
    for flow in flows:
        if flow["value"] < flow_other:
            other_sums[flow["source"]] = (
                other_sums.get(flow["source"], 0.0) + flow["value"]
            )
        else:
            filtered.append(flow)
    flows = filtered
    for source, other_sum in other_sums.items():
        if other_sum <= 0:
            continue
        flows.append(
            {
                "source": source,
                "target": other_label,
                "value": other_sum,
                "label": None,
                "color": None,
                "group": None,
            }
        )
    return flows


def _ensure_nodes(
    nodes: Any,
    flows: Sequence[Mapping[str, Any]],
    node_order: Sequence[Any] | None,
) -> tuple[dict[Any, dict[str, Any]], list[Any]]:
    """Ensure all flow endpoints exist in nodes and validate ordering."""
    node_map, node_order_default = _normalize_nodes(nodes, flows)
    # Add any missing flow endpoints to the node list if ordering is implicit.
    flow_nodes = {flow["source"] for flow in flows} | {flow["target"] for flow in flows}
    missing_nodes = [node for node in flow_nodes if node not in node_map]
    if missing_nodes and node_order is not None:
        raise ValueError("node_order must include every node exactly once.")
    if missing_nodes:
        for node in missing_nodes:
            node_map[node] = {"id": node, "label": str(node), "color": None}
            node_order_default.append(node)
    node_order = node_order or node_order_default
    if set(node_order) != set(node_map.keys()):
        raise ValueError("node_order must include every node exactly once.")
    return node_map, node_order


def _assign_flow_colors(
    flows: Sequence[Mapping[str, Any]],
    flow_cycle: Sequence[Any] | None,
    group_cycle: Sequence[Any] | None,
) -> dict[Any, Any]:
    """Assign colors to flows by group or source."""
    if flow_cycle is None:
        flow_cycle = ["0.6"]
    if group_cycle is None:
        group_cycle = flow_cycle
    group_iter = iter(group_cycle)
    flow_color_map = {}
    # Assign a stable color per group (or per source if no group).
    for flow in flows:
        if flow["color"] is not None:
            continue
        group = flow["group"] or flow["source"]
        if group not in flow_color_map:
            try:
                flow_color_map[group] = next(group_iter)
            except StopIteration:
                group_iter = iter(group_cycle)
                flow_color_map[group] = next(group_iter)
        flow["color"] = flow_color_map[group]
    return flow_color_map


def _sort_flows(
    flows: Sequence[Mapping[str, Any]],
    node_order: Sequence[Any],
    layout: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Sort flows by target position to reduce crossings."""
    # Order outgoing links by target center to reduce line crossings.
    node_centers = {
        node: layout["nodes"][node]["y"] + layout["nodes"][node]["height"] / 2
        for node in node_order
    }
    ordered = []
    seen = set()
    for source in node_order:
        outgoing = [flow for flow in flows if flow["source"] == source]
        outgoing = sorted(outgoing, key=lambda f: node_centers[f["target"]])
        for flow in outgoing:
            ordered.append(flow)
            seen.add(id(flow))
    for flow in flows:
        if id(flow) not in seen:
            ordered.append(flow)
    return ordered


def _flow_label_text(
    flow: Mapping[str, Any], value_format: str | Callable[[float], str] | None
) -> str:
    """Resolve the text for a flow label."""
    label_text = flow.get("label", None)
    if label_text is not None:
        return label_text
    if value_format is None:
        return f"{flow['value']:.3g}"
    if callable(value_format):
        return value_format(flow["value"])
    return value_format.format(flow["value"])


def _flow_label_frac(idx: int, count: int, base: float) -> float:
    """Return alternating label positions around the midpoint."""
    if count <= 1:
        return base
    step = 0.25 if count == 2 else 0.2
    offset = (idx // 2 + 1) * step
    frac = base - offset if idx % 2 == 0 else base + offset
    return min(max(frac, 0.05), 0.95)


def _prepare_inputs(
    *,
    nodes: Any,
    flows: Any,
    flow_other: float | None,
    other_label: str,
    node_order: Sequence[Any] | None,
    style: str | None,
    flow_cycle: Sequence[Any] | None,
    node_facecolor: Any,
    flow_alpha: float,
    flow_curvature: float,
    node_label_box: bool | Mapping[str, Any] | None,
    node_label_kw: Mapping[str, Any],
    group_cycle: Sequence[Any] | None,
) -> tuple[
    list[dict[str, Any]],
    dict[Any, dict[str, Any]],
    list[Any],
    dict[str, Any],
    dict[Any, Any],
]:
    """Normalize inputs, apply style, and assign colors."""
    # Parse flows and optional "other" aggregation.
    flows = _normalize_flows(flows)
    flows = _apply_flow_other(flows, flow_other, other_label)
    # Ensure nodes include all flow endpoints.
    node_map, node_order = _ensure_nodes(nodes, flows, node_order)
    # Apply style presets and merge overrides.
    style_config = _apply_style(
        style,
        flow_cycle=flow_cycle,
        node_facecolor=node_facecolor,
        flow_alpha=flow_alpha,
        flow_curvature=flow_curvature,
        node_label_box=node_label_box,
        node_label_kw=node_label_kw,
    )
    # Resolve flow colors after style is applied.
    flow_color_map = _assign_flow_colors(flows, style_config["flow_cycle"], group_cycle)
    return flows, node_map, node_order, style_config, flow_color_map


def _validate_layer_order(
    layer_order: Sequence[int] | None,
    flows: Sequence[Mapping[str, Any]],
    node_order: Sequence[Any],
    layers: Mapping[Any, int] | None,
) -> None:
    """Validate that layer_order is consistent with computed layers."""
    if layer_order is None:
        return
    # Compare explicit ordering with the computed layer set.
    layer_map = _assign_layers(flows, node_order, layers)
    if set(layer_order) != set(layer_map.values()):
        raise ValueError("layer_order must include every layer.")


def _layer_positions(
    layout: Mapping[str, Any], layer_order: Sequence[int] | None
) -> tuple[dict[Any, int], dict[int, int]]:
    """Return layer maps and positions for label placement."""
    # Map layer ids to positions for outside-label placement.
    layer_map = layout["layers"]
    if layer_order is not None:
        layer_position = {layer: idx for idx, layer in enumerate(layer_order)}
    else:
        layer_position = {layer: layer for layer in set(layer_map.values())}
    return layer_map, layer_position


def _label_box(
    node_label_box: bool | Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Return a bbox dict for node labels, if requested."""
    if not node_label_box:
        return None
    if node_label_box is True:
        # Default rounded box styling.
        return dict(
            boxstyle="round,pad=0.2,rounding_size=0.1",
            facecolor="white",
            edgecolor="none",
            alpha=0.9,
        )
    return dict(node_label_box)


def _draw_flows(
    ax,
    *,
    flows: Sequence[Mapping[str, Any]],
    node_order: Sequence[Any],
    layout: Mapping[str, Any],
    flow_color_map: Mapping[Any, Any],
    flow_kw: Mapping[str, Any],
    label_kw: Mapping[str, Any],
    flow_label_kw: Mapping[str, Any],
    flow_labels: bool,
    value_format: str | Callable[[float], str] | None,
    flow_label_pos: float,
    flow_alpha: float,
    flow_curvature: float,
) -> tuple[list[mpatches.PathPatch], dict[Any, Any]]:
    """Draw flow ribbons and optional labels."""
    flow_patches = []
    labels_out = {}
    label_items = []
    # Track running offsets per node so flows stack without overlap.
    out_offsets = {node: 0.0 for node in node_order}
    in_offsets = {node: 0.0 for node in node_order}
    link_counts = {}
    link_seen = {}
    if flow_labels:
        # Count links so multiple labels on the same link can be spaced.
        for flow in flows:
            key = (flow["source"], flow["target"])
            link_counts[key] = link_counts.get(key, 0) + 1
    for flow in flows:
        source = flow["source"]
        target = flow["target"]
        thickness = flow["value"] * layout["scale"]
        src = layout["nodes"][source]
        tgt = layout["nodes"][target]
        x0 = src["x"] + src["width"]
        x1 = tgt["x"]
        y0 = src["y"] + out_offsets[source] + thickness / 2
        y1 = tgt["y"] + in_offsets[target] + thickness / 2
        out_offsets[source] += thickness
        in_offsets[target] += thickness
        # Resolve color and build the ribbon patch.
        color = flow["color"] or flow_color_map.get(flow["group"] or source, "0.6")
        facecolor = _tint(color, 0.35)
        path = _ribbon_path(x0, y0, x1, y1, thickness, flow_curvature)
        base_flow_kw = {"edgecolor": "none", "linewidth": 0.0}
        base_flow_kw.update(flow_kw)
        flow_facecolor = base_flow_kw.pop("facecolor", facecolor)
        patch = mpatches.PathPatch(
            path,
            facecolor=flow_facecolor,
            alpha=flow_alpha,
            **base_flow_kw,
        )
        ax.add_patch(patch)
        flow_patches.append(patch)

        if flow_labels:
            # Place label along the ribbon length.
            label_text = _flow_label_text(flow, value_format)
            if label_text:
                key = (source, target)
                count = link_counts.get(key, 1)
                idx = link_seen.get(key, 0)
                link_seen[key] = idx + 1
                frac = _flow_label_frac(idx, count, flow_label_pos)
                label_x, label_y = _flow_label_point(
                    x0, y0, x1, y1, thickness, flow_curvature, frac
                )
                text = ax.text(
                    label_x,
                    label_y,
                    str(label_text),
                    ha="center",
                    va="center",
                    **{**label_kw, **flow_label_kw},
                )
                labels_out[(source, target, idx)] = text
                label_items.append(
                    {
                        "text": text,
                        "source": source,
                        "target": target,
                        "x0": x0,
                        "x1": x1,
                        "y0": y0,
                        "y1": y1,
                        "thickness": thickness,
                        "curvature": flow_curvature,
                        "frac": frac,
                        "adjusted": False,
                    }
                )

    if flow_labels and len(label_items) > 1:

        def _set_label_position(item: dict[str, Any], frac: float) -> None:
            label_x, label_y = _flow_label_point(
                item["x0"],
                item["y0"],
                item["x1"],
                item["y1"],
                item["thickness"],
                item["curvature"],
                frac,
            )
            item["text"].set_position((label_x, label_y))
            item["frac"] = frac

        for i in range(len(label_items)):
            for j in range(i + 1, len(label_items)):
                a = label_items[i]
                b = label_items[j]
                if (a["y0"] - b["y0"]) * (a["y1"] - b["y1"]) < 0:
                    if not a["adjusted"] and not b["adjusted"]:
                        _set_label_position(a, 0.25)
                        _set_label_position(b, 0.75)
                        a["adjusted"] = True
                        b["adjusted"] = True
                    elif a["adjusted"] ^ b["adjusted"]:
                        primary = a if a["adjusted"] else b
                        secondary = b if a["adjusted"] else a
                        if abs(primary["frac"] - 0.25) < 1.0e-6:
                            target = 0.75
                        elif abs(primary["frac"] - 0.75) < 1.0e-6:
                            target = 0.25
                        else:
                            target = 0.25
                        _set_label_position(secondary, target)
                        secondary["adjusted"] = True
    return flow_patches, labels_out


def _draw_nodes(
    ax,
    *,
    node_order: Sequence[Any],
    node_map: Mapping[Any, Mapping[str, Any]],
    layout: Mapping[str, Any],
    layer_map: Mapping[Any, int],
    layer_position: Mapping[int, int],
    node_facecolor: Any,
    node_kw: Mapping[str, Any],
    label_kw: Mapping[str, Any],
    node_label_kw: Mapping[str, Any],
    node_label_box: bool | Mapping[str, Any] | None,
    node_labels: bool,
    node_label_outside: bool | str,
    node_label_offset: float,
) -> tuple[dict[Any, mpatches.Patch], dict[Any, Any]]:
    """Draw node rectangles and optional labels."""
    node_patches = {}
    labels_out = {}
    for node in node_order:
        node_info = layout["nodes"][node]
        facecolor = node_map[node]["color"] or node_facecolor
        # Draw the node block.
        base_node_kw = {"edgecolor": "none", "linewidth": 0.0}
        base_node_kw.update(node_kw)
        node_face = base_node_kw.pop("facecolor", facecolor)
        patch = mpatches.FancyBboxPatch(
            (node_info["x"], node_info["y"]),
            node_info["width"],
            node_info["height"],
            boxstyle="round,pad=0.0,rounding_size=0.008",
            facecolor=node_face,
            **base_node_kw,
        )
        ax.add_patch(patch)
        node_patches[node] = patch
        if node_labels:
            # Place labels inside or outside based on width and position.
            box_kw = _label_box(node_label_box)
            label_x = node_info["x"] + node_info["width"] / 2
            label_y = node_info["y"] + node_info["height"] / 2
            ha = "center"
            if node_label_outside:
                mode = node_label_outside
                if mode == "auto":
                    mode = node_info["width"] < 0.04
                if mode:
                    layer = layer_position[layer_map[node]]
                    if layer == 0:
                        label_x = node_info["x"] - node_label_offset
                        ha = "right"
                    elif layer == max(layer_position.values()):
                        label_x = (
                            node_info["x"] + node_info["width"] + node_label_offset
                        )
                        ha = "left"
            labels_out[node] = ax.text(
                label_x,
                label_y,
                node_map[node]["label"],
                ha=ha,
                va="center",
                bbox=box_kw,
                **{**label_kw, **node_label_kw},
            )
    return node_patches, labels_out


def sankey_diagram(
    ax,
    *,
    nodes=None,
    flows=None,
    layers=None,
    flow_cycle=None,
    group_cycle=None,
    node_order=None,
    layer_order=None,
    style=None,
    flow_other=None,
    other_label="Other",
    value_format=None,
    node_pad=0.02,
    node_width=0.03,
    node_kw=None,
    flow_kw=None,
    label_kw=None,
    node_label_kw=None,
    flow_label_kw=None,
    node_label_box=None,
    node_labels=True,
    flow_labels=False,
    flow_sort=True,
    flow_label_pos=0.5,
    node_label_outside="auto",
    node_label_offset=0.01,
    align="center",
    margin=0.05,
    flow_alpha=0.75,
    flow_curvature=0.5,
    node_facecolor="0.75",
) -> SankeyDiagram:
    """Render a layered Sankey diagram with optional labels."""
    node_kw = node_kw or {}
    flow_kw = flow_kw or {}
    label_kw = label_kw or {}
    node_label_kw = node_label_kw or {}
    flow_label_kw = flow_label_kw or {}

    # Normalize inputs, apply presets, and assign colors.
    flows, node_map, node_order, style_config, flow_color_map = _prepare_inputs(
        nodes=nodes,
        flow_cycle=flow_cycle,
        flow_other=flow_other,
        other_label=other_label,
        node_order=node_order,
        style=style,
        node_label_box=node_label_box,
        node_label_kw=node_label_kw,
        node_facecolor=node_facecolor,
        flow_alpha=flow_alpha,
        flow_curvature=flow_curvature,
        group_cycle=group_cycle,
        flows=flows,
    )
    node_facecolor = style_config["node_facecolor"]
    flow_alpha = style_config["flow_alpha"]
    flow_curvature = style_config["flow_curvature"]
    node_label_box = style_config["node_label_box"]
    node_label_kw = style_config["node_label_kw"]

    # Validate optional layer ordering before layout.
    _validate_layer_order(layer_order, flows, node_order, layers)

    layout, _, _, _ = _compute_layout(
        node_order,
        flows,
        node_pad=node_pad,
        node_width=node_width,
        align=align,
        layers=layers,
        margin=margin,
        layer_order=layer_order,
    )

    layout["groups"] = flow_color_map

    # Cache layer indices for label placement.
    layer_map, layer_position = _layer_positions(layout, layer_order)

    if flow_sort:
        # Reorder flows to reduce crossings.
        flows = _sort_flows(flows, node_order, layout)

    # Draw flows and nodes, then merge their label handles.
    flow_patches, flow_labels_out = _draw_flows(
        ax,
        flows=flows,
        node_order=node_order,
        layout=layout,
        flow_color_map=flow_color_map,
        flow_kw=flow_kw,
        label_kw=label_kw,
        flow_label_kw=flow_label_kw,
        flow_labels=flow_labels,
        value_format=value_format,
        flow_label_pos=flow_label_pos,
        flow_alpha=flow_alpha,
        flow_curvature=flow_curvature,
    )
    node_patches, node_labels_out = _draw_nodes(
        ax,
        node_order=node_order,
        node_map=node_map,
        layout=layout,
        layer_map=layer_map,
        layer_position=layer_position,
        node_facecolor=node_facecolor,
        node_kw=node_kw,
        label_kw=label_kw,
        node_label_kw=node_label_kw,
        node_label_box=node_label_box,
        node_labels=node_labels,
        node_label_outside=node_label_outside,
        node_label_offset=node_label_offset,
    )
    labels_out = {**flow_labels_out, **node_labels_out}

    # Lock axes to the unit square.
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()

    return SankeyDiagram(
        nodes=node_patches,
        flows=flow_patches,
        labels=labels_out,
        layout=layout,
    )
