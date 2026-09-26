"""
Feature Extraction Demo

Shows how to use the pairwise feature extraction framework for entity resolution.
"""

import os
import sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from blocking.base import Entity
from features.pairwise import extract_features, FEATURE_NAMES


def demo_identical_match():
    """Example 1: Identical entities (should be a match)."""
    print("=" * 70)
    print("EXAMPLE 1: Identical Entities")
    print("=" * 70)

    s1 = Entity(
        entity_id="S1-12345",
        name_cleaned="acme incorporated",
        name_alphanumeric="acme incorporated",
        country_cleaned="us",
        addr_cleaned="123 main street",
        addr_alphanumeric="123 main street",
    )

    s2 = Entity(
        entity_id="S2-67890",
        name_cleaned="acme incorporated",
        name_alphanumeric="acme incorporated",
        country_cleaned="us",
        addr_cleaned="123 main street",
        addr_alphanumeric="123 main street",
    )

    print(f"\nS1 Entity: {s1.entity_id}")
    print(f"  Name: {s1.name_alphanumeric}")
    print(f"  Address: {s1.addr_alphanumeric}")
    print(f"  Country: {s1.country_cleaned}")

    print(f"\nCandidate: {s2.entity_id}")
    print(f"  Name: {s2.name_alphanumeric}")
    print(f"  Address: {s2.addr_alphanumeric}")
    print(f"  Country: {s2.country_cleaned}")

    result = extract_features(s1, s2, blocking_route="exact_name")

    print("\n--- Key Features ---")
    print(f"  name_exact_alphanumeric: {result.features['name_exact_alphanumeric']:.2f}")
    print(f"  name_token_jaccard: {result.features['name_token_jaccard']:.2f}")
    print(f"  addr_exact_alphanumeric: {result.features['addr_exact_alphanumeric']:.2f}")
    print(f"  country_exact_match: {result.features['country_exact_match']:.2f}")
    print(f"  name_and_addr_exact: {result.features['name_and_addr_exact']:.2f}")
    print("\n>>> PREDICTION: MATCH [YES]\n")


def demo_fuzzy_match():
    """Example 2: Similar but not identical (fuzzy match)."""
    print("=" * 70)
    print("EXAMPLE 2: Fuzzy Match (Name variation + same address)")
    print("=" * 70)

    s1 = Entity(
        entity_id="S1-11111",
        name_cleaned="acme inc",
        name_alphanumeric="acme inc",
        country_cleaned="us",
        addr_cleaned="456 oak avenue suite 200",
        addr_alphanumeric="456 oak avenue suite 200",
    )

    s2 = Entity(
        entity_id="S2-22222",
        name_cleaned="acme incorporated",
        name_alphanumeric="acme incorporated",
        country_cleaned="us",
        addr_cleaned="456 oak avenue ste 200",
        addr_alphanumeric="456 oak avenue ste 200",
    )

    print(f"\nS1 Entity: {s1.entity_id}")
    print(f"  Name: {s1.name_alphanumeric}")
    print(f"  Address: {s1.addr_alphanumeric}")
    print(f"  Country: {s1.country_cleaned}")

    print(f"\nCandidate: {s2.entity_id}")
    print(f"  Name: {s2.name_alphanumeric}")
    print(f"  Address: {s2.addr_alphanumeric}")
    print(f"  Country: {s2.country_cleaned}")

    result = extract_features(s1, s2, blocking_route="token_overlap")

    print("\n--- Key Features ---")
    print(f"  name_exact_alphanumeric: {result.features['name_exact_alphanumeric']:.2f}")
    print(f"  name_token_jaccard: {result.features['name_token_jaccard']:.2f}")
    print(f"  name_token_intersection_count: {result.features['name_token_intersection_count']:.0f}")
    print(f"  addr_exact_alphanumeric: {result.features['addr_exact_alphanumeric']:.2f}")
    print(f"  addr_token_jaccard: {result.features['addr_token_jaccard']:.2f}")
    print(f"  addr_numeric_intersection_count: {result.features['addr_numeric_intersection_count']:.0f}")
    print(f"  country_exact_match: {result.features['country_exact_match']:.2f}")
    print(f"  strong_name_weak_addr: {result.features['strong_name_weak_addr']:.2f}")
    print("\n>>> PREDICTION: LIKELY MATCH [YES]\n")


def demo_non_match():
    """Example 3: Different entities (should not match)."""
    print("=" * 70)
    print("EXAMPLE 3: Non-Match (Different entities)")
    print("=" * 70)

    s1 = Entity(
        entity_id="S1-99999",
        name_cleaned="tech solutions llc",
        name_alphanumeric="tech solutions llc",
        country_cleaned="us",
        addr_cleaned="789 pine rd",
        addr_alphanumeric="789 pine rd",
    )

    s3 = Entity(
        entity_id="S3-88888",
        name_cleaned="global services pvt ltd",
        name_alphanumeric="global services pvt ltd",
        country_cleaned="india",
        addr_cleaned="plot 42 sector 18",
        addr_alphanumeric="plot 42 sector 18",
    )

    print(f"\nS1 Entity: {s1.entity_id}")
    print(f"  Name: {s1.name_alphanumeric}")
    print(f"  Address: {s1.addr_alphanumeric}")
    print(f"  Country: {s1.country_cleaned}")

    print(f"\nCandidate: {s3.entity_id}")
    print(f"  Name: {s3.name_alphanumeric}")
    print(f"  Address: {s3.addr_alphanumeric}")
    print(f"  Country: {s3.country_cleaned}")

    result = extract_features(s1, s3, blocking_route="country_only")

    print("\n--- Key Features ---")
    print(f"  name_exact_alphanumeric: {result.features['name_exact_alphanumeric']:.2f}")
    print(f"  name_token_jaccard: {result.features['name_token_jaccard']:.2f}")
    print(f"  name_token_intersection_count: {result.features['name_token_intersection_count']:.0f}")
    print(f"  addr_token_jaccard: {result.features['addr_token_jaccard']:.2f}")
    print(f"  country_exact_match: {result.features['country_exact_match']:.2f}")
    print("\n>>> PREDICTION: NON-MATCH [NO]\n")


def demo_missing_data():
    """Example 4: Handling missing data."""
    print("=" * 70)
    print("EXAMPLE 4: Missing Data (Address missing for S1)")
    print("=" * 70)

    s1 = Entity(
        entity_id="S1-55555",
        name_cleaned="retail store inc",
        name_alphanumeric="retail store inc",
        country_cleaned="us",
        addr_cleaned="",
        addr_alphanumeric="",
    )

    s2 = Entity(
        entity_id="S2-66666",
        name_cleaned="retail store incorporated",
        name_alphanumeric="retail store incorporated",
        country_cleaned="us",
        addr_cleaned="100 market st",
        addr_alphanumeric="100 market st",
    )

    print(f"\nS1 Entity: {s1.entity_id}")
    print(f"  Name: {s1.name_alphanumeric}")
    print(f"  Address: {s1.addr_alphanumeric or '[MISSING]'}")
    print(f"  Country: {s1.country_cleaned}")

    print(f"\nCandidate: {s2.entity_id}")
    print(f"  Name: {s2.name_alphanumeric}")
    print(f"  Address: {s2.addr_alphanumeric}")
    print(f"  Country: {s2.country_cleaned}")

    result = extract_features(s1, s2, blocking_route="exact_name")

    print("\n--- Key Features ---")
    print(f"  name_token_jaccard: {result.features['name_token_jaccard']:.2f}")
    print(f"  name_token_intersection_count: {result.features['name_token_intersection_count']:.0f}")
    print(f"  s1_addr_missing: {result.features['s1_addr_missing']:.0f}")
    print(f"  cand_addr_missing: {result.features['cand_addr_missing']:.0f}")
    print(f"  addr_token_jaccard: {result.features['addr_token_jaccard']:.2f}")
    print(f"  country_exact_match: {result.features['country_exact_match']:.2f}")
    print("\n>>> PREDICTION: UNCERTAIN (need more features or manual review)\n")


def demo_feature_vector():
    """Example 5: Feature vector for ML model."""
    print("=" * 70)
    print("EXAMPLE 5: Feature Vector for ML Model")
    print("=" * 70)

    s1 = Entity(
        entity_id="S1-00001",
        name_cleaned="sample company",
        name_alphanumeric="sample company",
        country_cleaned="us",
        addr_cleaned="999 test st",
        addr_alphanumeric="999 test st",
    )

    s2 = Entity(
        entity_id="S2-00002",
        name_cleaned="sample co",
        name_alphanumeric="sample co",
        country_cleaned="us",
        addr_cleaned="999 test street",
        addr_alphanumeric="999 test street",
    )

    print(f"\nS1 Entity: {s1.entity_id}")
    print(f"Candidate: {s2.entity_id}")

    result = extract_features(s1, s2)

    print(f"\n--- Feature Dictionary ({len(result.features)} features) ---")
    for i, (name, value) in enumerate(result.features.items()):
        if i < 10:  # Show first 10
            print(f"  {name}: {value:.4f}")
    print(f"  ... ({len(result.features) - 10} more features)")

    print(f"\n--- Feature Vector (ordered) ---")
    vector = result.to_vector()
    print(f"  Vector length: {len(vector)}")
    print(f"  First 10 values: {[f'{v:.3f}' for v in vector[:10]]}")
    print(f"  ... ({len(vector) - 10} more values)")

    print("\n>>> This vector can be fed into sklearn/xgboost/neural networks\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("FEATURE EXTRACTION DEMO")
    print("Entity Resolution Pipeline - Step 5")
    print("=" * 70 + "\n")

    demo_identical_match()
    demo_fuzzy_match()
    demo_non_match()
    demo_missing_data()
    demo_feature_vector()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nTotal features extracted: {len(FEATURE_NAMES)}")
    print("\nFeature groups:")
    print("  - Name features: 9")
    print("  - Address features: 10")
    print("  - Cross-field features: 4")
    print("  - Data quality features: 8")
    print("\nReady for ML model training!")
    print("\n" + "=" * 70 + "\n")
