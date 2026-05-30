# plone.palette

[![PyPI](https://img.shields.io/pypi/v/plone.palette.svg)](https://pypi.org/project/plone.palette)
[![Python Versions](https://img.shields.io/pypi/pyversions/plone.palette.svg)](https://pypi.org/project/plone.palette)
[![License](https://img.shields.io/pypi/l/plone.palette.svg)](https://github.com/collective/plone.palette/blob/main/backend/LICENSE.md)
[![Backend Tests](https://github.com/collective/plone.palette/actions/workflows/backend.yml/badge.svg)](https://github.com/collective/plone.palette/actions/workflows/backend.yml)

A through-the-web (TTW) theming customizer for Plone Classic UI.

`plone.palette` lets site managers adjust Bootstrap 5 design tokens — colors, typography, borders, shadows, and more — without editing SCSS or restarting the server.
Changes are stored in the Plone registry and injected at runtime as CSS custom properties via `plone.app.theming`.

## Features

- **Bootstrap 5 color palette** — customize the six semantic colors (primary, secondary, success, danger, warning, info) with live preview.
- **Typography** — set body font size, font weight, line height, body/heading colors, and background color.
- **Google Fonts** — pick any Google Font from a built-in vocabulary (optionally fetched live via a Google Fonts API key).
- **Borders and shadows** — adjust border width, color, and all border-radius sizes (sm, lg, xl, xxl), plus three box-shadow presets.
- **Navbar and footer** — override Barceloneta's navbar background and footer background/text colors.
- **Plone UI colors** — control portlet hover backgrounds, bullet colors, and link colors on dark/grey backgrounds.
- **Workflow state colors** — configure the colors used for draft, pending, private, internal, and internally-published states.
- **Bootstrap properties** — toggle fourteen `$enable-*` flags (rounded corners, shadows, transitions, smooth scroll, RFS, and more) via checkboxes.
- **Custom CSS** — append arbitrary CSS that is merged into the generated stylesheet.
- **Offcanvas customizer** — a floating sidebar panel available to site managers on every page, powered by `pat-inject` for instant save-and-preview.

## Requirements

- Plone 6.2
- Python 3.10 or later
- `plone.app.theming` (included with Plone Classic UI / Barceloneta)

## Installation

Install `plone.palette` into your Plone backend.

```shell
pip install plone.palette
```

Activate the add-on through the Plone control panel under **Add-ons**, or run the GenericSetup profile programmatically:

```python
from plone import api
api.portal.run_setup(profile_id="plone.palette:default")
```

### Development installation

Clone the monorepo and install the backend in development mode.

```shell
git clone git@github.com:collective/plone.palette.git
cd plone.palette/backend
make install
make create-site
make start
```

The Plone backend will be available at `http://localhost:8080/`.

## Usage

### Offcanvas customizer

After installation, any user with the **Manage portal** permission sees a floating toggle button on the right edge of every page.
Clicking it opens an offcanvas panel with all theming controls grouped into tabs:

- **Colors** — Bootstrap semantic colors and Plone UI colors.
- **Typography** — font family (Google Fonts), size, weight, and line height.
- **Borders** — border width, color, and radius presets.
- **Shadows** — three box-shadow definitions.
- **Navbar & Footer** — background and text colors for the site chrome.
- **States** — workflow state indicator colors.
- **Properties** — Bootstrap `$enable-*` feature flags.
- **Custom CSS** — a raw textarea for additional rules.

Clicking **Save** sends a POST request to `@@save-customizer`, which persists all values in the Plone registry and regenerates the `custom_css` field of `IThemeSettings`.
The generated stylesheet consists of `:root { … }` CSS custom property overrides, button-variant rules, and any extra rules derived from the enabled/disabled Bootstrap property flags.

### Standalone customizer view

The same form is also available as a full-page view at `@@customizer` on any content object.

### Google Fonts API key

To populate the font selector from the live Google Fonts API instead of the built-in static list, store your API key in the registry:

```python
from plone import api
api.portal.set_registry_record("plone.palette.google_fonts_api_key", "YOUR_KEY")
```

## Configuration reference

All settings are stored under the `plone.palette.*` registry prefix.

| Registry key | Type | Default | Description |
|---|---|---|---|
| `primary_color` | TextLine | `#0d6efd` | Bootstrap primary color |
| `secondary_color` | TextLine | `#6c757d` | Bootstrap secondary color |
| `success_color` | TextLine | `#198754` | Bootstrap success color |
| `danger_color` | TextLine | `#dc3545` | Bootstrap danger color |
| `warning_color` | TextLine | `#ffc107` | Bootstrap warning color |
| `info_color` | TextLine | `#0dcaf0` | Bootstrap info color |
| `body_font_size` | TextLine | `1` | Body font size in rem |
| `google_font_family` | TextLine | `` | Google Font family name |
| `google_fonts_api_key` | TextLine | `` | Google Fonts API key |
| `border_width` | TextLine | `1` | Border width in px |
| `border_color` | TextLine | `#dee2e6` | Default border color |
| `border_radius` | TextLine | `0.375` | Default border radius in rem |
| `body_color` | TextLine | `#212529` | Body text color |
| `body_bg` | TextLine | `#ffffff` | Body background color |
| `heading_color` | TextLine | `#212529` | Heading text color |
| `navbar_bg` | TextLine | `#007bb1` | Barceloneta navbar background |
| `footer_bg` | TextLine | `#212529` | Footer background color |
| `footer_color` | TextLine | `#dee2e6` | Footer text color |
| `enabled_properties` | List | (see below) | Bootstrap `$enable-*` flags |
| `custom_css` | Text | `` | Additional CSS appended to the generated sheet |

The default enabled Bootstrap properties are: `enable_caret`, `enable_rounded`, `enable_transitions`, `enable_reduced_motion`, `enable_smooth_scroll`, `enable_grid_classes`, `enable_container_classes`, `enable_button_pointers`, `enable_rfs`, `enable_validation_icons`, and `enable_negative_margins`.

## Contributing

- [Issue tracker](https://github.com/collective/plone.palette/issues)
- [Source code](https://github.com/collective/plone.palette/)

### Code quality

```shell
make lint     # check code style
make format   # auto-format code
```

| Tool | Scope | Configuration |
|---|---|---|
| Ruff | Python formatting and import sorting | [`pyproject.toml`](./pyproject.toml) |
| zpretty | XML and ZCML formatting | — |

### Internationalization

```shell
make i18n
```

Translation files are located under `src/plone/palette/locales/`.

## License

This project is licensed under the GNU General Public License v2.
See [LICENSE.GPL](./LICENSE.GPL) for details.
