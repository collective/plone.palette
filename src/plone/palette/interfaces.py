"""Module where all interfaces, events and exceptions live."""

from zope import schema
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IPaletteLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IPaletteSettings(Interface):
    """Registry settings for plone.palette."""

    primary_color = schema.TextLine(title=u"Primary color", default=u"#0d6efd", required=False)
    secondary_color = schema.TextLine(title=u"Secondary color", default=u"#6c757d", required=False)
    success_color = schema.TextLine(title=u"Success color", default=u"#198754", required=False)
    danger_color = schema.TextLine(title=u"Danger color", default=u"#dc3545", required=False)
    warning_color = schema.TextLine(title=u"Warning color", default=u"#ffc107", required=False)
    info_color = schema.TextLine(title=u"Info color", default=u"#0dcaf0", required=False)

    body_font_size = schema.TextLine(title=u"Body font size (rem)", default=u"1", required=False)

    # Borders
    border_width = schema.TextLine(title=u"Border width", default=u"1", required=False)
    border_color = schema.TextLine(title=u"Border color", default=u"#dee2e6", required=False)
    border_radius = schema.TextLine(title=u"Border radius", default=u"0.375", required=False)
    border_radius_sm = schema.TextLine(title=u"Border radius SM", default=u"0.25", required=False)
    border_radius_lg = schema.TextLine(title=u"Border radius LG", default=u"0.5", required=False)
    border_radius_xl = schema.TextLine(title=u"Border radius XL", default=u"1", required=False)
    border_radius_xxl = schema.TextLine(title=u"Border radius XXL", default=u"2", required=False)
    box_shadow = schema.TextLine(title=u"Box shadow", default=u"0 .5rem 1rem rgba(0,0,0,.15)", required=False)
    box_shadow_sm = schema.TextLine(title=u"Box shadow SM", default=u"0 .125rem .25rem rgba(0,0,0,.075)", required=False)
    box_shadow_lg = schema.TextLine(title=u"Box shadow LG", default=u"0 1rem 3rem rgba(0,0,0,.175)", required=False)

    # Typography extras
    body_color = schema.TextLine(title=u"Body color", default=u"#212529", required=False)
    body_bg = schema.TextLine(title=u"Body background", default=u"#ffffff", required=False)
    heading_color = schema.TextLine(title=u"Heading color", default=u"#212529", required=False)
    body_font_weight = schema.TextLine(title=u"Body font weight", default=u"400", required=False)
    body_line_height = schema.TextLine(title=u"Body line height", default=u"1.5", required=False)

    # Navbar & Footer (Barceloneta-specific)
    navbar_bg = schema.TextLine(title=u"Navbar background", default=u"#007bb1", required=False)
    footer_bg = schema.TextLine(title=u"Footer background", default=u"#212529", required=False)
    footer_color = schema.TextLine(title=u"Footer text color", default=u"#dee2e6", required=False)

    google_font_family = schema.TextLine(title=u"Google Font family", default=u"", required=False)
    google_fonts_api_key = schema.TextLine(title=u"Google Fonts API key", default=u"", required=False)

    # Plone UI colors ($plone-* from _variables.colors.plone.scss)
    plone_link_color_on_dark = schema.TextLine(title=u"Link color on dark", default=u"#16a1e3", required=False)
    plone_link_color_on_grey = schema.TextLine(title=u"Link color on grey", default=u"#086ca3", required=False)
    plone_portlet_list_hover_bg = schema.TextLine(title=u"Portlet list hover bg", default=u"#fcfcfd", required=False)
    plone_portlet_footer_bg = schema.TextLine(title=u"Portlet footer bg", default=u"#fcfcfd", required=False)
    plone_portlet_list_bullet = schema.TextLine(title=u"Portlet list bullet", default=u"#64bee8", required=False)

    # Workflow state colors ($state-* from _variables.colors.plone.scss)
    state_draft_color = schema.TextLine(title=u"Draft state color", default=u"#fab82a", required=False)
    state_pending_color = schema.TextLine(title=u"Pending state color", default=u"#ccd111", required=False)
    state_private_color = schema.TextLine(title=u"Private state color", default=u"#c4183c", required=False)
    state_internal_color = schema.TextLine(title=u"Internal state color", default=u"#fab82a", required=False)
    state_internally_published_color = schema.TextLine(title=u"Internally published color", default=u"#883dfa", required=False)

    enabled_properties = schema.List(
        title=u"Enabled Bootstrap properties",
        value_type=schema.TextLine(),
        required=False,
        defaultFactory=list,
    )

    custom_css = schema.Text(title=u"Custom CSS", default=u"", required=False)
