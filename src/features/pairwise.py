"""
Pairwise feature extraction for entity resolution.

Computes matching features between an S1 entity and a candidate (S2 or S3).
Reuses existing normalized representations from the blocking framework.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from blocking.base import Entity


# Feature names in deterministic order
FEATURE_NAMES = [
    # Name features
    "name_exact_cleaned",
    "name_exact_alphanumeric",
    "name_token_intersection_count",
    "name_token_jaccard",
    "name_token_containment_s1",
    "name_token_containment_cand",
    "name_length_ratio",
    "name_char_jaccard",
    "name_token_count_diff",
    # Address features
    "addr_exact_cleaned",
    "addr_exact_alphanumeric",
    "addr_token_intersection_count",
    "addr_token_jaccard",
    "addr_token_containment_s1",
    "addr_token_containment_cand",
    "addr_numeric_intersection_count",
    "addr_numeric_jaccard",
    "addr_length_ratio",
    "addr_token_count_diff",
    # Cross-field features
    "country_exact_match",
    "name_and_addr_exact",
    "strong_name_weak_addr",
    "weak_name_strong_addr",
    # Data quality features
    "s1_name_missing",
    "cand_name_missing",
    "s1_addr_missing",
    "cand_addr_missing",
    "s1_name_token_count",
    "cand_name_token_count",
    "s1_addr_token_count",
    "cand_addr_token_count",
]


@dataclass(slots=True)
class PairwiseFeatures:
    """Container for extracted pairwise features.

    Attributes
    ----------
    features : dict[str, float]
        Feature name -> numerical value.
    s1_id : str
        S1 entity ID.
    candidate_id : str
        Candidate entity ID (S2-* or S3-*).
    blocking_route : str, optional
        Which blocking route generated this candidate.
    """

    features: dict[str, float]
    s1_id: str
    candidate_id: str
    blocking_route: str = ""

    def to_vector(self) -> list[float]:
        """Return feature values in deterministic order matching FEATURE_NAMES."""
        return [self.features[name] for name in FEATURE_NAMES]


def _safe_divide(num: float, denom: float, default: float = 0.0) -> float:
    """Divide num/denom, return default if denom is zero or result is inf/nan."""
    if denom == 0.0:
        return default
    result = num / denom
    if not (-1e308 < result < 1e308):  # Check for inf
        return default
    # NaN check
    if result != result:  # NaN != NaN
        return default
    return result


def _jaccard(set_a: set, set_b: set) -> float:
    """Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0  # Both empty -> identical
    union_size = len(set_a | set_b)
    if union_size == 0:
        return 0.0
    return len(set_a & set_b) / union_size


def _containment(set_a: set, set_b: set) -> float:
    """Containment: |A ∩ B| / |A|. Returns 1.0 if A is empty."""
    if not set_a:
        return 1.0
    return len(set_a & set_b) / len(set_a)


def _char_jaccard(str_a: str, str_b: str) -> float:
    """Character-level Jaccard similarity."""
    if not str_a and not str_b:
        return 1.0
    set_a = set(str_a)
    set_b = set(str_b)
    return _jaccard(set_a, set_b)


def _length_ratio(str_a: str, str_b: str) -> float:
    """Length ratio: min(len(a), len(b)) / max(len(a), len(b)).

    Returns 1.0 if both empty, 0.0 if one empty.
    """
    len_a = len(str_a)
    len_b = len(str_b)
    if len_a == 0 and len_b == 0:
        return 1.0
    if len_a == 0 or len_b == 0:
        return 0.0
    return min(len_a, len_b) / max(len_a, len_b)


def _tokenize_for_features(text: str) -> list[str]:
    """Tokenize text for feature computation.

    Assumes text is already normalized (alphanumeric).
    """
    return text.split()


def extract_features(
    s1_entity: Entity,
    candidate_entity: Entity,
    blocking_route: str = "",
) -> PairwiseFeatures:
    """Extract pairwise matching features between S1 and a candidate.

    Parameters
    ----------
    s1_entity : Entity
        Source 1 entity with normalized fields.
    candidate_entity : Entity
        Candidate entity (S2 or S3) with normalized fields.
    blocking_route : str, optional
        Name of the blocking route that generated this candidate.

    Returns
    -------
    PairwiseFeatures
        Feature dictionary with all numerical features.
    """
    features: dict[str, float] = {}

    # Extract fields
    s1_name_cleaned = s1_entity.name_cleaned
    s1_name_alnum = s1_entity.name_alphanumeric
    s1_addr_cleaned = s1_entity.addr_cleaned
    s1_addr_alnum = s1_entity.addr_alphanumeric
    s1_country = s1_entity.country_cleaned

    cand_name_cleaned = candidate_entity.name_cleaned
    cand_name_alnum = candidate_entity.name_alphanumeric
    cand_addr_cleaned = candidate_entity.addr_cleaned
    cand_addr_alnum = candidate_entity.addr_alphanumeric
    cand_country = candidate_entity.country_cleaned

    # Data quality features: missingness indicators
    s1_name_missing = 1.0 if not s1_name_alnum else 0.0
    cand_name_missing = 1.0 if not cand_name_alnum else 0.0
    s1_addr_missing = 1.0 if not s1_addr_alnum else 0.0
    cand_addr_missing = 1.0 if not cand_addr_alnum else 0.0

    features["s1_name_missing"] = s1_name_missing
    features["cand_name_missing"] = cand_name_missing
    features["s1_addr_missing"] = s1_addr_missing
    features["cand_addr_missing"] = cand_addr_missing

    # Tokenize names and addresses
    s1_name_tokens = _tokenize_for_features(s1_name_alnum)
    cand_name_tokens = _tokenize_for_features(cand_name_alnum)
    s1_addr_tokens = _tokenize_for_features(s1_addr_alnum)
    cand_addr_tokens = _tokenize_for_features(cand_addr_alnum)

    # Token counts
    features["s1_name_token_count"] = float(len(s1_name_tokens))
    features["cand_name_token_count"] = float(len(cand_name_tokens))
    features["s1_addr_token_count"] = float(len(s1_addr_tokens))
    features["cand_addr_token_count"] = float(len(cand_addr_tokens))

    # Convert to sets for overlap computation
    s1_name_set = set(s1_name_tokens)
    cand_name_set = set(cand_name_tokens)
    s1_addr_set = set(s1_addr_tokens)
    cand_addr_set = set(cand_addr_tokens)

    # =========================================================================
    # NAME FEATURES
    # =========================================================================

    # Exact matches
    features["name_exact_cleaned"] = 1.0 if s1_name_cleaned == cand_name_cleaned else 0.0
    features["name_exact_alphanumeric"] = 1.0 if s1_name_alnum == cand_name_alnum else 0.0

    # Token overlap
    name_intersection = s1_name_set & cand_name_set
    features["name_token_intersection_count"] = float(len(name_intersection))
    features["name_token_jaccard"] = _jaccard(s1_name_set, cand_name_set)
    features["name_token_containment_s1"] = _containment(s1_name_set, cand_name_set)
    features["name_token_containment_cand"] = _containment(cand_name_set, s1_name_set)

    # Length and character similarity
    features["name_length_ratio"] = _length_ratio(s1_name_alnum, cand_name_alnum)
    features["name_char_jaccard"] = _char_jaccard(s1_name_alnum, cand_name_alnum)

    # Token count difference
    features["name_token_count_diff"] = abs(len(s1_name_tokens) - len(cand_name_tokens))

    # =========================================================================
    # ADDRESS FEATURES
    # =========================================================================

    # Exact matches
    features["addr_exact_cleaned"] = 1.0 if s1_addr_cleaned == cand_addr_cleaned else 0.0
    features["addr_exact_alphanumeric"] = 1.0 if s1_addr_alnum == cand_addr_alnum else 0.0

    # Token overlap
    addr_intersection = s1_addr_set & cand_addr_set
    features["addr_token_intersection_count"] = float(len(addr_intersection))
    features["addr_token_jaccard"] = _jaccard(s1_addr_set, cand_addr_set)
    features["addr_token_containment_s1"] = _containment(s1_addr_set, cand_addr_set)
    features["addr_token_containment_cand"] = _containment(cand_addr_set, s1_addr_set)

    # Numeric token overlap (house numbers, postal codes, etc.)
    # Extract numeric tokens from address
    s1_addr_numeric = {t for t in s1_addr_tokens if any(c.isdigit() for c in t)}
    cand_addr_numeric = {t for t in cand_addr_tokens if any(c.isdigit() for c in t)}
    addr_numeric_intersection = s1_addr_numeric & cand_addr_numeric
    features["addr_numeric_intersection_count"] = float(len(addr_numeric_intersection))
    features["addr_numeric_jaccard"] = _jaccard(s1_addr_numeric, cand_addr_numeric)

    # Length and token count
    features["addr_length_ratio"] = _length_ratio(s1_addr_alnum, cand_addr_alnum)
    features["addr_token_count_diff"] = abs(len(s1_addr_tokens) - len(cand_addr_tokens))

    # =========================================================================
    # CROSS-FIELD FEATURES
    # =========================================================================

    # Country match
    features["country_exact_match"] = 1.0 if s1_country == cand_country else 0.0

    # Name AND address exact match
    name_exact = (s1_name_alnum == cand_name_alnum) and s1_name_alnum
    addr_exact = (s1_addr_alnum == cand_addr_alnum) and s1_addr_alnum
    features["name_and_addr_exact"] = 1.0 if (name_exact and addr_exact) else 0.0

    # Strong name + weak address
    # Strong name: Jaccard >= 0.8 or exact match
    # Weak address: Jaccard >= 0.3 or some overlap
    strong_name = (features["name_token_jaccard"] >= 0.8 or name_exact)
    weak_addr = (features["addr_token_jaccard"] >= 0.3 or len(addr_intersection) > 0)
    features["strong_name_weak_addr"] = 1.0 if (strong_name and weak_addr) else 0.0

    # Weak name + strong address
    weak_name = (features["name_token_jaccard"] >= 0.3 or len(name_intersection) > 0)
    strong_addr = (features["addr_token_jaccard"] >= 0.8 or addr_exact)
    features["weak_name_strong_addr"] = 1.0 if (weak_name and strong_addr) else 0.0

    return PairwiseFeatures(
        features=features,
        s1_id=s1_entity.entity_id,
        candidate_id=candidate_entity.entity_id,
        blocking_route=blocking_route,
    )


def extract_features_batch(
    s1_entities: dict[str, Entity],
    candidate_entities: dict[str, Entity],
    candidate_pairs: list[tuple[str, str]],
    blocking_routes: dict[tuple[str, str], str] | None = None,
) -> list[PairwiseFeatures]:
    """Extract features for a batch of candidate pairs.

    Parameters
    ----------
    s1_entities : dict[str, Entity]
        S1 entity ID -> Entity.
    candidate_entities : dict[str, Entity]
        Candidate entity ID -> Entity (S2 and S3 combined).
    candidate_pairs : list[tuple[str, str]]
        List of (s1_id, candidate_id) pairs.
    blocking_routes : dict[tuple[str, str], str], optional
        Map from (s1_id, candidate_id) to blocking route name.

    Returns
    -------
    list[PairwiseFeatures]
        Features for each pair.
    """
    if blocking_routes is None:
        blocking_routes = {}

    results = []
    for s1_id, cand_id in candidate_pairs:
        if s1_id not in s1_entities:
            continue
        if cand_id not in candidate_entities:
            continue

        route = blocking_routes.get((s1_id, cand_id), "")
        feats = extract_features(
            s1_entities[s1_id],
            candidate_entities[cand_id],
            blocking_route=route,
        )
        results.append(feats)

    return results
