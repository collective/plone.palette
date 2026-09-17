from plone import api

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
