"""
Route contribution analysis for blocking unions.

Tracks which routes contribute which candidates and true pairs,
enabling marginal value analysis of each blocking route.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from blocking.base import Entity


@dataclass
class CandidateSet:
    """Candidate set with source tracking.

    Maps S1 entity ID -> set of candidate IDs, with metadata
    about which routes contributed which candidates.
    """

    s1_to_candidates: dict[str, set[str]] = field(default_factory=dict)
    route_name: str = ""

    def add_candidate(self, s1_id: str, candidate_id: str) -> None:
        """Add a single candidate for an S1 entity."""
        if s1_id not in self.s1_to_candidates:
            self.s1_to_candidates[s1_id] = set()
        self.s1_to_candidates[s1_id].add(candidate_id)

    def get_candidates(self, s1_id: str) -> set[str]:
        """Get all candidates for a given S1 entity."""
        return self.s1_to_candidates.get(s1_id, set())

    def get_s2_candidates(self, s1_id: str) -> set[str]:
        """Get only S2 candidates for a given S1 entity."""
        return {c for c in self.get_candidates(s1_id) if c.startswith("S2-")}

    def get_s3_candidates(self, s1_id: str) -> set[str]:
        """Get only S3 candidates for a given S1 entity."""
        return {c for c in self.get_candidates(s1_id) if c.startswith("S3-")}

    def total_candidate_pairs(self) -> int:
        """Total number of (S1, candidate) pairs."""
        return sum(len(cands) for cands in self.s1_to_candidates.values())

    def union_with(self, other: CandidateSet) -> CandidateSet:
        """Return a new CandidateSet that is the union of self and other."""
        result = CandidateSet(route_name=f"{self.route_name}+{other.route_name}")
        for s1_id in set(self.s1_to_candidates.keys()) | set(other.s1_to_candidates.keys()):
            result.s1_to_candidates[s1_id] = (
                self.get_candidates(s1_id) | other.get_candidates(s1_id)
            )
        return result


def build_candidate_set(
    route_name: str,
    s1_entities: dict[str, Entity],
    retriever: Callable[[Entity], set[str]],
) -> CandidateSet:
    """Build a CandidateSet by running a retriever on all S1 entities.

    Parameters
    ----------
    route_name : str
        Label for this blocking route.
    s1_entities : dict
        S1 entity ID -> Entity.
    retriever : callable
        Takes an Entity, returns a set of candidate IDs.

    Returns
    -------
    CandidateSet with all candidates populated.
    """
    cset = CandidateSet(route_name=route_name)
    for s1_id, s1_ent in s1_entities.items():
        candidates = retriever(s1_ent)
        if candidates:
            cset.s1_to_candidates[s1_id] = candidates
    return cset


def compute_true_pair_sets(
    candidate_sets: list[CandidateSet],
    ground_truth: dict[str, list[str]],
) -> dict[str, set[tuple[str, str]]]:
    """For each route, compute the set of true pairs it retrieves.

    Returns
    -------
    dict[route_name, set[(s1_id, match_id)]]
    """
    result = {}
    for cset in candidate_sets:
        true_pairs: set[tuple[str, str]] = set()
        for s1_id, true_matches in ground_truth.items():
            candidates = cset.get_candidates(s1_id)
            for match_id in true_matches:
                if match_id in candidates:
                    true_pairs.add((s1_id, match_id))
        result[cset.route_name] = true_pairs
    return result


@dataclass
class RouteContribution:
    """Contribution analysis for a single route within a union."""

    route_name: str

    # True pairs retrieved by this route only
    unique_true_pairs: int = 0

    # True pairs retrieved by this route and at least one other
    shared_true_pairs: int = 0

    # Total true pairs retrieved by this route
    total_true_pairs: int = 0

    # Recall contribution (what fraction of total GT this route retrieves)
    recall: float = 0.0

    # Marginal contribution (how many new true pairs this route adds vs. all previous)
    marginal_true_pairs: int = 0
    marginal_recall: float = 0.0


@dataclass
class UnionContribution:
    """Contribution analysis for a union of routes."""

    route_names: list[str] = field(default_factory=list)

    # Overall union metrics
    total_gt_pairs: int = 0
    total_retrieved: int = 0
    overall_recall: float = 0.0

    # Per-route contributions
    contributions: list[RouteContribution] = field(default_factory=list)

    # Overlap matrix: how many true pairs are shared between routes
    # overlap[(route_a, route_b)] = count of shared true pairs
    overlap: dict[tuple[str, str], int] = field(default_factory=dict)


def analyze_union_contribution(
    candidate_sets: list[CandidateSet],
    ground_truth: dict[str, list[str]],
) -> UnionContribution:
    """Analyze the contribution of each route in a union.

    For each route, compute:
    - How many true pairs it retrieves uniquely (no other route gets them)
    - How many true pairs it shares with other routes
    - Marginal value: how many new true pairs it adds vs. all previous routes

    Parameters
    ----------
    candidate_sets : list[CandidateSet]
        One CandidateSet per route.
    ground_truth : dict
        S1 entity ID -> list of true matched S2/S3 IDs.

    Returns
    -------
    UnionContribution with all metrics filled.
    """
    if not candidate_sets:
        return UnionContribution()

    # Compute true pair sets for each route
    route_true_pairs = compute_true_pair_sets(candidate_sets, ground_truth)

    # Count total GT pairs
    total_gt = sum(len(matches) for matches in ground_truth.values())

    # Union of all retrieved true pairs
    all_retrieved = set()
    for pairs in route_true_pairs.values():
        all_retrieved |= pairs

    result = UnionContribution(
        route_names=[cs.route_name for cs in candidate_sets],
        total_gt_pairs=total_gt,
        total_retrieved=len(all_retrieved),
        overall_recall=len(all_retrieved) / total_gt if total_gt > 0 else 0.0,
    )

    # Compute per-route contributions
    cumulative_pairs: set[tuple[str, str]] = set()

    for cset in candidate_sets:
        route_name = cset.route_name
        route_pairs = route_true_pairs[route_name]

        # Unique pairs: retrieved by this route only
        unique_pairs = route_pairs.copy()
        for other_name, other_pairs in route_true_pairs.items():
            if other_name != route_name:
                unique_pairs -= other_pairs

        # Shared pairs: retrieved by this route and at least one other
        shared_pairs = route_pairs - unique_pairs

        # Marginal contribution: new pairs vs. all previous routes
        marginal_pairs = route_pairs - cumulative_pairs
        cumulative_pairs |= route_pairs

        contrib = RouteContribution(
            route_name=route_name,
            unique_true_pairs=len(unique_pairs),
            shared_true_pairs=len(shared_pairs),
            total_true_pairs=len(route_pairs),
            recall=len(route_pairs) / total_gt if total_gt > 0 else 0.0,
            marginal_true_pairs=len(marginal_pairs),
            marginal_recall=len(marginal_pairs) / total_gt if total_gt > 0 else 0.0,
        )
        result.contributions.append(contrib)

    # Compute overlap matrix
    route_names = [cs.route_name for cs in candidate_sets]
    for i, name_a in enumerate(route_names):
        for j, name_b in enumerate(route_names):
            if i < j:
                shared = route_true_pairs[name_a] & route_true_pairs[name_b]
                result.overlap[(name_a, name_b)] = len(shared)

    return result


def print_union_contribution(contrib: UnionContribution) -> None:
    """Print a formatted contribution analysis report."""
    print(f"\n=== Union Contribution Analysis ===")
    print(f"Routes: {' + '.join(contrib.route_names)}")
    print(f"Total GT pairs: {contrib.total_gt_pairs:,}")
    print(f"Union retrieved: {contrib.total_retrieved:,}")
    print(f"Union recall: {contrib.overall_recall:.4f}\n")

    print("Per-route contributions:")
    print(f"{'Route':<30} {'Recall':>8} {'Unique':>8} {'Shared':>8} {'Marginal':>8} {'Marg %':>8}")
    print("-" * 90)

    for c in contrib.contributions:
        print(
            f"{c.route_name:<30} "
            f"{c.recall:>8.4f} "
            f"{c.unique_true_pairs:>8,} "
            f"{c.shared_true_pairs:>8,} "
            f"{c.marginal_true_pairs:>8,} "
            f"{c.marginal_recall:>8.4f}"
        )

    if contrib.overlap:
        print("\nPairwise overlap (shared true pairs):")
        for (route_a, route_b), count in sorted(contrib.overlap.items()):
            print(f"  {route_a} ∩ {route_b}: {count:,}")
