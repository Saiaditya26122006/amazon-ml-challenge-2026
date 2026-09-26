"""
Unit tests for src/blocking/route_contribution.py

Run from the project root:
    python -m pytest tests/test_route_contribution.py -v
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from blocking.base import Entity
from blocking.route_contribution import (
    CandidateSet,
    build_candidate_set,
    compute_true_pair_sets,
    analyze_union_contribution,
    RouteContribution,
    UnionContribution,
)


def _make_entity(eid, name_cleaned="", name_alnum="", country="", addr="", addr_alnum=""):
    return Entity(
        entity_id=eid,
        name_cleaned=name_cleaned,
        name_alphanumeric=name_alnum,
        country_cleaned=country,
        addr_cleaned=addr,
        addr_alphanumeric=addr_alnum,
    )


class TestCandidateSet:

    def test_empty_candidate_set(self):
        cs = CandidateSet(route_name="test")
        assert cs.get_candidates("S1-1") == set()
        assert cs.total_candidate_pairs() == 0

    def test_add_candidates(self):
        cs = CandidateSet(route_name="test")
        cs.add_candidate("S1-1", "S2-1")
        cs.add_candidate("S1-1", "S2-2")
        cs.add_candidate("S1-2", "S3-1")
        assert cs.get_candidates("S1-1") == {"S2-1", "S2-2"}
        assert cs.get_candidates("S1-2") == {"S3-1"}
        assert cs.total_candidate_pairs() == 3

    def test_s2_s3_separation(self):
        cs = CandidateSet(route_name="test")
        cs.add_candidate("S1-1", "S2-1")
        cs.add_candidate("S1-1", "S2-2")
        cs.add_candidate("S1-1", "S3-1")
        assert cs.get_s2_candidates("S1-1") == {"S2-1", "S2-2"}
        assert cs.get_s3_candidates("S1-1") == {"S3-1"}

    def test_union_of_candidate_sets(self):
        cs1 = CandidateSet(route_name="route_a")
        cs1.add_candidate("S1-1", "S2-1")
        cs1.add_candidate("S1-1", "S2-2")

        cs2 = CandidateSet(route_name="route_b")
        cs2.add_candidate("S1-1", "S2-2")
        cs2.add_candidate("S1-1", "S3-1")
        cs2.add_candidate("S1-2", "S2-3")

        union = cs1.union_with(cs2)
        assert union.get_candidates("S1-1") == {"S2-1", "S2-2", "S3-1"}
        assert union.get_candidates("S1-2") == {"S2-3"}
        assert union.route_name == "route_a+route_b"

    def test_union_empty_sets(self):
        cs1 = CandidateSet(route_name="route_a")
        cs2 = CandidateSet(route_name="route_b")
        union = cs1.union_with(cs2)
        assert union.total_candidate_pairs() == 0


class TestBuildCandidateSet:

    def test_build_from_retriever(self):
        s1_entities = {
            "S1-1": _make_entity("S1-1", country="us"),
            "S1-2": _make_entity("S1-2", country="india"),
        }
        retriever = lambda ent: {"S2-1", "S2-2"} if ent.country_cleaned == "us" else {"S3-1"}
        cs = build_candidate_set("test_route", s1_entities, retriever)

        assert cs.route_name == "test_route"
        assert cs.get_candidates("S1-1") == {"S2-1", "S2-2"}
        assert cs.get_candidates("S1-2") == {"S3-1"}

    def test_build_empty_results(self):
        s1_entities = {"S1-1": _make_entity("S1-1", country="us")}
        retriever = lambda ent: set()
        cs = build_candidate_set("empty", s1_entities, retriever)
        assert cs.total_candidate_pairs() == 0


class TestTruePairSets:

    def test_compute_true_pairs_single_route(self):
        cs = CandidateSet(route_name="route_a")
        cs.add_candidate("S1-1", "S2-1")
        cs.add_candidate("S1-1", "S2-2")
        cs.add_candidate("S1-2", "S3-1")

        gt = {
            "S1-1": ["S2-1", "S2-99"],
            "S1-2": ["S3-1"],
        }

        result = compute_true_pair_sets([cs], gt)
        expected = {("S1-1", "S2-1"), ("S1-2", "S3-1")}
        assert result["route_a"] == expected

    def test_compute_true_pairs_multiple_routes(self):
        cs1 = CandidateSet(route_name="route_a")
        cs1.add_candidate("S1-1", "S2-1")

        cs2 = CandidateSet(route_name="route_b")
        cs2.add_candidate("S1-1", "S2-1")
        cs2.add_candidate("S1-1", "S2-2")

        gt = {"S1-1": ["S2-1", "S2-2"]}

        result = compute_true_pair_sets([cs1, cs2], gt)
        assert result["route_a"] == {("S1-1", "S2-1")}
        assert result["route_b"] == {("S1-1", "S2-1"), ("S1-1", "S2-2")}

    def test_no_ground_truth(self):
        cs = CandidateSet(route_name="route_a")
        cs.add_candidate("S1-1", "S2-1")
        result = compute_true_pair_sets([cs], {})
        assert result["route_a"] == set()


class TestUnionContribution:

    def test_single_route_contribution(self):
        cs = CandidateSet(route_name="route_a")
        cs.add_candidate("S1-1", "S2-1")
        cs.add_candidate("S1-1", "S2-2")
        cs.add_candidate("S1-2", "S3-1")

        gt = {
            "S1-1": ["S2-1", "S2-2"],
            "S1-2": ["S3-1"],
        }

        contrib = analyze_union_contribution([cs], gt)

        assert contrib.total_gt_pairs == 3
        assert contrib.total_retrieved == 3
        assert contrib.overall_recall == 1.0

        assert len(contrib.contributions) == 1
        c = contrib.contributions[0]
        assert c.route_name == "route_a"
        assert c.total_true_pairs == 3
        assert c.unique_true_pairs == 3
        assert c.shared_true_pairs == 0
        assert c.marginal_true_pairs == 3
        assert c.recall == 1.0
        assert c.marginal_recall == 1.0

    def test_two_routes_overlapping(self):
        cs1 = CandidateSet(route_name="route_a")
        cs1.add_candidate("S1-1", "S2-1")
        cs1.add_candidate("S1-1", "S2-2")

        cs2 = CandidateSet(route_name="route_b")
        cs2.add_candidate("S1-1", "S2-2")
        cs2.add_candidate("S1-1", "S2-3")

        gt = {"S1-1": ["S2-1", "S2-2", "S2-3"]}

        contrib = analyze_union_contribution([cs1, cs2], gt)

        assert contrib.total_gt_pairs == 3
        assert contrib.total_retrieved == 3
        assert contrib.overall_recall == 1.0

        c1, c2 = contrib.contributions

        # Route A: retrieves S2-1 (unique) and S2-2 (shared)
        assert c1.route_name == "route_a"
        assert c1.total_true_pairs == 2
        assert c1.unique_true_pairs == 1  # S2-1
        assert c1.shared_true_pairs == 1  # S2-2
        assert c1.marginal_true_pairs == 2  # First route gets full credit
        assert c1.recall == 2 / 3

        # Route B: retrieves S2-2 (shared) and S2-3 (unique)
        assert c2.route_name == "route_b"
        assert c2.total_true_pairs == 2
        assert c2.unique_true_pairs == 1  # S2-3
        assert c2.shared_true_pairs == 1  # S2-2
        assert c2.marginal_true_pairs == 1  # Only S2-3 is new
        assert c2.recall == 2 / 3
        assert c2.marginal_recall == 1 / 3

        # Overlap
        assert contrib.overlap[("route_a", "route_b")] == 1  # S2-2

    def test_three_routes_cumulative(self):
        cs1 = CandidateSet(route_name="exact_name")
        cs1.add_candidate("S1-1", "S2-1")

        cs2 = CandidateSet(route_name="token_overlap")
        cs2.add_candidate("S1-1", "S2-1")
        cs2.add_candidate("S1-1", "S2-2")

        cs3 = CandidateSet(route_name="address_token")
        cs3.add_candidate("S1-1", "S2-3")

        gt = {"S1-1": ["S2-1", "S2-2", "S2-3", "S2-4"]}

        contrib = analyze_union_contribution([cs1, cs2, cs3], gt)

        assert contrib.total_gt_pairs == 4
        assert contrib.total_retrieved == 3
        assert contrib.overall_recall == 0.75

        c1, c2, c3 = contrib.contributions

        # Route 1: exact_name retrieves S2-1
        assert c1.route_name == "exact_name"
        assert c1.total_true_pairs == 1
        assert c1.marginal_true_pairs == 1
        assert c1.marginal_recall == 0.25

        # Route 2: token_overlap retrieves S2-1 (already in) + S2-2 (new)
        assert c2.route_name == "token_overlap"
        assert c2.total_true_pairs == 2
        assert c2.marginal_true_pairs == 1  # Only S2-2 is new
        assert c2.marginal_recall == 0.25

        # Route 3: address_token retrieves S2-3 (new)
        assert c3.route_name == "address_token"
        assert c3.total_true_pairs == 1
        assert c3.marginal_true_pairs == 1
        assert c3.marginal_recall == 0.25

    def test_routes_fully_overlapping(self):
        cs1 = CandidateSet(route_name="route_a")
        cs1.add_candidate("S1-1", "S2-1")

        cs2 = CandidateSet(route_name="route_b")
        cs2.add_candidate("S1-1", "S2-1")

        gt = {"S1-1": ["S2-1"]}

        contrib = analyze_union_contribution([cs1, cs2], gt)

        c1, c2 = contrib.contributions

        # Both retrieve the same pair
        assert c1.unique_true_pairs == 0
        assert c1.shared_true_pairs == 1
        assert c1.marginal_true_pairs == 1

        assert c2.unique_true_pairs == 0
        assert c2.shared_true_pairs == 1
        assert c2.marginal_true_pairs == 0  # No new contribution

    def test_routes_disjoint(self):
        cs1 = CandidateSet(route_name="route_a")
        cs1.add_candidate("S1-1", "S2-1")

        cs2 = CandidateSet(route_name="route_b")
        cs2.add_candidate("S1-2", "S2-2")

        gt = {
            "S1-1": ["S2-1"],
            "S1-2": ["S2-2"],
        }

        contrib = analyze_union_contribution([cs1, cs2], gt)

        c1, c2 = contrib.contributions

        # No overlap
        assert c1.unique_true_pairs == 1
        assert c1.shared_true_pairs == 0
        assert c2.unique_true_pairs == 1
        assert c2.shared_true_pairs == 0
        assert len(contrib.overlap) == 1
        assert contrib.overlap[("route_a", "route_b")] == 0

    def test_empty_candidate_sets(self):
        cs1 = CandidateSet(route_name="route_a")
        gt = {"S1-1": ["S2-1"]}
        contrib = analyze_union_contribution([cs1], gt)

        assert contrib.total_gt_pairs == 1
        assert contrib.total_retrieved == 0
        assert contrib.overall_recall == 0.0

    def test_empty_ground_truth(self):
        cs1 = CandidateSet(route_name="route_a")
        cs1.add_candidate("S1-1", "S2-1")
        contrib = analyze_union_contribution([cs1], {})

        assert contrib.total_gt_pairs == 0
        assert contrib.total_retrieved == 0
        assert contrib.overall_recall == 0.0


class TestIntegration:

    def test_end_to_end_workflow(self):
        """Test complete workflow: build candidate sets, analyze union."""

        s1_entities = {
            "S1-1": _make_entity("S1-1", name_cleaned="acme inc", country="us"),
            "S1-2": _make_entity("S1-2", name_cleaned="beta corp", country="india"),
        }

        # Route A: exact name blocking
        def exact_name_retriever(ent):
            if ent.name_cleaned == "acme inc":
                return {"S2-1", "S2-2"}
            elif ent.name_cleaned == "beta corp":
                return {"S3-1"}
            return set()

        # Route B: fuzzy name blocking
        def fuzzy_retriever(ent):
            if ent.name_cleaned == "acme inc":
                return {"S2-1", "S2-3"}
            elif ent.name_cleaned == "beta corp":
                return {"S3-1", "S3-2"}
            return set()

        cs1 = build_candidate_set("exact_name", s1_entities, exact_name_retriever)
        cs2 = build_candidate_set("fuzzy_name", s1_entities, fuzzy_retriever)

        gt = {
            "S1-1": ["S2-1", "S2-2", "S2-3"],
            "S1-2": ["S3-1", "S3-2"],
        }

        contrib = analyze_union_contribution([cs1, cs2], gt)

        assert contrib.total_gt_pairs == 5
        assert contrib.total_retrieved == 5
        assert contrib.overall_recall == 1.0

        c1, c2 = contrib.contributions

        # Exact name: S2-1, S2-2, S3-1
        assert c1.total_true_pairs == 3

        # Fuzzy name: S2-1, S2-3, S3-1, S3-2
        assert c2.total_true_pairs == 4

        # Marginal contribution: fuzzy adds S2-3 and S3-2
        assert c2.marginal_true_pairs == 2
