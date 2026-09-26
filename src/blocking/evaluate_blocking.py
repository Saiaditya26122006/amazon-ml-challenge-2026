"""
Blocking evaluation: recall, candidate volume, and coverage metrics.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Callable

from blocking.base import Entity


@dataclass
class BlockingResult:
    route_name: str
    s1_evaluated: int = 0
    gt_s2_matches: int = 0
    gt_s3_matches: int = 0
    retrieved_s2: int = 0
    retrieved_s3: int = 0
    s2_recall: float = 0.0
    s3_recall: float = 0.0
    overall_recall: float = 0.0
    entity_full_coverage: float = 0.0
    avg_candidates: float = 0.0
    median_candidates: float = 0.0
    p95_candidates: float = 0.0
    max_candidates: int = 0
    runtime_s: float = 0.0
    peak_memory_mb: float = 0.0


def evaluate_blocking(
    route_name: str,
    s1_entities: dict[str, Entity],
    ground_truth: dict[str, list[str]],
    retriever: Callable[[Entity], set[str]],
) -> BlockingResult:
    """Evaluate a blocking strategy against ground truth.

    Parameters
    ----------
    route_name : str
        Label for this blocking route.
    s1_entities : dict
        S1 entity ID -> Entity (only evaluated S1 entities).
    ground_truth : dict
        S1 entity ID -> list of true matched S2/S3 IDs.
    retriever : callable
        Takes an Entity, returns a set of candidate IDs.

    Returns
    -------
    BlockingResult with all metrics filled in.
    """
    gt_s2_total = 0
    gt_s3_total = 0
    retrieved_s2_total = 0
    retrieved_s3_total = 0
    candidate_counts: list[int] = []

    entities_with_gt = 0
    entities_fully_covered = 0

    for s1_id, s1_ent in s1_entities.items():
        true_matches = ground_truth.get(s1_id, [])
        true_s2 = {m for m in true_matches if m.startswith("S2-")}
        true_s3 = {m for m in true_matches if m.startswith("S3-")}

        gt_s2_total += len(true_s2)
        gt_s3_total += len(true_s3)

        candidates = retriever(s1_ent)
        candidate_counts.append(len(candidates))

        hit_s2 = true_s2 & candidates
        hit_s3 = true_s3 & candidates
        retrieved_s2_total += len(hit_s2)
        retrieved_s3_total += len(hit_s3)

        if true_matches:
            entities_with_gt += 1
            if (true_s2 | true_s3) <= candidates:
                entities_fully_covered += 1

    total_gt = gt_s2_total + gt_s3_total
    total_retrieved = retrieved_s2_total + retrieved_s3_total

    result = BlockingResult(route_name=route_name)
    result.s1_evaluated = len(s1_entities)
    result.gt_s2_matches = gt_s2_total
    result.gt_s3_matches = gt_s3_total
    result.retrieved_s2 = retrieved_s2_total
    result.retrieved_s3 = retrieved_s3_total
    result.s2_recall = retrieved_s2_total / gt_s2_total if gt_s2_total > 0 else 0.0
    result.s3_recall = retrieved_s3_total / gt_s3_total if gt_s3_total > 0 else 0.0
    result.overall_recall = total_retrieved / total_gt if total_gt > 0 else 0.0
    result.entity_full_coverage = (
        entities_fully_covered / entities_with_gt if entities_with_gt > 0 else 0.0
    )

    if candidate_counts:
        result.avg_candidates = statistics.mean(candidate_counts)
        result.median_candidates = statistics.median(candidate_counts)
        sorted_counts = sorted(candidate_counts)
        p95_idx = min(int(len(sorted_counts) * 0.95), len(sorted_counts) - 1)
        result.p95_candidates = sorted_counts[p95_idx]
        result.max_candidates = max(candidate_counts)

    return result


def country_match_analysis(
    s1_entities: dict[str, Entity],
    other_entities: dict[str, Entity],
    ground_truth: dict[str, list[str]],
) -> dict:
    """Check whether any true matches have different countries."""
    total_pairs = 0
    same_country = 0
    diff_country = 0
    diff_examples: list[tuple[str, str, str, str]] = []

    for s1_id, s1_ent in s1_entities.items():
        for match_id in ground_truth.get(s1_id, []):
            if match_id not in other_entities:
                continue
            total_pairs += 1
            other_ent = other_entities[match_id]
            if s1_ent.country_cleaned == other_ent.country_cleaned:
                same_country += 1
            else:
                diff_country += 1
                if len(diff_examples) < 20:
                    diff_examples.append((
                        s1_id, match_id,
                        s1_ent.country_cleaned, other_ent.country_cleaned,
                    ))

    return {
        "total_pairs": total_pairs,
        "same_country": same_country,
        "diff_country": diff_country,
        "diff_examples": diff_examples,
    }


def common_name_analysis(
    s2_entities: dict[str, Entity],
    s3_entities: dict[str, Entity],
    top_n: int = 30,
) -> list[dict]:
    """Find the most frequent normalized names across S2 and S3."""
    from collections import Counter

    name_counts: Counter[tuple[str, str]] = Counter()
    name_examples: dict[tuple[str, str], str] = {}

    for source_label, entities in [("S2", s2_entities), ("S3", s3_entities)]:
        for eid, ent in entities.items():
            if not ent.name_cleaned:
                continue
            key = (ent.country_cleaned, ent.name_cleaned)
            name_counts[key] += 1
            if key not in name_examples:
                name_examples[key] = eid

    results = []
    for (country, name), count in name_counts.most_common(top_n):
        results.append({
            "country": country,
            "name_cleaned": name,
            "count": count,
            "example_id": name_examples.get((country, name), ""),
        })
    return results
