"""Google Fonts vocabulary for plone.palette."""
from plone import api
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import json
import logging
import time
from urllib import request
from urllib.error import URLError

_log = logging.getLogger(__name__)

# ── static fallback ───────────────────────────────────────────────────────────
# Used when no API key is configured or the API is unreachable.

POPULAR_FONTS = [
    "ABeeZee", "Abel", "Abril Fatface", "Acme", "Alegreya", "Alegreya Sans",
    "Alfa Slab One", "Alice", "Amatic SC", "Amiri", "Arimo", "Arvo", "Asap",
    "Assistant", "Barlow", "Barlow Condensed", "Bebas Neue", "Bitter",
    "Bodoni Moda", "Cabin", "Cantarell", "Cardo", "Catamaran", "Cinzel",
    "Cormorant Garamond", "Crimson Text", "DM Sans", "DM Serif Display",
    "Dancing Script", "Dosis", "EB Garamond", "Exo 2", "Fira Sans",
    "Fjalla One", "Fraunces", "Gentium Book Plus", "Great Vibes",
    "IBM Plex Mono", "IBM Plex Sans", "IBM Plex Serif", "Inconsolata",
    "Indie Flower", "Inter", "Josefin Sans", "Josefin Slab", "Jost",
    "Lato", "Libre Baskerville", "Libre Franklin", "Lobster", "Lora",
    "Merriweather", "Merriweather Sans", "Montserrat", "Mukta", "Mulish",
    "Noto Sans", "Noto Serif", "Nunito", "Nunito Sans", "Open Sans", "Oswald",
    "PT Sans", "PT Serif", "Pacifico", "Playfair Display", "Poppins", "Prompt",
    "Quicksand", "Raleway", "Roboto", "Roboto Condensed", "Roboto Mono",
    "Roboto Slab", "Rubik", "Source Code Pro", "Source Serif 4",
    "Space Grotesk", "Space Mono", "Spectral", "Teko", "Titillium Web",
    "Ubuntu", "Ubuntu Condensed", "Ubuntu Mono", "Varela Round", "Work Sans",
    "Yanone Kaffeesatz", "Yeseva One", "Zilla Slab",
]

# ── module-level cache ────────────────────────────────────────────────────────

_cache = {"families": None, "expires": 0.0}
_CACHE_TTL = 3600  # 1 hour


def _fetch_families(api_key):
    """Return sorted list of font family names from Google Fonts API v2."""
    now = time.time()
    if _cache["families"] is not None and now < _cache["expires"]:
        return _cache["families"]

    url = (
        "https://www.googleapis.com/webfonts/v1/webfonts"
        f"?sort=ALPHA&key={api_key}"
    )
    try:
        with request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        families = [item["family"] for item in data.get("items", [])]
        _cache["families"] = families
        _cache["expires"] = now + _CACHE_TTL
        return families
    except (URLError, Exception):
        _log.warning("plone.palette: Google Fonts API fetch failed, using fallback list")
        return POPULAR_FONTS


def _get_api_key():
    try:
        return api.portal.get_registry_record("plone.palette.google_fonts_api_key") or ""
    except Exception:
        return ""


# ── vocabulary ────────────────────────────────────────────────────────────────

@implementer(IVocabularyFactory)
class GoogleFontsVocabulary:
    """plone.palette.GoogleFonts — lists Google Font family names."""

    def __call__(self, context):
        api_key = _get_api_key()
        families = _fetch_families(api_key) if api_key else list(POPULAR_FONTS)

        terms = [SimpleTerm("", "", "— system default —")]
        for family in families:
            terms.append(SimpleTerm(family, family, family))
        return SimpleVocabulary(terms)


GoogleFontsVocabularyFactory = GoogleFontsVocabulary()
