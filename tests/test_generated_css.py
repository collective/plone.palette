"""The generated stylesheet has to reach both themes.

plonetheme.bootstrap6 runs on Bootstrap 6, which dropped the --bs- prefix; its
own --bs-* declarations are one-way aliases for legacy Mockup components, so a
stylesheet written only in --bs-* names has no effect there.
"""

from plone.palette.browser.customizer import BOOTSTRAP6_ALIASES
from plone.palette.browser.customizer import generate_css


class TestGeneratedCSS:
    def test_brand_color_emitted_under_both_names(self):
        css = generate_css({"primary": "#74f40b"})

        assert "--bs-primary: #74f40b;" in css
        # bootstrap6 derives --primary-bg, --link-color, --navbar-bg and every
        # .btn-primary token from --primary-base
        assert "--primary-base: #74f40b;" in css

    def test_extra_root_vars_aliased(self):
        css = generate_css({}, extra_root_vars={"--bs-border-radius": "0.5rem"})

        assert "--bs-border-radius: 0.5rem;" in css
        assert "--radius-4: 0.5rem;" in css

    def test_typography_aliased(self):
        css = generate_css({}, body_font_size="1.125", google_font_family="Roboto")

        assert "--bs-body-font-size: 1.125rem;" in css
        assert "--body-font-size: 1.125rem;" in css
        assert "--body-font-family: 'Roboto', sans-serif;" in css

    def test_unaliased_vars_emitted_once(self):
        """--bs-*-rgb has no Bootstrap 6 counterpart; it must not sprout one."""
        css = generate_css({"primary": "#74f40b"})

        assert "--bs-primary-rgb: 116, 244, 11;" in css
        assert css.count("116, 244, 11") == 2  # --bs-primary-rgb + --bs-link-color-rgb

    def test_navbar_covers_both_themes(self):
        css = generate_css({}, extra_css_rules=[])
        assert "navbar" not in css

        from plone.palette.browser.customizer import _navbar_rules

        rules = "\n".join(_navbar_rules("#8e44ad"))
        assert ".navbar-barceloneta { --bs-navbar-background: #8e44ad; }" in rules
        assert ".navbar-bootstrap6 { --navbar-bg: #8e44ad; }" in rules
        # bootstrap6 paints the band and the offcanvas the nav collapses into;
        # the theme's own rule is three classes deep, so ours has to match it
        assert "#mainnavigation-wrapper:has(.navbar-bootstrap6)," in rules
        assert ".navbar-bootstrap6 .offcanvas .offcanvas-body" in rules

    def test_alias_table_has_no_bs_prefixed_targets(self):
        for source, alias in BOOTSTRAP6_ALIASES.items():
            assert source.startswith("--bs-")
            assert not alias.startswith("--bs-")

    def test_bootstrap6_rules_cannot_touch_barceloneta(self):
        """Every bootstrap6-only rule carries a selector Barceloneta never matches."""
        from plone.palette.browser.customizer import _navbar_rules

        for rule in _navbar_rules("#8e44ad"):
            if "barceloneta" in rule:
                continue
            assert "navbar-bootstrap6" in rule
