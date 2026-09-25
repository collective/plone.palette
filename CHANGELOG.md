# Changelog

<!--
   You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst
-->

<!-- towncrier release notes start -->

## 1.0.0b0 (2026-09-25)


### Breaking changes:

- `plonetheme.bootstrap6` is no longer a hard dependency. It moved to the `bootstrap6` extra (`pip install "plone.palette[bootstrap6]"`) and its ZCML is only included when the package is installed; the palette drives Barceloneta on its own. Sites that relied on the theme being pulled in implicitly need the extra. 


### New features:

- Add `plonetheme.bootstrap6` as a dependency, pulled from git via mxdev. 
- Add a "Reset to defaults" button to the customizer: every `plone.palette.*` record goes back to its schema default and the generated stylesheet is cleared, which returns the site to the theme's stock look (the state of a fresh install). The Google Fonts API key is configuration, not design, and is left alone. 
- Move the theme customizer from a `portal_actions` site action into the Plone toolbar: a "Theming" entry rendered by the `plone.palette.toolbar` viewlet (`plone.toolbar` / `IToolbar` manager) opens the customizer in an offcanvas, with the form already in the page instead of ajax-loaded into a modal. 


### Bug fixes:

- Fix `IPaletteSettings.enabled_properties` defaulting to an empty list instead of the Bootstrap-true-by-default properties. This made every Properties-tab checkbox show unchecked on a fresh site or after "Reset to defaults", and caused enabling a single off-by-default property (e.g. Box shadows) to silently disable every other untouched property (rounded corners, dropdown carets, transitions, smooth scroll, button cursor, validation icons). `BOOTSTRAP_PROPERTIES` is now defined once in `interfaces.py` and imported by `browser/customizer.py` instead of being duplicated. 
- Make the generated theme CSS apply to `plonetheme.bootstrap6` as well as Barceloneta. Bootstrap 6 dropped the `--bs-` prefix and renamed the semantic tokens, and the theme's own `--bs-*` declarations are one-way aliases for legacy Mockup components — so a stylesheet written only in `--bs-*` names had no effect there. Every declaration is now emitted under its Bootstrap 6 name as well (`--bs-primary` → `--primary-base`, `--bs-body-bg` → `--bg-body`, radii onto the numeric scale, ...), in the saved CSS and in the live preview. One stylesheet serves both themes: the Bootstrap 6 names are neither defined nor read anywhere in Barceloneta, and the bootstrap6-only rules (the navigation band and the offcanvas the nav collapses into, which the theme paints from `--primary-base`) are scoped to selectors Barceloneta never matches. 


### Internal:

- Add `regenerate_css()`, which derives `IThemeSettings.custom_css` from the `plone.palette.*` records without a form post. The save view now only writes records and ends with it, so there is one derivation instead of two; upgrade steps and provisioning scripts that set records call it too. Upgrade step 1001→1002 runs it on sites that already carry a generated stylesheet, so they pick up the Bootstrap 6 token names without a manual save. The live preview no longer runs on page load: the saved stylesheet is already linked, and previewing on load painted the form's defaults over a freshly reset site. 
- Declare the Python versions Plone 6.2 supports (3.10–3.14) consistently across `requires-python`, the classifiers and ruff's target. Fix the CI workflows, which assumed a `backend/` subfolder and never ran. Remove a stale `plone.theminghelper` translation file and the unused test matrix workflow. The uninstall profile now also removes the palette's registry records and JS bundle; `IThemeSettings.custom_css` is deliberately left in place. README: document the extra, the toolbar entry, reset, and the actual view names. 
- Update sources to Plone 6.2.1. 
- Update sources to Plone 6.2.2. 


### Tests

- Fix the browser layer tests, which imported `IBrowserLayer` where the interface is named `IPaletteLayer`.
