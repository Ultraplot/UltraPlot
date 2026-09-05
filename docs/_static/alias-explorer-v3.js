(function () {
  "use strict";

  const apiTargets = {
    "figure.init": "api/ultraplot.figure.Figure.html#ultraplot.figure.Figure",
    "figure.format": "api/ultraplot.figure.Figure.html#ultraplot.figure.Figure.format",
    "axes.format": "api/ultraplot.axes.Axes.html#ultraplot.axes.Axes.format",
    "cartesian.format": "api/ultraplot.axes.CartesianAxes.html#ultraplot.axes.CartesianAxes.format",
    "geo.format": "api/ultraplot.axes.GeoAxes.html#ultraplot.axes.GeoAxes.format",
    "polar.format": "api/ultraplot.axes.PolarAxes.html#ultraplot.axes.PolarAxes.format",
    "taylor.format": "api/ultraplot.axes.TaylorAxes.html#ultraplot.axes.TaylorAxes.format",
    colorbar: "api/ultraplot.axes.Axes.html#ultraplot.axes.Axes.colorbar",
    legend: "api/ultraplot.axes.Axes.html#ultraplot.axes.Axes.legend",
    gridspec: "api/ultraplot.gridspec.GridSpec.html#ultraplot.gridspec.GridSpec",
    subplot: "api/ultraplot.ui.subplots.html#ultraplot.ui.subplots",
    inset: "api/ultraplot.axes.Axes.html#ultraplot.axes.Axes.inset",
    cycle: "api/ultraplot.constructor.Cycle.html#ultraplot.constructor.Cycle",
    projection: "api/ultraplot.constructor.Proj.html#ultraplot.constructor.Proj",
    "scale.log": "api/ultraplot.scale.LogScale.html#ultraplot.scale.LogScale",
    "scale.symlog": "api/ultraplot.scale.SymmetricalLogScale.html#ultraplot.scale.SymmetricalLogScale",
    "plot.labels": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes",
    "plot.text": "api/ultraplot.axes.Axes.html#ultraplot.axes.Axes.text",
    "plot.contour_labels": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.contour",
    "plot.error_bars": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.plot",
    "plot.error_shading": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.plot",
    "plot.colormap": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.contour",
    "plot.levels": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.contour",
    "plot.stacked": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.bar",
    "plot.statistics": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.boxplot",
    "plot.boxplot": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.boxplot",
    "plot.violinplot": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.violinplot",
    "plot.hist": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.hist",
    "plot.pie": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.pie",
    "style.rgba": "api.html#colormaps-and-normalizers",
    "style.hsla": "api.html#colormaps-and-normalizers",
    "style.patch": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.bar",
    "style.line": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.plot",
    "style.collection": "api/ultraplot.axes.PlotAxes.html#ultraplot.axes.PlotAxes.scatter",
    "style.text": "api/ultraplot.axes.Axes.html#ultraplot.axes.Axes.text",
    "rc (dotless)": "api/ultraplot.config.Configurator.html#ultraplot.config.Configurator",
  };

  function splitContexts(value) {
    return String(value || "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function contextMatches(context, pattern) {
    if (pattern.endsWith(".*")) {
      return context.startsWith(pattern.slice(0, -1));
    }
    return context === pattern;
  }

  function rowMatchesContexts(row, patterns) {
    return (
      !patterns.length ||
      patterns.some((pattern) => contextMatches(row.context, pattern))
    );
  }

  function makeCode(value) {
    const code = document.createElement("code");
    code.textContent = value;
    return code;
  }

  function highlightedApiUrl(context, canonical) {
    const target = apiTargets[context];
    if (!target) return "";
    const hashIndex = target.indexOf("#");
    const base = hashIndex === -1 ? target : target.slice(0, hashIndex);
    const hash = hashIndex === -1 ? "" : target.slice(hashIndex);
    const joiner = base.includes("?") ? "&" : "?";
    return `${base}${joiner}highlight=${encodeURIComponent(canonical)}${hash}`;
  }

  function makeKeywordLink(row, value) {
    const target = highlightedApiUrl(row.context, row.canonical);
    if (!target) return makeCode(value);
    const link = document.createElement("a");
    link.className = "uplt-alias-keyword-link";
    link.href = target;
    link.title = `Open the canonical API documentation for ${row.canonical}`;
    link.appendChild(makeCode(value));
    return link;
  }

  function initializeAliasExplorer(root) {
    const sectionIds = [
      "function-keyword-aliases",
      "artist-property-aliases",
      "dotless-rc-aliases",
    ];
    const sections = sectionIds
      .map((id) => document.getElementById(id))
      .filter(Boolean);
    const rows = [];

    sections.forEach((section) => {
      const table = section.querySelector("table");
      if (!table) return;
      table.classList.add("uplt-alias-table");
      Array.from(table.querySelectorAll("tbody tr")).forEach((element) => {
        const cells = Array.from(element.querySelectorAll("td"));
        if (cells.length < 3) return;
        const row = {
          element,
          context: cells[0].textContent.trim(),
          accepted: cells[1].textContent.trim(),
          canonical: cells[2].textContent.trim(),
        };
        element.dataset.aliasContext = row.context;
        rows.push(row);
      });
    });

    if (!rows.length) return;

    const contextCount = new Set(rows.map((row) => row.context)).size;
    const totalNode = root.querySelector("[data-alias-total]");
    const contextTotalNode = root.querySelector("[data-alias-context-total]");
    const titleNode = root.querySelector("[data-alias-detail-title]");
    const copyNode = root.querySelector("[data-alias-detail-copy]");
    const previewNode = root.querySelector("[data-alias-preview]");
    const apiNode = root.querySelector("[data-alias-api]");
    const searchNode = root.querySelector("#uplt-alias-search");
    const resetNode = root.querySelector("[data-alias-reset]");
    const statusNode = root.querySelector("[data-alias-filter-status]");
    const controls = Array.from(
      root.querySelectorAll("[data-contexts][data-label]"),
    );
    const targets = Array.from(root.querySelectorAll("[data-alias-target]"));
    const svg = root.querySelector(".uplt-alias-map svg");
    const draggableNodes = Array.from(
      root.querySelectorAll(".uplt-alias-node[data-layout-key]"),
    );
    const suppressedClicks = new WeakSet();

    function svgPoint(event) {
      const point = svg.createSVGPoint();
      point.x = event.clientX;
      point.y = event.clientY;
      return point.matrixTransform(svg.getScreenCTM().inverse());
    }

    function nodePosition(node) {
      const match = /translate\(\s*([-+\d.]+)[ ,]+([-+\d.]+)\s*\)/.exec(
        node.getAttribute("transform") || "",
      );
      return {
        x: match ? Number(match[1]) : 0,
        y: match ? Number(match[2]) : 0,
      };
    }

    function updateLeader(node, x, y) {
      const rect = node.querySelector("rect");
      const wire = node.querySelector(".uplt-alias-wire");
      if (!rect || !wire) return;
      const width = Number(rect.getAttribute("width"));
      const height = Number(rect.getAttribute("height"));
      const targetX = Number(node.dataset.anchorX);
      const targetY = Number(node.dataset.anchorY);
      const centerX = x + width / 2;
      const centerY = y + height / 2;
      const dx = targetX - centerX;
      const dy = targetY - centerY;
      if (!dx && !dy) {
        wire.setAttribute("d", "");
        return;
      }
      const factor = Math.min(
        dx ? width / 2 / Math.abs(dx) : Infinity,
        dy ? height / 2 / Math.abs(dy) : Infinity,
      );
      const length = Math.hypot(dx, dy) || 1;
      const overlap = 3;
      const startX = centerX + dx * factor - (dx / length) * overlap;
      const startY = centerY + dy * factor - (dy / length) * overlap;
      wire.setAttribute(
        "d",
        `M${(startX - x).toFixed(1)} ${(startY - y).toFixed(1)} ` +
          `L${(targetX - x).toFixed(1)} ${(targetY - y).toFixed(1)}`,
      );
    }

    function setNodePosition(node, x, y) {
      node.setAttribute("transform", `translate(${x.toFixed(1)} ${y.toFixed(1)})`);
      updateLeader(node, x, y);
    }

    function layoutSnapshot() {
      return Object.fromEntries(
        draggableNodes.map((node) => {
          const position = nodePosition(node);
          return [
            node.dataset.layoutKey,
            [Number(position.x.toFixed(1)), Number(position.y.toFixed(1))],
          ];
        }),
      );
    }

    function saveDraftLayout() {
      fetch("/__alias_layout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version: 1, nodes: layoutSnapshot() }),
      }).catch(() => {});
    }

    function restoreDraftLayout() {
      fetch("/__alias_layout")
        .then((response) => (response.ok ? response.json() : null))
        .then((draft) => {
          if (!draft || !draft.nodes) return;
          draggableNodes.forEach((node) => {
            const position = draft.nodes[node.dataset.layoutKey];
            if (
              Array.isArray(position) &&
              position.length === 2 &&
              position.every(Number.isFinite)
            ) {
              setNodePosition(node, position[0], position[1]);
            }
          });
        })
        .catch(() => {});
    }

    draggableNodes.forEach((node) => {
      const rect = node.querySelector("rect");
      const width = Number(rect.getAttribute("width"));
      const height = Number(rect.getAttribute("height"));
      let drag = null;

      updateLeader(node, nodePosition(node).x, nodePosition(node).y);
      node.addEventListener("pointerdown", (event) => {
        if (event.button !== 0) return;
        const point = svgPoint(event);
        const position = nodePosition(node);
        drag = {
          pointerId: event.pointerId,
          offsetX: point.x - position.x,
          offsetY: point.y - position.y,
          originX: point.x,
          originY: point.y,
          moved: false,
        };
        node.setPointerCapture(event.pointerId);
        node.classList.add("is-dragging");
        event.preventDefault();
      });
      node.addEventListener("pointermove", (event) => {
        if (!drag || event.pointerId !== drag.pointerId) return;
        const point = svgPoint(event);
        drag.moved ||= Math.hypot(
          point.x - drag.originX,
          point.y - drag.originY,
        ) > 2;
        const viewBox = svg.viewBox.baseVal;
        const grip = 16;
        const x = Math.max(
          viewBox.x + grip - width,
          Math.min(viewBox.x + viewBox.width - grip, point.x - drag.offsetX),
        );
        const y = Math.max(
          viewBox.y + grip - height,
          Math.min(viewBox.y + viewBox.height - grip, point.y - drag.offsetY),
        );
        setNodePosition(node, x, y);
      });
      node.addEventListener("pointerup", (event) => {
        if (!drag || event.pointerId !== drag.pointerId) return;
        if (drag.moved) {
          suppressedClicks.add(node);
          saveDraftLayout();
        }
        node.classList.remove("is-dragging");
        node.releasePointerCapture(event.pointerId);
        drag = null;
      });
      node.addEventListener("pointercancel", () => {
        node.classList.remove("is-dragging");
        drag = null;
      });
    });

    restoreDraftLayout();

    rows.forEach((row) => {
      const cells = Array.from(row.element.querySelectorAll("td"));
      cells[1].replaceChildren(makeKeywordLink(row, row.accepted));
      cells[2].replaceChildren(makeKeywordLink(row, row.canonical));
    });

    totalNode.textContent = rows.length.toLocaleString();
    contextTotalNode.textContent = contextCount.toLocaleString();

    let selected = {
      patterns: [],
      targets: [],
      label: "All aliases",
      api: "",
    };

    function getRows(patterns) {
      return rows.filter((row) => rowMatchesContexts(row, patterns));
    }

    function renderDetail(state, temporary) {
      const matches = getRows(state.patterns);
      titleNode.textContent = state.label;
      copyNode.textContent = matches.length
        ? `${matches.length.toLocaleString()} accepted ${
            matches.length === 1 ? "spelling" : "spellings"
          } in this area${temporary ? " — click to keep this view" : ""}.`
        : "No compatibility aliases are registered for this area.";
      previewNode.replaceChildren();

      matches.slice(0, 8).forEach((row) => {
        const item = document.createElement("div");
        item.className = "uplt-alias-pair";
        item.appendChild(makeKeywordLink(row, row.accepted));
        const arrow = document.createElement("span");
        arrow.setAttribute("aria-hidden", "true");
        arrow.textContent = "→";
        item.appendChild(arrow);
        item.appendChild(makeKeywordLink(row, row.canonical));
        const context = document.createElement("small");
        context.textContent = row.context;
        item.appendChild(context);
        previewNode.appendChild(item);
      });

      if (matches.length > 8) {
        const more = document.createElement("p");
        more.className = "uplt-alias-more";
        more.textContent = `+ ${(matches.length - 8).toLocaleString()} more below`;
        previewNode.appendChild(more);
      }

      if (state.api) {
        apiNode.href = state.api;
        apiNode.hidden = false;
      } else {
        apiNode.removeAttribute("href");
        apiNode.hidden = true;
      }

      targets.forEach((target) => {
        const name = target.dataset.aliasTarget;
        target.classList.toggle("is-active", selected.targets.includes(name));
        target.classList.toggle(
          "is-preview",
          temporary && state.targets.includes(name),
        );
      });
    }

    function updateControlState() {
      controls.forEach((control) => {
        const patterns = splitContexts(control.dataset.contexts);
        const active =
          selected.patterns.length > 0 &&
          patterns.some((pattern) =>
            getRows(selected.patterns).some((row) =>
              contextMatches(row.context, pattern),
            ),
          );
        control.classList.toggle("is-active", active);
        control.setAttribute("aria-pressed", active ? "true" : "false");
      });
    }

    function applyFilter() {
      const query = searchNode.value.trim().toLowerCase();
      let visible = 0;
      rows.forEach((row) => {
        const inArea = rowMatchesContexts(row, selected.patterns);
        const inSearch =
          !query ||
          `${row.context} ${row.accepted} ${row.canonical}`
            .toLowerCase()
            .includes(query);
        const show = inArea && inSearch;
        row.element.hidden = !show;
        row.element.classList.toggle("is-alias-match", show && Boolean(query));
        if (show) visible += 1;
      });

      sections.forEach((section) => {
        section.hidden = !section.querySelector("tbody tr:not([hidden])");
      });

      const area = selected.patterns.length ? ` · ${selected.label}` : "";
      statusNode.textContent = `${visible.toLocaleString()} of ${rows.length.toLocaleString()} mappings shown${area}`;
      root.classList.toggle("has-filter", Boolean(query || selected.patterns.length));
      updateControlState();
    }

    function stateForControl(control) {
      return {
        patterns: splitContexts(control.dataset.contexts),
        targets: splitContexts(control.dataset.targets),
        label: control.dataset.label,
        api: control.dataset.api || "",
      };
    }

    function previewControl(control) {
      control.classList.add("is-preview");
      renderDetail(stateForControl(control), true);
    }

    function stopPreview(control) {
      control.classList.remove("is-preview");
      renderDetail(selected, false);
    }

    function selectControl(control) {
      const next = stateForControl(control);
      const same =
        next.patterns.join("|") === selected.patterns.join("|");
      selected = same
        ? { patterns: [], targets: [], label: "All aliases", api: "" }
        : next;
      renderDetail(selected, false);
      applyFilter();
    }

    controls.forEach((control) => {
      control.addEventListener("pointerenter", () => previewControl(control));
      control.addEventListener("pointerleave", () => stopPreview(control));
      control.addEventListener("focus", () => previewControl(control));
      control.addEventListener("blur", () => stopPreview(control));
      control.addEventListener("click", (event) => {
        if (suppressedClicks.has(control)) {
          suppressedClicks.delete(control);
          event.preventDefault();
          return;
        }
        selectControl(control);
      });
      if (control.tagName.toLowerCase() !== "button") {
        control.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            selectControl(control);
          }
        });
      }
    });

    searchNode.addEventListener("input", applyFilter);
    resetNode.addEventListener("click", () => {
      selected = {
        patterns: [],
        targets: [],
        label: "All aliases",
        api: "",
      };
      searchNode.value = "";
      renderDetail(selected, false);
      applyFilter();
      searchNode.focus();
    });

    renderDetail(selected, false);
    applyFilter();
    root.dataset.aliasExplorerReady = "true";
  }

  document.addEventListener("DOMContentLoaded", function () {
    document
      .querySelectorAll(".uplt-alias-explorer")
      .forEach(initializeAliasExplorer);
  });
})();
