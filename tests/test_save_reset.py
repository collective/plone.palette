"""Save, reset and regenerate: the registry is the seed, the stylesheet is derived."""

from plone import api
from plone.app.theming.interfaces import IThemeSettings
from plone.palette.browser.customizer import regenerate_css
from plone.palette.browser.customizer import reset_to_defaults
from plone.palette.browser.customizer import SaveCustomizerView
from plone.palette.upgrades import regenerate_theme_css
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import pytest


def theme_css():
    return getUtility(IRegistry).forInterface(IThemeSettings, False).custom_css


@pytest.fixture()
def save(portal, http_request):
    def post(**form):
        http_request.form.clear()
        http_request.form.update(form)
        http_request["REQUEST_METHOD"] = "POST"
        return SaveCustomizerView(portal, http_request)()

    return post


class TestSave:
    def test_writes_records_and_derives_stylesheet(self, save):
        out = save(primary_color="#74f40b", navbar_bg="#8e44ad", body_font_size="1.25")

        assert "alert-success" in out
        assert api.portal.get_registry_record("plone.palette.primary_color") == "#74f40b"
        css = theme_css()
        assert "--bs-primary: #74f40b;" in css
        assert "--primary-base: #74f40b;" in css
        assert "--navbar-bg: #8e44ad;" in css
        assert "--body-font-size: 1.25rem;" in css

    def test_partial_post_keeps_other_records(self, save):
        save(primary_color="#74f40b")
        save(secondary_color="#123456")

        assert api.portal.get_registry_record("plone.palette.primary_color") == "#74f40b"
        assert "--bs-primary: #74f40b;" in theme_css()

    def test_rejects_non_colors_and_non_numbers(self, save):
        save(primary_color="red", body_font_size="big")

        assert api.portal.get_registry_record("plone.palette.primary_color") == "#0d6efd"
        assert api.portal.get_registry_record("plone.palette.body_font_size") == "1"

    def test_get_is_refused(self, portal, http_request):
        http_request["REQUEST_METHOD"] = "GET"
        assert "POST required" in SaveCustomizerView(portal, http_request)()


class TestReset:
    def test_restores_defaults_and_clears_stylesheet(self, save):
        save(primary_color="#74f40b", custom_css="body { color: red }")
        api.portal.set_registry_record("plone.palette.google_fonts_api_key", "KEY")
        assert theme_css()

        out = save(**{"form.button.reset": "reset"})

        assert "reset" in out
        assert api.portal.get_registry_record("plone.palette.primary_color") == "#0d6efd"
        assert api.portal.get_registry_record("plone.palette.custom_css") == ""
        assert api.portal.get_registry_record("plone.palette.enabled_properties") == []
        # clearing, not regenerating: the theme's stock look, as on a fresh install
        assert theme_css() == ""
        # configuration, not design — untouched
        assert api.portal.get_registry_record("plone.palette.google_fonts_api_key") == "KEY"

    def test_reset_function_alone(self, save):
        save(primary_color="#74f40b")
        reset_to_defaults()

        assert theme_css() == ""


class TestRegenerate:
    def test_regenerates_from_records_without_a_form(self, portal):
        api.portal.set_registry_record("plone.palette.primary_color", "#abcdef")

        css = regenerate_css()

        assert "--primary-base: #abcdef;" in css
        assert theme_css() == css

    def test_upgrade_step_skips_uncustomized_sites(self, portal):
        assert theme_css() == ""

        regenerate_theme_css()

        assert theme_css() == ""

    def test_upgrade_step_adds_bootstrap6_names(self, save):
        # a stylesheet from before the aliases existed
        settings = getUtility(IRegistry).forInterface(IThemeSettings, False)
        api.portal.set_registry_record("plone.palette.primary_color", "#74f40b")
        settings.custom_css = ":root {\n  --bs-primary: #74f40b;\n}"

        regenerate_theme_css()

        assert "--primary-base: #74f40b;" in theme_css()
