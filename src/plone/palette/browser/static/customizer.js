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

  // ── Bootstrap 6 token aliases (mirrors BOOTSTRAP6_ALIASES in customizer.py) ──
  // plonetheme.bootstrap6 runs on Bootstrap 6, which dropped the --bs- prefix.
  // Its --bs-* declarations are one-way aliases for legacy Mockup components,
  // so a preview that only writes --bs-* names changes nothing there. Every
  // declaration is emitted under both names; the surplus one is inert.

  var BOOTSTRAP6_ALIASES = {
    "--bs-primary": "--primary-base",
    "--bs-secondary": "--secondary-bg",
    "--bs-success": "--success-bg",
    "--bs-danger": "--danger-bg",
    "--bs-warning": "--warning-bg",
    "--bs-info": "--info-bg",
    "--bs-link-color": "--link-color",
    "--bs-link-hover-color": "--link-hover-color",
    "--bs-body-bg": "--bg-body",
    "--bs-body-color": "--fg-body",
    "--bs-heading-color": "--heading-color",
    "--bs-body-font-family": "--body-font-family",
    "--bs-body-font-size": "--body-font-size",
    "--bs-body-font-weight": "--body-font-weight",
    "--bs-body-line-height": "--body-line-height",
    "--bs-border-color": "--border-color",
    "--bs-border-width": "--border-width",
    "--bs-border-radius": "--radius-4",
    "--bs-border-radius-sm": "--radius-3",
    "--bs-border-radius-lg": "--radius-5",
    "--bs-border-radius-xl": "--radius-8",
    "--bs-border-radius-xxl": "--radius-9",
    "--bs-box-shadow": "--box-shadow",
    "--bs-box-shadow-sm": "--box-shadow-sm",
    "--bs-box-shadow-lg": "--box-shadow-lg"
  };

  // Push "  <var>: <val>;" plus its Bootstrap 6 alias, if there is one.
  function pushDecl(lines, cssVar, value) {
    lines.push("  " + cssVar + ": " + value + ";");
    var alias = BOOTSTRAP6_ALIASES[cssVar];
    if (alias) { lines.push("  " + alias + ": " + value + ";"); }
  }

  // ── Bootstrap property CSS maps (mirrors Python _DISABLED_CSS / _ENABLED_CSS) ──
  // Keyed by $enable-* flag name. Applied in buildCss when a checkbox is toggled.

  var PROPERTY_DEFAULTS = {
    enable_caret: true, enable_rounded: true, enable_transitions: true,
    enable_reduced_motion: true, enable_smooth_scroll: true,
    enable_grid_classes: true, enable_container_classes: true,
    enable_button_pointers: true, enable_rfs: true,
    enable_validation_icons: true, enable_negative_margins: true,
    enable_deprecation_messages: true,
    enable_shadows: false, enable_gradients: false,
    enable_cssgrid: false, enable_important_utilities: false
  };

  var DISABLED_CSS = {
    enable_caret:
      ".dropdown-toggle::after, .dropup .dropdown-toggle::after," +
      ".dropend .dropdown-toggle::after { display: none; }" +
      " .dropstart .dropdown-toggle::before { display: none; }",
    enable_rounded:
      ":root { --bs-border-radius: 0; --bs-border-radius-sm: 0;" +
      " --bs-border-radius-lg: 0; --bs-border-radius-xl: 0;" +
      " --bs-border-radius-xxl: 0; --bs-border-radius-pill: 0; }",
    enable_transitions:
      "*, *::before, *::after { transition: none !important; animation: none !important; }",
    enable_smooth_scroll:
      "html { scroll-behavior: auto !important; }",
    enable_button_pointers:
      ".btn:not(:disabled) { cursor: default; }",
    enable_validation_icons:
      ".form-control.is-valid, .was-validated .form-control:valid," +
      ".form-control.is-invalid, .was-validated .form-control:invalid" +
      " { background-image: none; padding-right: revert; }"
  };

  var ENABLED_CSS = {
    enable_shadows:
      ":root { --bs-box-shadow: 0 .5rem 1rem rgba(0,0,0,.15);" +
      " --bs-box-shadow-sm: 0 .125rem .25rem rgba(0,0,0,.075);" +
      " --bs-box-shadow-lg: 0 1rem 3rem rgba(0,0,0,.175);" +
      " --bs-box-shadow-inset: inset 0 1px 2px rgba(0,0,0,.075); }" +
      " .btn { box-shadow: var(--bs-box-shadow-sm); }" +
      " .card { box-shadow: var(--bs-box-shadow); }"
  };

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
    // (navbar is special-cased below: the two themes paint the bar differently)
    var ruleMap = {};
    document.querySelectorAll("[data-css-selector]").forEach(function(el) {
      if (el.id === "th-navbar-bg") return;
      var sel  = el.getAttribute("data-css-selector");
      var prop = el.getAttribute("data-css-prop");
      var val  = el.value;
      if (sel && prop && val) {
        if (!ruleMap[sel]) ruleMap[sel] = {};
        ruleMap[sel][prop] = val;
      }
    });

    // Properties checkboxes — collect which flags are currently checked
    var enabledProps = {};
    document.querySelectorAll("input[type=checkbox][name=enabled_properties]").forEach(function(cb) {
      if (cb.value) enabledProps[cb.value] = cb.checked;
    });

    var navbarPicker = document.getElementById("th-navbar-bg");

    return {
      navbarBg:     navbarPicker ? navbarPicker.value : "",
      primaryColor: primaryPicker ? primaryPicker.value : null,
      fontFamily:   fontSelect    ? fontSelect.value    : "",
      rootVars:     rootVars,
      ruleMap:      ruleMap,
      enabledProps: enabledProps,
      customCss:    cssTA ? cssTA.value : ""
    };
  }

  // ── CSS builder ───────────────────────────────────────────────────────────

  function buildCss(primaryColor, fontFamily, rootVars, ruleMap, enabledProps, customCss, navbarBg) {
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
      pushDecl(rootLines, "--bs-body-font-family", "'" + fontFamily + "', sans-serif");
    }
    // rootVars from data-css-var inputs (everything except primary)
    Object.keys(rootVars).forEach(function(cssVar) {
      if (cssVar === "--bs-primary") return; // primary handled below
      var val = rootVars[cssVar];
      if (val !== "" && val !== null) {
        pushDecl(rootLines, cssVar, val);
      }
    });
    // primary color vars
    if (primaryColor && primaryColor.startsWith("#")) {
      var rgb = hexToRgb(primaryColor);
      if (rgb) {
        var rgbStr = rgb.r + ", " + rgb.g + ", " + rgb.b;
        var hover  = darken(primaryColor);
        pushDecl(rootLines, "--bs-primary", primaryColor);
        pushDecl(rootLines, "--bs-link-color", primaryColor);
        pushDecl(rootLines, "--bs-link-hover-color", hover);
        rootLines.push(
          "  --bs-primary-rgb: " + rgbStr + ";",
          "  --bs-link-color-rgb: " + rgbStr + ";",
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

    // Navbar — mirrors _navbar_rules() in customizer.py. Barceloneta reads a
    // token off .navbar-barceloneta; bootstrap6 paints the bar in three places,
    // and missing any of them leaves the colour showing only at the edges.
    if (navbarBg) {
      parts.push(
        ".navbar-barceloneta { --bs-navbar-background: " + navbarBg + "; }",
        ".navbar-bootstrap6 { --navbar-bg: " + navbarBg + "; }",
        "#mainnavigation-wrapper:has(.navbar-bootstrap6),"
        + " .navbar-bootstrap6 .offcanvas .offcanvas-header,"
        + " .navbar-bootstrap6 .offcanvas .offcanvas-body"
        + " { background-color: " + navbarBg + "; }"
      );
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

    // Bootstrap $enable-* property overrides
    if (enabledProps) {
      Object.keys(PROPERTY_DEFAULTS).forEach(function(name) {
        var isEnabled = (name in enabledProps) ? enabledProps[name] : PROPERTY_DEFAULTS[name];
        if (!isEnabled && DISABLED_CSS[name]) {
          parts.push(DISABLED_CSS[name]);
        } else if (isEnabled && !PROPERTY_DEFAULTS[name] && ENABLED_CSS[name]) {
          parts.push(ENABLED_CSS[name]);
        }
      });
    }

    if (customCss) {
      parts.push(customCss);
    }

    return parts.join("\n");
  }

  // ── apply live preview ────────────────────────────────────────────────────

  function applyLive() {
    var v = getFormValues();
    if (v.fontFamily) loadGoogleFont(v.fontFamily);
    getLiveStyleEl().textContent = buildCss(v.primaryColor, v.fontFamily, v.rootVars, v.ruleMap, v.enabledProps, v.customCss, v.navbarBg);
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

    // Reset: restore every setting server-side, then reload so the inputs
    // repopulate from the (now default) registry. Confirm first — it is
    // destructive and cannot be undone.
    var resetBtn = document.getElementById("palette-reset-btn");
    if (resetBtn) {
      resetBtn.addEventListener("click", function (e) {
        e.preventDefault();
        if (!window.confirm(
            "Reset all theme settings (colors, fonts, borders, properties and " +
            "custom CSS) to their defaults? This cannot be undone.")) {
          return;
        }
        var body = new FormData();
        body.append("form.button.reset", "reset");
        var auth = form.querySelector('input[name="_authenticator"]');
        if (auth) body.append("_authenticator", auth.value);
        fetch(form.getAttribute("action"), { method: "POST", body: body, credentials: "same-origin" })
          .then(function () { window.location.reload(); })
          .catch(function () { window.location.reload(); });
      });
    }

    // Properties checkboxes — wire change → applyLive (pat-checklist re-fires change events)
    form.querySelectorAll("input[type=checkbox][name=enabled_properties]").forEach(function(cb) {
      cb.addEventListener("change", function() { applyLive(); });
    });

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

    // No initial applyLive(): the saved stylesheet is already linked in the
    // page, and the form is on every page for managers now. Previewing on
    // load would paint the form's defaults over a freshly reset site, so the
    // preview starts with the first change instead.
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
