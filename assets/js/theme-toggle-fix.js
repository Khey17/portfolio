// al-folio cycles system → light → dark, which can require two clicks when "system"
// matches the current appearance. Flip the visible theme directly instead.
(function () {
  function patchToggle() {
    if (typeof setThemeSetting !== "function" || typeof determineComputedTheme !== "function") {
      return;
    }

    toggleThemeSetting = function () {
      setThemeSetting(determineComputedTheme() === "dark" ? "light" : "dark");
    };
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", patchToggle);
  } else {
    patchToggle();
  }
})();
