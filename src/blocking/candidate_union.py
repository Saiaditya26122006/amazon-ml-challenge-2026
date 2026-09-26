"""
Candidate union: merge candidate sets from multiple blocking strategies.
"""

from __future__ import annotations

from typing import Callable

from blocking.base import Entity


def candidate_union(
    s1_entity: Entity,
    retrievers: list[Callable[[Entity], set[str]]],
) -> set[str]:
    """Return the union of candidates from all retrievers."""
    result: set[str] = set()
    for retriever in retrievers:
        result |= retriever(s1_entity)
    return result
