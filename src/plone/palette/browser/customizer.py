from datetime import datetime
from plone import api
from plone.app.layout.viewlets.common import ViewletBase
from plone.app.theming.interfaces import IThemeSettings
from plone.palette.interfaces import IPaletteSettings
from plone.registry.interfaces import IRegistry
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility
from zope.component import queryUtility
from zope.schema import getFields
from zope.schema.interfaces import IVocabularyFactory

import logging


_log = logging.getLogger(__name__)

COLOR_FIELDS = ("primary", "secondary", "success", "danger", "warning", "info")

# Plone-specific color fields from _variables.colors.plone.scss
# (field_name, css_var, label, default_hex)
PLONE_UI_COLOR_FIELDS = (
    (
        "plone_link_color_on_dark",
        "--plone-link-color-on-dark",
        "Link on dark bg",
        "#16a1e3",
    ),
    (
        "plone_link_color_on_grey",
        "--plone-link-color-on-grey",
        "Link on grey bg",
        "#086ca3",
    ),
    (
        "plone_portlet_list_hover_bg",
        "--plone-portlet-list-hover-bg",
        "Portlet hover bg",
        "#fcfcfd",
    ),
    (
        "plone_portlet_footer_bg",
        "--plone-portlet-footer-bg",
        "Portlet footer bg",
        "#fcfcfd",
    ),
    (
        "plone_portlet_list_bullet",
        "--plone-portlet-list-bullet",
        "Portlet bullet",
        "#64bee8",
    ),
)

STATE_COLOR_FIELDS = (
    ("state_draft_color", "--plone-state-draft", "Draft", "#fab82a"),
    ("state_pending_color", "--plone-state-pending", "Pending", "#ccd111"),
    ("state_private_color", "--plone-state-private", "Private", "#c4183c"),
    ("state_internal_color", "--plone-state-internal", "Internal", "#fab82a"),
    (
        "state_internally_published_color",
        "--plone-state-internally-published",
        "Internally published",
        "#883dfa",
    ),
)

# (field_name, css_var, default, css_unit)  — write to :root
BORDER_NUMBER_FIELDS = (
    ("border_width", "--bs-border-width", "1", "px"),
    ("border_radius", "--bs-border-radius", "0.375", "rem"),
    ("border_radius_sm", "--bs-border-radius-sm", "0.25", "rem"),
    ("border_radius_lg", "--bs-border-radius-lg", "0.5", "rem"),
    ("border_radius_xl", "--bs-border-radius-xl", "1", "rem"),
    ("border_radius_xxl", "--bs-border-radius-xxl", "2", "rem"),
)
SHADOW_TEXT_FIELDS = (
    ("box_shadow", "--bs-box-shadow", "0 .5rem 1rem rgba(0,0,0,.15)", ""),
    ("box_shadow_sm", "--bs-box-shadow-sm", "0 .125rem .25rem rgba(0,0,0,.075)", ""),
    ("box_shadow_lg", "--bs-box-shadow-lg", "0 1rem 3rem rgba(0,0,0,.175)", ""),
)
BORDER_COLOR_FIELDS_EXTRA = (("border_color", "--bs-border-color", "#dee2e6"),)
TYPOGRAPHY_COLOR_FIELDS_EXTRA = (
    ("body_color", "--bs-body-color", "#212529"),
    ("body_bg", "--bs-body-bg", "#ffffff"),
    ("heading_color", "--bs-heading-color", "#212529"),
)
TYPOGRAPHY_VAR_FIELDS = (
    ("body_font_weight", "--bs-body-font-weight", "400", ""),
    ("body_line_height", "--bs-body-line-height", "1.5", ""),
)
NAVBAR_FOOTER_FIELDS = (
    ("navbar_bg", "#007bb1"),
    ("footer_bg", "#212529"),
    ("footer_color", "#dee2e6"),
)

COLOR_DEFAULTS = {
    "primary": "#0d6efd",
    "secondary": "#6c757d",
    "success": "#198754",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "info": "#0dcaf0",
}

# Bootstrap $enable-* variables from _variables.properties.scss
# (name, label, default)
BOOTSTRAP_PROPERTIES = (
    ("enable_caret", "Caret on dropdowns", True),
    ("enable_rounded", "Rounded corners", True),
    ("enable_shadows", "Box shadows", False),
    ("enable_gradients", "Gradients on buttons", False),
    ("enable_transitions", "CSS transitions", True),
    ("enable_reduced_motion", "Respect reduced-motion", True),
    ("enable_smooth_scroll", "Smooth scroll", True),
    ("enable_grid_classes", "Grid utility classes", True),
    ("enable_container_classes", "Container classes", True),
    ("enable_cssgrid", "CSS Grid layout mode", False),
    ("enable_button_pointers", "Pointer cursor on buttons", True),
    ("enable_rfs", "Responsive font scaling (RFS)", True),
    ("enable_validation_icons", "Validation icons", True),
    ("enable_negative_margins", "Negative margin utilities", True),
    ("enable_important_utilities", "!important on utilities", False),
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
    "enable_smooth_scroll": ("html { scroll-behavior: auto !important; }"),
    "enable_button_pointers": (".btn:not(:disabled) { cursor: default; }"),
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


# plonetheme.bootstrap6 is built on Bootstrap 6, which dropped the --bs- prefix
# and renamed the semantic tokens.  Its own --bs-* declarations are *one-way*
# aliases kept for legacy Mockup components (--bs-primary: var(--primary-base)),
# so a stylesheet that only writes --bs-* names has no effect on that theme —
# nothing reads them back.  Mapping every declaration onto its Bootstrap 6 name
# as well keeps one generated stylesheet working on Barceloneta and bootstrap6
# alike; the extra declarations are inert on whichever theme is not active.
#
# --primary-base is the one to set for the brand colour: the theme derives
# --primary-bg, --link-color, --navbar-bg and every .btn-primary token from it
# (hover shades included, via oklch()), so no per-button rules are needed.
# Radii map onto Bootstrap 6's numeric scale, matching the Bootstrap 5 default
# each step corresponds to (sm .25 → radius-3, base .375 → radius-4, ...).
BOOTSTRAP6_ALIASES = {
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
    "--bs-box-shadow-lg": "--box-shadow-lg",
}


def _navbar_rules(color):
    """Navbar background for both themes.

    Barceloneta reads --bs-navbar-background off .navbar-barceloneta.  The
    bootstrap6 theme paints the bar in three places, all defaulting to
    var(--primary-base): the --navbar-bg token on .navbar-bootstrap6, the
    #mainnavigation-wrapper band behind it, and the offcanvas panel the nav
    collapses into.  Miss any of them and the picked colour only shows at the
    edges of the bar.
    """
    return [
        f".navbar-barceloneta {{ --bs-navbar-background: {color}; }}",
        f".navbar-bootstrap6 {{ --navbar-bg: {color}; }}",
        # #mainnavigation-wrapper exists in both themes, so scope it by the
        # bootstrap6 navbar it wraps — Barceloneta paints the bar through its
        # own token above and must not be touched here.  The offcanvas rule is
        # three classes deep because the theme's own rule is, and a shallower
        # selector loses to it.
        "#mainnavigation-wrapper:has(.navbar-bootstrap6),"
        " .navbar-bootstrap6 .offcanvas .offcanvas-header,"
        " .navbar-bootstrap6 .offcanvas .offcanvas-body"
        f" {{ background-color: {color}; }}",
    ]


def _root_declarations(pairs):
    """Render (css_var, value) pairs, each followed by its Bootstrap 6 alias."""
    lines = []
    for css_var, value in pairs:
        lines.append(f"  {css_var}: {value};")
        alias = BOOTSTRAP6_ALIASES.get(css_var)
        if alias:
            lines.append(f"  {alias}: {value};")
    return lines


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


def generate_css(
    colors,
    custom_css="",
    body_font_size=None,
    enabled_properties=None,
    plone_colors=None,
    google_font_family=None,
    extra_root_vars=None,
    extra_css_rules=None,
):
    """Build CSS custom property overrides for colors, typography and properties.

    Declarations are emitted under both the Bootstrap 5 (--bs-*) and the
    Bootstrap 6 names, so the result applies to Barceloneta and to
    plonetheme.bootstrap6 — see BOOTSTRAP6_ALIASES.
    """
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
        root_vars.append((
            "--bs-body-font-family",
            f"'{google_font_family}', sans-serif",
        ))

    if body_font_size:
        try:
            float(body_font_size)
            root_vars.append(("--bs-body-font-size", f"{body_font_size}rem"))
        except (ValueError, TypeError):
            pass

    # Plone-specific CSS custom properties
    if plone_colors:
        for css_var, color in plone_colors.items():
            if color and color.startswith("#"):
                root_vars.append((css_var, color))

    if extra_root_vars:
        for css_var, value in extra_root_vars.items():
            if value:
                root_vars.append((css_var, value))

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
            (f"--bs-{name}", color),
            (f"--bs-{name}-rgb", rgb_str),
        ]
        if name == "primary":
            root_vars += [
                ("--bs-link-color", color),
                ("--bs-link-color-rgb", rgb_str),
                ("--bs-link-hover-color", hover),
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
            "}",
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
        parts.append(":root {\n" + "\n".join(_root_declarations(root_vars)) + "\n}")
    parts.extend(btn_rules)
    parts.extend(extra_rules)
    if custom_css:
        parts.append(custom_css)
    return "\n".join(parts)


class _CustomizerMixin:
    """Shared read properties for view and viewlets."""

    # The customizer form itself, as a macro: rendered both by the standalone
    # @@palette-customizer page and by the offcanvas in the toolbar viewlet.
    form_template = ViewPageTemplateFile("templates/customizer_form.pt")

    @property
    def google_fonts_terms(self):
        """Returns [(value, title), ...] for the font select box."""
        factory = queryUtility(IVocabularyFactory, name="plone.palette.GoogleFonts")
        if factory is None:
            return [("", "— system default —")]
        try:
            vocab = factory(self.context)
            return [(t.value, t.title) for t in vocab]
        except Exception:
            _log.warning("Could not load Google Fonts vocabulary")
            return [("", "— system default —")]

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
    def primary_color(self):
        return self._get_color("primary")

    @property
    def secondary_color(self):
        return self._get_color("secondary")

    @property
    def success_color(self):
        return self._get_color("success")

    @property
    def danger_color(self):
        return self._get_color("danger")

    @property
    def warning_color(self):
        return self._get_color("warning")

    @property
    def info_color(self):
        return self._get_color("info")

    def _get_plone_color(self, field_name, default):
        try:
            return (
                api.portal.get_registry_record(f"plone.palette.{field_name}") or default
            )
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
            return (
                api.portal.get_registry_record("plone.palette.google_font_family") or ""
            )
        except Exception:
            return ""

    # Borders
    @property
    def border_width(self):
        return self._get_field("border_width", "1")

    @property
    def border_color(self):
        return self._get_field("border_color", "#dee2e6")

    @property
    def border_radius(self):
        return self._get_field("border_radius", "0.375")

    @property
    def border_radius_sm(self):
        return self._get_field("border_radius_sm", "0.25")

    @property
    def border_radius_lg(self):
        return self._get_field("border_radius_lg", "0.5")

    @property
    def border_radius_xl(self):
        return self._get_field("border_radius_xl", "1")

    @property
    def border_radius_xxl(self):
        return self._get_field("border_radius_xxl", "2")

    @property
    def box_shadow(self):
        return self._get_field("box_shadow", "0 .5rem 1rem rgba(0,0,0,.15)")

    @property
    def box_shadow_sm(self):
        return self._get_field("box_shadow_sm", "0 .125rem .25rem rgba(0,0,0,.075)")

    @property
    def box_shadow_lg(self):
        return self._get_field("box_shadow_lg", "0 1rem 3rem rgba(0,0,0,.175)")

    # Typography extras
    @property
    def body_color(self):
        return self._get_field("body_color", "#212529")

    @property
    def body_bg(self):
        return self._get_field("body_bg", "#ffffff")

    @property
    def heading_color(self):
        return self._get_field("heading_color", "#212529")

    @property
    def body_font_weight(self):
        return self._get_field("body_font_weight", "400")

    @property
    def body_line_height(self):
        return self._get_field("body_line_height", "1.5")

    # Navbar & Footer
    @property
    def navbar_bg(self):
        return self._get_field("navbar_bg", "#007bb1")

    @property
    def footer_bg(self):
        return self._get_field("footer_bg", "#212529")

    @property
    def footer_color(self):
        return self._get_field("footer_color", "#dee2e6")

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
            extra_css_rules.extend(_navbar_rules(nb))
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
            self.colors,
            self.custom_css,
            self.body_font_size,
            self.enabled_properties,
            self._all_plone_colors(),
            self.google_font_family,
            extra_root_vars,
            extra_css_rules,
        )


def regenerate_css():
    """Write ``IThemeSettings.custom_css`` from the ``plone.palette.*`` records.

    The records are only the seed; the CSS visitors get is derived from them.
    Anything that writes records without the form — an upgrade step, a site
    provisioning script — has to call this, or the site keeps rendering the
    previous stylesheet until somebody opens the customizer and saves.  The
    save view ends with it too, so there is exactly one derivation.
    """
    css = _CustomizerMixin().generated_css
    _write_theme_css(css)
    return css


def reset_to_defaults():
    """Put every ``IPaletteSettings`` record back to its schema default and
    drop the generated stylesheet.

    Clearing ``custom_css`` (rather than regenerating from the defaults) is
    what returns the site to the *theme's* stock look: the palette defaults
    are Bootstrap's, and Barceloneta's primary is not Bootstrap blue.  This is
    also the state a fresh install is in.  ``google_fonts_api_key`` is
    configuration, not design, and is left alone.
    """
    for name, field in getFields(IPaletteSettings).items():
        if name == "google_fonts_api_key":
            continue
        value = field.default
        if value is None:
            value = field.defaultFactory() if field.defaultFactory else ""
        api.portal.set_registry_record(f"plone.palette.{name}", value)
    _write_theme_css("")


def _write_theme_css(css):
    registry = getUtility(IRegistry)
    settings = registry.forInterface(IThemeSettings, False)
    settings.custom_css = css
    # plone.app.theming keys @@custom.css's Last-Modified off this
    settings.custom_css_timestamp = datetime.now()


class CustomizerView(_CustomizerMixin, BrowserView):
    """Renders the TTW Theming form inside the Plone main template."""

    index = ViewPageTemplateFile("templates/customizer.pt")

    def __call__(self):
        return self.index()


# Records the save loop writes only when the form carries a value, so a
# partial autosubmit never blanks one.  Colour fields must look like a hex
# colour, body_font_size like a number; anything else is stored as posted.
_COLOR_RECORDS = frozenset(
    [f"{name}_color" for name in COLOR_FIELDS]
    + [fn for fn, *_ in PLONE_UI_COLOR_FIELDS + STATE_COLOR_FIELDS]
    + [fn for fn, *_ in BORDER_COLOR_FIELDS_EXTRA + TYPOGRAPHY_COLOR_FIELDS_EXTRA]
    + ["navbar_bg", "footer_bg", "footer_color"]
)
_VALUE_RECORDS = frozenset(
    [fn for fn, *_ in BORDER_NUMBER_FIELDS + SHADOW_TEXT_FIELDS + TYPOGRAPHY_VAR_FIELDS]
    + ["body_font_size"]
)


def _is_number(value):
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


class SaveCustomizerView(BrowserView):
    """POST endpoint for pat-inject: writes the posted records, then derives
    the stylesheet from the registry (regenerate_css).

    ``form.button.reset`` instead restores every record to its default and
    clears the stylesheet; the JS reloads the page afterwards so the form
    repopulates.
    """

    def __call__(self):
        response = self.request.response
        response.setHeader("Content-Type", "text/html; charset=utf-8")

        if self.request.get("REQUEST_METHOD", "GET") != "POST":
            return '<div id="form-feedback" class="alert alert-error"><p>POST required.</p></div>'

        form = self.request.form
        try:
            if form.get("form.button.reset"):
                reset_to_defaults()
                return '<div class="alert alert-info">Theme reset to defaults.</div>'

            for name in _COLOR_RECORDS:
                value = (form.get(name) or "").strip()
                if value.startswith("#"):
                    api.portal.set_registry_record(f"plone.palette.{name}", value)

            for name in _VALUE_RECORDS:
                value = (form.get(name) or "").strip()
                if not value:
                    continue
                if name == "body_font_size" and not _is_number(value):
                    continue
                api.portal.set_registry_record(f"plone.palette.{name}", value)

            # These three may legitimately be emptied, so they are always written.
            api.portal.set_registry_record(
                "plone.palette.google_font_family",
                (form.get("google_font_family") or "").strip(),
            )
            # Checkboxes: only checked ones are submitted; a hidden sentinel keeps
            # the key present so an all-unchecked state still saves correctly.
            raw = form.get("enabled_properties", [])
            if isinstance(raw, str):
                raw = [raw]
            valid_names = {name for name, _label, _default in BOOTSTRAP_PROPERTIES}
            api.portal.set_registry_record(
                "plone.palette.enabled_properties", [v for v in raw if v in valid_names]
            )
            api.portal.set_registry_record(
                "plone.palette.custom_css", (form.get("custom_css") or "").strip()
            )

            regenerate_css()
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


class CustomizerToolbarViewlet(_CustomizerMixin, ViewletBase):
    """The "Theming" entry in the Plone toolbar plus the customizer it opens.

    Registered in the ``plone.toolbar`` viewlet manager (IToolbar), which wraps
    its viewlets in the toolbar's own ``<ul>`` — so the template renders an
    ``<li>`` next to Contents/Edit/Actions, and the offcanvas it toggles.  This
    replaces the site_actions entry the customizer used to be reached through:
    no portal_actions round trip, no modal, and the form is already in the page
    so customizer.js can preview live.
    """

    index = ViewPageTemplateFile("templates/customizer_toolbar.pt")

    @property
    def available(self):
        if not api.user.has_permission("Manage portal", obj=self.context):
            return False
        # The standalone view renders the same form (same element ids); don't
        # emit a second copy behind it.
        published = self.request.get("PUBLISHED", None)
        return getattr(published, "__name__", "") != "palette-customizer"

    def render(self):
        if not self.available:
            return ""
        return self.index()
