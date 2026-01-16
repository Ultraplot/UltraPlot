document.addEventListener("DOMContentLoaded", function () {
  // Check if current page has opted out of the TOC
  if (document.body.classList.contains("no-right-toc")) {
    return;
  }

  const isWhatsNewPage =
    document.body.classList.contains("whats_new") ||
    window.location.pathname.endsWith("/whats_new.html") ||
    window.location.pathname.endsWith("/whats_new/");

  if (isWhatsNewPage) {
    const nav = document.querySelector(".wy-menu-vertical");
    if (nav) {
      nav.querySelectorAll('li[class*="toctree-l"]').forEach((item) => {
        if (!item.className.match(/toctree-l1/)) {
          item.remove();
        }
      });
      nav.querySelectorAll('a[href*="#"]').forEach((link) => {
        const li = link.closest("li");
        if (li && !li.className.match(/toctree-l1/)) {
          li.remove();
        }
      });
    }
  }

  const content = document.querySelector(".rst-content");
  if (!content) return;

  const isWhatsNew = isWhatsNewPage;
  const headerSelector = isWhatsNew ? "h2" : "h1:not(.document-title), h2, h3";

  // Find all headers in the main content
  const headers = Array.from(content.querySelectorAll(headerSelector)).filter(
    (header) => !header.classList.contains("no-toc"),
  );

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
    // If header already has an ID, keep it
    if (header.id) {
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

  if (isWhatsNew) {
    headers.forEach((header) => {
      const tag = header.tagName.toLowerCase();
      const rawText = header.textContent || "";
      const cleanText = rawText
        .replace(/\s*\uf0c1\s*$/, "")
        .replace(/\s*[¶§#†‡]\s*$/, "")
        .trim();
      const isReleaseHeading = tag === "h2" && /^v\d/i.test(cleanText || "");

      if (isReleaseHeading) {
        const item = document.createElement("li");
        const link = document.createElement("a");

        link.href = "#" + header.id;

        link.textContent = cleanText;
        link.className = "right-toc-link right-toc-level-h1";
        item.appendChild(link);
        tocList.appendChild(item);
      }
    });
  } else {
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
  }

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
  const navLinks = document.querySelectorAll(
    ".wy-menu-vertical a.reference.internal",
  );
  navLinks.forEach((link) => {
    const href = link.getAttribute("href") || "";
    const isGalleryLink = href.includes("gallery/");
    const isGalleryIndex = href.includes("gallery/index");
    if (isGalleryLink && !isGalleryIndex) {
      const item = link.closest("li");
      if (item) {
        item.remove();
      }
    }
  });

  const galleryRoot = document.querySelector(".sphx-glr-thumbcontainer");
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
        `section#${sectionId} .gallery-section-header`,
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

  const topicList = [
    { id: "layouts", label: "Layouts", slug: "layouts" },
    {
      id: "legends_colorbars",
      label: "Legends & Colorbars",
      slug: "legends-colorbars",
    },
    { id: "geo", label: "GeoAxes", slug: "geoaxes" },
    { id: "plot_types", label: "Plot Types", slug: "plot-types" },
    { id: "colors", label: "Colors", slug: "colors" },
  ];
  const topicMap = Object.fromEntries(
    topicList.map((topic) => [topic.id, topic]),
  );
  const originalThumbnails = new Set();

  function getTopicInfo(thumb) {
    const link = thumb.querySelector("a.reference.internal");
    if (!link) {
      return { label: "Other", slug: "other" };
    }
    const href = link.getAttribute("href") || "";
    const path = new URL(href, window.location.href).pathname;
    const match = path.match(/\/gallery\/([^/]+)\//);
    const key = match ? match[1] : "";
    return topicMap[key] || { label: "Other", slug: "other" };
  }

  thumbContainers.forEach((thumb) => {
    const info = getTopicInfo(thumb);
    thumb.dataset.topic = info.slug;
    const group = thumb.closest(".sphx-glr-thumbnails");
    if (group) {
      originalThumbnails.add(group);
    }
  });

  const topics = topicList.filter((topic) =>
    thumbContainers.some((thumb) => thumb.dataset.topic === topic.slug),
  );

  if (topics.length === 0) {
    return;
  }

  const firstGroup = thumbContainers[0].closest(".sphx-glr-thumbnails");
  const parent =
    (firstGroup && firstGroup.parentNode) ||
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
  parent.insertBefore(controls, firstGroup);

  originalThumbnails.forEach((group) => {
    group.classList.add("gallery-section-hidden");
  });
  document
    .querySelectorAll(".gallery-section-header, .gallery-section-description")
    .forEach((node) => {
      node.classList.add("gallery-section-hidden");
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
