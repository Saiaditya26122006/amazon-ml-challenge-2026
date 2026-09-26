"""
Evaluate unions of blocking routes and analyze route contributions.

This script demonstrates how to:
1. Build candidate sets from different blocking routes
2. Evaluate unions of routes
3. Analyze marginal contribution of each route

Usage:
    python experiments/blocking/evaluate_route_unions.py
"""

from __future__ import annotations

import io
import os
import sys
from functools import partial

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from blocking.base import load_ground_truth, DATA_DIR
from blocking.exact_blocking import (
    build_country_name_cleaned_index,
    build_country_name_alphanumeric_index,
    retrieve_by_country_name_cleaned,
    retrieve_by_country_name_alphanumeric,
)
from blocking.evaluate_blocking import evaluate_blocking
from blocking.route_contribution import (
    build_candidate_set,
    analyze_union_contribution,
    print_union_contribution,
)
from preprocessing.normalize import normalize_name, normalize_country


def load_blocking_keys_needed(filepath: str, needed_ids: set[str]) -> dict:
    """Load only specific IDs, normalizing only name + country."""
    from blocking.base import Entity, DELIMITER

    entities = {}
    remaining = set(needed_ids)
    with open(filepath, encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split(DELIMITER)
            if len(parts) < 4:
                continue
            eid = parts[0]
            if eid not in remaining:
                continue
            remaining.discard(eid)
            raw_name, raw_country = parts[1], parts[3]
            nn = normalize_name(raw_name)
            nc = normalize_country(raw_country)
            entities[eid] = type(
                "Entity",
                (),
                {
                    "entity_id": eid,
                    "name_cleaned": nn.cleaned,
                    "name_alphanumeric": nn.alphanumeric,
                    "country_cleaned": nc.cleaned,
                    "addr_cleaned": "",
                    "addr_alphanumeric": "",
                },
            )()
            if not remaining:
                break
    return entities


def load_blocking_keys_only(filepath: str) -> dict:
    """Load entities normalizing only name + country (skip address)."""
    from blocking.base import Entity, DELIMITER

    entities = {}
    with open(filepath, encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split(DELIMITER)
            if len(parts) < 4:
                continue
            eid, raw_name, raw_country = parts[0], parts[1], parts[3]
            nn = normalize_name(raw_name)
            nc = normalize_country(raw_country)
            entities[eid] = type(
                "Entity",
                (),
                {
                    "entity_id": eid,
                    "name_cleaned": nn.cleaned,
                    "name_alphanumeric": nn.alphanumeric,
                    "country_cleaned": nc.cleaned,
                    "addr_cleaned": "",
                    "addr_alphanumeric": "",
                },
            )()
    return entities


def main():
    print("=== Route Union Evaluation Demo ===\n")

    # Config
    SAMPLE_S1 = 10_000  # Small sample for demo
    TRAIN_DIR = os.path.join(DATA_DIR, "train")
    S1_FILE = os.path.join(TRAIN_DIR, "train_source1.tsv")
    S2_FILE = os.path.join(TRAIN_DIR, "train_source2.tsv")
    S3_FILE = os.path.join(TRAIN_DIR, "train_source3.tsv")
    GT_FILE = os.path.join(TRAIN_DIR, "train_ground_truth.tsv")

    # Load ground truth
    print(f"Loading ground truth (first {SAMPLE_S1:,} S1 entities)...")
    gt = load_ground_truth(GT_FILE, limit=SAMPLE_S1)
    print(f"  {len(gt):,} S1 entries with matches\n")

    s1_ids_needed = set(gt.keys())

    # Load S1 entities
    print("Loading S1 entities...")
    s1_entities = load_blocking_keys_needed(S1_FILE, s1_ids_needed)
    print(f"  {len(s1_entities):,} loaded\n")

    # Load S2 and S3 (full datasets for indices)
    print("Loading S2 entities...")
    s2_entities = load_blocking_keys_only(S2_FILE)
    print(f"  {len(s2_entities):,} loaded\n")

    print("Loading S3 entities...")
    s3_entities = load_blocking_keys_only(S3_FILE)
    print(f"  {len(s3_entities):,} loaded\n")

    all_s2s3 = {**s2_entities, **s3_entities}

    # Build indices for exact-match routes
    print("Building blocking indices...")
    name_cleaned_idx = build_country_name_cleaned_index(all_s2s3)
    name_alnum_idx = build_country_name_alphanumeric_index(all_s2s3)
    print("  Indices ready\n")

    # =========================================================================
    # Build candidate sets for each route
    # =========================================================================
    print("--- Building Candidate Sets ---\n")

    # Route A: Country + exact name_cleaned
    print("Route A: country + exact name_cleaned")
    route_a_retriever = lambda ent: retrieve_by_country_name_cleaned(
        ent, name_cleaned_idx
    )
    candidate_set_a = build_candidate_set("exact_name", s1_entities, route_a_retriever)
    print(
        f"  Candidate pairs: {candidate_set_a.total_candidate_pairs():,}\n"
    )

    # Route B: Country + exact name_alphanumeric
    print("Route B: country + exact name_alphanumeric")
    route_b_retriever = lambda ent: retrieve_by_country_name_alphanumeric(
        ent, name_alnum_idx
    )
    candidate_set_b = build_candidate_set(
        "alphanumeric_name", s1_entities, route_b_retriever
    )
    print(
        f"  Candidate pairs: {candidate_set_b.total_candidate_pairs():,}\n"
    )

    # Future routes would be added here like:
    # Route C: Token overlap (to be implemented by Freebuff)
    # Route D: Address token (Friend 2's experiments)
    # Route E: Numeric blocking
    # etc.

    # =========================================================================
    # Evaluate individual routes
    # =========================================================================
    print("\n--- Individual Route Performance ---\n")

    result_a = evaluate_blocking(
        "exact_name", s1_entities, gt, route_a_retriever
    )
    print(f"Route A (exact_name):")
    print(f"  Recall: {result_a.overall_recall:.4f}")
    print(f"  Avg candidates: {result_a.avg_candidates:.1f}")
    print(f"  P95 candidates: {result_a.p95_candidates:.0f}\n")

    result_b = evaluate_blocking(
        "alphanumeric_name", s1_entities, gt, route_b_retriever
    )
    print(f"Route B (alphanumeric_name):")
    print(f"  Recall: {result_b.overall_recall:.4f}")
    print(f"  Avg candidates: {result_b.avg_candidates:.1f}")
    print(f"  P95 candidates: {result_b.p95_candidates:.0f}\n")

    # =========================================================================
    # Analyze union contribution
    # =========================================================================
    print("\n--- Union Analysis ---\n")

    contrib = analyze_union_contribution([candidate_set_a, candidate_set_b], gt)

    print_union_contribution(contrib)

    print("\n=== Summary ===\n")
    print(
        f"Union of {len(contrib.route_names)} routes achieves "
        f"{contrib.overall_recall:.4f} recall."
    )
    print("\nMarginal contributions:")
    for c in contrib.contributions:
        print(
            f"  {c.route_name}: "
            f"+{c.marginal_true_pairs:,} pairs "
            f"(+{c.marginal_recall:.4f} recall)"
        )

    print("\n" + "=" * 70)
    print("HOW TO ADD MORE ROUTES")
    print("=" * 70)
    print("""
When new blocking routes are ready (token-overlap, address-token, etc.):

1. Build the route's index (if needed):
   token_overlap_idx = build_token_overlap_index(all_s2s3)

2. Create a retriever function:
   route_c_retriever = lambda ent: retrieve_by_token_overlap(ent, token_overlap_idx)

3. Build the candidate set:
   candidate_set_c = build_candidate_set("token_overlap", s1_entities, route_c_retriever)

4. Add to the union analysis:
   contrib = analyze_union_contribution(
       [candidate_set_a, candidate_set_b, candidate_set_c],
       gt
   )

5. Evaluate combinations:
   - A only
   - B only
   - A + B
   - A + C
   - B + C
   - A + B + C
   etc.

The framework automatically tracks:
- Total recall for each union
- Marginal contribution of each route
- Overlap between routes
- Which pairs are unique to each route
""")
    print("=" * 70)


if __name__ == "__main__":
    main()
