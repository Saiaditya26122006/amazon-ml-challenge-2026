"""
Unit tests for src/blocking/

Run from the project root:
    python -m pytest tests/test_blocking.py -v
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from blocking.base import Entity
from blocking.exact_blocking import (
    build_country_index,
    build_country_name_cleaned_index,
    build_country_name_alphanumeric_index,
    retrieve_by_country,
    retrieve_by_country_name_cleaned,
    retrieve_by_country_name_alphanumeric,
)
from blocking.candidate_union import candidate_union
from blocking.evaluate_blocking import evaluate_blocking, BlockingResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entity(eid, name_cleaned="", name_alnum="", country="", addr="", addr_alnum=""):
    return Entity(
        entity_id=eid,
        name_cleaned=name_cleaned,
        name_alphanumeric=name_alnum,
        country_cleaned=country,
        addr_cleaned=addr,
        addr_alphanumeric=addr_alnum,
    )


# ---------------------------------------------------------------------------
# Country blocking
# ---------------------------------------------------------------------------


class TestCountryBlocking:

    def test_basic_country_blocking(self):
        entities = {
            "S2-1": _make_entity("S2-1", country="us"),
            "S2-2": _make_entity("S2-2", country="india"),
            "S2-3": _make_entity("S2-3", country="us"),
        }
        idx = build_country_index(entities)
        s1 = _make_entity("S1-1", country="us")
        result = retrieve_by_country(s1, idx)
        assert result == {"S2-1", "S2-3"}

    def test_country_blocking_no_match(self):
        entities = {
            "S2-1": _make_entity("S2-1", country="us"),
        }
        idx = build_country_index(entities)
        s1 = _make_entity("S1-1", country="france")
        result = retrieve_by_country(s1, idx)
        assert result == set()

    def test_country_blocking_empty_country(self):
        entities = {
            "S2-1": _make_entity("S2-1", country=""),
        }
        idx = build_country_index(entities)
        s1 = _make_entity("S1-1", country="us")
        result = retrieve_by_country(s1, idx)
        assert result == set()

    def test_country_blocking_s1_empty(self):
        entities = {
            "S2-1": _make_entity("S2-1", country="us"),
        }
        idx = build_country_index(entities)
        s1 = _make_entity("S1-1", country="")
        result = retrieve_by_country(s1, idx)
        assert result == set()


# ---------------------------------------------------------------------------
# Exact name blocking
# ---------------------------------------------------------------------------


class TestExactNameBlocking:

    def test_country_name_cleaned(self):
        entities = {
            "S2-1": _make_entity("S2-1", name_cleaned="acme inc", country="us"),
            "S2-2": _make_entity("S2-2", name_cleaned="acme inc", country="india"),
            "S2-3": _make_entity("S2-3", name_cleaned="acme inc", country="us"),
            "S3-1": _make_entity("S3-1", name_cleaned="beta llc", country="us"),
        }
        idx = build_country_name_cleaned_index(entities)
        s1 = _make_entity("S1-1", name_cleaned="acme inc", country="us")
        result = retrieve_by_country_name_cleaned(s1, idx)
        assert result == {"S2-1", "S2-3"}

    def test_country_name_alphanumeric(self):
        entities = {
            "S2-1": _make_entity("S2-1", name_alnum="acme inc", country="us"),
            "S2-2": _make_entity("S2-2", name_alnum="acme inc", country="us"),
            "S3-1": _make_entity("S3-1", name_alnum="acme incorporated", country="us"),
        }
        idx = build_country_name_alphanumeric_index(entities)
        s1 = _make_entity("S1-1", name_alnum="acme inc", country="us")
        result = retrieve_by_country_name_alphanumeric(s1, idx)
        assert result == {"S2-1", "S2-2"}

    def test_empty_name_not_indexed(self):
        entities = {
            "S2-1": _make_entity("S2-1", name_cleaned="", country="us"),
        }
        idx = build_country_name_cleaned_index(entities)
        assert len(idx) == 0

    def test_empty_name_no_retrieval(self):
        entities = {
            "S2-1": _make_entity("S2-1", name_cleaned="acme", country="us"),
        }
        idx = build_country_name_cleaned_index(entities)
        s1 = _make_entity("S1-1", name_cleaned="", country="us")
        result = retrieve_by_country_name_cleaned(s1, idx)
        assert result == set()

    def test_duplicate_names_multiple_candidates(self):
        entities = {
            "S2-1": _make_entity("S2-1", name_cleaned="national bank", country="india"),
            "S2-2": _make_entity("S2-2", name_cleaned="national bank", country="india"),
            "S3-1": _make_entity("S3-1", name_cleaned="national bank", country="india"),
            "S3-2": _make_entity("S3-2", name_cleaned="national bank", country="india"),
            "S3-3": _make_entity("S3-3", name_cleaned="national bank", country="india"),
        }
        idx = build_country_name_cleaned_index(entities)
        s1 = _make_entity("S1-1", name_cleaned="national bank", country="india")
        result = retrieve_by_country_name_cleaned(s1, idx)
        assert len(result) == 5

    def test_s2_s3_separation(self):
        entities = {
            "S2-10": _make_entity("S2-10", name_cleaned="xyz", country="us"),
            "S3-20": _make_entity("S3-20", name_cleaned="xyz", country="us"),
        }
        idx = build_country_name_cleaned_index(entities)
        s1 = _make_entity("S1-1", name_cleaned="xyz", country="us")
        result = retrieve_by_country_name_cleaned(s1, idx)
        s2_cands = {c for c in result if c.startswith("S2-")}
        s3_cands = {c for c in result if c.startswith("S3-")}
        assert s2_cands == {"S2-10"}
        assert s3_cands == {"S3-20"}


# ---------------------------------------------------------------------------
# Candidate union
# ---------------------------------------------------------------------------


class TestCandidateUnion:

    def test_union_of_two(self):
        s1 = _make_entity("S1-1", name_cleaned="acme", name_alnum="acme", country="us")
        r1 = lambda ent: {"S2-1", "S2-2"}
        r2 = lambda ent: {"S2-2", "S3-1"}
        result = candidate_union(s1, [r1, r2])
        assert result == {"S2-1", "S2-2", "S3-1"}

    def test_union_no_duplicates(self):
        s1 = _make_entity("S1-1", country="us")
        r1 = lambda ent: {"S2-1"}
        r2 = lambda ent: {"S2-1"}
        result = candidate_union(s1, [r1, r2])
        assert result == {"S2-1"}
        assert len(result) == 1

    def test_union_empty(self):
        s1 = _make_entity("S1-1", country="us")
        r1 = lambda ent: set()
        r2 = lambda ent: set()
        result = candidate_union(s1, [r1, r2])
        assert result == set()

    def test_union_single_retriever(self):
        s1 = _make_entity("S1-1", country="us")
        r1 = lambda ent: {"S2-1", "S3-1"}
        result = candidate_union(s1, [r1])
        assert result == {"S2-1", "S3-1"}


# ---------------------------------------------------------------------------
# Recall evaluation
# ---------------------------------------------------------------------------


class TestEvaluateBlocking:

    def test_perfect_recall(self):
        s1_entities = {
            "S1-1": _make_entity("S1-1", country="us"),
        }
        gt = {"S1-1": ["S2-1", "S3-1"]}
        retriever = lambda ent: {"S2-1", "S3-1", "S2-99"}
        result = evaluate_blocking("test", s1_entities, gt, retriever)
        assert result.overall_recall == 1.0
        assert result.s2_recall == 1.0
        assert result.s3_recall == 1.0
        assert result.entity_full_coverage == 1.0

    def test_partial_recall(self):
        s1_entities = {
            "S1-1": _make_entity("S1-1", country="us"),
        }
        gt = {"S1-1": ["S2-1", "S2-2", "S3-1"]}
        retriever = lambda ent: {"S2-1"}
        result = evaluate_blocking("test", s1_entities, gt, retriever)
        assert result.overall_recall == 1 / 3
        assert result.s2_recall == 0.5
        assert result.s3_recall == 0.0
        assert result.entity_full_coverage == 0.0

    def test_zero_recall(self):
        s1_entities = {
            "S1-1": _make_entity("S1-1", country="us"),
        }
        gt = {"S1-1": ["S2-1"]}
        retriever = lambda ent: {"S3-99"}
        result = evaluate_blocking("test", s1_entities, gt, retriever)
        assert result.overall_recall == 0.0

    def test_zero_match_entity(self):
        s1_entities = {
            "S1-1": _make_entity("S1-1", country="us"),
            "S1-2": _make_entity("S1-2", country="us"),
        }
        gt = {"S1-1": ["S2-1"]}
        retriever = lambda ent: {"S2-1"} if ent.entity_id == "S1-1" else set()
        result = evaluate_blocking("test", s1_entities, gt, retriever)
        assert result.overall_recall == 1.0
        assert result.s1_evaluated == 2

    def test_multiple_s1_entities(self):
        s1_entities = {
            "S1-1": _make_entity("S1-1", country="us"),
            "S1-2": _make_entity("S1-2", country="us"),
        }
        gt = {
            "S1-1": ["S2-1", "S3-1"],
            "S1-2": ["S2-2"],
        }
        retriever = lambda ent: {"S2-1", "S3-1"} if ent.entity_id == "S1-1" else {"S2-2"}
        result = evaluate_blocking("test", s1_entities, gt, retriever)
        assert result.overall_recall == 1.0
        assert result.gt_s2_matches == 2
        assert result.gt_s3_matches == 1
        assert result.retrieved_s2 == 2
        assert result.retrieved_s3 == 1

    def test_candidate_volume_stats(self):
        s1_entities = {
            "S1-1": _make_entity("S1-1", country="us"),
            "S1-2": _make_entity("S1-2", country="us"),
            "S1-3": _make_entity("S1-3", country="us"),
        }
        gt = {}
        counts = {"S1-1": 10, "S1-2": 20, "S1-3": 30}
        retriever = lambda ent: set(f"S2-{i}" for i in range(counts[ent.entity_id]))
        result = evaluate_blocking("test", s1_entities, gt, retriever)
        assert result.avg_candidates == 20.0
        assert result.median_candidates == 20.0
        assert result.max_candidates == 30

    def test_deterministic_output(self):
        s1_entities = {
            "S1-1": _make_entity("S1-1", name_cleaned="abc", country="us"),
        }
        gt = {"S1-1": ["S2-1"]}
        retriever = lambda ent: {"S2-1", "S2-2"}
        r1 = evaluate_blocking("test", s1_entities, gt, retriever)
        r2 = evaluate_blocking("test", s1_entities, gt, retriever)
        assert r1.overall_recall == r2.overall_recall
        assert r1.avg_candidates == r2.avg_candidates
