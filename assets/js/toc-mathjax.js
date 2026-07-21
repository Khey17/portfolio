// Tocbot fills #toc-sidebar from heading textContent. After MathJax typesets
// headings, that textContent becomes broken spaced glyphs (e.g. "u 3", "T τ").
// Copy the rendered heading DOM (including mjx nodes) into each TOC link.
(function () {
  let syncing = false;
  let scheduled = null;

  function syncTocMath() {
    const toc = document.querySelector("#toc-sidebar");
    if (!toc || syncing) {
      return;
    }

    syncing = true;
    try {
      toc.querySelectorAll("a.toc-link").forEach((link) => {
        const href = link.getAttribute("href") || "";
        const id = decodeURIComponent(href.replace(/^#/, ""));
        if (!id) {
          return;
        }

        const heading = document.getElementById(id);
        if (!heading || !heading.querySelector("mjx-container, .MathJax")) {
          return;
        }

        link.replaceChildren(...Array.from(heading.childNodes).map((node) => node.cloneNode(true)));
      });
    } finally {
      syncing = false;
    }
  }

  function schedule() {
    if (scheduled) {
      clearTimeout(scheduled);
    }
    scheduled = setTimeout(syncTocMath, 0);
  }

  function afterMathJax(callback) {
    if (window.MathJax?.startup?.promise) {
      window.MathJax.startup.promise.then(callback).catch(callback);
      return;
    }
    if (window.MathJax?.typesetPromise) {
      window.MathJax.typesetPromise().then(callback).catch(callback);
      return;
    }
    callback();
  }

  function start() {
    afterMathJax(() => {
      syncTocMath();
      setTimeout(syncTocMath, 200);
      setTimeout(syncTocMath, 800);
    });

    const toc = document.querySelector("#toc-sidebar");
    if (toc && typeof MutationObserver === "function") {
      const observer = new MutationObserver(() => {
        if (!syncing) {
          schedule();
        }
      });
      observer.observe(toc, { childList: true, subtree: true });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
