document.addEventListener("DOMContentLoaded", function () {
  // Check if current page has opted out of the TOC
  if (document.body.classList.contains("no-right-toc")) {
    return;
  }

  const content = document.querySelector(".rst-content");
  if (!content) return;

  // Find all headers in the main content
  const headers = Array.from(
    content.querySelectorAll("h1:not(.document-title), h2, h3"),
  ).filter((header) => !header.classList.contains("no-toc"));

  // Only create TOC if there are headers
  if (headers.length === 0) return;

  // Create TOC container
  const toc = document.createElement("div");
  toc.className = "right-toc";
  toc.innerHTML =
    '<div class="right-toc-header">' +
    '<div class="right-toc-title">On This Page</div>' +
    '<div class="right-toc-buttons">' +
    '<button class="right-toc-toggle-btn" title="Toggle TOC visibility">−</button>' +
    "</div></div>" +
    '<div class="right-toc-content"><ul class="right-toc-list"></ul></div>';

  const tocList = toc.querySelector(".right-toc-list");
  const tocContent = toc.querySelector(".right-toc-content");
  const tocToggleBtn = toc.querySelector(".right-toc-toggle-btn");

  // Set up the toggle button
  tocToggleBtn.addEventListener("click", function () {
    if (tocContent.style.display === "none") {
      tocContent.style.display = "block";
      tocToggleBtn.textContent = "−";
      toc.classList.remove("right-toc-collapsed");
      localStorage.setItem("tocVisible", "true");
    } else {
      tocContent.style.display = "none";
      tocToggleBtn.textContent = "+";
      toc.classList.add("right-toc-collapsed");
      localStorage.setItem("tocVisible", "false");
    }
  });

  // Check saved state
  if (localStorage.getItem("tocVisible") === "false") {
    tocContent.style.display = "none";
    tocToggleBtn.textContent = "+";
    toc.classList.add("right-toc-collapsed");
  }

  // Track used IDs to avoid duplicates
  const usedIds = new Set();

  // Get all existing IDs in the document
  document.querySelectorAll("[id]").forEach((el) => {
    usedIds.add(el.id);
  });

  // Generate unique IDs for headers that need them
  headers.forEach((header, index) => {
    // If header already has a unique ID, use that
    if (header.id && !usedIds.has(header.id)) {
      usedIds.add(header.id);
      return;
    }

    // Create a slug from the header text
    let headerText = header.textContent || "";

    // Clean the text (remove icons and special characters)
    headerText = headerText.replace(/\s*\uf0c1\s*$/, "");
    headerText = headerText.replace(/\s*[¶§#†‡]\s*$/, "");
    headerText = headerText.trim();

    let slug = headerText
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/--+/g, "-")
      .trim();

    // Make sure slug is not empty
    if (!slug) {
      slug = "section";
    }

    // Ensure the ID is unique
    let uniqueId = slug;
    let counter = 1;

    while (usedIds.has(uniqueId)) {
      uniqueId = `${slug}-${counter}`;
      counter++;
    }

    // Set the unique ID and add to our tracking set
    header.id = uniqueId;
    usedIds.add(uniqueId);
  });

  // Add entries for each header
  headers.forEach((header) => {
    const item = document.createElement("li");
    const link = document.createElement("a");

    link.href = "#" + header.id;

    // Get clean text without icons
    let headerText = header.textContent || "";
    headerText = headerText.replace(/\s*\uf0c1\s*$/, "");
    headerText = headerText.replace(/\s*[¶§#†‡]\s*$/, "");

    link.textContent = headerText.trim();
    link.className =
      "right-toc-link right-toc-level-" + header.tagName.toLowerCase();

    item.appendChild(link);
    tocList.appendChild(item);
  });

  // Add TOC to page
  document.body.appendChild(toc);

  // Add active link highlighting
  const tocLinks = document.querySelectorAll(".right-toc-link");
  const headerElements = Array.from(headers);

  if (tocLinks.length > 0 && headerElements.length > 0) {
    // Highlight the current section on scroll
    window.addEventListener(
      "scroll",
      debounce(function () {
        let currentSection = null;
        let smallestDistanceFromTop = Infinity;

        headerElements.forEach((header) => {
          const distance = Math.abs(header.getBoundingClientRect().top);
          if (distance < smallestDistanceFromTop) {
            smallestDistanceFromTop = distance;
            currentSection = header.id;
          }
        });

        tocLinks.forEach((link) => {
          link.classList.remove("active");
          if (link.getAttribute("href") === `#${currentSection}`) {
            link.classList.add("active");
          }
        });
      }, 100),
    );
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const galleryRoot = document.querySelector("#ultraplot-gallery");
  if (galleryRoot) {
    const gallerySections = [
      "layouts",
      "legends-and-colorbars",
      "geoaxes",
      "plot-types",
      "colors-and-cycles",
    ];
    gallerySections.forEach((sectionId) => {
      const heading = document.querySelector(
        `section#${sectionId} > h1, section#${sectionId} > h2`,
      );
      if (heading) {
        heading.classList.add("no-toc");
      }
    });
  }

  const thumbContainers = Array.from(
    document.querySelectorAll(".sphx-glr-thumbcontainer"),
  );
  if (thumbContainers.length < 6) {
    return;
  }

  const topicMap = {
    layouts: { label: "Layouts", slug: "layouts" },
    "legends and colorbars": {
      label: "Legends & Colorbars",
      slug: "legends-colorbars",
    },
    geoaxes: { label: "GeoAxes", slug: "geoaxes" },
    "plot types": { label: "Plot Types", slug: "plot-types" },
    "colors and cycles": { label: "Colors", slug: "colors" },
  };

  const topics = [];
  const topicOrder = new Set();
  const originalSections = new Set();

  function normalize(text) {
    return text
      .toLowerCase()
      .replace(/[^\w\s-]/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  thumbContainers.forEach((thumb) => {
    const section = thumb.closest("section");
    const heading = section ? section.querySelector("h1, h2") : null;
    const key = heading ? normalize(heading.textContent || "") : "";
    const info = topicMap[key] || { label: "Other", slug: "other" };
    thumb.dataset.topic = info.slug;
    if (section) {
      originalSections.add(section);
    }
    if (!topicOrder.has(info.slug) && info.slug !== "other") {
      topicOrder.add(info.slug);
      topics.push(info);
    }
  });

  if (topics.length === 0) {
    return;
  }

  const firstSection = thumbContainers[0].closest("section");
  const parent =
    (firstSection && firstSection.parentNode) ||
    document.querySelector(".rst-content");
  if (!parent) {
    return;
  }

  const controls = document.createElement("div");
  controls.className = "gallery-filter-controls";

  const filterBar = document.createElement("div");
  filterBar.className = "gallery-filter-bar";

  function makeButton(label, slug) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "gallery-filter-button";
    button.textContent = label;
    button.dataset.topic = slug;
    return button;
  }

  const buttons = [
    makeButton("All", "all"),
    ...topics.map((topic) => makeButton(topic.label, topic.slug)),
  ];

  const counts = {};
  thumbContainers.forEach((thumb) => {
    const topic = thumb.dataset.topic || "other";
    counts[topic] = (counts[topic] || 0) + 1;
  });
  counts.all = thumbContainers.length;

  buttons.forEach((button) => {
    const topic = button.dataset.topic;
    const count = counts[topic] || 0;
    button.textContent = `${button.textContent} (${count})`;
    filterBar.appendChild(button);
  });

  const unified = document.createElement("div");
  unified.className = "sphx-glr-thumbnails gallery-unified";
  thumbContainers.forEach((thumb) => unified.appendChild(thumb));

  controls.appendChild(filterBar);
  controls.appendChild(unified);
  parent.insertBefore(controls, firstSection);

  originalSections.forEach((section) => {
    section.classList.add("gallery-section-hidden");
  });
  document.body.classList.add("gallery-filter-active");

  function setFilter(slug) {
    buttons.forEach((button) => {
      button.classList.toggle("is-active", button.dataset.topic === slug);
    });
    thumbContainers.forEach((thumb) => {
      const matches = slug === "all" || thumb.dataset.topic === slug;
      thumb.style.display = matches ? "" : "none";
    });
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      setFilter(button.dataset.topic);
    });
  });

  setFilter("all");
});

// Debounce function to limit scroll event firing
function debounce(func, wait) {
  let timeout;
  return function () {
    const context = this;
    const args = arguments;
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(context, args), wait);
  };
}
