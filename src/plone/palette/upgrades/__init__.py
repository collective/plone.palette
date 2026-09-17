from plone import api
from plone.app.theming.interfaces import IThemeSettings
from plone.palette.browser.customizer import regenerate_css
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import logging


_log = logging.getLogger(__name__)


def remove_customizer_action(setup_tool=None):
    """Drop the site_actions entry the customizer used to be reached through.

    The customizer now lives in the Plone toolbar (the plone.palette.toolbar
    viewlet), so the action is dead weight — and leaving it would show a second,
    modal-based entry point next to the toolbar one.
    """
    actions = api.portal.get_tool("portal_actions")
    category = actions.get("site_actions", None)
    if category is not None and "palette_customizer" in category.objectIds():
        category.manage_delObjects(["palette_customizer"])
        _log.info("Removed the palette_customizer site action.")


def regenerate_theme_css(setup_tool=None):
    """Re-derive the stylesheet so it carries the Bootstrap 6 token names.

    Sites customized before the aliases existed have a custom_css written in
    --bs-* names only, which plonetheme.bootstrap6 ignores; nothing fixes that
    until somebody saves the customizer again.  Skipped when the stylesheet is
    empty: that site never customized, and generating from the defaults would
    paint it Bootstrap blue instead of leaving the theme's stock look.
    """
    registry = getUtility(IRegistry)
    settings = registry.forInterface(IThemeSettings, False)
    if not settings.custom_css:
        _log.info("No generated stylesheet to regenerate; skipping.")
        return
    regenerate_css()
    _log.info("Regenerated the theme stylesheet from the plone.palette records.")
