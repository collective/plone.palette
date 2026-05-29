from plone import api
from plone.app.layout.viewlets.common import ViewletBase
from plone.app.theming.interfaces import IThemeSettings
from plone.registry.interfaces import IRegistry
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility

import logging

_log = logging.getLogger(__name__)

COLOR_FIELDS = ("primary", "secondary", "success", "danger", "warning", "info")

# Plone-specific color fields from _variables.colors.plone.scss
# (field_name, css_var, label, default_hex)
PLONE_UI_COLOR_FIELDS = (
    ("plone_link_color_on_dark",    "--plone-link-color-on-dark",    "Link on dark bg",   "#16a1e3"),
    ("plone_link_color_on_grey",    "--plone-link-color-on-grey",    "Link on grey bg",   "#086ca3"),
    ("plone_portlet_list_hover_bg", "--plone-portlet-list-hover-bg", "Portlet hover bg",  "#fcfcfd"),
    ("plone_portlet_footer_bg",     "--plone-portlet-footer-bg",     "Portlet footer bg", "#fcfcfd"),
    ("plone_portlet_list_bullet",   "--plone-portlet-list-bullet",   "Portlet bullet",    "#64bee8"),
)

STATE_COLOR_FIELDS = (
    ("state_draft_color",                "--plone-state-draft",                "Draft",                "#fab82a"),
    ("state_pending_color",              "--plone-state-pending",              "Pending",              "#ccd111"),
    ("state_private_color",             "--plone-state-private",              "Private",              "#c4183c"),
    ("state_internal_color",             "--plone-state-internal",             "Internal",             "#fab82a"),
    ("state_internally_published_color", "--plone-state-internally-published", "Internally published", "#883dfa"),
)

# (field_name, css_var, default, css_unit)  — write to :root
BORDER_NUMBER_FIELDS = (
    ("border_width",      "--bs-border-width",     "1",     "px"),
    ("border_radius",     "--bs-border-radius",    "0.375", "rem"),
    ("border_radius_sm",  "--bs-border-radius-sm", "0.25",  "rem"),
    ("border_radius_lg",  "--bs-border-radius-lg", "0.5",   "rem"),
    ("border_radius_xl",  "--bs-border-radius-xl", "1",     "rem"),
    ("border_radius_xxl", "--bs-border-radius-xxl","2",     "rem"),
)
SHADOW_TEXT_FIELDS = (
    ("box_shadow",    "--bs-box-shadow",    "0 .5rem 1rem rgba(0,0,0,.15)",      ""),
    ("box_shadow_sm", "--bs-box-shadow-sm", "0 .125rem .25rem rgba(0,0,0,.075)", ""),
    ("box_shadow_lg", "--bs-box-shadow-lg", "0 1rem 3rem rgba(0,0,0,.175)",      ""),
)
BORDER_COLOR_FIELDS_EXTRA = (
    ("border_color", "--bs-border-color", "#dee2e6"),
)
TYPOGRAPHY_COLOR_FIELDS_EXTRA = (
    ("body_color",    "--bs-body-color",    "#212529"),
    ("body_bg",       "--bs-body-bg",       "#ffffff"),
    ("heading_color", "--bs-heading-color", "#212529"),
)
TYPOGRAPHY_VAR_FIELDS = (
    ("body_font_weight", "--bs-body-font-weight", "400", ""),
    ("body_line_height", "--bs-body-line-height", "1.5", ""),
)
NAVBAR_FOOTER_FIELDS = (
    ("navbar_bg",    "#007bb1"),
    ("footer_bg",    "#212529"),
    ("footer_color", "#dee2e6"),
)

COLOR_DEFAULTS = {
    "primary":   "#0d6efd",
    "secondary": "#6c757d",
    "success":   "#198754",
    "danger":    "#dc3545",
    "warning":   "#ffc107",
    "info":      "#0dcaf0",
}

# Bootstrap $enable-* variables from _variables.properties.scss
# (name, label, default)
BOOTSTRAP_PROPERTIES = (
    ("enable_caret",               "Caret on dropdowns",            True),
    ("enable_rounded",             "Rounded corners",               True),
    ("enable_shadows",             "Box shadows",                   False),
    ("enable_gradients",           "Gradients on buttons",          False),
    ("enable_transitions",         "CSS transitions",               True),
    ("enable_reduced_motion",      "Respect reduced-motion",        True),
    ("enable_smooth_scroll",       "Smooth scroll",                 True),
    ("enable_grid_classes",        "Grid utility classes",          True),
    ("enable_container_classes",   "Container classes",             True),
    ("enable_cssgrid",             "CSS Grid layout mode",          False),
    ("enable_button_pointers",     "Pointer cursor on buttons",     True),
    ("enable_rfs",                 "Responsive font scaling (RFS)", True),
    ("enable_validation_icons",    "Validation icons",              True),
    ("enable_negative_margins",    "Negative margin utilities",     True),
    ("enable_important_utilities", "!important on utilities",       False),
)

# CSS injected at runtime when a property is DISABLED (i.e. not in enabled list)
# Only properties whose effect can be replicated with CSS custom properties or
# simple overrides are listed here; compile-time-only flags are skipped.
_DISABLED_CSS = {
    "enable_caret": (
        ".dropdown-toggle::after,"
        ".dropup .dropdown-toggle::after,"
        ".dropend .dropdown-toggle::after { display: none; }"
        " .dropstart .dropdown-toggle::before { display: none; }"
    ),
    "enable_rounded": (
        ":root {"
        " --bs-border-radius: 0;"
        " --bs-border-radius-sm: 0;"
        " --bs-border-radius-lg: 0;"
        " --bs-border-radius-xl: 0;"
        " --bs-border-radius-xxl: 0;"
        " --bs-border-radius-pill: 0; }"
    ),
    "enable_transitions": (
        "*, *::before, *::after { transition: none !important; animation: none !important; }"
    ),
    "enable_smooth_scroll": (
        "html { scroll-behavior: auto !important; }"
    ),
    "enable_button_pointers": (
        ".btn:not(:disabled) { cursor: default; }"
    ),
    "enable_validation_icons": (
        ".form-control.is-valid, .was-validated .form-control:valid,"
        ".form-control.is-invalid, .was-validated .form-control:invalid"
        " { background-image: none; padding-right: revert; }"
    ),
}

# CSS injected when a property is ENABLED but its Bootstrap default is False
_ENABLED_CSS = {
    "enable_shadows": (
        ":root {"
        " --bs-box-shadow: 0 .5rem 1rem rgba(0,0,0,.15);"
        " --bs-box-shadow-sm: 0 .125rem .25rem rgba(0,0,0,.075);"
        " --bs-box-shadow-lg: 0 1rem 3rem rgba(0,0,0,.175);"
        " --bs-box-shadow-inset: inset 0 1px 2px rgba(0,0,0,.075); }"
        " .btn { box-shadow: var(--bs-box-shadow-sm); }"
        " .card { box-shadow: var(--bs-box-shadow); }"
    ),
}


def _hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _darken(hex_color, amount=0.1):
    r, g, b = _hex_to_rgb(hex_color)
    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_css(colors, custom_css="", body_font_size=None, enabled_properties=None,
                 plone_colors=None, google_font_family=None,
                 extra_root_vars=None, extra_css_rules=None):
    """Build Bootstrap 5 CSS variable overrides for colors, typography and properties."""
    import_lines = []
    root_vars = []
    btn_rules = []
    extra_rules = []

    if google_font_family:
        family_param = google_font_family.replace(" ", "+")
        import_lines.append(
            f"@import url('https://fonts.googleapis.com/css2"
            f"?family={family_param}:ital,wght@0,300;0,400;0,700;1,400&display=swap');"
        )
        root_vars.append(f"  --bs-body-font-family: '{google_font_family}', sans-serif;")

    if body_font_size:
        try:
            float(body_font_size)
            root_vars.append(f"  --bs-body-font-size: {body_font_size}rem;")
        except (ValueError, TypeError):
            pass

    # Plone-specific CSS custom properties
    if plone_colors:
        for css_var, color in plone_colors.items():
            if color and color.startswith("#"):
                root_vars.append(f"  {css_var}: {color};")

    if extra_root_vars:
        for css_var, value in extra_root_vars.items():
            if value:
                root_vars.append(f"  {css_var}: {value};")

    for name in COLOR_FIELDS:
        color = colors.get(name, "")
        if not color or not color.startswith("#"):
            continue
        try:
            r, g, b = _hex_to_rgb(color)
        except (ValueError, IndexError):
            continue
        rgb_str = f"{r}, {g}, {b}"
        hover = _darken(color)

        root_vars += [
            f"  --bs-{name}: {color};",
            f"  --bs-{name}-rgb: {rgb_str};",
        ]
        if name == "primary":
            root_vars += [
                f"  --bs-link-color: {color};",
                f"  --bs-link-color-rgb: {rgb_str};",
                f"  --bs-link-hover-color: {hover};",
            ]

        btn_rules += [
            f".btn-{name} {{",
            f"  --bs-btn-bg: {color};",
            f"  --bs-btn-border-color: {color};",
            f"  --bs-btn-hover-bg: {hover};",
            f"  --bs-btn-hover-border-color: {hover};",
            f"  --bs-btn-active-bg: {hover};",
            f"  --bs-btn-active-border-color: {hover};",
            f"  --bs-btn-disabled-bg: {color};",
            f"  --bs-btn-disabled-border-color: {color};",
            f"}}",
        ]

    # Bootstrap property overrides
    if enabled_properties is not None:
        enabled_set = set(enabled_properties)
        for name, _label, default in BOOTSTRAP_PROPERTIES:
            is_enabled = name in enabled_set
            if not is_enabled and name in _DISABLED_CSS:
                extra_rules.append(_DISABLED_CSS[name])
            elif is_enabled and not default and name in _ENABLED_CSS:
                extra_rules.append(_ENABLED_CSS[name])

    if extra_css_rules:
        extra_rules.extend(extra_css_rules)

    if not import_lines and not root_vars and not btn_rules and not extra_rules:
        return custom_css or ""

    parts = []
    parts.extend(import_lines)
    if root_vars:
        parts.append(":root {\n" + "\n".join(root_vars) + "\n}")
    parts.extend(btn_rules)
    parts.extend(extra_rules)
    if custom_css:
        parts.append(custom_css)
    return "\n".join(parts)


class _CustomizerMixin:
    """Shared read properties for view and viewlet."""

    def _get_color(self, name):
        try:
            return (
                api.portal.get_registry_record(f"plone.palette.{name}_color")
                or COLOR_DEFAULTS[name]
            )
        except Exception:
            return COLOR_DEFAULTS[name]

    @property
    def colors(self):
        return {name: self._get_color(name) for name in COLOR_FIELDS}

    @property
    def primary_color(self):   return self._get_color("primary")
    @property
    def secondary_color(self): return self._get_color("secondary")
    @property
    def success_color(self):   return self._get_color("success")
    @property
    def danger_color(self):    return self._get_color("danger")
    @property
    def warning_color(self):   return self._get_color("warning")
    @property
    def info_color(self):      return self._get_color("info")

    def _get_plone_color(self, field_name, default):
        try:
            return api.portal.get_registry_record(f"plone.palette.{field_name}") or default
        except Exception:
            return default

    def _get_field(self, name, default=""):
        try:
            return api.portal.get_registry_record(f"plone.palette.{name}") or default
        except Exception:
            return default

    @property
    def plone_ui_colors(self):
        """List of (field_name, css_var, label, value) for template iteration."""
        return [
            (fn, cv, lbl, self._get_plone_color(fn, dflt))
            for fn, cv, lbl, dflt in PLONE_UI_COLOR_FIELDS
        ]

    @property
    def state_colors(self):
        """List of (field_name, css_var, label, value) for template iteration."""
        return [
            (fn, cv, lbl, self._get_plone_color(fn, dflt))
            for fn, cv, lbl, dflt in STATE_COLOR_FIELDS
        ]

    def _all_plone_colors(self):
        """Dict of css_var → color for all Plone-specific fields."""
        result = {}
        for fn, cv, _lbl, dflt in PLONE_UI_COLOR_FIELDS + STATE_COLOR_FIELDS:
            result[cv] = self._get_plone_color(fn, dflt)
        return result

    @property
    def body_font_size(self):
        try:
            return api.portal.get_registry_record("plone.palette.body_font_size") or "1"
        except Exception:
            return "1"

    @property
    def google_font_family(self):
        try:
            return api.portal.get_registry_record("plone.palette.google_font_family") or ""
        except Exception:
            return ""

    # Borders
    @property
    def border_width(self): return self._get_field("border_width", "1")
    @property
    def border_color(self): return self._get_field("border_color", "#dee2e6")
    @property
    def border_radius(self): return self._get_field("border_radius", "0.375")
    @property
    def border_radius_sm(self): return self._get_field("border_radius_sm", "0.25")
    @property
    def border_radius_lg(self): return self._get_field("border_radius_lg", "0.5")
    @property
    def border_radius_xl(self): return self._get_field("border_radius_xl", "1")
    @property
    def border_radius_xxl(self): return self._get_field("border_radius_xxl", "2")
    @property
    def box_shadow(self): return self._get_field("box_shadow", "0 .5rem 1rem rgba(0,0,0,.15)")
    @property
    def box_shadow_sm(self): return self._get_field("box_shadow_sm", "0 .125rem .25rem rgba(0,0,0,.075)")
    @property
    def box_shadow_lg(self): return self._get_field("box_shadow_lg", "0 1rem 3rem rgba(0,0,0,.175)")

    # Typography extras
    @property
    def body_color(self): return self._get_field("body_color", "#212529")
    @property
    def body_bg(self): return self._get_field("body_bg", "#ffffff")
    @property
    def heading_color(self): return self._get_field("heading_color", "#212529")
    @property
    def body_font_weight(self): return self._get_field("body_font_weight", "400")
    @property
    def body_line_height(self): return self._get_field("body_line_height", "1.5")

    # Navbar & Footer
    @property
    def navbar_bg(self): return self._get_field("navbar_bg", "#007bb1")
    @property
    def footer_bg(self): return self._get_field("footer_bg", "#212529")
    @property
    def footer_color(self): return self._get_field("footer_color", "#dee2e6")

    @property
    def enabled_properties(self):
        try:
            return list(
                api.portal.get_registry_record("plone.palette.enabled_properties") or []
            )
        except Exception:
            return [name for name, _label, default in BOOTSTRAP_PROPERTIES if default]

    @property
    def bootstrap_properties(self):
        """Return BOOTSTRAP_PROPERTIES for template iteration."""
        return BOOTSTRAP_PROPERTIES

    @property
    def custom_css(self):
        try:
            return api.portal.get_registry_record("plone.palette.custom_css") or ""
        except Exception:
            return ""

    @property
    def generated_css(self):
        extra_root_vars = {}
        for fn, cv, dflt, unit in BORDER_NUMBER_FIELDS:
            v = self._get_field(fn, dflt)
            if v:
                extra_root_vars[cv] = v + unit
        for fn, cv, dflt, unit in SHADOW_TEXT_FIELDS:
            v = self._get_field(fn, dflt)
            if v:
                extra_root_vars[cv] = v
        for fn, cv, dflt in BORDER_COLOR_FIELDS_EXTRA + TYPOGRAPHY_COLOR_FIELDS_EXTRA:
            v = self._get_field(fn, dflt)
            if v:
                extra_root_vars[cv] = v
        for fn, cv, dflt, unit in TYPOGRAPHY_VAR_FIELDS:
            v = self._get_field(fn, dflt)
            if v:
                extra_root_vars[cv] = v

        extra_css_rules = []
        nb = self._get_field("navbar_bg", "#007bb1")
        if nb:
            extra_css_rules.append(f".navbar-barceloneta {{ --bs-navbar-background: {nb}; }}")
        fb = self._get_field("footer_bg", "#212529")
        fc = self._get_field("footer_color", "#dee2e6")
        if fb or fc:
            props = ""
            if fb:
                props += f"  background-color: {fb};\n"
            if fc:
                props += f"  color: {fc};\n"
            extra_css_rules.append(f"#portal-footer-wrapper {{\n{props}}}")

        return generate_css(
            self.colors, self.custom_css, self.body_font_size,
            self.enabled_properties, self._all_plone_colors(),
            self.google_font_family, extra_root_vars, extra_css_rules,
        )


class CustomizerView(_CustomizerMixin, BrowserView):
    """Renders the TTW Theming form inside the Plone main template."""

    index = ViewPageTemplateFile("templates/customizer.pt")

    def __call__(self):
        return self.index()

    @property
    def google_fonts_terms(self):
        """Returns [(value, title), ...] for the font select box."""
        from zope.component import queryUtility
        from zope.schema.interfaces import IVocabularyFactory
        factory = queryUtility(IVocabularyFactory, name="plone.palette.GoogleFonts")
        if factory is None:
            return [("", "— system default —")]
        try:
            vocab = factory(self.context)
            return [(t.value, t.title) for t in vocab]
        except Exception:
            _log.warning("Could not load Google Fonts vocabulary")
            return [("", "— system default —")]


class SaveCustomizerView(BrowserView):
    """POST endpoint for pat-inject: saves colors + custom CSS, returns HTML feedback."""

    def __call__(self):
        response = self.request.response
        response.setHeader("Content-Type", "text/html; charset=utf-8")

        if self.request.get("REQUEST_METHOD", "GET") != "POST":
            return '<div id="form-feedback" class="alert alert-error"><p>POST required.</p></div>'

        form = self.request.form
        try:
            colors = {}
            for name in COLOR_FIELDS:
                color = (form.get(f"{name}_color") or "").strip()
                if color and color.startswith("#"):
                    api.portal.set_registry_record(
                        f"plone.palette.{name}_color", color
                    )
                    colors[name] = color
                else:
                    try:
                        colors[name] = (
                            api.portal.get_registry_record(
                                f"plone.palette.{name}_color"
                            ) or COLOR_DEFAULTS[name]
                        )
                    except Exception:
                        colors[name] = COLOR_DEFAULTS[name]

            # Plone color fields
            plone_colors = {}
            for fn, cv, _lbl, dflt in PLONE_UI_COLOR_FIELDS + STATE_COLOR_FIELDS:
                color = (form.get(fn) or "").strip()
                if color and color.startswith("#"):
                    api.portal.set_registry_record(f"plone.palette.{fn}", color)
                else:
                    try:
                        color = api.portal.get_registry_record(f"plone.palette.{fn}") or dflt
                    except Exception:
                        color = dflt
                plone_colors[cv] = color

            google_font_family = (form.get("google_font_family") or "").strip()
            api.portal.set_registry_record("plone.palette.google_font_family", google_font_family)

            # Border, shadow, typography-extra and navbar/footer fields
            extra_root_vars = {}
            for fn, cv, dflt, unit in BORDER_NUMBER_FIELDS:
                v = (form.get(fn) or "").strip()
                if not v:
                    try:
                        v = api.portal.get_registry_record(f"plone.palette.{fn}") or dflt
                    except Exception:
                        v = dflt
                else:
                    api.portal.set_registry_record(f"plone.palette.{fn}", v)
                if v:
                    extra_root_vars[cv] = v + unit

            for fn, cv, dflt, unit in SHADOW_TEXT_FIELDS:
                v = (form.get(fn) or "").strip()
                if not v:
                    try:
                        v = api.portal.get_registry_record(f"plone.palette.{fn}") or dflt
                    except Exception:
                        v = dflt
                else:
                    api.portal.set_registry_record(f"plone.palette.{fn}", v)
                if v:
                    extra_root_vars[cv] = v

            for fn, cv, dflt in BORDER_COLOR_FIELDS_EXTRA + TYPOGRAPHY_COLOR_FIELDS_EXTRA:
                v = (form.get(fn) or "").strip()
                if not v:
                    try:
                        v = api.portal.get_registry_record(f"plone.palette.{fn}") or dflt
                    except Exception:
                        v = dflt
                else:
                    api.portal.set_registry_record(f"plone.palette.{fn}", v)
                if v:
                    extra_root_vars[cv] = v

            for fn, cv, dflt, unit in TYPOGRAPHY_VAR_FIELDS:
                v = (form.get(fn) or "").strip()
                if not v:
                    try:
                        v = api.portal.get_registry_record(f"plone.palette.{fn}") or dflt
                    except Exception:
                        v = dflt
                else:
                    api.portal.set_registry_record(f"plone.palette.{fn}", v)
                if v:
                    extra_root_vars[cv] = v

            extra_css_rules = []
            nb = (form.get("navbar_bg") or "").strip()
            if not nb:
                try:
                    nb = api.portal.get_registry_record("plone.palette.navbar_bg") or "#007bb1"
                except Exception:
                    nb = "#007bb1"
            else:
                api.portal.set_registry_record("plone.palette.navbar_bg", nb)
            if nb:
                extra_css_rules.append(f".navbar-barceloneta {{ --bs-navbar-background: {nb}; }}")

            fb = (form.get("footer_bg") or "").strip()
            if not fb:
                try:
                    fb = api.portal.get_registry_record("plone.palette.footer_bg") or "#212529"
                except Exception:
                    fb = "#212529"
            else:
                api.portal.set_registry_record("plone.palette.footer_bg", fb)

            fc = (form.get("footer_color") or "").strip()
            if not fc:
                try:
                    fc = api.portal.get_registry_record("plone.palette.footer_color") or "#dee2e6"
                except Exception:
                    fc = "#dee2e6"
            else:
                api.portal.set_registry_record("plone.palette.footer_color", fc)

            if fb or fc:
                props = ""
                if fb:
                    props += f"  background-color: {fb};\n"
                if fc:
                    props += f"  color: {fc};\n"
                extra_css_rules.append(f"#portal-footer-wrapper {{\n{props}}}")

            body_font_size = (form.get("body_font_size") or "").strip()
            if body_font_size:
                try:
                    float(body_font_size)
                    api.portal.set_registry_record("plone.palette.body_font_size", body_font_size)
                except (ValueError, TypeError):
                    body_font_size = None
            if not body_font_size:
                try:
                    body_font_size = api.portal.get_registry_record("plone.palette.body_font_size") or "1"
                except Exception:
                    body_font_size = "1"

            # Checkboxes: only checked ones are submitted; hidden sentinel ensures
            # the key is always present so an all-unchecked state still saves correctly.
            raw = form.get("enabled_properties", [])
            if isinstance(raw, str):
                raw = [raw]
            valid_names = {name for name, _label, _default in BOOTSTRAP_PROPERTIES}
            enabled_properties = [v for v in raw if v in valid_names]
            api.portal.set_registry_record(
                "plone.palette.enabled_properties", enabled_properties
            )

            custom_css = (form.get("custom_css") or "").strip()
            api.portal.set_registry_record("plone.palette.custom_css", custom_css)

            generated = generate_css(colors, custom_css, body_font_size, enabled_properties, plone_colors, google_font_family, extra_root_vars, extra_css_rules)
            registry = getUtility(IRegistry)
            theme_settings = registry.forInterface(IThemeSettings, False)
            theme_settings.custom_css = generated

            return '<div class="alert alert-success">Value saved!</div>'

        except Exception as e:
            _log.exception("Error saving theme settings")
            return (
                f'<div id="form-feedback" class="alert alert-error">'
                f"<p>Error: {e}</p></div>"
            )


class CustomizerViewlet(_CustomizerMixin, ViewletBase):
    """Renders the offcanvas theme customizer + sidebar trigger for managers."""

    index = ViewPageTemplateFile("templates/customizer_viewlet.pt")

    @property
    def available(self):
        return api.user.has_permission("Manage portal", obj=self.context)

    def render(self):
        if not self.available:
            return ""
        return self.index()
