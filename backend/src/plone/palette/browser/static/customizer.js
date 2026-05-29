/* plone.palette — live theme preview
 *
 * Injects a <style id="palette-live"> into <head> (after Bootstrap/Barceloneta
 * stylesheets) and rewrites its text on every picker / range / select change.  This wins
 * at cascade because same-specificity rules that appear later in the stylesheet order
 * override earlier ones — so .btn-primary { --bs-btn-bg: ... } in our <style> beats
 * the compiled Bootstrap value, unlike document.documentElement.style.setProperty
 * which cannot override class-scoped custom property declarations.
 *
 * Persistence is handled by pat-autosubmit + pat-inject on the form.
 *
 * Data-attribute protocol:
 *   data-css-var + optional data-css-unit  →  collected into rootVars, written to :root
 *   data-css-selector + data-css-prop      →  collected into ruleMap, written as selector { prop: val }
 */
(function () {
  "use strict";

  // ── helpers ──────────────────────────────────────────────────────────────

  function hexToRgb(hex) {
    var h = hex.replace("#", "");
    if (h.length === 3) { h = h[0]+h[0]+h[1]+h[1]+h[2]+h[2]; }
    if (h.length !== 6) return null;
    return {
      r: parseInt(h.slice(0,2), 16),
      g: parseInt(h.slice(2,4), 16),
      b: parseInt(h.slice(4,6), 16)
    };
  }

  function darken(hex, amount) {
    amount = amount || 0.1;
    var c = hexToRgb(hex);
    if (!c) return hex;
    var d = function(v) { return Math.max(0, Math.floor(v * (1 - amount))); };
    return "#" + [d(c.r), d(c.g), d(c.b)]
      .map(function(n) { return n.toString(16).padStart(2, "0"); }).join("");
  }

  // ── live <style> injection ────────────────────────────────────────────────

  function getLiveStyleEl() {
    var el = document.getElementById("palette-live");
    if (!el) {
      el = document.createElement("style");
      el.id = "palette-live";
      document.head.appendChild(el);
    }
    return el;
  }

  // ── Google Font loader ────────────────────────────────────────────────────

  function loadGoogleFont(family) {
    if (!family) return;
    var linkId = "palette-google-font-link";
    var existing = document.getElementById(linkId);
    var href = "https://fonts.googleapis.com/css2?family="
             + family.replace(/ /g, "+")
             + ":ital,wght@0,300;0,400;0,700;1,400&display=swap";
    if (existing) {
      existing.href = href;
    } else {
      var link = document.createElement("link");
      link.id = linkId; link.rel = "stylesheet"; link.href = href;
      document.head.appendChild(link);
    }
  }

  // ── read current form values ──────────────────────────────────────────────

  function getFormValues() {
    var primaryPicker = document.getElementById("th-primary");
    var fontSelect    = document.getElementById("th-google-font");
    var cssTA         = document.getElementById("palette-custom-css");

    // All inputs/selects with data-css-var → :root  (primary handled separately)
    var rootVars = {};
    document.querySelectorAll("[data-css-var]").forEach(function(el) {
      if (el.id === "th-primary") return;
      var cssVar = el.getAttribute("data-css-var");
      var unit   = el.getAttribute("data-css-unit") || "";
      var val    = el.value;
      if (cssVar && val !== "" && val !== null) {
        rootVars[cssVar] = val + unit;
      }
    });

    // Inputs with data-css-selector → scoped rules
    var ruleMap = {};
    document.querySelectorAll("[data-css-selector]").forEach(function(el) {
      var sel  = el.getAttribute("data-css-selector");
      var prop = el.getAttribute("data-css-prop");
      var val  = el.value;
      if (sel && prop && val) {
        if (!ruleMap[sel]) ruleMap[sel] = {};
        ruleMap[sel][prop] = val;
      }
    });

    return {
      primaryColor: primaryPicker ? primaryPicker.value : null,
      fontFamily:   fontSelect    ? fontSelect.value    : "",
      rootVars:     rootVars,
      ruleMap:      ruleMap,
      customCss:    cssTA ? cssTA.value : ""
    };
  }

  // ── CSS builder ───────────────────────────────────────────────────────────

  function buildCss(primaryColor, fontFamily, rootVars, ruleMap, customCss) {
    var parts = [];

    // @import for Google Font
    if (fontFamily) {
      parts.push(
        "@import url('https://fonts.googleapis.com/css2?family="
        + fontFamily.replace(/ /g, "+")
        + ":ital,wght@0,300;0,400;0,700;1,400&display=swap');"
      );
    }

    // :root block
    var rootLines = [];
    if (fontFamily) {
      rootLines.push("  --bs-body-font-family: '" + fontFamily + "', sans-serif;");
    }
    // rootVars from data-css-var inputs (everything except primary)
    Object.keys(rootVars).forEach(function(cssVar) {
      if (cssVar === "--bs-primary") return; // primary handled below
      var val = rootVars[cssVar];
      if (val !== "" && val !== null) {
        rootLines.push("  " + cssVar + ": " + val + ";");
      }
    });
    // primary color vars
    if (primaryColor && primaryColor.startsWith("#")) {
      var rgb = hexToRgb(primaryColor);
      if (rgb) {
        var rgbStr = rgb.r + ", " + rgb.g + ", " + rgb.b;
        var hover  = darken(primaryColor);
        rootLines.push(
          "  --bs-primary: " + primaryColor + ";",
          "  --bs-primary-rgb: " + rgbStr + ";",
          "  --bs-link-color: " + primaryColor + ";",
          "  --bs-link-color-rgb: " + rgbStr + ";",
          "  --bs-link-hover-color: " + hover + ";",
          "  --plone-link-color: " + primaryColor + ";",
          "  --plone-link-hover-color: " + hover + ";"
        );
      }
    }
    if (rootLines.length) {
      parts.push(":root {\n" + rootLines.join("\n") + "\n}");
    }

    // .btn-primary and .btn-outline-primary rules
    if (primaryColor && primaryColor.startsWith("#")) {
      var rgb2 = hexToRgb(primaryColor);
      if (rgb2) {
        var hover2 = darken(primaryColor);
        parts.push(
          ".btn-primary {",
          "  --bs-btn-bg: " + primaryColor + ";",
          "  --bs-btn-border-color: " + primaryColor + ";",
          "  --bs-btn-hover-bg: " + hover2 + ";",
          "  --bs-btn-hover-border-color: " + hover2 + ";",
          "  --bs-btn-active-bg: " + hover2 + ";",
          "  --bs-btn-active-border-color: " + hover2 + ";",
          "  --bs-btn-disabled-bg: " + primaryColor + ";",
          "  --bs-btn-disabled-border-color: " + primaryColor + ";",
          "}",
          ".btn-outline-primary {",
          "  --bs-btn-color: " + primaryColor + ";",
          "  --bs-btn-border-color: " + primaryColor + ";",
          "  --bs-btn-hover-bg: " + primaryColor + ";",
          "  --bs-btn-hover-border-color: " + primaryColor + ";",
          "  --bs-btn-active-bg: " + primaryColor + ";",
          "  --bs-btn-active-border-color: " + primaryColor + ";",
          "  --bs-btn-disabled-color: " + primaryColor + ";",
          "  --bs-btn-disabled-border-color: " + primaryColor + ";",
          "}"
        );
      }
    }

    // Scoped selector rules from data-css-selector inputs
    Object.keys(ruleMap).forEach(function(sel) {
      var props = ruleMap[sel];
      var propLines = Object.keys(props).map(function(p) {
        return "  " + p + ": " + props[p] + ";";
      });
      if (propLines.length) {
        parts.push(sel + " {\n" + propLines.join("\n") + "\n}");
      }
    });

    if (customCss) {
      parts.push(customCss);
    }

    return parts.join("\n");
  }

  // ── apply live preview ────────────────────────────────────────────────────

  function applyLive() {
    var v = getFormValues();
    if (v.fontFamily) loadGoogleFont(v.fontFamily);
    getLiveStyleEl().textContent = buildCss(v.primaryColor, v.fontFamily, v.rootVars, v.ruleMap, v.customCss);
    var preview = document.getElementById("palette-generated-css");
    if (preview) { preview.value = getLiveStyleEl().textContent; }
  }

  // ── form init ─────────────────────────────────────────────────────────────

  function initForm(form) {
    if (form.dataset.customizerReady) return;
    form.dataset.customizerReady = "1";

    // Primary color picker — special handling (RGB vars + button rules)
    var picker = document.getElementById("th-primary");
    var text   = document.getElementById("th-primary-text");
    if (picker) {
      picker.addEventListener("input", function() {
        if (text) text.value = this.value;
        applyLive();
      });
    }
    if (text) {
      text.addEventListener("change", function() {
        var val = this.value.trim();
        if (/^#[0-9a-fA-F]{6}$/.test(val)) {
          if (picker) picker.value = val;
          applyLive();
        }
      });
    }

    // Google Font select
    var fontSelect = document.getElementById("th-google-font");
    if (fontSelect) {
      if (fontSelect.value) loadGoogleFont(fontSelect.value);
      fontSelect.addEventListener("change", function() { applyLive(); });
    }

    // Body font size range — has its own display span; handled separately
    var range   = document.getElementById("th-body-font-size");
    var display = document.getElementById("th-body-font-size-display");
    if (range) {
      range.addEventListener("input", function() {
        if (display) display.textContent = this.value;
        applyLive();
      });
    }

    // Custom CSS textarea
    var cssTA = document.getElementById("palette-custom-css");
    if (cssTA) {
      cssTA.addEventListener("input", function() { applyLive(); });
    }

    // Reset button
    var resetBtn = document.getElementById("palette-reset-btn");
    if (resetBtn) {
      resetBtn.addEventListener("click", function() { window.location.reload(); });
    }

    // Generic: all data-css-var and data-css-selector inputs (except those handled above)
    var specificIds = {
      "th-primary": true,
      "th-primary-text": true,
      "th-google-font": true,
      "th-body-font-size": true,
      "palette-custom-css": true,
      "palette-reset-btn": true
    };

    document.querySelectorAll("[data-css-var], [data-css-selector]").forEach(function(el) {
      if (specificIds[el.id]) return;
      var displayEl = document.getElementById(el.id + "-display");
      el.addEventListener("input", function() {
        if (displayEl) displayEl.textContent = this.value;
        applyLive();
      });
      el.addEventListener("change", function() { applyLive(); });
      // Sync text twin for color pickers
      if (el.type === "color") {
        var textEl = document.getElementById(el.id + "-text");
        if (textEl) {
          el.addEventListener("input", function() { textEl.value = this.value; });
          textEl.addEventListener("change", function() {
            var val = this.value.trim();
            if (/^#[0-9a-fA-F]{6}$/.test(val)) {
              el.value = val;
              applyLive();
            }
          });
        }
      }
    });

    applyLive();
  }

  // ── boot ──────────────────────────────────────────────────────────────────

  function checkAndInit() {
    var form = document.getElementById("palette-customizer-form");
    if (form) initForm(form);
  }

  var observer = new MutationObserver(checkAndInit);
  observer.observe(document.documentElement, { childList: true, subtree: true });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", checkAndInit);
  } else {
    checkAndInit();
  }
})();
