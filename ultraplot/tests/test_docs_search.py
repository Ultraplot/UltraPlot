import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_docs_search_prioritizes_api_references_for_generic_function_queries():
    if shutil.which("node") is None:
        pytest.skip("Node.js is required to exercise the docs search JavaScript.")

    script = textwrap.dedent(r"""
        const fs = require("fs");
        const vm = require("vm");
        const listeners = [];
        const classList = {
          add() {},
          remove() {},
          contains() { return false; },
          toggle() {},
        };
        const context = {
          console,
          Scorer: {},
          Search: {
            _parseQuery(query) {
              const objectTerms = new Set(query.toLowerCase().split(/\s+/).filter(Boolean));
              return [query, new Set(), new Set(), new Set(), objectTerms];
            },
            performObjectSearch(_object, objectTerms) {
              this.lastObjectTerms = Array.from(objectTerms);
              return this.lastObjectTerms;
            },
          },
        };
        context.window = {
          innerWidth: 1024,
          location: { hash: "", pathname: "/search.html" },
          requestAnimationFrame(callback) { callback(); },
          scrollY: 0,
          addEventListener() {},
        };
        context.document = {
          body: {
            classList,
            dataset: {},
            appendChild() {},
            getAttribute() { return ""; },
          },
          documentElement: { classList, dataset: {} },
          addEventListener(type, callback) {
            if (type === "DOMContentLoaded") listeners.push(callback);
          },
          querySelector() { return null; },
          querySelectorAll() { return []; },
        };
        context.localStorage = {
          getItem() { return null; },
          setItem() {},
        };

        vm.runInNewContext(fs.readFileSync("docs/_static/custom.js", "utf8"), context);
        for (const callback of listeners) callback.call(context.document);

        const parsed = context.Search._parseQuery("format function");
        const filteredTerms = context.Search.performObjectSearch("format", parsed[4]);
        const apiObjectScore = context.Scorer.score([
          "api/ultraplot.axes.Axes",
          "ultraplot.axes.Axes.format",
          "#ultraplot.axes.Axes.format",
          "Python method, in Axes",
          16,
          "api/ultraplot.axes.Axes.html",
          "object",
        ]);
        const apiTextScore = context.Scorer.score([
          "api/ultraplot.axes.Axes",
          "Axes",
          "",
          null,
          16,
          "api/ultraplot.axes.Axes.html",
          "text",
        ]);
        const guideScore = context.Scorer.score([
          "basics",
          "The basics",
          "",
          null,
          16,
          "basics.html",
          "text",
        ]);

        console.log(JSON.stringify({
          apiLikeQuery: context.Search.upltApiLikeQuery,
          apiObjectScore,
          apiTextScore,
          filteredTerms,
          guideScore,
        }));
        """)

    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    data = json.loads(result.stdout)

    assert data["apiLikeQuery"] is True
    assert data["filteredTerms"] == ["format"]
    assert data["apiObjectScore"] > data["apiTextScore"] > data["guideScore"]
