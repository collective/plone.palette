from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getMultiAdapter
from zope.interface import alsoProvides

import pytest


@pytest.fixture()
def toolbar(portal, http_request):
    """The rendered plone.toolbar viewlet manager, as a Manager sees it."""
    from plone.palette.interfaces import IPaletteLayer

    def render():
        alsoProvides(http_request, IPaletteLayer)
        view = portal.restrictedTraverse("@@view")
        manager = getMultiAdapter(
            (portal, http_request, view), name="plone.toolbar"
        )
        manager.update()
        return manager.render()

    return render


class TestToolbarCustomizer:
    def test_toolbar_entry_rendered(self, portal, toolbar):
        """The Theming entry and its offcanvas are in the toolbar for managers."""
        setRoles(portal, TEST_USER_ID, ["Manager"])
        markup = toolbar()

        assert 'id="contentview-palette"' in markup
        assert 'data-bs-toggle="offcanvas"' in markup
        assert 'id="palette-customizer-offcanvas"' in markup
        # the shared form macro renders inside the offcanvas
        assert 'id="palette-customizer-form"' in markup

    def test_entry_sits_below_content_views(self, portal, toolbar):
        """viewlets.xml orders plone.palette.toolbar after plone.contentviews."""
        setRoles(portal, TEST_USER_ID, ["Manager"])
        markup = toolbar()

        assert markup.index("contentview-folderContents") < markup.index(
            "contentview-palette"
        )

    def test_hidden_for_non_managers(self, portal, toolbar):
        setRoles(portal, TEST_USER_ID, ["Member"])

        assert 'id="contentview-palette"' not in toolbar()

    def test_no_site_action_left(self, portal):
        """The customizer is no longer a portal_actions entry."""
        site_actions = portal.portal_actions.get("site_actions")

        assert "palette_customizer" not in site_actions.objectIds()


class TestStandaloneView:
    def test_toolbar_entry_not_duplicated(self, request_factory):
        """On @@palette-customizer the toolbar must not render a second form.

        Both render the same macro, so a second copy would duplicate every
        element id in the page.
        """
        session = request_factory(role="Manager", api=False)
        response = session.get("/@@palette-customizer", headers={"Accept": "text/html"})

        assert response.status_code == 200
        assert response.text.count('id="palette-customizer-form"') == 1
        assert 'id="contentview-palette"' not in response.text
