/* Fetch SVG-heavy draw.io pages only when they approach the viewport. */
(() => {
  "use strict";
  let viewerPromise;
  function viewer() {
    if (window.GraphViewer && window.DOMPurify && window.pako) return Promise.resolve();
    if (!viewerPromise) {
      viewerPromise = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        // The standalone viewer bundles DOMPurify, pako and Spinner as UMD
        // libraries but consumes their browser globals. Sphinx's RequireJS
        // otherwise captures them as anonymous AMD modules instead.
        const define = window.define;
        const amd = define && define.amd;
        if (amd) define.amd = undefined;
        const restoreAMD = () => {
          if (amd) define.amd = amd;
        };
        script.src = "https://viewer.diagrams.net/js/viewer-static.min.js";
        script.onload = () => {
          restoreAMD();
          if (window.GraphViewer && window.DOMPurify && window.pako) resolve();
          else reject(new Error("Viewer dependencies unavailable"));
        };
        script.onerror = () => {
          restoreAMD();
          script.remove();
          reject(new Error("Viewer download failed"));
        };
        document.head.appendChild(script);
      }).catch(error => {
        viewerPromise = undefined;
        throw error;
      });
    }
    return viewerPromise;
  }

  async function load(element) {
    if (element.dataset.loading) return;
    element.dataset.loading = "true";
    element.setAttribute("aria-busy", "true");
    try {
      const [xml] = await Promise.all([
        fetch(element.dataset.drawioUrl).then(response => {
          if (!response.ok) throw new Error(`Diagram download failed (${response.status})`);
          return response.text();
        }),
        viewer(),
      ]);
      element.setAttribute("data-mxgraph", JSON.stringify({
        xml, resize: true, fit: true, nav: false, lightbox: false, toolbar: "",
      }));
      element.replaceChildren();
      window.GraphViewer.createViewerForElement(element);
      element.removeAttribute("data-mxgraph");
      element.style.minHeight = "";
      element.setAttribute("aria-busy", "false");
    } catch (error) {
      delete element.dataset.loading;
      element.setAttribute("aria-busy", "false");
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "Diagram could not be loaded. Retry";
      button.addEventListener("click", () => load(element));
      element.replaceChildren(button);
      console.warn("Draw.io diagram:", error);
    }
  }

  function init() {
    const elements = document.querySelectorAll(".drawio-lazy");
    const observer = "IntersectionObserver" in window ? new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          observer.unobserve(entry.target);
          load(entry.target);
        }
      }
    }, { rootMargin: "300px" }) : null;
    for (const element of elements) {
      element.querySelector("a").addEventListener("click", event => {
        event.preventDefault();
        if (observer) observer.unobserve(element);
        load(element);
      });
      if (observer) observer.observe(element);
      else load(element);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
