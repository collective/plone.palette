from plone.palette import PACKAGE_NAME

import pytest


class TestSetupUninstall:
    @pytest.fixture(autouse=True)
    def uninstalled(self, installer):
        installer.uninstall_product(PACKAGE_NAME)

    def test_addon_uninstalled(self, installer):
        """Test if plone.palette is uninstalled."""
        assert installer.is_product_installed(PACKAGE_NAME) is False

    def test_browserlayer_not_registered(self, browser_layers):
        """Test that IPaletteLayer is not registered."""
        from plone.palette.interfaces import IPaletteLayer

        assert IPaletteLayer not in browser_layers

    def test_registry_records_removed(self, portal):
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        registry = getUtility(IRegistry)

        assert "plone.palette.primary_color" not in registry
        assert "plone.bundles/plone-palette.jscompilation" not in registry
