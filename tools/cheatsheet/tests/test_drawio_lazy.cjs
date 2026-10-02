const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const loader = fs.readFileSync(path.join(__dirname, "../../../docs/_ext/drawio-lazy.js"), "utf8");
const tick = () => new Promise(resolve => setImmediate(resolve));

function element() {
  return {
    dataset: { drawioUrl: "../_drawio/page.xml" }, style: { minHeight: "24rem" },
    attrs: {}, link: { addEventListener(type, fn) { this.click = fn; } },
    setAttribute(key, value) { this.attrs[key] = value; },
    removeAttribute(key) { delete this.attrs[key]; },
    querySelector() { return this.link; },
    replaceChildren(...children) { this.children = children; },
  };
}
function harness({ observer = true } = {}) {
  const elements = [element(), element()];
  const scripts = [], requests = [], renders = [];
  const context = {
    window: {}, console: { warn() {} },
    document: {
      readyState: "complete",
      querySelectorAll: () => elements,
      createElement: () => ({ remove() {}, addEventListener(type, fn) { this.click = fn; } }),
      head: { appendChild: script => scripts.push(script) },
    },
    fetch: async url => { requests.push(url); return { ok: true, text: async () => "<mxGraphModel/>" }; },
  };
  if (observer) {
    context.IntersectionObserver = context.window.IntersectionObserver = class {
      constructor(callback, options) { this.callback = callback; this.options = options; context.observer = this; }
      observe() {}
      unobserve() {}
    };
  }
  vm.runInNewContext(loader, context);
  const ready = () => {
    context.window.DOMPurify = {};
    context.window.pako = {};
    context.window.GraphViewer = { createViewerForElement(el) { renders.push(JSON.parse(el.attrs["data-mxgraph"])); } };
    scripts[0].onload();
  };
  return { context, elements, scripts, requests, renders, ready };
}

test("offscreen pages do not fetch or render; visible pages share the viewer", async () => {
  const h = harness();
  assert.equal(h.requests.length, 0);
  assert.equal(h.scripts.length, 0);
  assert.equal(h.context.observer.options.rootMargin, "300px");
  h.context.observer.callback(h.elements.map(target => ({ target, isIntersecting: true })));
  assert.equal(h.requests.length, 2);
  assert.equal(h.scripts.length, 1);
  h.ready();
  await tick();
  assert.equal(h.renders.length, 2);
  assert.equal(h.renders[0].xml, "<mxGraphModel/>");
  assert.equal(h.elements[0].attrs["aria-busy"], "false");
  assert.equal(h.elements[0].attrs["data-mxgraph"], undefined);
  h.elements[0].link.click({ preventDefault() {} });
  assert.equal(h.requests.length, 2);
});

test("failed viewer requests can be retried", async () => {
  const h = harness();
  h.elements[0].link.click({ preventDefault() {} });
  h.scripts[0].onerror();
  await tick();
  assert.equal(h.elements[0].attrs["aria-busy"], "false");
  assert.equal(h.elements[0].dataset.loading, undefined);
  h.elements[0].children[0].click();
  assert.equal(h.scripts.length, 2);
  h.context.window.DOMPurify = {};
  h.context.window.pako = {};
  h.context.window.GraphViewer = { createViewerForElement() {} };
  h.scripts[1].onload();
  await tick();
  assert.equal(h.elements[0].style.minHeight, "");
});

test("browsers without IntersectionObserver still load diagrams", async () => {
  const h = harness({ observer: false });
  assert.equal(h.requests.length, 2);
  h.ready();
  await tick();
  assert.equal(h.renders.length, 2);
});

test("RequireJS AMD registration is suppressed for the standalone viewer and restored", async () => {
  const h = harness();
  const amd = {};
  h.context.window.define = () => {};
  h.context.window.define.amd = amd;
  h.elements[0].link.click({ preventDefault() {} });
  assert.equal(h.context.window.define.amd, undefined);
  h.ready();
  await tick();
  assert.equal(h.context.window.define.amd, amd);
  assert.equal(h.renders.length, 1);
});

test("RequireJS AMD registration is restored after a failed download", async () => {
  const h = harness();
  const amd = {};
  h.context.window.define = () => {};
  h.context.window.define.amd = amd;
  h.elements[0].link.click({ preventDefault() {} });
  h.scripts[0].onerror();
  await tick();
  assert.equal(h.context.window.define.amd, amd);
});

test("HTTP failures show a retry button and reuse the loaded viewer", async () => {
  const h = harness();
  h.context.fetch = async () => ({ ok: false, status: 404 });
  h.elements[0].link.click({ preventDefault() {} });
  h.ready();
  await tick();
  assert.equal(h.renders.length, 0);
  assert.match(h.elements[0].children[0].textContent, /Retry/);
  h.context.fetch = async () => ({ ok: true, text: async () => "<mxGraphModel/>" });
  h.elements[0].children[0].click();
  await tick();
  assert.equal(h.renders.length, 1);
  assert.equal(h.scripts.length, 1);
});
