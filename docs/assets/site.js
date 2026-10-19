// Theme switch (follows the system until the visitor picks one) and the install tabs.
(function () {
  var root = document.documentElement;
  var btn = document.querySelector(".theme-btn");
  function current() {
    var forced = root.getAttribute("data-theme");
    if (forced) return forced;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  function label() {
    if (!btn) return;
    var dark = current() === "dark";
    btn.textContent = dark ? "☀" : "☾";
    btn.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
    btn.title = btn.getAttribute("aria-label");
  }
  if (btn) {
    btn.addEventListener("click", function () {
      var next = current() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) { /* private mode */ }
      label();
    });
    label();
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", label);
  }

  var tabs = document.querySelectorAll("[role=tab]");
  function select(tab) {
    tabs.forEach(function (t) {
      var on = t === tab;
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
    });
  }
  tabs.forEach(function (t) {
    t.addEventListener("click", function () { select(t); });
  });
  if (tabs.length) {
    var ua = navigator.userAgent;
    var guess = /Windows/.test(ua) ? "tab-windows" : /Mac OS X|Macintosh/.test(ua) && !/iPhone|iPad/.test(ua)
      ? "tab-macos" : /Linux|X11/.test(ua) && !/Android/.test(ua) ? "tab-linux" : null;
    var hash = location.hash.replace("#install-", "tab-");
    select(document.getElementById(hash) || document.getElementById(guess) || tabs[0]);
  }
})();
