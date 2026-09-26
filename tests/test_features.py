"""
Unit tests for src/features/pairwise.py

Run from the project root:
    python -m pytest tests/test_features.py -v
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from blocking.base import Entity
from features.pairwise import (
    extract_features,
    extract_features_batch,
    FEATURE_NAMES,
    PairwiseFeatures,
)


def _make_entity(eid, name_cleaned="", name_alnum="", country="", addr_cleaned="", addr_alnum=""):
    return Entity(
        entity_id=eid,
        name_cleaned=name_cleaned,
        name_alphanumeric=name_alnum,
        country_cleaned=country,
        addr_cleaned=addr_cleaned,
        addr_alphanumeric=addr_alnum,
    )


class TestFeatureExtraction:

    def test_identical_entities(self):
        """Two identical entities should have perfect feature scores."""
        s1 = _make_entity(
            "S1-1",
            name_cleaned="acme incorporated",
            name_alnum="acme incorporated",
            country="us",
            addr_cleaned="123 main st",
            addr_alnum="123 main st",
        )
        s2 = _make_entity(
            "S2-1",
            name_cleaned="acme incorporated",
            name_alnum="acme incorporated",
            country="us",
            addr_cleaned="123 main st",
            addr_alnum="123 main st",
        )
        result = extract_features(s1, s2)

        assert result.features["name_exact_cleaned"] == 1.0
        assert result.features["name_exact_alphanumeric"] == 1.0
        assert result.features["name_token_jaccard"] == 1.0
        assert result.features["addr_exact_cleaned"] == 1.0
        assert result.features["addr_exact_alphanumeric"] == 1.0
        assert result.features["addr_token_jaccard"] == 1.0
        assert result.features["country_exact_match"] == 1.0
        assert result.features["name_and_addr_exact"] == 1.0

    def test_completely_different_entities(self):
        """Completely different entities should have minimal overlap."""
        s1 = _make_entity(
            "S1-1",
            name_cleaned="acme inc",
            name_alnum="acme inc",
            country="us",
            addr_cleaned="123 main st",
            addr_alnum="123 main st",
        )
        s2 = _make_entity(
            "S2-1",
            name_cleaned="beta corp",
            name_alnum="beta corp",
            country="india",
            addr_cleaned="456 oak ave",
            addr_alnum="456 oak ave",
        )
        result = extract_features(s1, s2)

        assert result.features["name_exact_cleaned"] == 0.0
        assert result.features["name_exact_alphanumeric"] == 0.0
        assert result.features["name_token_jaccard"] == 0.0
        assert result.features["name_token_intersection_count"] == 0.0
        assert result.features["addr_exact_cleaned"] == 0.0
        assert result.features["addr_token_jaccard"] == 0.0
        assert result.features["country_exact_match"] == 0.0

    def test_reordered_tokens(self):
        """Reordered tokens should not match exactly but have high token overlap."""
        s1 = _make_entity("S1-1", name_alnum="acme incorporated", country="us")
        s2 = _make_entity("S2-1", name_alnum="incorporated acme", country="us")
        result = extract_features(s1, s2)

        assert result.features["name_exact_alphanumeric"] == 0.0  # Not exact
        assert result.features["name_token_jaccard"] == 1.0  # Same tokens
        assert result.features["name_token_intersection_count"] == 2.0

    def test_partial_token_overlap(self):
        """Partial token overlap should compute correct Jaccard and containment."""
        s1 = _make_entity("S1-1", name_alnum="acme inc", country="us")
        s2 = _make_entity("S2-1", name_alnum="acme corp", country="us")
        result = extract_features(s1, s2)

        # Intersection: {acme}, Union: {acme, inc, corp}
        assert result.features["name_token_intersection_count"] == 1.0
        assert result.features["name_token_jaccard"] == 1 / 3  # 1 shared / 3 total
        assert result.features["name_token_containment_s1"] == 0.5  # 1 / 2 (s1 has 2 tokens)
        assert result.features["name_token_containment_cand"] == 0.5  # 1 / 2

    def test_missing_name_values(self):
        """Missing names should be handled safely."""
        s1 = _make_entity("S1-1", name_alnum="", country="us")
        s2 = _make_entity("S2-1", name_alnum="acme inc", country="us")
        result = extract_features(s1, s2)

        assert result.features["s1_name_missing"] == 1.0
        assert result.features["cand_name_missing"] == 0.0
        assert result.features["name_exact_alphanumeric"] == 0.0
        assert result.features["name_token_jaccard"] == 0.0
        assert result.features["name_token_containment_s1"] == 1.0  # Empty set contained in any set

    def test_both_names_missing(self):
        """Both names missing should return sensible defaults."""
        s1 = _make_entity("S1-1", name_alnum="", country="us")
        s2 = _make_entity("S2-1", name_alnum="", country="us")
        result = extract_features(s1, s2)

        assert result.features["s1_name_missing"] == 1.0
        assert result.features["cand_name_missing"] == 1.0
        assert result.features["name_token_jaccard"] == 1.0  # Both empty -> identical
        assert result.features["name_length_ratio"] == 1.0

    def test_missing_address_values(self):
        """Missing addresses should be handled safely."""
        s1 = _make_entity("S1-1", name_alnum="acme inc", addr_alnum="", country="us")
        s2 = _make_entity("S2-1", name_alnum="acme inc", addr_alnum="123 main st", country="us")
        result = extract_features(s1, s2)

        assert result.features["s1_addr_missing"] == 1.0
        assert result.features["cand_addr_missing"] == 0.0
        assert result.features["addr_exact_alphanumeric"] == 0.0
        assert result.features["addr_token_jaccard"] == 0.0

    def test_country_match_and_mismatch(self):
        """Country matching should work correctly."""
        s1 = _make_entity("S1-1", name_alnum="acme", country="us")
        s2_match = _make_entity("S2-1", name_alnum="acme", country="us")
        s2_mismatch = _make_entity("S2-2", name_alnum="acme", country="india")

        result_match = extract_features(s1, s2_match)
        result_mismatch = extract_features(s1, s2_mismatch)

        assert result_match.features["country_exact_match"] == 1.0
        assert result_mismatch.features["country_exact_match"] == 0.0

    def test_address_numeric_overlap(self):
        """Numeric token overlap in addresses."""
        s1 = _make_entity("S1-1", name_alnum="acme", addr_alnum="123 main st apt 4b", country="us")
        s2 = _make_entity("S2-1", name_alnum="acme", addr_alnum="123 oak ave floor 5", country="us")
        result = extract_features(s1, s2)

        # Numeric tokens: s1 = {123, 4b}, s2 = {123, 5}
        # Intersection: {123}
        assert result.features["addr_numeric_intersection_count"] == 1.0
        # Jaccard: 1 / 3
        assert abs(result.features["addr_numeric_jaccard"] - (1/3)) < 1e-6

    def test_length_ratio(self):
        """Length ratio computation."""
        s1 = _make_entity("S1-1", name_alnum="acme", country="us")
        s2 = _make_entity("S2-1", name_alnum="acme incorporated", country="us")
        result = extract_features(s1, s2)

        # len("acme") = 4, len("acme incorporated") = 17 (space counts)
        # ratio = 4 / 17 ≈ 0.235
        assert 0.20 < result.features["name_length_ratio"] < 0.25

    def test_char_jaccard(self):
        """Character-level Jaccard similarity."""
        s1 = _make_entity("S1-1", name_alnum="abc", country="us")
        s2 = _make_entity("S2-1", name_alnum="bcd", country="us")
        result = extract_features(s1, s2)

        # s1 chars: {a, b, c}, s2 chars: {b, c, d}
        # Intersection: {b, c}, Union: {a, b, c, d}
        # Jaccard: 2/4 = 0.5
        assert result.features["name_char_jaccard"] == 0.5

    def test_token_count_diff(self):
        """Token count difference."""
        s1 = _make_entity("S1-1", name_alnum="acme inc", country="us")
        s2 = _make_entity("S2-1", name_alnum="acme incorporated company", country="us")
        result = extract_features(s1, s2)

        # s1: 2 tokens, s2: 3 tokens
        assert result.features["name_token_count_diff"] == 1.0

    def test_cross_field_features(self):
        """Cross-field combination features."""
        s1 = _make_entity(
            "S1-1",
            name_alnum="acme incorporated",
            addr_alnum="123 main st",
            country="us",
        )
        s2 = _make_entity(
            "S2-1",
            name_alnum="acme incorporated",
            addr_alnum="123 main st",
            country="us",
        )
        result = extract_features(s1, s2)

        # Both name and address exact
        assert result.features["name_and_addr_exact"] == 1.0

    def test_strong_name_weak_addr(self):
        """Strong name + weak address feature."""
        s1 = _make_entity(
            "S1-1",
            name_alnum="acme incorporated",
            addr_alnum="123 main st",
            country="us",
        )
        s2 = _make_entity(
            "S2-1",
            name_alnum="acme incorporated",  # Exact match -> strong
            addr_alnum="456 main st",  # Some overlap -> weak
            country="us",
        )
        result = extract_features(s1, s2)

        assert result.features["strong_name_weak_addr"] == 1.0

    def test_weak_name_strong_addr(self):
        """Weak name + strong address feature."""
        s1 = _make_entity(
            "S1-1",
            name_alnum="acme inc",
            addr_alnum="123 main st",
            country="us",
        )
        s2 = _make_entity(
            "S2-1",
            name_alnum="acme corp",  # Some overlap -> weak
            addr_alnum="123 main st",  # Exact match -> strong
            country="us",
        )
        result = extract_features(s1, s2)

        assert result.features["weak_name_strong_addr"] == 1.0

    def test_s2_and_s3_use_same_api(self):
        """S2 and S3 candidates should work identically."""
        s1 = _make_entity("S1-1", name_alnum="acme inc", country="us")
        s2 = _make_entity("S2-1", name_alnum="acme corp", country="us")
        s3 = _make_entity("S3-1", name_alnum="acme corp", country="us")

        result_s2 = extract_features(s1, s2)
        result_s3 = extract_features(s1, s3)

        # Features should be identical (IDs differ but feature values same)
        for name in FEATURE_NAMES:
            assert result_s2.features[name] == result_s3.features[name]

    def test_no_nan_outputs(self):
        """Feature extraction should never produce NaN."""
        s1 = _make_entity("S1-1", name_alnum="acme", addr_alnum="", country="us")
        s2 = _make_entity("S2-1", name_alnum="", addr_alnum="123 main", country="india")
        result = extract_features(s1, s2)

        for name, value in result.features.items():
            assert not math.isnan(value), f"Feature {name} is NaN"

    def test_no_inf_outputs(self):
        """Feature extraction should never produce inf."""
        s1 = _make_entity("S1-1", name_alnum="acme" * 1000, country="us")
        s2 = _make_entity("S2-1", name_alnum="beta" * 1000, country="us")
        result = extract_features(s1, s2)

        for name, value in result.features.items():
            assert not math.isinf(value), f"Feature {name} is inf"
            assert -1e308 < value < 1e308, f"Feature {name} is too large: {value}"

    def test_deterministic_output(self):
        """Same inputs should produce identical features."""
        s1 = _make_entity("S1-1", name_alnum="acme inc", addr_alnum="123 main", country="us")
        s2 = _make_entity("S2-1", name_alnum="acme corp", addr_alnum="456 oak", country="us")

        result1 = extract_features(s1, s2)
        result2 = extract_features(s1, s2)

        for name in FEATURE_NAMES:
            assert result1.features[name] == result2.features[name]

    def test_all_feature_names_present(self):
        """All declared feature names should be in the result."""
        s1 = _make_entity("S1-1", name_alnum="acme", country="us")
        s2 = _make_entity("S2-1", name_alnum="beta", country="india")
        result = extract_features(s1, s2)

        for name in FEATURE_NAMES:
            assert name in result.features, f"Missing feature: {name}"

    def test_to_vector(self):
        """to_vector should return features in correct order."""
        s1 = _make_entity("S1-1", name_alnum="acme", country="us")
        s2 = _make_entity("S2-1", name_alnum="beta", country="india")
        result = extract_features(s1, s2)

        vector = result.to_vector()
        assert len(vector) == len(FEATURE_NAMES)

        # Verify order
        for i, name in enumerate(FEATURE_NAMES):
            assert vector[i] == result.features[name]

    def test_blocking_route_tracking(self):
        """Blocking route should be tracked correctly."""
        s1 = _make_entity("S1-1", name_alnum="acme", country="us")
        s2 = _make_entity("S2-1", name_alnum="acme", country="us")
        result = extract_features(s1, s2, blocking_route="exact_name")

        assert result.blocking_route == "exact_name"
        assert result.s1_id == "S1-1"
        assert result.candidate_id == "S2-1"


class TestBatchExtraction:

    def test_batch_extraction_basic(self):
        """Batch extraction should work for multiple pairs."""
        s1_entities = {
            "S1-1": _make_entity("S1-1", name_alnum="acme", country="us"),
            "S1-2": _make_entity("S1-2", name_alnum="beta", country="india"),
        }
        candidate_entities = {
            "S2-1": _make_entity("S2-1", name_alnum="acme corp", country="us"),
            "S3-1": _make_entity("S3-1", name_alnum="beta llc", country="india"),
        }
        pairs = [("S1-1", "S2-1"), ("S1-2", "S3-1")]

        results = extract_features_batch(s1_entities, candidate_entities, pairs)

        assert len(results) == 2
        assert results[0].s1_id == "S1-1"
        assert results[0].candidate_id == "S2-1"
        assert results[1].s1_id == "S1-2"
        assert results[1].candidate_id == "S3-1"

    def test_batch_with_blocking_routes(self):
        """Batch extraction should track blocking routes."""
        s1_entities = {
            "S1-1": _make_entity("S1-1", name_alnum="acme", country="us"),
        }
        candidate_entities = {
            "S2-1": _make_entity("S2-1", name_alnum="acme", country="us"),
            "S2-2": _make_entity("S2-2", name_alnum="acme inc", country="us"),
        }
        pairs = [("S1-1", "S2-1"), ("S1-1", "S2-2")]
        routes = {
            ("S1-1", "S2-1"): "exact_name",
            ("S1-1", "S2-2"): "token_overlap",
        }

        results = extract_features_batch(s1_entities, candidate_entities, pairs, routes)

        assert len(results) == 2
        assert results[0].blocking_route == "exact_name"
        assert results[1].blocking_route == "token_overlap"

    def test_batch_skips_missing_entities(self):
        """Batch should skip pairs with missing entities."""
        s1_entities = {
            "S1-1": _make_entity("S1-1", name_alnum="acme", country="us"),
        }
        candidate_entities = {
            "S2-1": _make_entity("S2-1", name_alnum="acme", country="us"),
        }
        pairs = [
            ("S1-1", "S2-1"),  # Valid
            ("S1-99", "S2-1"),  # S1 missing
            ("S1-1", "S2-99"),  # Candidate missing
        ]

        results = extract_features_batch(s1_entities, candidate_entities, pairs)

        assert len(results) == 1
        assert results[0].s1_id == "S1-1"
        assert results[0].candidate_id == "S2-1"

    def test_batch_empty_input(self):
        """Batch with empty input should return empty list."""
        results = extract_features_batch({}, {}, [])
        assert len(results) == 0


class TestEdgeCases:

    def test_very_long_strings(self):
        """Feature extraction should handle very long strings."""
        long_name = "acme " * 1000
        s1 = _make_entity("S1-1", name_alnum=long_name, country="us")
        s2 = _make_entity("S2-1", name_alnum=long_name, country="us")
        result = extract_features(s1, s2)

        assert result.features["name_exact_alphanumeric"] == 1.0
        assert not math.isnan(result.features["name_char_jaccard"])

    def test_unicode_names(self):
        """Feature extraction should handle Unicode correctly."""
        s1 = _make_entity("S1-1", name_alnum="मार्केटिंग कंपनी", country="india")
        s2 = _make_entity("S2-1", name_alnum="मार्केटिंग कंपनी", country="india")
        result = extract_features(s1, s2)

        assert result.features["name_exact_alphanumeric"] == 1.0
        assert result.features["name_token_jaccard"] == 1.0

    def test_single_character_names(self):
        """Single character names should be handled."""
        s1 = _make_entity("S1-1", name_alnum="a", country="us")
        s2 = _make_entity("S2-1", name_alnum="b", country="us")
        result = extract_features(s1, s2)

        assert result.features["name_exact_alphanumeric"] == 0.0
        assert result.features["name_token_jaccard"] == 0.0
        assert result.features["name_char_jaccard"] == 0.0

    def test_whitespace_only_values(self):
        """Whitespace-only values should be treated as empty after tokenization."""
        s1 = _make_entity("S1-1", name_alnum="   ", country="us")
        s2 = _make_entity("S2-1", name_alnum="acme", country="us")
        result = extract_features(s1, s2)

        # Whitespace-only after split() becomes empty token list
        # Missing indicator is based on non-empty string, but token count will be 0
        assert result.features["s1_name_token_count"] == 0.0
        assert result.features["name_token_jaccard"] == 0.0
