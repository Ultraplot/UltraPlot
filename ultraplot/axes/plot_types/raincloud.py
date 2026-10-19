"""Composition of half violins, observations, and boxplots."""

import numpy as np

from ...internals import _canonicalize_kwargs, _pop_props, warnings


def _component_style(options, category):
    """Resolve artist aliases before applying raincloud's component defaults."""
    style = dict(options or {})
    style.update(_pop_props(style, category))
    if category == "patch":
        # Box/violin wrappers style faces and edges separately rather than
        # accepting the generic Patch colour argument themselves.
        color = style.pop("color", None)
        if color is not None:
            style.setdefault("facecolor", color)
            style.setdefault("edgecolor", color)
    return style


def raincloud(
    ax,
    data,
    *,
    positions=None,
    labels=None,
    orientation="vertical",
    side="high",
    jitter=0.08,
    offset=0.15,
    cloud=True,
    rain=True,
    box=True,
    seed=0,
    color=None,
    cycle=None,
    cycle_kw=None,
    cloud_kw=None,
    rain_kw=None,
    box_kw=None,
):
    """Draw the components of :meth:`PlotAxes.raincloud`."""
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
    columns = getattr(data, "columns", None)
    if labels is None and columns is not None:
        labels = list(columns)
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
    cleaned = []
    for values in distributions:
        if np.ndim(values) != 1:
            raise ValueError("Each distribution must be one-dimensional")
        values = np.ma.masked_invalid(np.ma.asarray(values, dtype=float)).compressed()
        cleaned.append(values)
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
    colors = [
        color if color is not None else ax._get_patches_for_fill.get_next_color()
        for _ in range(n)
    ]
    rng = np.random.default_rng(seed)
    vert = orientation == "vertical"
    direction = 1 if side == "high" else -1
    artists = {key: [None] * n for key in ("cloud", "rain", "box")}

    for i, (position, values, group_color) in enumerate(
        zip(positions, cleaned, colors)
    ):
        if not values.size:
            warnings._warn_ultraplot(
                f"Distribution {i} has no finite observations, skipping"
            )
            continue
        if cloud:
            kw = {"widths": 0.6, **styles[0]}
            props = _pop_props(kw, "patch")
            props.setdefault("alpha", 0.4)
            bodies = ax.violinplot(
                [position + direction * offset],
                values,
                vert=vert,
                side=side,
                fillcolor=group_color,
                **kw,
            )
            artists["cloud"][i] = bodies[0]
            bodies[0].update(props)
        if rain:
            locations = (
                position
                - direction * offset
                + rng.uniform(-jitter, jitter, values.size)
            )
            kw = {"alpha": 0.5, "linewidths": 0, **styles[1]}
            if not any(key in kw for key in ("sizes", "size")):
                kw["sizes"] = 12
            if not any(key in kw for key in ("colors", "facecolors")):
                kw["colors"] = group_color
            coords = (locations, values) if vert else (values, locations)
            artists["rain"][i] = ax.scatter(*coords, **kw)
        if box:
            kw = {
                "facecolor": group_color,
                "widths": 0.12,
                "fill": True,
                "showfliers": False,
                "zorder": 3,
                **styles[2],
            }
            artists["box"][i] = ax.boxplot(
                [position],
                values,
                vert=vert,
                manage_ticks=False,
                **kw,
            )

    axis = ax.xaxis if vert else ax.yaxis
    axis.set_ticks(positions)
    if labels is not None:
        axis.set_ticklabels(labels)
    if columns is not None and columns.name and axis.isDefault_label:
        axis.set_label_text(str(columns.name))
    return artists
