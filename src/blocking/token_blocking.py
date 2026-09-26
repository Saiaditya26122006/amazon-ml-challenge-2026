"""
Token-overlap blocking strategies.

Builds a (country, token) inverted index over name tokens and retrieves
candidates that share at least ``min_overlap`` tokens with the S1 entity,
restricted to the same country (100% of ground-truth pairs are
same-country per the core experiment).

Tokens are the whitespace-split fields of ``name_alphanumeric`` — exactly
what ``normalize_name(...).tokens`` produces — so no extra normalization
is needed at query time.

Document frequency of a key equals ``len(posting)`` because each entity
contributes each distinct token at most once.
"""

from __future__ import annotations

from collections import defaultdict

from blocking.base import Entity


def tokenize_name(name_alphanumeric: str) -> frozenset[str]:
    """Unique whitespace-split tokens of an alphanumeric name."""
    return frozenset(name_alphanumeric.split())


def build_country_token_index(
    entities: dict[str, Entity],
) -> dict[tuple[str, str], set[str]]:
    """Map (country_cleaned, token) -> set of entity IDs.

    Entities with an empty country or empty name are skipped.
    """
    idx: dict[tuple[str, str], set[str]] = defaultdict(set)
    for eid, ent in entities.items():
        country = ent.country_cleaned
        if not country:
            continue
        for token in tokenize_name(ent.name_alphanumeric):
            idx[(country, token)].add(eid)
    return dict(idx)


def filter_index_by_df(
    index: dict[tuple[str, str], set[str]],
    *,
    min_df: int = 1,
    max_df: int | None = None,
) -> dict[tuple[str, str], set[str]]:
    """Return a view of *index* keeping only keys with min_df <= df <= max_df.

    Posting sets are shared (not copied) — treat the result as read-only.
    """
    return {
        key: posting
        for key, posting in index.items()
        if len(posting) >= min_df and (max_df is None or len(posting) <= max_df)
    }


def retrieve_by_token_overlap(
    s1_entity: Entity,
    index: dict[tuple[str, str], set[str]],
    *,
    min_overlap: int = 1,
) -> set[str]:
    """Return candidate IDs sharing at least *min_overlap* tokens.

    Candidates are restricted to the S1 entity's country and to tokens
    present in *index* (df-filtered tokens are simply not retrievable).

    For ``min_overlap <= 1`` this is a plain union of posting lists; for
    higher thresholds the overlap count is tallied per candidate.
    """
    country = s1_entity.country_cleaned
    if not country:
        return set()
    tokens = tokenize_name(s1_entity.name_alphanumeric)
    if not tokens:
        return set()

    if min_overlap <= 1:
        candidates: set[str] = set()
        for token in tokens:
            posting = index.get((country, token))
            if posting:
                candidates |= posting
        return candidates

    counts: dict[str, int] = {}
    for token in tokens:
        posting = index.get((country, token))
        if not posting:
            continue
        for cid in posting:
            counts[cid] = counts.get(cid, 0) + 1
    return {cid for cid, n in counts.items() if n >= min_overlap}


def top_tokens_by_df(
    index: dict[tuple[str, str], set[str]],
    top_n: int = 30,
) -> list[dict]:
    """The *top_n* (country, token) keys with the largest posting lists."""
    ranked = sorted(index.items(), key=lambda kv: len(kv[1]), reverse=True)
    return [
        {"country": country, "token": token, "df": len(posting)}
        for (country, token), posting in ranked[:top_n]
    ]


def df_percentiles(index: dict[tuple[str, str], set[str]]) -> dict[str, float]:
    """Summary statistics of posting-list sizes (document frequencies)."""
    import statistics

    sizes = sorted(len(p) for p in index.values())
    if not sizes:
        return {"keys": 0}

    def pct(p: float) -> int:
        idx = min(int(len(sizes) * p), len(sizes) - 1)
        return sizes[idx]

    return {
        "keys": len(sizes),
        "median": statistics.median(sizes),
        "p90": pct(0.90),
        "p95": pct(0.95),
        "p99": pct(0.99),
        "max": sizes[-1],
        "total_postings": sum(sizes),
    }
