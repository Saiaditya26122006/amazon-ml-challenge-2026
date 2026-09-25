"""
Business Entity Resolution — Normalization Module

Deterministic, reusable text normalization for business names, addresses,
and country labels.  Stdlib only (unicodedata, re, string).

Design principles:
  - Never destroy original information; produce *derived* representations.
  - Handle every script present in the data (Latin, Devanagari, Tamil,
    Bengali, Kannada, French accented Latin, etc.) without aggressive
    transliteration or suffix removal.
  - Treat country as an open set of string labels.
  - Recognise literal missing-value sentinels ("null", "nan", "NaN", …)
    so they never become useful tokens.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Missing-value detection
# ---------------------------------------------------------------------------

_MISSING_LITERALS: set[str] = {
    "",
    "null",
    "nan",
    "none",
    "n/a",
    "na",
    "undefined",
    "missing",
    "-",
    "--",
    ".",
}


def is_missing_value(value: object) -> bool:
    """Return True when *value* represents a missing / empty datum.

    Recognised sentinels:
      - Python ``None``
      - ``float('nan')``
      - Empty or whitespace-only strings
      - Literal strings: "null", "NULL", "nan", "NaN", "None", "N/A",
        "NA", "undefined", "missing", "-", "--", "."
    """
    if value is None:
        return True
    if isinstance(value, float):
        import math
        return math.isnan(value)
    if isinstance(value, str):
        return value.strip().lower() in _MISSING_LITERALS
    return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Matches one or more whitespace characters (including non-breaking spaces
# that survive Unicode normalisation).
_MULTI_WS = re.compile(r"\s+")


# Matches embedded "null" tokens that appear in noisy address data.
# Anchored to word boundaries so we don't corrupt words like "annulled".
_NULL_TOKEN = re.compile(r"\bnull\b", re.IGNORECASE)


def _unicode_normalize(text: str) -> str:
    """NFC-normalise, collapse whitespace, strip leading/trailing space."""
    text = unicodedata.normalize("NFC", text)
    text = _MULTI_WS.sub(" ", text)
    return text.strip()


def _strip_accents_latin(text: str) -> str:
    """Remove combining marks from *Latin-script* characters only.

    Non-Latin scripts (Devanagari, Tamil, etc.) rely on combining marks
    for correct representation, so we leave them intact.
    """
    out: list[str] = []
    for ch in unicodedata.normalize("NFD", text):
        cat = unicodedata.category(ch)
        if cat.startswith("M"):  # combining mark
            # Keep the mark if the preceding base character is non-Latin.
            if out and not _is_latin(out[-1]):
                out.append(ch)
            # Otherwise drop it (strips accents from Latin letters).
        else:
            out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def _is_latin(ch: str) -> bool:
    """True if *ch* is a basic or extended Latin letter."""
    try:
        name = unicodedata.name(ch, "")
    except ValueError:
        return False
    return "LATIN" in name


def _to_alphanumeric(text: str) -> str:
    """Keep Unicode letters, digits, combining marks, and whitespace.

    Combining marks (Unicode category M — Mn, Mc, Me) are preserved because
    Indic scripts use them for vowel signs, virama, anusvara, etc.  Stripping
    them would shatter words like "मार्केटिंग" into isolated consonants.
    """
    out: list[str] = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch.isalnum() or ch.isspace() or cat.startswith("M"):
            out.append(ch)
        else:
            out.append(" ")
    return _MULTI_WS.sub(" ", "".join(out)).strip()


def _tokenize(text: str) -> list[str]:
    """Split on whitespace; return list of non-empty tokens."""
    return text.split()


# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class NormalizedName:
    """Multiple derived representations of a business name.

    Attributes
    ----------
    original : str
        Verbatim input (stripped of leading/trailing whitespace).
    cleaned : str
        Unicode-normalised, lowered, whitespace-collapsed.
    no_accents : str
        ``cleaned`` with Latin-script accents removed (non-Latin marks
        are preserved).
    alphanumeric : str
        ``no_accents`` with all punctuation removed.
    tokens : list[str]
        Whitespace-split tokens from ``alphanumeric``.
    """
    original: str
    cleaned: str
    no_accents: str
    alphanumeric: str
    tokens: list[str]


def normalize_name(value: object) -> NormalizedName:
    """Normalise a ``business_name`` value.

    Returns a :class:`NormalizedName` with several derived representations,
    from lightly cleaned to fully tokenised.  None of the representations
    remove legal suffixes or attempt transliteration — those are separate
    downstream steps.

    If *value* is missing (see :func:`is_missing_value`), every field
    except ``original`` is the empty string / empty list.
    """
    if is_missing_value(value):
        raw = str(value) if value is not None else ""
        return NormalizedName(
            original=raw,
            cleaned="",
            no_accents="",
            alphanumeric="",
            tokens=[],
        )

    raw = str(value).strip()

    # 1. Unicode NFC + whitespace collapse + lowercase
    cleaned = _unicode_normalize(raw).lower()

    # 2. Strip Latin accents only
    no_accents = _strip_accents_latin(cleaned)

    # 3. Remove all punctuation -> alphanumeric + whitespace
    alphanumeric = _to_alphanumeric(no_accents)

    # 4. Tokenize
    tokens = _tokenize(alphanumeric)

    return NormalizedName(
        original=raw,
        cleaned=cleaned,
        no_accents=no_accents,
        alphanumeric=alphanumeric,
        tokens=tokens,
    )


# ---------------------------------------------------------------------------
# Address normalization
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class NormalizedAddress:
    """Multiple derived representations of a business address.

    Attributes
    ----------
    original : str
        Verbatim input (stripped of leading/trailing whitespace).
    cleaned : str
        Unicode-normalised, lowered, whitespace-collapsed, with embedded
        "null" tokens removed.
    no_accents : str
        ``cleaned`` with Latin-script accents removed.
    alphanumeric : str
        ``no_accents`` with all punctuation removed.
    tokens : list[str]
        Whitespace-split tokens from ``alphanumeric``.
    numeric_tokens : list[str]
        Tokens from ``alphanumeric`` that contain at least one digit
        (house numbers, PIN/ZIP codes, floor numbers, etc.).
    """
    original: str
    cleaned: str
    no_accents: str
    alphanumeric: str
    tokens: list[str]
    numeric_tokens: list[str]


def normalize_address(value: object) -> NormalizedAddress:
    """Normalise a ``business_address`` value.

    Returns a :class:`NormalizedAddress` with several derived
    representations.  Embedded "null" sentinel tokens are removed but no
    country-specific rewriting is applied.

    If *value* is missing, every field except ``original`` is the empty
    string / empty list.
    """
    if is_missing_value(value):
        raw = str(value) if value is not None else ""
        return NormalizedAddress(
            original=raw,
            cleaned="",
            no_accents="",
            alphanumeric="",
            tokens=[],
            numeric_tokens=[],
        )

    raw = str(value).strip()

    # 1. Unicode NFC + whitespace collapse + lowercase
    cleaned = _unicode_normalize(raw).lower()

    # 2. Remove literal "null" tokens that appear as noise
    cleaned = _NULL_TOKEN.sub(" ", cleaned)
    cleaned = _MULTI_WS.sub(" ", cleaned).strip()

    # 3. Strip Latin accents
    no_accents = _strip_accents_latin(cleaned)

    # 4. Alphanumeric
    alphanumeric = _to_alphanumeric(no_accents)

    # 5. Tokenize
    tokens = _tokenize(alphanumeric)

    # 6. Extract numeric tokens (contain at least one digit)
    numeric_tokens = [t for t in tokens if any(c.isdigit() for c in t)]

    return NormalizedAddress(
        original=raw,
        cleaned=cleaned,
        no_accents=no_accents,
        alphanumeric=alphanumeric,
        tokens=tokens,
        numeric_tokens=numeric_tokens,
    )


# ---------------------------------------------------------------------------
# Country normalization
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class NormalizedCountry:
    """Normalised country representation.

    Attributes
    ----------
    original : str
        Verbatim input (stripped of leading/trailing whitespace).
    cleaned : str
        Lowercased, whitespace-collapsed, Unicode-normalised.
    """
    original: str
    cleaned: str


def normalize_country(value: object) -> NormalizedCountry:
    """Normalise a ``country`` value.

    Simple lowercase + whitespace normalisation.  Does **not** map country
    names to codes or vice-versa — the value space is treated as an open
    set of string labels.

    If *value* is missing, ``cleaned`` is the empty string.
    """
    if is_missing_value(value):
        raw = str(value) if value is not None else ""
        return NormalizedCountry(original=raw, cleaned="")

    raw = str(value).strip()
    cleaned = _unicode_normalize(raw).lower()
    return NormalizedCountry(original=raw, cleaned=cleaned)
