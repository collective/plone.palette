"""Module where all interfaces, events and exceptions live."""

from zope import schema
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IPaletteLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


# Bootstrap $enable-* variables from _variables.properties.scss.
# (name, label, default) — the canonical list; browser/customizer.py's
# BOOTSTRAP_PROPERTIES and static/customizer.js's PROPERTY_DEFAULTS must be
# kept in sync with the `default` column here.
#
# `default` is what a fresh install (and "Reset to defaults") should ship
# with checked. IPaletteSettings.enabled_properties must default to exactly
# the names with default=True below (see default_enabled_properties()) —
# an empty-list default would make generate_css() treat every one of these
# as explicitly disabled, since it has no way to tell "never configured"
# apart from "user unchecked it".
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


def default_enabled_properties():
    """defaultFactory for IPaletteSettings.enabled_properties."""
    return [name for name, _label, default in BOOTSTRAP_PROPERTIES if default]


class IPaletteSettings(Interface):
    """Registry settings for plone.palette."""

    primary_color = schema.TextLine(
        title="Primary color", default="#0d6efd", required=False
    )
    secondary_color = schema.TextLine(
        title="Secondary color", default="#6c757d", required=False
    )
    success_color = schema.TextLine(
        title="Success color", default="#198754", required=False
    )
    danger_color = schema.TextLine(
        title="Danger color", default="#dc3545", required=False
    )
    warning_color = schema.TextLine(
        title="Warning color", default="#ffc107", required=False
    )
    info_color = schema.TextLine(title="Info color", default="#0dcaf0", required=False)

    body_font_size = schema.TextLine(
        title="Body font size (rem)", default="1", required=False
    )

    # Borders
    border_width = schema.TextLine(title="Border width", default="1", required=False)
    border_color = schema.TextLine(
        title="Border color", default="#dee2e6", required=False
    )
    border_radius = schema.TextLine(
        title="Border radius", default="0.375", required=False
    )
    border_radius_sm = schema.TextLine(
        title="Border radius SM", default="0.25", required=False
    )
    border_radius_lg = schema.TextLine(
        title="Border radius LG", default="0.5", required=False
    )
    border_radius_xl = schema.TextLine(
        title="Border radius XL", default="1", required=False
    )
    border_radius_xxl = schema.TextLine(
        title="Border radius XXL", default="2", required=False
    )
    box_shadow = schema.TextLine(
        title="Box shadow", default="0 .5rem 1rem rgba(0,0,0,.15)", required=False
    )
    box_shadow_sm = schema.TextLine(
        title="Box shadow SM",
        default="0 .125rem .25rem rgba(0,0,0,.075)",
        required=False,
    )
    box_shadow_lg = schema.TextLine(
        title="Box shadow LG", default="0 1rem 3rem rgba(0,0,0,.175)", required=False
    )

    # Typography extras
    body_color = schema.TextLine(title="Body color", default="#212529", required=False)
    body_bg = schema.TextLine(
        title="Body background", default="#ffffff", required=False
    )
    heading_color = schema.TextLine(
        title="Heading color", default="#212529", required=False
    )
    body_font_weight = schema.TextLine(
        title="Body font weight", default="400", required=False
    )
    body_line_height = schema.TextLine(
        title="Body line height", default="1.5", required=False
    )

    # Navbar & Footer (Barceloneta-specific)
    navbar_bg = schema.TextLine(
        title="Navbar background", default="#007bb1", required=False
    )
    footer_bg = schema.TextLine(
        title="Footer background", default="#212529", required=False
    )
    footer_color = schema.TextLine(
        title="Footer text color", default="#dee2e6", required=False
    )

    google_font_family = schema.TextLine(
        title="Google Font family", default="", required=False
    )
    google_fonts_api_key = schema.TextLine(
        title="Google Fonts API key", default="", required=False
    )

    # Plone UI colors ($plone-* from _variables.colors.plone.scss)
    plone_link_color_on_dark = schema.TextLine(
        title="Link color on dark", default="#16a1e3", required=False
    )
    plone_link_color_on_grey = schema.TextLine(
        title="Link color on grey", default="#086ca3", required=False
    )
    plone_portlet_list_hover_bg = schema.TextLine(
        title="Portlet list hover bg", default="#fcfcfd", required=False
    )
    plone_portlet_footer_bg = schema.TextLine(
        title="Portlet footer bg", default="#fcfcfd", required=False
    )
    plone_portlet_list_bullet = schema.TextLine(
        title="Portlet list bullet", default="#64bee8", required=False
    )

    # Workflow state colors ($state-* from _variables.colors.plone.scss)
    state_draft_color = schema.TextLine(
        title="Draft state color", default="#fab82a", required=False
    )
    state_pending_color = schema.TextLine(
        title="Pending state color", default="#ccd111", required=False
    )
    state_private_color = schema.TextLine(
        title="Private state color", default="#c4183c", required=False
    )
    state_internal_color = schema.TextLine(
        title="Internal state color", default="#fab82a", required=False
    )
    state_internally_published_color = schema.TextLine(
        title="Internally published color", default="#883dfa", required=False
    )

    enabled_properties = schema.List(
        title="Enabled Bootstrap properties",
        value_type=schema.TextLine(),
        required=False,
        defaultFactory=default_enabled_properties,
    )

    custom_css = schema.Text(title="Custom CSS", default="", required=False)
