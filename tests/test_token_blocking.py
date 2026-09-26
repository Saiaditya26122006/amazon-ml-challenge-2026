"""
Unit tests for src/blocking/token_blocking.py

Run from the project root:
    python -m pytest tests/test_token_blocking.py -v
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from blocking.base import Entity
from blocking.token_blocking import (
    tokenize_name,
    build_country_token_index,
    filter_index_by_df,
    retrieve_by_token_overlap,
    top_tokens_by_df,
    df_percentiles,
)
from blocking.candidate_union import candidate_union
from blocking.evaluate_blocking import evaluate_blocking


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entity(eid, name_alnum="", country=""):
    return Entity(
        entity_id=eid,
        name_cleaned="",
        name_alphanumeric=name_alnum,
        country_cleaned=country,
        addr_cleaned="",
        addr_alphanumeric="",
    )


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------


class TestTokenizeName:

    def test_basic_split(self):
        assert tokenize_name("acme incorporated") == {"acme", "incorporated"}

    def test_deduplicates(self):
        assert tokenize_name("abc abc abc") == {"abc"}

    def test_empty_string(self):
        assert tokenize_name("") == frozenset()

    def test_whitespace_only(self):
        assert tokenize_name("   ") == frozenset()

    def test_single_token(self):
        assert tokenize_name("acme") == {"acme"}

    def test_extra_whitespace(self):
        assert tokenize_name("  acme   inc  ") == {"acme", "inc"}


# ---------------------------------------------------------------------------
# Index building
# ---------------------------------------------------------------------------


class TestBuildCountryTokenIndex:

    def test_basic_index(self):
        entities = {
            "S2-1": _make_entity("S2-1", name_alnum="acme inc", country="us"),
            "S2-2": _make_entity("S2-2", name_alnum="acme corp", country="us"),
        }
        idx = build_country_token_index(entities)
        assert idx[("us", "acme")] == {"S2-1", "S2-2"}
        assert idx[("us", "inc")] == {"S2-1"}
        assert idx[("us", "corp")] == {"S2-2"}

    def test_country_separates_keys(self):
        entities = {
            "S2-1": _make_entity("S2-1", name_alnum="acme inc", country="us"),
            "S2-2": _make_entity("S2-2", name_alnum="acme inc", country="india"),
        }
        idx = build_country_token_index(entities)
        assert idx[("us", "acme")] == {"S2-1"}
        assert idx[("india", "acme")] == {"S2-2"}

    def test_empty_country_skipped(self):
        entities = {"S2-1": _make_entity("S2-1", name_alnum="acme inc", country="")}
        idx = build_country_token_index(entities)
        assert len(idx) == 0

    def test_empty_name_skipped(self):
        entities = {"S2-1": _make_entity("S2-1", name_alnum="", country="us")}
        idx = build_country_token_index(entities)
        assert len(idx) == 0

    def test_duplicate_tokens_count_once(self):
        entities = {"S2-1": _make_entity("S2-1", name_alnum="abc abc", country="us")}
        idx = build_country_token_index(entities)
        assert idx[("us", "abc")] == {"S2-1"}
        assert len(idx[("us", "abc")]) == 1

    def test_empty_entities(self):
        assert build_country_token_index({}) == {}


# ---------------------------------------------------------------------------
# df filtering
# ---------------------------------------------------------------------------


class TestFilterIndexByDf:

    def _index(self):
        entities = {
            "S2-1": _make_entity("S2-1", name_alnum="common rare1", country="us"),
            "S2-2": _make_entity("S2-2", name_alnum="common rare2", country="us"),
            "S2-3": _make_entity("S2-3", name_alnum="common", country="us"),
        }
        return build_country_token_index(entities)

    def test_max_df_filters_common_token(self):
        idx = self._index()
        filtered = filter_index_by_df(idx, max_df=2)
        assert ("us", "common") not in filtered  # df=3
        assert ("us", "rare1") in filtered       # df=1
        assert ("us", "rare2") in filtered       # df=1

    def test_min_df_filters_rare_token(self):
        idx = self._index()
        filtered = filter_index_by_df(idx, min_df=2)
        assert ("us", "common") in filtered
        assert ("us", "rare1") not in filtered

    def test_no_filter_returns_all(self):
        idx = self._index()
        filtered = filter_index_by_df(idx)
        assert len(filtered) == len(idx)

    def test_postings_shared_not_copied(self):
        idx = self._index()
        filtered = filter_index_by_df(idx, max_df=2)
        assert filtered[("us", "rare1")] is idx[("us", "rare1")]


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


class TestRetrieveByTokenOverlap:

    def _index(self):
        entities = {
            # shares "acme" only
            "S2-1": _make_entity("S2-1", name_alnum="acme incorporated", country="us"),
            # shares "acme" and "inc"
            "S2-2": _make_entity("S2-2", name_alnum="acme inc", country="us"),
            # shares nothing
            "S2-3": _make_entity("S2-3", name_alnum="beta llc", country="us"),
            # same tokens but different country
            "S3-1": _make_entity("S3-1", name_alnum="acme inc", country="india"),
        }
        return build_country_token_index(entities)

    def test_min_overlap_1_unions_postings(self):
        s1 = _make_entity("S1-1", name_alnum="acme inc", country="us")
        result = retrieve_by_token_overlap(s1, self._index(), min_overlap=1)
        assert result == {"S2-1", "S2-2"}

    def test_min_overlap_2_requires_two_shared(self):
        s1 = _make_entity("S1-1", name_alnum="acme inc", country="us")
        result = retrieve_by_token_overlap(s1, self._index(), min_overlap=2)
        assert result == {"S2-2"}

    def test_restricted_to_same_country(self):
        s1 = _make_entity("S1-1", name_alnum="acme inc", country="us")
        result = retrieve_by_token_overlap(s1, self._index(), min_overlap=1)
        assert "S3-1" not in result

    def test_no_shared_tokens(self):
        s1 = _make_entity("S1-1", name_alnum="gamma delta", country="us")
        result = retrieve_by_token_overlap(s1, self._index(), min_overlap=1)
        assert result == set()

    def test_empty_s1_country(self):
        s1 = _make_entity("S1-1", name_alnum="acme inc", country="")
        result = retrieve_by_token_overlap(s1, self._index(), min_overlap=1)
        assert result == set()

    def test_empty_s1_name(self):
        s1 = _make_entity("S1-1", name_alnum="", country="us")
        result = retrieve_by_token_overlap(s1, self._index(), min_overlap=1)
        assert result == set()

    def test_df_filtered_token_not_retrievable(self):
        idx = build_country_token_index({
            "S2-1": _make_entity("S2-1", name_alnum="acme inc", country="us"),
            "S2-2": _make_entity("S2-2", name_alnum="acme inc", country="us"),
        })
        filtered = filter_index_by_df(idx, max_df=1)  # drops (us, acme) and (us, inc)
        s1 = _make_entity("S1-1", name_alnum="acme inc", country="us")
        assert retrieve_by_token_overlap(s1, filtered, min_overlap=1) == set()

    def test_min_overlap_higher_than_token_count(self):
        s1 = _make_entity("S1-1", name_alnum="acme", country="us")
        result = retrieve_by_token_overlap(s1, self._index(), min_overlap=2)
        assert result == set()

    def test_duplicate_s1_tokens_counted_once(self):
        # "acme acme" is one distinct token -> overlap with S2-1 is 1
        s1 = _make_entity("S1-1", name_alnum="acme acme", country="us")
        result = retrieve_by_token_overlap(s1, self._index(), min_overlap=2)
        assert result == set()

    def test_empty_index(self):
        s1 = _make_entity("S1-1", name_alnum="acme inc", country="us")
        assert retrieve_by_token_overlap(s1, {}, min_overlap=1) == set()
        assert retrieve_by_token_overlap(s1, {}, min_overlap=2) == set()


# ---------------------------------------------------------------------------
# df analysis helpers
# ---------------------------------------------------------------------------


class TestDfAnalysis:

    def test_top_tokens_by_df(self):
        entities = {
            "S2-1": _make_entity("S2-1", name_alnum="common rare", country="us"),
            "S2-2": _make_entity("S2-2", name_alnum="common", country="us"),
        }
        idx = build_country_token_index(entities)
        top = top_tokens_by_df(idx, top_n=1)
        assert len(top) == 1
        assert top[0]["token"] == "common"
        assert top[0]["country"] == "us"
        assert top[0]["df"] == 2

    def test_df_percentiles_empty_index(self):
        assert df_percentiles({}) == {"keys": 0}

    def test_df_percentiles_values(self):
        entities = {
            "S2-1": _make_entity("S2-1", name_alnum="a b", country="us"),
            "S2-2": _make_entity("S2-2", name_alnum="a", country="us"),
        }
        idx = build_country_token_index(entities)
        stats = df_percentiles(idx)
        assert stats["keys"] == 2
        assert stats["max"] == 2
        assert stats["total_postings"] == 3


# ---------------------------------------------------------------------------
# Integration with union + evaluation
# ---------------------------------------------------------------------------


class TestTokenBlockingIntegration:

    def test_union_with_exact_retriever(self):
        s1 = _make_entity("S1-1", name_alnum="acme inc", country="us")
        idx = build_country_token_index({
            "S2-1": _make_entity("S2-1", name_alnum="acme incorporated", country="us"),
            "S2-2": _make_entity("S2-2", name_alnum="zzz", country="us"),
        })
        result = candidate_union(s1, [
            lambda e: retrieve_by_token_overlap(e, idx, min_overlap=1),
            lambda e: {"S2-2"},
        ])
        assert result == {"S2-1", "S2-2"}

    def test_evaluate_token_retriever(self):
        entities = {
            "S2-1": _make_entity("S2-1", name_alnum="acme incorporated", country="us"),
            "S2-2": _make_entity("S2-2", name_alnum="beta llc", country="us"),
        }
        idx = build_country_token_index(entities)
        s1_entities = {"S1-1": _make_entity("S1-1", name_alnum="acme inc", country="us")}
        gt = {"S1-1": ["S2-1", "S2-2"]}
        result = evaluate_blocking(
            "token_test", s1_entities, gt,
            lambda e: retrieve_by_token_overlap(e, idx, min_overlap=1),
        )
        assert result.overall_recall == 0.5
        assert result.avg_candidates == 1.0
