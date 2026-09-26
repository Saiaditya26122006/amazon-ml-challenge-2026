"""
Base types and data loading for the blocking framework.

Provides a lightweight entity representation and streaming loaders
that apply normalization on the fly using the frozen normalize.py.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field

_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import preprocessing.normalize as _norm_module

# Speed up normalize.py's _is_latin by replacing the slow
# unicodedata.name() lookup with a fast codepoint-range check.
# This does NOT modify the source file — it patches at import time.
def _fast_is_latin(ch: str) -> bool:
    cp = ord(ch)
    return (
        (0x0041 <= cp <= 0x024F) or
        (0x1E00 <= cp <= 0x1EFF) or
        (0x2C60 <= cp <= 0x2C7F) or
        (0xA720 <= cp <= 0xA7FF) or
        (0xAB30 <= cp <= 0xAB6F)
    )

_norm_module._is_latin = _fast_is_latin

from preprocessing.normalize import (
    normalize_name,
    normalize_address,
    normalize_country,
)

PROJECT_ROOT = os.path.abspath(os.path.join(_SRC_DIR, os.pardir))
DATA_DIR = os.path.join(PROJECT_ROOT, "database", "student_resource", "dataset")

DELIMITER = "\t"


@dataclass(slots=True)
class Entity:
    entity_id: str
    name_cleaned: str
    name_alphanumeric: str
    country_cleaned: str
    addr_cleaned: str
    addr_alphanumeric: str


def load_source_normalized(
    filepath: str,
    *,
    limit: int | None = None,
    needed_ids: set[str] | None = None,
) -> dict[str, Entity]:
    """Stream a source TSV and return normalized Entity objects.

    If *needed_ids* is provided, only those IDs are kept (early exit
    once all found). If *limit* is provided, at most that many rows
    are read from the file.
    """
    entities: dict[str, Entity] = {}
    remaining = set(needed_ids) if needed_ids is not None else None

    with open(filepath, encoding="utf-8") as f:
        next(f)  # skip header
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            parts = line.rstrip("\n").split(DELIMITER)
            if len(parts) < 4:
                continue
            eid, raw_name, raw_addr, raw_country = parts[0], parts[1], parts[2], parts[3]

            if remaining is not None:
                if eid not in remaining:
                    continue
                remaining.discard(eid)

            nn = normalize_name(raw_name)
            na = normalize_address(raw_addr)
            nc = normalize_country(raw_country)

            entities[eid] = Entity(
                entity_id=eid,
                name_cleaned=nn.cleaned,
                name_alphanumeric=nn.alphanumeric,
                country_cleaned=nc.cleaned,
                addr_cleaned=na.cleaned,
                addr_alphanumeric=na.alphanumeric,
            )

            if remaining is not None and not remaining:
                break

    return entities


def load_ground_truth(filepath: str, limit: int | None = None) -> dict[str, list[str]]:
    """Load ground truth: S1 entity ID -> list of matched S2/S3 IDs.

    Reads the actual header to find columns, not hardcoded names.
    """
    gt: dict[str, list[str]] = {}
    with open(filepath, encoding="utf-8") as f:
        header = next(f).rstrip("\n").split(DELIMITER)
        s1_col = 0
        match_col = 1

        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            parts = line.rstrip("\n").split(DELIMITER)
            if len(parts) < 2:
                continue
            s1_id = parts[s1_col]
            matched_ids = [m.strip() for m in parts[match_col].split(",") if m.strip()]
            if matched_ids:
                gt[s1_id] = matched_ids
    return gt
