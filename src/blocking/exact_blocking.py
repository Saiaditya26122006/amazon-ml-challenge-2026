"""
Exact blocking strategies using inverted indices.

Each blocker builds a dict from blocking-key -> list of entity IDs,
then retrieves candidates by looking up the S1 entity's key.
"""

from __future__ import annotations

from collections import defaultdict

from blocking.base import Entity


def build_country_index(entities: dict[str, Entity]) -> dict[str, set[str]]:
    """Map country_cleaned -> set of entity IDs."""
    idx: dict[str, set[str]] = defaultdict(set)
    for eid, ent in entities.items():
        key = ent.country_cleaned
        if key:
            idx[key].add(eid)
    return dict(idx)


def build_country_name_cleaned_index(
    entities: dict[str, Entity],
) -> dict[tuple[str, str], set[str]]:
    """Map (country_cleaned, name_cleaned) -> set of entity IDs."""
    idx: dict[tuple[str, str], set[str]] = defaultdict(set)
    for eid, ent in entities.items():
        if ent.country_cleaned and ent.name_cleaned:
            key = (ent.country_cleaned, ent.name_cleaned)
            idx[key].add(eid)
    return dict(idx)


def build_country_name_alphanumeric_index(
    entities: dict[str, Entity],
) -> dict[tuple[str, str], set[str]]:
    """Map (country_cleaned, name_alphanumeric) -> set of entity IDs."""
    idx: dict[tuple[str, str], set[str]] = defaultdict(set)
    for eid, ent in entities.items():
        if ent.country_cleaned and ent.name_alphanumeric:
            key = (ent.country_cleaned, ent.name_alphanumeric)
            idx[key].add(eid)
    return dict(idx)


def retrieve_by_country(
    s1_entity: Entity,
    index: dict[str, set[str]],
) -> set[str]:
    """Return candidate IDs sharing the same country."""
    key = s1_entity.country_cleaned
    if not key:
        return set()
    return index.get(key, set())


def retrieve_by_country_name_cleaned(
    s1_entity: Entity,
    index: dict[tuple[str, str], set[str]],
) -> set[str]:
    """Return candidate IDs with same (country, name_cleaned)."""
    if not s1_entity.country_cleaned or not s1_entity.name_cleaned:
        return set()
    key = (s1_entity.country_cleaned, s1_entity.name_cleaned)
    return index.get(key, set())


def retrieve_by_country_name_alphanumeric(
    s1_entity: Entity,
    index: dict[tuple[str, str], set[str]],
) -> set[str]:
    """Return candidate IDs with same (country, name_alphanumeric)."""
    if not s1_entity.country_cleaned or not s1_entity.name_alphanumeric:
        return set()
    key = (s1_entity.country_cleaned, s1_entity.name_alphanumeric)
    return index.get(key, set())
