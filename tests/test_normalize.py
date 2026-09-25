"""
Unit tests for src/preprocessing/normalize.py

Run from the project root:
    python -m pytest tests/test_normalize.py -v
"""

import math
import sys
import os

# Ensure src/ is importable regardless of how pytest is invoked.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from preprocessing.normalize import (
    NormalizedAddress,
    NormalizedCountry,
    NormalizedName,
    is_missing_value,
    normalize_address,
    normalize_country,
    normalize_name,
)


# ===================================================================
# 1. is_missing_value
# ===================================================================


class TestIsMissingValue:

    # --- True cases ---

    def test_none(self):
        assert is_missing_value(None) is True

    def test_float_nan(self):
        assert is_missing_value(float("nan")) is True

    def test_math_nan(self):
        assert is_missing_value(math.nan) is True

    def test_empty_string(self):
        assert is_missing_value("") is True

    def test_whitespace_only_space(self):
        assert is_missing_value("   ") is True

    def test_whitespace_only_tab(self):
        assert is_missing_value("\t") is True

    def test_whitespace_only_newline(self):
        assert is_missing_value(" \n ") is True

    def test_null_lower(self):
        assert is_missing_value("null") is True

    def test_null_upper(self):
        assert is_missing_value("NULL") is True

    def test_null_mixed(self):
        assert is_missing_value("Null") is True

    def test_nan_lower(self):
        assert is_missing_value("nan") is True

    def test_nan_camel(self):
        assert is_missing_value("NaN") is True

    def test_none_string(self):
        assert is_missing_value("None") is True

    def test_na_slash(self):
        assert is_missing_value("N/A") is True

    def test_na_noslash(self):
        assert is_missing_value("NA") is True

    def test_na_lower(self):
        assert is_missing_value("na") is True

    def test_undefined(self):
        assert is_missing_value("undefined") is True

    def test_missing(self):
        assert is_missing_value("missing") is True

    def test_dash(self):
        assert is_missing_value("-") is True

    def test_double_dash(self):
        assert is_missing_value("--") is True

    def test_dot(self):
        assert is_missing_value(".") is True

    def test_null_with_whitespace(self):
        assert is_missing_value("  null  ") is True

    # --- False cases ---

    def test_actual_name(self):
        assert is_missing_value("Raj Investments") is False

    def test_zero_string(self):
        assert is_missing_value("0") is False

    def test_false_string(self):
        assert is_missing_value("false") is False

    def test_integer_zero(self):
        assert is_missing_value(0) is False

    def test_regular_float(self):
        assert is_missing_value(1.5) is False

    def test_word_containing_null(self):
        assert is_missing_value("annulled") is False

    def test_word_nullable(self):
        assert is_missing_value("nullable") is False

    def test_us_country(self):
        assert is_missing_value("US") is False

    def test_india_country(self):
        assert is_missing_value("India") is False


# ===================================================================
# 2. normalize_name — business names
# ===================================================================


class TestNormalizeName:

    def test_returns_dataclass(self):
        r = normalize_name("Hello")
        assert isinstance(r, NormalizedName)

    def test_lowercase(self):
        r = normalize_name("PAYNE ENTERPRISES")
        assert r.cleaned == "payne enterprises"

    def test_whitespace_collapse(self):
        r = normalize_name("  Summit   Health    LLC  ")
        assert r.cleaned == "summit health llc"
        assert r.original == "Summit   Health    LLC"

    def test_punctuation_in_cleaned(self):
        r = normalize_name("B+ Retail Inc")
        assert r.cleaned == "b+ retail inc"

    def test_punctuation_removed_in_alphanumeric(self):
        r = normalize_name("B+ Retail Inc")
        assert r.alphanumeric == "b retail inc"

    def test_hyphen_removed_in_alphanumeric(self):
        r = normalize_name("PAYNE-ENRTPRMISES")
        assert r.alphanumeric == "payne enrtprmises"

    def test_angle_brackets_removed(self):
        r = normalize_name("<< Team Ecole")
        assert r.alphanumeric == "team ecole"

    def test_dot_in_legal_suffix(self):
        r = normalize_name("Fractales Amis Groupe S.A.S")
        assert r.cleaned == "fractales amis groupe s.a.s"
        assert r.alphanumeric == "fractales amis groupe s a s"

    def test_apostrophe_in_name(self):
        r = normalize_name("Orelee's Barbershop")
        assert r.cleaned == "orelee’s barbershop" or r.cleaned == "orelee's barbershop"
        assert "orelee" in r.alphanumeric
        assert "barbershop" in r.alphanumeric

    def test_latin_accent_stripped(self):
        r = normalize_name("Payne Énterprises")
        assert r.cleaned == "payne énterprises"
        assert r.no_accents == "payne enterprises"
        assert r.alphanumeric == "payne enterprises"

    def test_french_a_grave(self):
        r = normalize_name("SCI Ptit Àmicale")
        assert r.no_accents == "sci ptit amicale"

    def test_devanagari_preserved(self):
        devanagari = "राम मार्केटिंग प्राइवेट लिमिटेड"
        r = normalize_name(devanagari)
        assert r.cleaned == devanagari
        assert r.no_accents == devanagari
        # Tokens should be whole Devanagari words, not shattered consonants
        assert len(r.tokens) == 4

    def test_tamil_preserved(self):
        tamil = "ராஜ் இன்வெஸ்ட்மெண்ட்ஸ் எல்எல்பி"
        r = normalize_name(tamil)
        assert len(r.tokens) == 3
        # Alphanumeric should not be empty
        assert len(r.alphanumeric) > 10

    def test_mixed_english_tamil(self):
        mixed = "Raj Investments எல்எல்பி"
        r = normalize_name(mixed)
        assert r.tokens[0] == "raj"
        assert r.tokens[1] == "investments"
        assert len(r.tokens) == 3

    def test_tokenization_basic(self):
        r = normalize_name("Nexnovi DBA Aguilar Diversified LLC")
        assert r.tokens == ["nexnovi", "dba", "aguilar", "diversified", "llc"]

    def test_url_as_name(self):
        r = normalize_name("maurewilliamscolombier.com")
        assert r.cleaned == "maurewilliamscolombier.com"
        assert "maurewilliamscolombier" in r.alphanumeric

    def test_missing_none(self):
        r = normalize_name(None)
        assert r.original == ""
        assert r.cleaned == ""
        assert r.tokens == []

    def test_missing_empty(self):
        r = normalize_name("")
        assert r.cleaned == ""
        assert r.tokens == []

    def test_missing_null_string(self):
        r = normalize_name("null")
        assert r.original == "null"
        assert r.cleaned == ""
        assert r.tokens == []

    def test_missing_nan_string(self):
        r = normalize_name("NaN")
        assert r.cleaned == ""
        assert r.tokens == []


# ===================================================================
# 3. normalize_address
# ===================================================================


class TestNormalizeAddress:

    def test_returns_dataclass(self):
        r = normalize_address("123 Main St")
        assert isinstance(r, NormalizedAddress)

    def test_lowercase(self):
        r = normalize_address("105 ELM ST, MORGANTON, NC")
        assert r.cleaned == "105 elm st, morganton, nc"

    def test_whitespace_collapse(self):
        r = normalize_address("  105   ELM ST ,  MORGANTON  ")
        assert r.cleaned == "105 elm st , morganton"

    def test_punctuation_preserved_in_cleaned(self):
        r = normalize_address("6(29), C.I.T. Colony, Chennai")
        assert "6(29)" in r.cleaned
        assert "c.i.t." in r.cleaned

    def test_punctuation_removed_in_alphanumeric(self):
        r = normalize_address("6(29), C.I.T. Colony, Chennai")
        assert r.alphanumeric == "6 29 c i t colony chennai"

    def test_numeric_tokens_extracted(self):
        r = normalize_address("1795 Westchester Drive, High Point, NC")
        assert "1795" in r.numeric_tokens

    def test_numeric_tokens_ordinals(self):
        r = normalize_address("Door No 183, 41St Cross, 22Nd Main")
        assert "183" in r.numeric_tokens
        assert "41st" in r.numeric_tokens
        assert "22nd" in r.numeric_tokens

    def test_numeric_tokens_indian_kh_no(self):
        r = normalize_address("KH NO. -570/13, NEW DELHI")
        assert "570" in r.numeric_tokens
        assert "13" in r.numeric_tokens

    def test_null_token_removed(self):
        r = normalize_address("067 PRODUCTION CT, NULL, INDEPENDENCE, KY")
        assert "null" not in r.cleaned.split()
        assert "null" not in r.tokens

    def test_null_lowercase_removed(self):
        r = normalize_address("22120 COYOTE CAVE TRL, null, SPICEWOOD, TX")
        assert "null" not in r.tokens

    def test_annulled_not_corrupted(self):
        r = normalize_address("123 Annulled Lane, Springfield")
        assert "annulled" in r.cleaned
        assert "annulled" in r.tokens

    def test_nullable_not_corrupted(self):
        r = normalize_address("Nullable Street, City")
        assert "nullable" in r.cleaned

    def test_french_address_accent_stripped(self):
        r = normalize_address("175 Boulevard du Président Franklin Roosevelt, Bordeaux")
        assert "president" in r.no_accents
        assert "president" in r.tokens

    def test_kannada_address_preserved(self):
        r = normalize_address("Bengaluru, ಕರ್ನಾಟಕ")
        assert "ಕರ್ನಾಟಕ" in r.alphanumeric

    def test_french_rue(self):
        r = normalize_address("63 R. DE DIEPPE, LILLE, Hauts-de-France")
        assert r.cleaned == "63 r. de dieppe, lille, hauts-de-france"
        assert "63" in r.numeric_tokens

    def test_missing_none(self):
        r = normalize_address(None)
        assert r.original == ""
        assert r.cleaned == ""
        assert r.tokens == []
        assert r.numeric_tokens == []

    def test_missing_empty(self):
        r = normalize_address("")
        assert r.cleaned == ""
        assert r.tokens == []

    def test_missing_null_string(self):
        r = normalize_address("null")
        assert r.original == "null"
        assert r.cleaned == ""
        assert r.tokens == []

    def test_tokens_non_empty(self):
        r = normalize_address("1795 Westchester Drive, High Point, NC")
        assert len(r.tokens) == 6


# ===================================================================
# 4. normalize_country
# ===================================================================


class TestNormalizeCountry:

    def test_returns_dataclass(self):
        r = normalize_country("US")
        assert isinstance(r, NormalizedCountry)

    def test_us(self):
        r = normalize_country("US")
        assert r.cleaned == "us"
        assert r.original == "US"

    def test_india(self):
        r = normalize_country("India")
        assert r.cleaned == "india"

    def test_france(self):
        r = normalize_country("France")
        assert r.cleaned == "france"

    def test_uppercase_india(self):
        r = normalize_country("INDIA")
        assert r.cleaned == "india"

    def test_whitespace_trimmed(self):
        r = normalize_country("  US  ")
        assert r.cleaned == "us"
        assert r.original == "US"

    def test_already_lowercase(self):
        r = normalize_country("france")
        assert r.cleaned == "france"

    def test_missing_none(self):
        r = normalize_country(None)
        assert r.cleaned == ""

    def test_missing_empty(self):
        r = normalize_country("")
        assert r.cleaned == ""

    def test_missing_null(self):
        r = normalize_country("null")
        assert r.cleaned == ""

    def test_distinct_countries_stay_distinct(self):
        us = normalize_country("US")
        india = normalize_country("India")
        france = normalize_country("France")
        assert us.cleaned != india.cleaned
        assert us.cleaned != france.cleaned
        assert india.cleaned != france.cleaned

    def test_novel_country_accepted(self):
        r = normalize_country("Brazil")
        assert r.cleaned == "brazil"
        assert r.original == "Brazil"


# ===================================================================
# 5. Information preservation
# ===================================================================


class TestInformationPreservation:

    def test_name_original_preserved(self):
        raw = "PVT. INDUSTRIES PMB LEASING LIMITED"
        r = normalize_name(raw)
        assert r.original == raw

    def test_name_original_strips_outer_whitespace_only(self):
        r = normalize_name("  Hello World  ")
        assert r.original == "Hello World"

    def test_address_original_preserved(self):
        raw = "KH NO. -570/13, NEW DELHI, WEST DELHI, Delhi"
        r = normalize_address(raw)
        assert r.original == raw

    def test_country_original_preserved(self):
        r = normalize_country("  France  ")
        assert r.original == "France"

    def test_devanagari_not_erased_in_name(self):
        devanagari = "राम"
        r = normalize_name(devanagari)
        assert devanagari in r.cleaned
        assert devanagari in r.alphanumeric
        assert len(r.tokens) == 1

    def test_devanagari_not_erased_in_address(self):
        addr = "123 Main, महाराष्ट्र"
        r = normalize_address(addr)
        assert "महाराष्ट्र" in r.alphanumeric

    def test_numeric_info_preserved_in_address(self):
        r = normalize_address("22120 1/2 COYOTE CAVE TRL, null, SPICEWOOD, TX")
        assert "22120" in r.numeric_tokens
        # The fraction 1/2 becomes separate tokens 1 and 2
        assert "1" in r.numeric_tokens
        assert "2" in r.numeric_tokens

    def test_pin_code_preserved(self):
        r = normalize_address("Bangalore 560082, Karnataka")
        assert "560082" in r.numeric_tokens

    def test_zip_code_preserved(self):
        r = normalize_address("1795 Westchester Drive, High Point, NC 27265")
        assert "27265" in r.numeric_tokens


# ===================================================================
# 6. Determinism
# ===================================================================


class TestDeterminism:

    def test_name_deterministic(self):
        inp = "Payne Énterprises LLC"
        r1 = normalize_name(inp)
        r2 = normalize_name(inp)
        assert r1.cleaned == r2.cleaned
        assert r1.no_accents == r2.no_accents
        assert r1.alphanumeric == r2.alphanumeric
        assert r1.tokens == r2.tokens

    def test_address_deterministic(self):
        inp = "067 PRODUCTION CT, NULL, INDEPENDENCE, KY"
        r1 = normalize_address(inp)
        r2 = normalize_address(inp)
        assert r1.cleaned == r2.cleaned
        assert r1.alphanumeric == r2.alphanumeric
        assert r1.tokens == r2.tokens
        assert r1.numeric_tokens == r2.numeric_tokens

    def test_country_deterministic(self):
        r1 = normalize_country("France")
        r2 = normalize_country("France")
        assert r1.cleaned == r2.cleaned

    def test_missing_deterministic(self):
        assert is_missing_value("null") == is_missing_value("null")
        assert is_missing_value(None) == is_missing_value(None)

    def test_devanagari_deterministic(self):
        inp = "राम मार्केटिंग"
        r1 = normalize_name(inp)
        r2 = normalize_name(inp)
        assert r1.alphanumeric == r2.alphanumeric
        assert r1.tokens == r2.tokens


# ===================================================================
# 7. Idempotence
# ===================================================================


class TestIdempotence:

    def test_name_cleaned_is_idempotent(self):
        r1 = normalize_name("  Summit   Health    LLC  ")
        r2 = normalize_name(r1.cleaned)
        assert r2.cleaned == r1.cleaned

    def test_name_alphanumeric_is_idempotent(self):
        r1 = normalize_name("B+ Retail Inc")
        r2 = normalize_name(r1.alphanumeric)
        assert r2.alphanumeric == r1.alphanumeric

    def test_address_cleaned_is_idempotent(self):
        r1 = normalize_address("105 ELM ST, MORGANTON, NC")
        r2 = normalize_address(r1.cleaned)
        assert r2.cleaned == r1.cleaned

    def test_address_alphanumeric_is_idempotent(self):
        r1 = normalize_address("6(29), C.I.T. Colony, Chennai")
        r2 = normalize_address(r1.alphanumeric)
        assert r2.alphanumeric == r1.alphanumeric

    def test_country_is_idempotent(self):
        r1 = normalize_country("France")
        r2 = normalize_country(r1.cleaned)
        assert r2.cleaned == r1.cleaned

    def test_devanagari_name_idempotent(self):
        inp = "राम मार्केटिंग"
        r1 = normalize_name(inp)
        r2 = normalize_name(r1.alphanumeric)
        assert r2.alphanumeric == r1.alphanumeric
        assert r2.tokens == r1.tokens
