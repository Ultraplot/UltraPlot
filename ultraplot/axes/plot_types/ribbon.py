#!/usr/bin/env python3
"""
Top-aligned ribbon flow diagram helper.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from matplotlib import patches as mpatches
from matplotlib import path as mpath


def _ribbon_path(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    thickness: float,
    curvature: float,
) -> mpath.Path:
    dx = max(x1 - x0, 1e-6)
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


def ribbon_diagram(
    ax: Any,
    data: Any,
    *,
    id_col: str,
    period_col: str,
    topic_col: str,
    value_col: str | None = None,
    period_order: Sequence[Any] | None = None,
    topic_order: Sequence[Any] | None = None,
    group_map: Mapping[Any, Any] | None = None,
    group_order: Sequence[Any] | None = None,
    group_colors: Mapping[Any, Any] | None = None,
    xmargin: float,
    ymargin: float,
    row_height_ratio: float,
    node_width: float,
    flow_curvature: float,
    flow_alpha: float,
    show_topic_labels: bool,
    topic_label_offset: float,
    topic_label_size: float,
    topic_label_box: bool,
) -> dict[str, Any]:
    """
    Build a fixed-row, top-aligned ribbon flow diagram from long-form assignments.
    """
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        df = pd.DataFrame(data)
    required = {id_col, period_col, topic_col}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"Missing required columns: {sorted(missing)}")
    if value_col is not None and value_col not in df.columns:
        raise KeyError(f"Invalid value_col={value_col!r}. Column not found.")
    if df.empty:
        raise ValueError("Input data is empty.")

    if period_order is None:
        periods = list(pd.unique(df[period_col]))
    else:
        periods = list(period_order)
        df = df[df[period_col].isin(periods)]
    if len(periods) < 2:
        raise ValueError("Need at least two periods for ribbon transitions.")
    period_idx = {period: i for i, period in enumerate(periods)}

    if value_col is None:
        df["value_internal"] = 1.0
    else:
        df["value_internal"] = pd.to_numeric(df[value_col], errors="coerce").fillna(0.0)
    df = df[df["value_internal"] > 0]
    if df.empty:
        raise ValueError("No positive values remain after parsing value column.")

    if topic_order is None:
        topic_counts_all = (
            df.groupby(topic_col)["value_internal"].sum().sort_values(ascending=False)
        )
        topics = list(topic_counts_all.index)
    else:
        topics = [topic for topic in topic_order if topic in set(df[topic_col])]
    if not topics:
        raise ValueError("No topics available after filtering.")

    if group_map is None:
        group_map = {topic: topic for topic in topics}
    else:
        group_map = dict(group_map)
        for topic in topics:
            group_map.setdefault(topic, topic)

    if group_order is None:
        groups = list(dict.fromkeys(group_map[topic] for topic in topics))
    else:
        groups = list(group_order)

    # Group topics by group, then keep topic ordering inside groups.
    grouped_topics = defaultdict(list)
    for topic in topics:
        grouped_topics[group_map[topic]].append(topic)
    ordered_topics = []
    for group in groups:
        ordered_topics.extend(grouped_topics.get(group, []))
    # Append any groups not listed in group_order.
    for group, topic_list in grouped_topics.items():
        if group not in groups:
            ordered_topics.extend(topic_list)
            groups.append(group)
    topics = ordered_topics

    cycle = ax._get_patches_for_fill
    if group_colors is None:
        group_colors = {group: cycle.get_next_color() for group in groups}
    else:
        group_colors = dict(group_colors)
        for group in groups:
            group_colors.setdefault(group, cycle.get_next_color())
    topic_colors = {topic: group_colors[group_map[topic]] for topic in topics}

    counts = (
        df.groupby([period_col, topic_col])["value_internal"]
        .sum()
        .rename("count")
        .reset_index()
    )
    counts = counts[counts[period_col].isin(periods) & counts[topic_col].isin(topics)]

    # Build consecutive transitions by entity.
    transitions = Counter()
    for _, group in df.groupby(id_col):
        group = group[group[period_col].isin(periods)].copy()
        if group.empty:
            continue
        # If multiple topics for same entity-period, keep strongest assignment.
        group = (
            group.sort_values("value_internal", ascending=False)
            .drop_duplicates(subset=[period_col], keep="first")
            .assign(_pidx=lambda d: d[period_col].map(period_idx))
            .sort_values("_pidx")
        )
        rows = list(group.itertuples(index=False))
        for i in range(len(rows) - 1):
            curr = rows[i]
            nxt = rows[i + 1]
            p0 = getattr(curr, period_col)
            p1 = getattr(nxt, period_col)
            if period_idx[p1] != period_idx[p0] + 1:
                continue
            t0 = getattr(curr, topic_col)
            t1 = getattr(nxt, topic_col)
            v = min(
                float(getattr(curr, "value_internal")),
                float(getattr(nxt, "value_internal")),
            )
            if v > 0 and t0 in topics and t1 in topics:
                transitions[(p0, t0, p1, t1)] += v

    row_gap = (1.0 - 2 * ymargin) / max(1, len(topics))
    topic_row_top = {
        topic: 1.0 - ymargin - i * row_gap for i, topic in enumerate(topics)
    }
    topic_label_y = {topic: topic_row_top[topic] - 0.5 * row_gap for topic in topics}
    row_height = row_gap * row_height_ratio

    xvals = np.linspace(xmargin, 1.0 - xmargin, len(periods))
    period_x = {period: xvals[i] for i, period in enumerate(periods)}

    max_count = max(float(counts["count"].max()) if not counts.empty else 0.0, 1.0)
    node_scale = row_height * 0.85 / max_count

    node_patches = []
    node_geom: dict[tuple[Any, Any], tuple[float, float]] = {}
    for row in counts.itertuples(index=False):
        period = getattr(row, period_col)
        topic = getattr(row, topic_col)
        count = float(getattr(row, "count"))
        if period not in period_x or topic not in topic_row_top:
            continue
        height = count * node_scale
        x = period_x[period]
        y_center = topic_row_top[topic] - height / 2
        node_geom[(period, topic)] = (y_center, height)
        patch = mpatches.FancyBboxPatch(
            (x - node_width / 2, y_center - height / 2),
            node_width,
            height,
            boxstyle="round,pad=0.0,rounding_size=0.006",
            facecolor=topic_colors[topic],
            edgecolor="none",
            alpha=0.95,
            zorder=3,
        )
        ax.add_patch(patch)
        node_patches.append(patch)

    by_pair = defaultdict(list)
    for (p0, t0, p1, t1), value in transitions.items():
        by_pair[(p0, p1)].append((t0, t1, value))

    flow_patches = []
    for (p0, p1), flows in by_pair.items():
        x0 = period_x[p0]
        x1 = period_x[p1]
        src_total = defaultdict(float)
        tgt_total = defaultdict(float)
        for t0, t1, value in flows:
            src_total[t0] += value
            tgt_total[t1] += value
        max_total = max(src_total.values()) if src_total else 1.0
        scale = row_height * 0.75 / max_total

        src_off = {}
        for topic, total in src_total.items():
            center, height = node_geom.get(
                (p0, topic), (topic_label_y[topic], total * scale)
            )
            top = center + height / 2
            src_off[topic] = top - total * scale
        tgt_off = {}
        for topic, total in tgt_total.items():
            center, height = node_geom.get(
                (p1, topic), (topic_label_y[topic], total * scale)
            )
            top = center + height / 2
            tgt_off[topic] = top - total * scale

        ordered_flows = sorted(
            flows, key=lambda item: (topics.index(item[0]), topics.index(item[1]))
        )
        src_mid = {}
        tgt_mid = {}
        for t0, t1, value in ordered_flows:
            thickness = value * scale
            src_mid[(t0, t1)] = (src_off[t0] + thickness / 2, thickness)
            src_off[t0] += thickness
        for t1, t0, value in sorted(
            [(f[1], f[0], f[2]) for f in ordered_flows],
            key=lambda item: (topics.index(item[0]), topics.index(item[1])),
        ):
            thickness = value * scale
            tgt_mid[(t0, t1)] = (tgt_off[t1] + thickness / 2, thickness)
            tgt_off[t1] += thickness

        for t0, t1, _ in ordered_flows:
            y0, thickness = src_mid[(t0, t1)]
            y1, _ = tgt_mid[(t0, t1)]
            if thickness <= 0:
                continue
            path = _ribbon_path(x0, y0, x1, y1, thickness, flow_curvature)
            patch = mpatches.PathPatch(
                path,
                facecolor=topic_colors[t0],
                edgecolor="none",
                alpha=flow_alpha,
                zorder=1,
            )
            ax.add_patch(patch)
            flow_patches.append(patch)

    topic_text = []
    if show_topic_labels:
        right_period = periods[-1]
        for topic in topics:
            text = ax.text(
                period_x[right_period] + topic_label_offset,
                topic_label_y[topic],
                str(topic),
                ha="left",
                va="center",
                fontsize=topic_label_size,
                color=topic_colors[topic],
                bbox=(
                    dict(facecolor="white", edgecolor="none", alpha=0.75, pad=0.25)
                    if topic_label_box
                    else None
                ),
            )
            topic_text.append(text)

    period_text = []
    for period in periods:
        text = ax.text(
            period_x[period],
            1.0 - ymargin / 2,
            str(period),
            ha="center",
            va="bottom",
            fontsize=max(topic_label_size + 1, 8),
        )
        period_text.append(text)

    ax.format(xlim=(0, 1), ylim=(0, 1), grid=False)
    ax.axis("off")
    return {
        "node_patches": node_patches,
        "flow_patches": flow_patches,
        "topic_text": topic_text,
        "period_text": period_text,
        "periods": periods,
        "topics": topics,
        "groups": groups,
    }
