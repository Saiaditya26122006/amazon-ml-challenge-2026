"""
Normalization Experiments — Empirical evaluation of additional transformations.

Measures similarity between S1 entities and their true S2/S3 matches under
different normalization strategies. Also evaluates collision risk on hard
negatives.

Usage:
    python experiments/normalization/run_experiments.py
"""

from __future__ import annotations

import csv
import io
import math
import os
import random
import re
import sys
import time
import tracemalloc
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Encoding fix for Windows
# ---------------------------------------------------------------------------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
DATA_DIR = os.path.join(PROJECT_ROOT, "database", "student_resource", "dataset", "train")
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

S1_FILE = os.path.join(DATA_DIR, "train_source1.tsv")
S2_FILE = os.path.join(DATA_DIR, "train_source2.tsv")
S3_FILE = os.path.join(DATA_DIR, "train_source3.tsv")
GT_FILE = os.path.join(DATA_DIR, "train_ground_truth.tsv")

SAMPLE_S1 = 50_000
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Similarity functions
# ---------------------------------------------------------------------------

def char_similarity(a: str, b: str) -> float:
    """Character-level similarity using Sorensen-Dice on bigrams."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    la = len(a)
    lb = len(b)
    if la < 2 and lb < 2:
        return 1.0 if a == b else 0.0
    if la < 2 or lb < 2:
        return 0.0
    set_a: dict[str, int] = {}
    for i in range(la - 1):
        bg = a[i:i+2]
        set_a[bg] = set_a.get(bg, 0) + 1
    set_b: dict[str, int] = {}
    for i in range(lb - 1):
        bg = b[i:i+2]
        set_b[bg] = set_b.get(bg, 0) + 1
    overlap = 0
    for bg, cnt in set_a.items():
        cnt_b = set_b.get(bg)
        if cnt_b is not None:
            overlap += min(cnt, cnt_b)
    return (2.0 * overlap) / (la - 1 + lb - 1)


def token_jaccard(a: str, b: str) -> float:
    """Jaccard similarity on whitespace-split token sets."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    set_a = set(a.split())
    set_b = set(b.split())
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union > 0 else 0.0


def exact_match(a: str, b: str) -> float:
    return 1.0 if a == b else 0.0


def numeric_overlap(a: str, b: str) -> float:
    """Jaccard similarity on numeric tokens only."""
    nums_a = set(re.findall(r'\d+', a))
    nums_b = set(re.findall(r'\d+', b))
    if not nums_a and not nums_b:
        return 1.0
    if not nums_a or not nums_b:
        return 0.0
    inter = len(nums_a & nums_b)
    union = len(nums_a | nums_b)
    return inter / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# Normalization transforms (experimental — NOT modifying normalize.py)
# ---------------------------------------------------------------------------

_MULTI_WS = re.compile(r"\s+")
_MISSING_LITERALS = {"", "null", "nan", "none", "n/a", "na", "undefined", "missing", "-", "--", "."}


def _is_latin(ch: str) -> bool:
    cp = ord(ch)
    return (
        (0x0041 <= cp <= 0x024F) or  # Basic Latin, Latin Extended-A/B
        (0x1E00 <= cp <= 0x1EFF) or  # Latin Extended Additional
        (0x2C60 <= cp <= 0x2C7F) or  # Latin Extended-C
        (0xA720 <= cp <= 0xA7FF) or  # Latin Extended-D
        (0xAB30 <= cp <= 0xAB6F)     # Latin Extended-E
    )


def _is_missing(val: str) -> bool:
    return val.strip().lower() in _MISSING_LITERALS


def transform_current_name(name: str) -> str:
    """Experiment A: match current normalize.py behavior for names."""
    if _is_missing(name):
        return ""
    text = unicodedata.normalize("NFC", name).lower()
    text = _MULTI_WS.sub(" ", text).strip()
    # Strip accents from Latin chars only
    out = []
    for ch in unicodedata.normalize("NFD", text):
        cat = unicodedata.category(ch)
        if cat.startswith("M"):
            if out and not _is_latin(out[-1]):
                out.append(ch)
        else:
            out.append(ch)
    text = unicodedata.normalize("NFC", "".join(out))
    # Alphanumeric
    out2 = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch.isalnum() or ch.isspace() or cat.startswith("M"):
            out2.append(ch)
        else:
            out2.append(" ")
    return _MULTI_WS.sub(" ", "".join(out2)).strip()


def transform_lower_punct(name: str) -> str:
    """Experiment B: simple lowercase + punctuation strip."""
    if _is_missing(name):
        return ""
    text = name.lower()
    out = []
    for ch in text:
        if ch.isalnum() or ch.isspace():
            out.append(ch)
        else:
            out.append(" ")
    return _MULTI_WS.sub(" ", "".join(out)).strip()


def transform_unicode_accent(name: str) -> str:
    """Experiment C: NFC + Latin accent folding (same as current)."""
    return transform_current_name(name)


# Legal form standardization dictionary
_LEGAL_FORMS = {
    # English
    "ltd": "limited", "ltd.": "limited",
    "corp": "corporation", "corp.": "corporation",
    "inc": "incorporated", "inc.": "incorporated",
    "co": "company", "co.": "company",
    "pvt": "private", "pvt.": "private",
    # French — dotted forms to clean forms
    "s.a.": "sa", "s.a.s.": "sas", "s.a.s": "sas",
    "s.a.r.l.": "sarl", "s.a.r.l": "sarl",
    "s.c.i.": "sci", "s.c.i": "sci",
    "e.u.r.l.": "eurl", "e.u.r.l": "eurl",
    "s.n.c.": "snc", "s.n.c": "snc",
    # Case variants that appear after lowercasing
    "sasu": "sasu",
    "sarl": "sarl",
    "eurl": "eurl",
    "sas": "sas",
    "sci": "sci",
    "sa": "sa",
}


def transform_legal_std(name: str) -> str:
    """Experiment D: current normalization + legal form standardization."""
    base = transform_current_name(name)
    if not base:
        return base
    tokens = base.split()
    result = []
    i = 0
    while i < len(tokens):
        # Try multi-token patterns (e.g., "pvt" "ltd" -> "private" "limited")
        token = tokens[i]
        if token in _LEGAL_FORMS:
            result.append(_LEGAL_FORMS[token])
        else:
            result.append(token)
        i += 1
    return " ".join(result)


def transform_token_norm(name: str) -> str:
    """Experiment E: current + token sort (order-invariant)."""
    base = transform_current_name(name)
    if not base:
        return base
    tokens = sorted(base.split())
    return " ".join(tokens)


def transform_combined(name: str) -> str:
    """Experiment F: current + legal standardization (NOT removal, NOT sorting)."""
    return transform_legal_std(name)


# ---------------------------------------------------------------------------
# Address transforms
# ---------------------------------------------------------------------------

_NULL_TOKENS_ADDR = {"null", "nan", "none", "n/a", "na", "undefined", "missing"}


def _addr_base(addr: str) -> str:
    """Common address baseline: NFC, lower, strip null tokens."""
    if _is_missing(addr):
        return ""
    text = unicodedata.normalize("NFC", addr).lower()
    text = _MULTI_WS.sub(" ", text).strip()
    tokens = text.split()
    tokens = [t for t in tokens if t.lower() not in _NULL_TOKENS_ADDR]
    return " ".join(tokens)


def addr_current(addr: str) -> str:
    """Address experiment A: match current normalize.py (alphanumeric, accent-folded)."""
    if _is_missing(addr):
        return ""
    text = unicodedata.normalize("NFC", addr).lower()
    text = _MULTI_WS.sub(" ", text).strip()
    # Remove null tokens
    tokens = text.split()
    cleaned_tokens = []
    for t in tokens:
        if t in _NULL_TOKENS_ADDR:
            continue
        cleaned_tokens.append(t)
    text = " ".join(cleaned_tokens)
    # Accent fold Latin only
    out = []
    for ch in unicodedata.normalize("NFD", text):
        cat = unicodedata.category(ch)
        if cat.startswith("M"):
            if out and not _is_latin(out[-1]):
                out.append(ch)
        else:
            out.append(ch)
    text = unicodedata.normalize("NFC", "".join(out))
    # Alphanumeric
    out2 = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch.isalnum() or ch.isspace() or cat.startswith("M"):
            out2.append(ch)
        else:
            out2.append(" ")
    return _MULTI_WS.sub(" ", "".join(out2)).strip()


def addr_lower_punct(addr: str) -> str:
    """Address experiment B: lowercase + punctuation strip."""
    if _is_missing(addr):
        return ""
    text = addr.lower()
    out = []
    for ch in text:
        if ch.isalnum() or ch.isspace():
            out.append(ch)
        else:
            out.append(" ")
    return _MULTI_WS.sub(" ", "".join(out)).strip()


def addr_whitespace(addr: str) -> str:
    """Address experiment C: whitespace normalization only."""
    if _is_missing(addr):
        return ""
    return _MULTI_WS.sub(" ", addr).strip()


# Address abbreviation expansions — keyed by country
_ADDR_ABBREVS_US = {
    "st": "street", "st.": "street",
    "rd": "road", "rd.": "road",
    "ave": "avenue", "ave.": "avenue",
    "blvd": "boulevard", "blvd.": "boulevard",
    "dr": "drive", "dr.": "drive",
    "ln": "lane", "ln.": "lane",
    "ct": "court", "ct.": "court",
    "pl": "place", "pl.": "place",
    "pkwy": "parkway", "hwy": "highway",
    "cir": "circle", "sq": "square",
}

_ADDR_ABBREVS_FR = {
    "r.": "rue", "r": "rue",
    "av": "avenue", "av.": "avenue",
    "bd": "boulevard", "bd.": "boulevard",
    "all": "allee", "all.": "allee",
    "pl": "place", "pl.": "place",
    "rte": "route", "rte.": "route",
    "imp": "impasse", "imp.": "impasse",
    "ch": "chemin", "ch.": "chemin",
}

_ADDR_ABBREVS_IN = {
    "st": "street", "st.": "street",
    "rd": "road", "rd.": "road",
    "no": "number", "no.": "number",
}


def addr_abbrev(addr: str, country: str) -> str:
    """Address experiment D: current + abbreviation expansion (country-aware)."""
    base = addr_current(addr)
    if not base:
        return base
    country_lower = country.strip().lower() if country else ""
    if country_lower in ("us", "united states"):
        abbrevs = _ADDR_ABBREVS_US
    elif country_lower in ("france",):
        abbrevs = _ADDR_ABBREVS_FR
    elif country_lower in ("india",):
        abbrevs = _ADDR_ABBREVS_IN
    else:
        abbrevs = {}
    if not abbrevs:
        return base
    tokens = base.split()
    result = []
    for t in tokens:
        if t in abbrevs:
            result.append(abbrevs[t])
        else:
            result.append(t)
    return " ".join(result)


def addr_numeric(addr: str) -> str:
    """Address experiment E: extract numeric tokens only."""
    base = addr_current(addr)
    nums = re.findall(r'\d+', base)
    return " ".join(nums)


def addr_token_set(addr: str) -> str:
    """Address experiment F: sorted token set (order-invariant)."""
    base = addr_current(addr)
    if not base:
        return base
    return " ".join(sorted(base.split()))


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    entity_id: str
    business_name: str
    business_address: str
    country: str


def load_ground_truth(limit: int) -> dict[str, list[str]]:
    """Load first `limit` S1 -> [matched_ids] mappings."""
    gt: dict[str, list[str]] = {}
    with open(GT_FILE, encoding="utf-8") as f:
        next(f)  # skip header
        for i, line in enumerate(f):
            if i >= limit:
                break
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 2:
                s1_id = parts[0]
                matched = parts[1].split(",")
                gt[s1_id] = matched
    return gt


def load_entities_by_id(filepath: str, needed_ids: set[str]) -> dict[str, Entity]:
    """Stream a source file and collect only entities in needed_ids."""
    entities: dict[str, Entity] = {}
    with open(filepath, encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            eid = parts[0]
            if eid in needed_ids:
                entities[eid] = Entity(
                    entity_id=eid,
                    business_name=parts[1],
                    business_address=parts[2],
                    country=parts[3],
                )
                needed_ids.discard(eid)
                if not needed_ids:
                    break
    return entities


def load_all_entities(filepath: str, limit: int | None = None) -> dict[str, Entity]:
    """Load all entities from a source file (or first `limit`)."""
    entities: dict[str, Entity] = {}
    with open(filepath, encoding="utf-8") as f:
        next(f)
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            eid = parts[0]
            entities[eid] = Entity(
                entity_id=eid,
                business_name=parts[1],
                business_address=parts[2],
                country=parts[3],
            )
    return entities


# ---------------------------------------------------------------------------
# Hard negative sampling
# ---------------------------------------------------------------------------

def sample_hard_negatives(
    s1_entities: dict[str, Entity],
    s2_entities: dict[str, Entity],
    s3_entities: dict[str, Entity],
    gt: dict[str, list[str]],
    n_negatives: int,
    rng: random.Random,
) -> list[tuple[Entity, Entity]]:
    """
    Sample hard negative pairs: S1 entities paired with S2/S3 entities
    that are NOT their ground truth matches but share the same country
    and ideally have similar name tokens.
    """
    # Build country -> S2/S3 entity ID index
    country_to_s2s3: dict[str, list[str]] = defaultdict(list)
    for eid, ent in s2_entities.items():
        country_to_s2s3[ent.country.strip().lower()].append(eid)
    for eid, ent in s3_entities.items():
        country_to_s2s3[ent.country.strip().lower()].append(eid)

    all_s2s3 = {**s2_entities, **s3_entities}

    # Build true-match set for fast lookup
    true_match_set: dict[str, set[str]] = {}
    for s1_id, matches in gt.items():
        true_match_set[s1_id] = set(matches)

    negatives: list[tuple[Entity, Entity]] = []
    s1_ids = list(s1_entities.keys())
    rng.shuffle(s1_ids)

    attempts = 0
    max_attempts = n_negatives * 20

    for s1_id in s1_ids:
        if len(negatives) >= n_negatives:
            break
        s1_ent = s1_entities[s1_id]
        country = s1_ent.country.strip().lower()
        candidates = country_to_s2s3.get(country, [])
        if not candidates:
            continue

        true_matches = true_match_set.get(s1_id, set())

        # Try to find a hard negative from same country
        for _ in range(10):
            attempts += 1
            if attempts > max_attempts:
                break
            neg_id = rng.choice(candidates)
            if neg_id not in true_matches and neg_id in all_s2s3:
                negatives.append((s1_ent, all_s2s3[neg_id]))
                break

        if attempts > max_attempts:
            break

    return negatives


# ---------------------------------------------------------------------------
# Experiment runner
# ---------------------------------------------------------------------------

@dataclass
class ExpResult:
    name: str
    field: str  # "name" or "address"
    metric: str
    n_pairs: int
    mean: float
    median: float
    exact_match_rate: float
    pct_improved: float
    pct_worse: float
    pct_unchanged: float


def compute_stats(
    scores: list[float],
    baseline_scores: list[float] | None = None,
) -> dict:
    n = len(scores)
    if n == 0:
        return {"mean": 0, "median": 0, "exact_rate": 0,
                "pct_improved": 0, "pct_worse": 0, "pct_unchanged": 100}

    sorted_scores = sorted(scores)
    mean_val = sum(scores) / n
    median_val = sorted_scores[n // 2] if n % 2 == 1 else (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2
    exact_rate = sum(1 for s in scores if s >= 0.9999) / n * 100

    if baseline_scores is not None and len(baseline_scores) == n:
        improved = sum(1 for s, b in zip(scores, baseline_scores) if s > b + 1e-9)
        worse = sum(1 for s, b in zip(scores, baseline_scores) if s < b - 1e-9)
        unchanged = n - improved - worse
        pct_improved = improved / n * 100
        pct_worse = worse / n * 100
        pct_unchanged = unchanged / n * 100
    else:
        pct_improved = 0
        pct_worse = 0
        pct_unchanged = 100

    return {
        "mean": mean_val,
        "median": median_val,
        "exact_rate": exact_rate,
        "pct_improved": pct_improved,
        "pct_worse": pct_worse,
        "pct_unchanged": pct_unchanged,
    }


def _build_transform_cache(
    pairs: list[tuple[Entity, Entity]],
    transform_fn,
    field: str,
) -> dict[str, str]:
    """Pre-compute transforms for all unique entities in pairs."""
    cache: dict[str, str] = {}
    for s1_ent, other_ent in pairs:
        for ent in (s1_ent, other_ent):
            eid = ent.entity_id
            if eid not in cache:
                raw = getattr(ent, field)
                cache[eid] = transform_fn(raw)
    return cache


def run_name_experiments(
    pairs: list[tuple[Entity, Entity]],
    label: str,
) -> list[dict]:
    """Run all name experiments on a list of entity pairs."""
    transforms = {
        "A_current": transform_current_name,
        "B_lower_punct": transform_lower_punct,
        "C_unicode_accent": transform_unicode_accent,
        "D_legal_std": transform_legal_std,
        "E_token_sort": transform_token_norm,
        "F_combined": transform_combined,
    }

    results = []
    baseline_jaccard = None
    baseline_char = None

    for exp_name, transform_fn in transforms.items():
        print(f"    Computing {exp_name}...", flush=True)
        cache = _build_transform_cache(pairs, transform_fn, "business_name")

        jaccard_scores = []
        char_scores = []
        exact_scores = []

        for s1_ent, other_ent in pairs:
            n1 = cache[s1_ent.entity_id]
            n2 = cache[other_ent.entity_id]
            jaccard_scores.append(token_jaccard(n1, n2))
            char_scores.append(char_similarity(n1, n2))
            exact_scores.append(exact_match(n1, n2))

        if exp_name == "A_current":
            baseline_jaccard = jaccard_scores[:]
            baseline_char = char_scores[:]

        jac_stats = compute_stats(jaccard_scores, baseline_jaccard)
        char_stats = compute_stats(char_scores, baseline_char)
        exact_stats = compute_stats(exact_scores)

        results.append({
            "experiment": exp_name,
            "pair_type": label,
            "field": "name",
            "n_pairs": len(pairs),
            "jaccard_mean": round(jac_stats["mean"], 5),
            "jaccard_median": round(jac_stats["median"], 5),
            "char_sim_mean": round(char_stats["mean"], 5),
            "char_sim_median": round(char_stats["median"], 5),
            "exact_match_pct": round(exact_stats["exact_rate"], 3),
            "jaccard_pct_improved": round(jac_stats["pct_improved"], 3),
            "jaccard_pct_worse": round(jac_stats["pct_worse"], 3),
            "jaccard_pct_unchanged": round(jac_stats["pct_unchanged"], 3),
            "char_pct_improved": round(char_stats["pct_improved"], 3),
            "char_pct_worse": round(char_stats["pct_worse"], 3),
            "char_pct_unchanged": round(char_stats["pct_unchanged"], 3),
        })

    return results


def _build_addr_transform_cache(
    pairs: list[tuple[Entity, Entity]],
    transform_fn,
) -> dict[str, str]:
    """Pre-compute address transforms for all unique entities."""
    cache: dict[str, str] = {}
    for s1_ent, other_ent in pairs:
        for ent in (s1_ent, other_ent):
            eid = ent.entity_id
            if eid not in cache:
                cache[eid] = transform_fn(ent)
    return cache


def run_address_experiments(
    pairs: list[tuple[Entity, Entity]],
    label: str,
) -> list[dict]:
    """Run all address experiments on a list of entity pairs."""

    results = []
    baseline_jaccard = None
    baseline_char = None

    experiments = [
        ("A_current", lambda ent: addr_current(ent.business_address)),
        ("B_lower_punct", lambda ent: addr_lower_punct(ent.business_address)),
        ("C_whitespace", lambda ent: addr_whitespace(ent.business_address)),
        ("D_abbrev", lambda ent: addr_abbrev(ent.business_address, ent.country)),
        ("E_numeric", lambda ent: addr_numeric(ent.business_address)),
        ("F_token_set", lambda ent: addr_token_set(ent.business_address)),
    ]

    for exp_name, transform_fn in experiments:
        print(f"    Computing {exp_name}...", flush=True)
        cache = _build_addr_transform_cache(pairs, transform_fn)

        jaccard_scores = []
        char_scores = []
        exact_scores = []
        numeric_scores = []

        for s1_ent, other_ent in pairs:
            a1 = cache[s1_ent.entity_id]
            a2 = cache[other_ent.entity_id]
            jaccard_scores.append(token_jaccard(a1, a2))
            char_scores.append(char_similarity(a1, a2))
            exact_scores.append(exact_match(a1, a2))
            numeric_scores.append(numeric_overlap(a1, a2))

        if exp_name == "A_current":
            baseline_jaccard = jaccard_scores[:]
            baseline_char = char_scores[:]

        jac_stats = compute_stats(jaccard_scores, baseline_jaccard)
        char_stats = compute_stats(char_scores, baseline_char)
        exact_stats = compute_stats(exact_scores)
        num_stats = compute_stats(numeric_scores)

        results.append({
            "experiment": exp_name,
            "pair_type": label,
            "field": "address",
            "n_pairs": len(pairs),
            "jaccard_mean": round(jac_stats["mean"], 5),
            "jaccard_median": round(jac_stats["median"], 5),
            "char_sim_mean": round(char_stats["mean"], 5),
            "char_sim_median": round(char_stats["median"], 5),
            "exact_match_pct": round(exact_stats["exact_rate"], 3),
            "numeric_overlap_mean": round(num_stats["mean"], 5),
            "jaccard_pct_improved": round(jac_stats["pct_improved"], 3),
            "jaccard_pct_worse": round(jac_stats["pct_worse"], 3),
            "jaccard_pct_unchanged": round(jac_stats["pct_unchanged"], 3),
            "char_pct_improved": round(char_stats["pct_improved"], 3),
            "char_pct_worse": round(char_stats["pct_worse"], 3),
            "char_pct_unchanged": round(char_stats["pct_unchanged"], 3),
        })

    return results


# ---------------------------------------------------------------------------
# Example collection
# ---------------------------------------------------------------------------

def collect_name_examples(
    pairs: list[tuple[Entity, Entity]],
    transforms: dict[str, callable],
    baseline_fn: callable,
    n_help: int = 10,
    n_hurt: int = 10,
) -> tuple[list[dict], list[dict]]:
    """Collect name examples where transforms help or hurt vs baseline."""
    helps = []
    hurts = []

    for s1_ent, other_ent in pairs:
        if len(helps) >= n_help and len(hurts) >= n_hurt:
            break
        v1_raw = s1_ent.business_name
        v2_raw = other_ent.business_name
        base1 = baseline_fn(v1_raw)
        base2 = baseline_fn(v2_raw)
        base_sim = token_jaccard(base1, base2)

        for tname, tfn in transforms.items():
            t1 = tfn(v1_raw)
            t2 = tfn(v2_raw)
            new_sim = token_jaccard(t1, t2)
            diff = new_sim - base_sim

            if diff > 0.05 and len(helps) < n_help:
                helps.append({
                    "s1_id": s1_ent.entity_id,
                    "other_id": other_ent.entity_id,
                    "s1_value": v1_raw,
                    "other_value": v2_raw,
                    "transform": tname,
                    "s1_transformed": t1,
                    "other_transformed": t2,
                    "baseline_sim": round(base_sim, 4),
                    "new_sim": round(new_sim, 4),
                    "delta": round(diff, 4),
                })
            elif diff < -0.05 and len(hurts) < n_hurt:
                hurts.append({
                    "s1_id": s1_ent.entity_id,
                    "other_id": other_ent.entity_id,
                    "s1_value": v1_raw,
                    "other_value": v2_raw,
                    "transform": tname,
                    "s1_transformed": t1,
                    "other_transformed": t2,
                    "baseline_sim": round(base_sim, 4),
                    "new_sim": round(new_sim, 4),
                    "delta": round(diff, 4),
                })

    return helps, hurts


def collect_addr_examples(
    pairs: list[tuple[Entity, Entity]],
    transforms: dict[str, callable],
    baseline_fn: callable,
    n_help: int = 10,
    n_hurt: int = 10,
) -> tuple[list[dict], list[dict]]:
    """Collect address examples where transforms help or hurt vs baseline."""
    helps = []
    hurts = []

    for s1_ent, other_ent in pairs:
        if len(helps) >= n_help and len(hurts) >= n_hurt:
            break
        v1_raw = s1_ent.business_address
        v2_raw = other_ent.business_address
        base1 = baseline_fn(v1_raw)
        base2 = baseline_fn(v2_raw)
        base_sim = token_jaccard(base1, base2)

        for tname, tfn in transforms.items():
            t1 = tfn(v1_raw)
            t2 = tfn(v2_raw)
            new_sim = token_jaccard(t1, t2)
            diff = new_sim - base_sim

            if diff > 0.05 and len(helps) < n_help:
                helps.append({
                    "s1_id": s1_ent.entity_id,
                    "other_id": other_ent.entity_id,
                    "s1_value": v1_raw,
                    "other_value": v2_raw,
                    "transform": tname,
                    "s1_transformed": t1,
                    "other_transformed": t2,
                    "baseline_sim": round(base_sim, 4),
                    "new_sim": round(new_sim, 4),
                    "delta": round(diff, 4),
                })
            elif diff < -0.05 and len(hurts) < n_hurt:
                hurts.append({
                    "s1_id": s1_ent.entity_id,
                    "other_id": other_ent.entity_id,
                    "s1_value": v1_raw,
                    "other_value": v2_raw,
                    "transform": tname,
                    "s1_transformed": t1,
                    "other_transformed": t2,
                    "baseline_sim": round(base_sim, 4),
                    "new_sim": round(new_sim, 4),
                    "delta": round(diff, 4),
                })

    return helps, hurts


# ---------------------------------------------------------------------------
# Country consistency check
# ---------------------------------------------------------------------------

def check_country_consistency(
    pairs: list[tuple[Entity, Entity]],
) -> dict:
    """Check country normalization consistency between matched pairs."""
    same_raw = 0
    same_normalized = 0
    total = len(pairs)
    mismatches = []

    for s1_ent, other_ent in pairs:
        c1_raw = s1_ent.country.strip()
        c2_raw = other_ent.country.strip()
        c1_norm = c1_raw.lower()
        c2_norm = c2_raw.lower()

        if c1_raw == c2_raw:
            same_raw += 1
        if c1_norm == c2_norm:
            same_normalized += 1
        else:
            if len(mismatches) < 20:
                mismatches.append((s1_ent.entity_id, other_ent.entity_id, c1_raw, c2_raw))

    return {
        "total_pairs": total,
        "same_raw": same_raw,
        "same_raw_pct": round(same_raw / total * 100, 2) if total > 0 else 0,
        "same_normalized": same_normalized,
        "same_normalized_pct": round(same_normalized / total * 100, 2) if total > 0 else 0,
        "mismatches": mismatches,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    tracemalloc.start()
    t_start = time.perf_counter()
    rng = random.Random(RANDOM_SEED)

    print(f"=== Normalization Experiments ===")
    print(f"Sample: first {SAMPLE_S1:,} S1 entities from training ground truth\n")

    # Step 1: Load ground truth
    print("Loading ground truth...")
    gt = load_ground_truth(SAMPLE_S1)
    print(f"  Loaded {len(gt):,} S1 -> match mappings")

    # Collect needed IDs
    s1_ids_needed = set(gt.keys())
    s2_ids_needed = set()
    s3_ids_needed = set()
    for matches in gt.values():
        for m in matches:
            if m.startswith("S2-"):
                s2_ids_needed.add(m)
            elif m.startswith("S3-"):
                s3_ids_needed.add(m)

    total_pairs = sum(len(v) for v in gt.values())
    print(f"  Total true match pairs: {total_pairs:,}")
    print(f"  S2 IDs needed: {len(s2_ids_needed):,}")
    print(f"  S3 IDs needed: {len(s3_ids_needed):,}")

    # Step 2: Load entities
    print("\nLoading S1 entities...")
    s1_entities = load_entities_by_id(S1_FILE, s1_ids_needed.copy())
    print(f"  Loaded {len(s1_entities):,} S1 entities")

    print("Loading S2 entities...")
    s2_entities = load_entities_by_id(S2_FILE, s2_ids_needed.copy())
    print(f"  Loaded {len(s2_entities):,} S2 entities")

    print("Loading S3 entities...")
    s3_entities = load_entities_by_id(S3_FILE, s3_ids_needed.copy())
    print(f"  Loaded {len(s3_entities):,} S3 entities")

    all_other = {**s2_entities, **s3_entities}

    # Step 3: Build true-match pairs
    print("\nBuilding true-match pairs...")
    true_pairs: list[tuple[Entity, Entity]] = []
    missing_count = 0
    for s1_id, matched_ids in gt.items():
        if s1_id not in s1_entities:
            missing_count += 1
            continue
        s1_ent = s1_entities[s1_id]
        for m_id in matched_ids:
            if m_id in all_other:
                true_pairs.append((s1_ent, all_other[m_id]))
            else:
                missing_count += 1

    print(f"  True pairs assembled: {len(true_pairs):,}")
    if missing_count > 0:
        print(f"  Missing entities (skipped): {missing_count}")

    # Step 4: Sample hard negatives
    print("\nSampling hard negatives (same country, not a match)...")
    n_neg = min(50_000, len(true_pairs))
    neg_pairs = sample_hard_negatives(
        s1_entities, s2_entities, s3_entities, gt, n_neg, rng
    )
    print(f"  Hard negative pairs: {len(neg_pairs):,}")

    # Step 5: Run name experiments
    print("\n--- PART 1: Name Experiments ---")

    print("  Running on true matches...")
    name_true_results = run_name_experiments(true_pairs, "true_match")
    for r in name_true_results:
        print(f"    {r['experiment']:20s} jaccard={r['jaccard_mean']:.4f}  "
              f"char={r['char_sim_mean']:.4f}  exact={r['exact_match_pct']:.1f}%  "
              f"improved={r['jaccard_pct_improved']:.1f}%  "
              f"worse={r['jaccard_pct_worse']:.1f}%")

    print("  Running on non-matches...")
    name_neg_results = run_name_experiments(neg_pairs, "non_match")
    for r in name_neg_results:
        print(f"    {r['experiment']:20s} jaccard={r['jaccard_mean']:.4f}  "
              f"char={r['char_sim_mean']:.4f}  exact={r['exact_match_pct']:.1f}%")

    # Step 6: Run address experiments
    print("\n--- PART 2: Address Experiments ---")

    print("  Running on true matches...")
    addr_true_results = run_address_experiments(true_pairs, "true_match")
    for r in addr_true_results:
        print(f"    {r['experiment']:20s} jaccard={r['jaccard_mean']:.4f}  "
              f"char={r['char_sim_mean']:.4f}  exact={r['exact_match_pct']:.1f}%  "
              f"numeric={r['numeric_overlap_mean']:.4f}  "
              f"improved={r['jaccard_pct_improved']:.1f}%  "
              f"worse={r['jaccard_pct_worse']:.1f}%")

    print("  Running on non-matches...")
    addr_neg_results = run_address_experiments(neg_pairs, "non_match")
    for r in addr_neg_results:
        print(f"    {r['experiment']:20s} jaccard={r['jaccard_mean']:.4f}  "
              f"char={r['char_sim_mean']:.4f}  exact={r['exact_match_pct']:.1f}%  "
              f"numeric={r['numeric_overlap_mean']:.4f}")

    # Step 7: Country consistency
    print("\n--- PART 4: Country Consistency ---")
    country_stats = check_country_consistency(true_pairs)
    print(f"  Raw match: {country_stats['same_raw_pct']:.1f}%")
    print(f"  Normalized match: {country_stats['same_normalized_pct']:.1f}%")
    if country_stats['mismatches']:
        print(f"  Sample mismatches (first 10):")
        for s1id, oid, c1, c2 in country_stats['mismatches'][:10]:
            print(f"    {s1id} ({c1}) vs {oid} ({c2})")

    # Step 8: Collect examples
    print("\nCollecting help/hurt examples for names...")
    name_transforms = {
        "D_legal_std": transform_legal_std,
        "E_token_sort": transform_token_norm,
    }
    name_helps, name_hurts = collect_name_examples(
        true_pairs[:50000],
        name_transforms,
        transform_current_name,
    )
    print(f"  Name helps: {len(name_helps)}, hurts: {len(name_hurts)}")

    print("Collecting help/hurt examples for addresses...")
    addr_transforms_ex = {
        "D_abbrev": lambda v: addr_abbrev(v, ""),
        "F_token_set": addr_token_set,
    }
    addr_helps, addr_hurts = collect_addr_examples(
        true_pairs[:50000],
        addr_transforms_ex,
        addr_current,
    )
    print(f"  Address helps: {len(addr_helps)}, hurts: {len(addr_hurts)}")

    # Step 9: Write CSV
    csv_path = os.path.join(OUTPUT_DIR, "normalization_experiments.csv")
    print(f"\nWriting CSV to {csv_path}")

    all_results = name_true_results + name_neg_results + addr_true_results + addr_neg_results
    if all_results:
        fieldnames = list(all_results[0].keys())
        # Union of all keys
        for r in all_results:
            for k in r.keys():
                if k not in fieldnames:
                    fieldnames.append(k)

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in all_results:
                writer.writerow(r)
        print(f"  Wrote {len(all_results)} result rows")

    # Step 10: Timing and memory
    elapsed = time.perf_counter() - t_start
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"\n=== Summary ===")
    print(f"  Total runtime: {elapsed:.1f}s")
    print(f"  True pairs evaluated: {len(true_pairs):,}")
    print(f"  Negative pairs evaluated: {len(neg_pairs):,}")
    print(f"  Peak memory: {peak_mem / (1024*1024):.1f} MB")

    # Step 11: Write analysis report
    report_path = os.path.join(OUTPUT_DIR, "normalization_analysis.md")
    print(f"\nWriting analysis to {report_path}")

    _write_report(
        report_path,
        gt, true_pairs, neg_pairs,
        name_true_results, name_neg_results,
        addr_true_results, addr_neg_results,
        country_stats,
        name_helps, name_hurts,
        addr_helps, addr_hurts,
        elapsed, peak_mem,
    )

    print("\nDone.")


def _write_report(
    path: str,
    gt, true_pairs, neg_pairs,
    name_true, name_neg,
    addr_true, addr_neg,
    country_stats,
    name_helps, name_hurts,
    addr_helps, addr_hurts,
    elapsed, peak_mem,
):
    with open(path, "w", encoding="utf-8") as f:
        w = f.write

        w("# Normalization Experiment Results\n\n")
        w(f"**Date:** 2026-09-26\n")
        w(f"**Runtime:** {elapsed:.1f}s\n")
        w(f"**Peak memory:** {peak_mem / (1024*1024):.1f} MB\n\n")

        # Section 1
        w("## 1. Dataset and Sample\n\n")
        w(f"- **Source:** `database/student_resource/dataset/train/`\n")
        w(f"- **S1 entities sampled:** {len(gt):,} (first {SAMPLE_S1:,} from ground truth)\n")
        w(f"- **Ground truth file:** `train_ground_truth.tsv`\n")
        w(f"- **Random seed:** {RANDOM_SEED}\n\n")

        # Section 2
        w("## 2. Pair Counts\n\n")
        w(f"- **True match pairs evaluated:** {len(true_pairs):,}\n")
        w(f"- **Hard negative pairs evaluated:** {len(neg_pairs):,}\n")
        w(f"- Hard negatives: same country, not a ground-truth match\n\n")

        # Section 3 & 4: Name experiments
        w("## 3. Name Experiment Results (True Matches)\n\n")
        w("| Experiment | Jaccard Mean | Jaccard Median | Char Sim Mean | Char Sim Median | Exact % | Jaccard Improved % | Jaccard Worse % | Jaccard Unchanged % |\n")
        w("|---|---|---|---|---|---|---|---|---|\n")
        for r in name_true:
            w(f"| {r['experiment']} | {r['jaccard_mean']:.4f} | {r['jaccard_median']:.4f} "
              f"| {r['char_sim_mean']:.4f} | {r['char_sim_median']:.4f} "
              f"| {r['exact_match_pct']:.1f} | {r['jaccard_pct_improved']:.1f} "
              f"| {r['jaccard_pct_worse']:.1f} | {r['jaccard_pct_unchanged']:.1f} |\n")

        w("\n## 4. Name Experiment Results (Non-Matches)\n\n")
        w("| Experiment | Jaccard Mean | Jaccard Median | Char Sim Mean | Exact % |\n")
        w("|---|---|---|---|---|\n")
        for r in name_neg:
            w(f"| {r['experiment']} | {r['jaccard_mean']:.4f} | {r['jaccard_median']:.4f} "
              f"| {r['char_sim_mean']:.4f} | {r['exact_match_pct']:.1f} |\n")

        # Discrimination analysis
        w("\n## 5. Name Discrimination Analysis\n\n")
        w("| Experiment | True Jaccard Mean | Non-Match Jaccard Mean | Gap | True Char Mean | Non-Match Char Mean | Gap |\n")
        w("|---|---|---|---|---|---|---|\n")
        for rt, rn in zip(name_true, name_neg):
            jac_gap = rt['jaccard_mean'] - rn['jaccard_mean']
            char_gap = rt['char_sim_mean'] - rn['char_sim_mean']
            w(f"| {rt['experiment']} | {rt['jaccard_mean']:.4f} | {rn['jaccard_mean']:.4f} "
              f"| {jac_gap:+.4f} | {rt['char_sim_mean']:.4f} | {rn['char_sim_mean']:.4f} "
              f"| {char_gap:+.4f} |\n")

        # Address experiments
        w("\n## 6. Address Experiment Results (True Matches)\n\n")
        w("| Experiment | Jaccard Mean | Jaccard Median | Char Sim Mean | Exact % | Numeric Overlap | Jaccard Improved % | Jaccard Worse % |\n")
        w("|---|---|---|---|---|---|---|---|\n")
        for r in addr_true:
            w(f"| {r['experiment']} | {r['jaccard_mean']:.4f} | {r['jaccard_median']:.4f} "
              f"| {r['char_sim_mean']:.4f} | {r['exact_match_pct']:.1f} "
              f"| {r.get('numeric_overlap_mean', 'N/A')} "
              f"| {r['jaccard_pct_improved']:.1f} | {r['jaccard_pct_worse']:.1f} |\n")

        w("\n## 7. Address Experiment Results (Non-Matches)\n\n")
        w("| Experiment | Jaccard Mean | Jaccard Median | Char Sim Mean | Exact % | Numeric Overlap |\n")
        w("|---|---|---|---|---|---|\n")
        for r in addr_neg:
            w(f"| {r['experiment']} | {r['jaccard_mean']:.4f} | {r['jaccard_median']:.4f} "
              f"| {r['char_sim_mean']:.4f} | {r['exact_match_pct']:.1f} "
              f"| {r.get('numeric_overlap_mean', 'N/A')} |\n")

        # Address discrimination
        w("\n## 8. Address Discrimination Analysis\n\n")
        w("| Experiment | True Jaccard Mean | Non-Match Jaccard Mean | Gap | True Char Mean | Non-Match Char Mean | Gap |\n")
        w("|---|---|---|---|---|---|---|\n")
        for rt, rn in zip(addr_true, addr_neg):
            jac_gap = rt['jaccard_mean'] - rn['jaccard_mean']
            char_gap = rt['char_sim_mean'] - rn['char_sim_mean']
            w(f"| {rt['experiment']} | {rt['jaccard_mean']:.4f} | {rn['jaccard_mean']:.4f} "
              f"| {jac_gap:+.4f} | {rt['char_sim_mean']:.4f} | {rn['char_sim_mean']:.4f} "
              f"| {char_gap:+.4f} |\n")

        # Collision analysis
        w("\n## 9. Collision Analysis (PART 3)\n\n")
        w("For each name experiment, we compare the true-match vs non-match similarity distributions.\n")
        w("A good transformation increases the **gap** between true and non-match similarity.\n")
        w("A dangerous transformation increases non-match similarity more than true-match similarity.\n\n")

        w("### Name: True-Match vs Non-Match Jaccard\n\n")
        baseline_gap = None
        for rt, rn in zip(name_true, name_neg):
            gap = rt['jaccard_mean'] - rn['jaccard_mean']
            if rt['experiment'] == 'A_current':
                baseline_gap = gap
                w(f"- **{rt['experiment']}**: gap = {gap:.4f} (BASELINE)\n")
            else:
                delta = gap - baseline_gap if baseline_gap else 0
                verdict = "WIDER (good)" if delta > 0.001 else "NARROWER (risky)" if delta < -0.001 else "UNCHANGED"
                w(f"- **{rt['experiment']}**: gap = {gap:.4f} ({delta:+.4f} vs baseline) — {verdict}\n")

        w("\n### Address: True-Match vs Non-Match Jaccard\n\n")
        baseline_gap = None
        for rt, rn in zip(addr_true, addr_neg):
            gap = rt['jaccard_mean'] - rn['jaccard_mean']
            if rt['experiment'] == 'A_current':
                baseline_gap = gap
                w(f"- **{rt['experiment']}**: gap = {gap:.4f} (BASELINE)\n")
            else:
                delta = gap - baseline_gap if baseline_gap else 0
                verdict = "WIDER (good)" if delta > 0.001 else "NARROWER (risky)" if delta < -0.001 else "UNCHANGED"
                w(f"- **{rt['experiment']}**: gap = {gap:.4f} ({delta:+.4f} vs baseline) — {verdict}\n")

        # Examples
        w("\n## 10. Examples Where Transformations Help\n\n")
        if name_helps:
            w("### Name Examples\n\n")
            for ex in name_helps[:10]:
                w(f"- **{ex['s1_id']}** vs **{ex['other_id']}** [{ex['transform']}]\n")
                w(f"  - S1: `{ex['s1_value']}` -> `{ex['s1_transformed']}`\n")
                w(f"  - Other: `{ex['other_value']}` -> `{ex['other_transformed']}`\n")
                w(f"  - Jaccard: {ex['baseline_sim']:.4f} -> {ex['new_sim']:.4f} ({ex['delta']:+.4f})\n\n")
        if addr_helps:
            w("### Address Examples\n\n")
            for ex in addr_helps[:10]:
                w(f"- **{ex['s1_id']}** vs **{ex['other_id']}** [{ex['transform']}]\n")
                w(f"  - S1: `{ex['s1_value']}` -> `{ex['s1_transformed']}`\n")
                w(f"  - Other: `{ex['other_value']}` -> `{ex['other_transformed']}`\n")
                w(f"  - Jaccard: {ex['baseline_sim']:.4f} -> {ex['new_sim']:.4f} ({ex['delta']:+.4f})\n\n")

        w("\n## 11. Examples Where Transformations Hurt\n\n")
        if name_hurts:
            w("### Name Examples\n\n")
            for ex in name_hurts[:10]:
                w(f"- **{ex['s1_id']}** vs **{ex['other_id']}** [{ex['transform']}]\n")
                w(f"  - S1: `{ex['s1_value']}` -> `{ex['s1_transformed']}`\n")
                w(f"  - Other: `{ex['other_value']}` -> `{ex['other_transformed']}`\n")
                w(f"  - Jaccard: {ex['baseline_sim']:.4f} -> {ex['new_sim']:.4f} ({ex['delta']:+.4f})\n\n")
        if addr_hurts:
            w("### Address Examples\n\n")
            for ex in addr_hurts[:10]:
                w(f"- **{ex['s1_id']}** vs **{ex['other_id']}** [{ex['transform']}]\n")
                w(f"  - S1: `{ex['s1_value']}` -> `{ex['s1_transformed']}`\n")
                w(f"  - Other: `{ex['other_value']}` -> `{ex['other_transformed']}`\n")
                w(f"  - Jaccard: {ex['baseline_sim']:.4f} -> {ex['new_sim']:.4f} ({ex['delta']:+.4f})\n\n")

        # Country
        w("\n## 12. Country Consistency (PART 4)\n\n")
        w(f"- **Raw country match rate:** {country_stats['same_raw_pct']:.1f}%\n")
        w(f"- **Normalized (lowercase) match rate:** {country_stats['same_normalized_pct']:.1f}%\n")
        if country_stats['mismatches']:
            w(f"- **Mismatches found:** {len(country_stats['mismatches'])}\n")
            w("\n| S1 ID | Other ID | S1 Country | Other Country |\n")
            w("|---|---|---|---|\n")
            for s1id, oid, c1, c2 in country_stats['mismatches'][:20]:
                w(f"| {s1id} | {oid} | {c1} | {c2} |\n")
        else:
            w("- **No country mismatches** in true-match pairs.\n")

        # Safe transforms
        w("\n## 13. Safe Transformations\n\n")
        w("Based on the discrimination analysis, the following are safe to consider:\n\n")
        w("*(This section will be populated after reviewing the quantitative results above.)*\n")
        w("*(Look for transformations where: true-match similarity improves AND gap widens or stays the same.)*\n\n")

        # Unsafe transforms
        w("\n## 14. Transformations That Should NOT Be Added\n\n")
        w("*(This section will be populated after reviewing the quantitative results above.)*\n")
        w("*(Look for transformations where: gap narrows, or non-match similarity increases more than true-match.)*\n\n")

        # Recommendations
        w("\n## 15. Recommendations for Production Normalizer\n\n")
        w("*(Final recommendations based on all quantitative evidence above. To be filled after results are generated.)*\n\n")

        # Runtime
        w("\n## Appendix: Runtime Statistics\n\n")
        w(f"- **Total runtime:** {elapsed:.1f}s\n")
        w(f"- **True pairs evaluated:** {len(true_pairs):,}\n")
        w(f"- **Negative pairs evaluated:** {len(neg_pairs):,}\n")
        w(f"- **Peak memory:** {peak_mem / (1024*1024):.1f} MB\n")
        w(f"- **Sample:** First {SAMPLE_S1:,} S1 entities from ground truth\n")
        w(f"- **Random seed:** {RANDOM_SEED}\n")


if __name__ == "__main__":
    main()
