"""
Core blocking experiments — evaluate exact-match blocking strategies.

Usage:
    python experiments/blocking/run_blocking.py
"""

from __future__ import annotations

import csv
import io
import os
import sys
import time
from functools import partial

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from blocking.base import (
    Entity, load_source_normalized, load_ground_truth,
    DATA_DIR,
)
from blocking.exact_blocking import (
    build_country_index,
    build_country_name_cleaned_index,
    build_country_name_alphanumeric_index,
    retrieve_by_country,
    retrieve_by_country_name_cleaned,
    retrieve_by_country_name_alphanumeric,
)
from blocking.candidate_union import candidate_union
from blocking.evaluate_blocking import (
    evaluate_blocking,
    BlockingResult,
    country_match_analysis,
    common_name_analysis,
)
from preprocessing.normalize import normalize_name, normalize_country

DELIMITER = "\t"


def load_blocking_keys_needed(filepath: str, needed_ids: set[str]) -> dict[str, Entity]:
    """Load only specific IDs, normalizing only name + country."""
    entities: dict[str, Entity] = {}
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
            entities[eid] = Entity(
                entity_id=eid,
                name_cleaned=nn.cleaned,
                name_alphanumeric=nn.alphanumeric,
                country_cleaned=nc.cleaned,
                addr_cleaned="",
                addr_alphanumeric="",
            )
            if not remaining:
                break
    return entities


def load_blocking_keys_only(filepath: str) -> dict[str, Entity]:
    """Load entities normalizing only name + country (skip address).

    Address normalization is ~50% of per-row cost and is unused by
    our current blocking keys, so skipping it halves load time.
    """
    entities: dict[str, Entity] = {}
    with open(filepath, encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split(DELIMITER)
            if len(parts) < 4:
                continue
            eid, raw_name, raw_addr, raw_country = parts[0], parts[1], parts[2], parts[3]
            nn = normalize_name(raw_name)
            nc = normalize_country(raw_country)
            entities[eid] = Entity(
                entity_id=eid,
                name_cleaned=nn.cleaned,
                name_alphanumeric=nn.alphanumeric,
                country_cleaned=nc.cleaned,
                addr_cleaned="",
                addr_alphanumeric="",
            )
    return entities

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SAMPLE_S1 = 100_000
TRAIN_DIR = os.path.join(DATA_DIR, "train")

S1_FILE = os.path.join(TRAIN_DIR, "train_source1.tsv")
S2_FILE = os.path.join(TRAIN_DIR, "train_source2.tsv")
S3_FILE = os.path.join(TRAIN_DIR, "train_source3.tsv")
GT_FILE = os.path.join(TRAIN_DIR, "train_ground_truth.tsv")

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def _get_process_memory_mb() -> float:
    """Get current process RSS in MB (Windows + Unix)."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except ImportError:
        pass
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(pmc)
        handle = kernel32.GetCurrentProcess()
        ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb)
        return pmc.PeakWorkingSetSize / (1024 * 1024)
    except Exception:
        return 0.0


def main():
    t_total = time.perf_counter()

    print("=== Core Blocking Experiments ===")
    print(f"Sample: first {SAMPLE_S1:,} S1 entities\n")

    # ------------------------------------------------------------------
    # Step 1: Load ground truth (first SAMPLE_S1 rows)
    # ------------------------------------------------------------------
    print("Loading ground truth...", flush=True)
    t0 = time.perf_counter()
    gt = load_ground_truth(GT_FILE, limit=SAMPLE_S1)
    print(f"  {len(gt):,} S1 entries, {time.perf_counter()-t0:.1f}s")

    s1_ids_needed = set(gt.keys())
    s2_ids_needed: set[str] = set()
    s3_ids_needed: set[str] = set()
    for matches in gt.values():
        for m in matches:
            if m.startswith("S2-"):
                s2_ids_needed.add(m)
            elif m.startswith("S3-"):
                s3_ids_needed.add(m)
    total_gt = sum(len(v) for v in gt.values())
    print(f"  Total GT pairs: {total_gt:,}  (S2: {len(s2_ids_needed):,}, S3: {len(s3_ids_needed):,})")

    # ------------------------------------------------------------------
    # Step 2: Load S1 entities (only those in GT, blocking keys only)
    # ------------------------------------------------------------------
    print("\nLoading S1 entities...", flush=True)
    t0 = time.perf_counter()
    s1_entities = load_blocking_keys_needed(S1_FILE, s1_ids_needed)
    print(f"  {len(s1_entities):,} loaded, {time.perf_counter()-t0:.1f}s")

    # ------------------------------------------------------------------
    # Step 3: Load ALL of S2 and S3 (for index building)
    #   We need full S2/S3 to build blocking indices — candidates come
    #   from the full pool, not just ground-truth matches.
    # ------------------------------------------------------------------
    print("\nLoading S2 entities (blocking keys only)...", flush=True)
    t0 = time.perf_counter()
    s2_entities = load_blocking_keys_only(S2_FILE)
    print(f"  {len(s2_entities):,} loaded, {time.perf_counter()-t0:.1f}s")

    print("Loading S3 entities (blocking keys only)...", flush=True)
    t0 = time.perf_counter()
    s3_entities = load_blocking_keys_only(S3_FILE)
    print(f"  {len(s3_entities):,} loaded, {time.perf_counter()-t0:.1f}s")

    all_s2s3 = {**s2_entities, **s3_entities}

    mem_after_load = _get_process_memory_mb()
    print(f"\nMemory after load: {mem_after_load:.1f} MB")

    # ------------------------------------------------------------------
    # Step 4: Country analysis
    # ------------------------------------------------------------------
    print("\n--- Country Analysis ---", flush=True)
    country_stats = country_match_analysis(s1_entities, all_s2s3, gt)
    print(f"  Total GT pairs (loaded): {country_stats['total_pairs']:,}")
    print(f"  Same country: {country_stats['same_country']:,}")
    print(f"  Different country: {country_stats['diff_country']:,}")
    if country_stats["diff_examples"]:
        print("  Examples of different-country matches:")
        for s1id, mid, c1, c2 in country_stats["diff_examples"][:10]:
            print(f"    {s1id} ({c1}) <-> {mid} ({c2})")

    # ------------------------------------------------------------------
    # Step 5: Build indices
    # ------------------------------------------------------------------
    print("\n--- Building Indices ---", flush=True)

    t0 = time.perf_counter()
    country_idx = build_country_index(all_s2s3)
    print(f"  Country index: {len(country_idx)} keys, {time.perf_counter()-t0:.1f}s")

    t0 = time.perf_counter()
    name_cleaned_idx = build_country_name_cleaned_index(all_s2s3)
    print(f"  Country+name_cleaned index: {len(name_cleaned_idx):,} keys, {time.perf_counter()-t0:.1f}s")

    t0 = time.perf_counter()
    name_alnum_idx = build_country_name_alphanumeric_index(all_s2s3)
    print(f"  Country+name_alphanumeric index: {len(name_alnum_idx):,} keys, {time.perf_counter()-t0:.1f}s")

    # ------------------------------------------------------------------
    # Step 6: Evaluate blocking routes
    # ------------------------------------------------------------------
    print("\n--- Evaluating Blocking Routes ---", flush=True)
    results: list[BlockingResult] = []

    # Route 1: Country only
    print("\nRoute 1: Country blocking...", flush=True)
    t0 = time.perf_counter()
    r1 = evaluate_blocking(
        "country_only",
        s1_entities, gt,
        lambda ent: retrieve_by_country(ent, country_idx),
    )
    r1.runtime_s = time.perf_counter() - t0
    results.append(r1)
    _print_result(r1)

    # Route 2: Country + exact name_cleaned
    print("\nRoute 2: Country + exact name_cleaned...", flush=True)
    t0 = time.perf_counter()
    r2 = evaluate_blocking(
        "country_name_cleaned",
        s1_entities, gt,
        lambda ent: retrieve_by_country_name_cleaned(ent, name_cleaned_idx),
    )
    r2.runtime_s = time.perf_counter() - t0
    results.append(r2)
    _print_result(r2)

    # Route 3: Country + exact name_alphanumeric
    print("\nRoute 3: Country + exact name_alphanumeric...", flush=True)
    t0 = time.perf_counter()
    r3 = evaluate_blocking(
        "country_name_alphanumeric",
        s1_entities, gt,
        lambda ent: retrieve_by_country_name_alphanumeric(ent, name_alnum_idx),
    )
    r3.runtime_s = time.perf_counter() - t0
    results.append(r3)
    _print_result(r3)

    # Route 4a: Union of name_cleaned + name_alphanumeric
    print("\nRoute 4a: Union (name_cleaned + name_alphanumeric)...", flush=True)
    t0 = time.perf_counter()
    r4a = evaluate_blocking(
        "union_name_cleaned_alphanumeric",
        s1_entities, gt,
        lambda ent: candidate_union(ent, [
            lambda e: retrieve_by_country_name_cleaned(e, name_cleaned_idx),
            lambda e: retrieve_by_country_name_alphanumeric(e, name_alnum_idx),
        ]),
    )
    r4a.runtime_s = time.perf_counter() - t0
    results.append(r4a)
    _print_result(r4a)

    # ------------------------------------------------------------------
    # Step 7: Common name analysis
    # ------------------------------------------------------------------
    print("\n--- Common Name Analysis ---", flush=True)
    common_names = common_name_analysis(s2_entities, s3_entities, top_n=30)
    print(f"  Top 30 most frequent (country, name_cleaned) keys:")
    print(f"  {'Country':<10} {'Count':>8}  Name")
    print(f"  {'-'*10} {'-'*8}  {'-'*40}")
    for cn in common_names:
        print(f"  {cn['country']:<10} {cn['count']:>8,}  {cn['name_cleaned'][:60]}")

    # ------------------------------------------------------------------
    # Step 8: Write CSV results
    # ------------------------------------------------------------------
    csv_path = os.path.join(OUTPUT_DIR, "core_blocking_results.csv")
    print(f"\nWriting CSV: {csv_path}", flush=True)

    fieldnames = [
        "route_name", "s1_evaluated",
        "gt_s2_matches", "gt_s3_matches",
        "retrieved_s2", "retrieved_s3",
        "s2_recall", "s3_recall", "overall_recall",
        "entity_full_coverage",
        "avg_candidates", "median_candidates", "p95_candidates", "max_candidates",
        "runtime_s",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "route_name": r.route_name,
                "s1_evaluated": r.s1_evaluated,
                "gt_s2_matches": r.gt_s2_matches,
                "gt_s3_matches": r.gt_s3_matches,
                "retrieved_s2": r.retrieved_s2,
                "retrieved_s3": r.retrieved_s3,
                "s2_recall": round(r.s2_recall, 6),
                "s3_recall": round(r.s3_recall, 6),
                "overall_recall": round(r.overall_recall, 6),
                "entity_full_coverage": round(r.entity_full_coverage, 6),
                "avg_candidates": round(r.avg_candidates, 1),
                "median_candidates": round(r.median_candidates, 1),
                "p95_candidates": round(r.p95_candidates, 1),
                "max_candidates": r.max_candidates,
                "runtime_s": round(r.runtime_s, 2),
            })
    print(f"  Wrote {len(results)} rows")

    # ------------------------------------------------------------------
    # Step 9: Write analysis report
    # ------------------------------------------------------------------
    elapsed_total = time.perf_counter() - t_total
    peak_mem_mb = _get_process_memory_mb()
    peak_mem = int(peak_mem_mb * 1024 * 1024)

    report_path = os.path.join(OUTPUT_DIR, "core_blocking_analysis.md")
    print(f"\nWriting report: {report_path}", flush=True)
    _write_report(
        report_path, results, gt, s1_entities, s2_entities, s3_entities,
        country_stats, common_names, elapsed_total, peak_mem,
    )

    print(f"\n=== Done ===")
    print(f"  Total runtime: {elapsed_total:.1f}s")
    print(f"  Peak memory: {peak_mem/(1024*1024):.1f} MB")


def _print_result(r: BlockingResult):
    print(f"  S1 evaluated: {r.s1_evaluated:,}")
    print(f"  GT: S2={r.gt_s2_matches:,} S3={r.gt_s3_matches:,}")
    print(f"  Retrieved: S2={r.retrieved_s2:,} S3={r.retrieved_s3:,}")
    print(f"  Recall: S2={r.s2_recall:.4f} S3={r.s3_recall:.4f} overall={r.overall_recall:.4f}")
    print(f"  Entity full coverage: {r.entity_full_coverage:.4f}")
    print(f"  Candidates: avg={r.avg_candidates:.1f} median={r.median_candidates:.0f} "
          f"p95={r.p95_candidates:.0f} max={r.max_candidates:,}")
    print(f"  Runtime: {r.runtime_s:.2f}s")


def _write_report(
    path, results, gt, s1_entities, s2_entities, s3_entities,
    country_stats, common_names, elapsed, peak_mem,
):
    with open(path, "w", encoding="utf-8") as f:
        w = f.write

        w("# Core Blocking Experiment Results\n\n")
        w(f"**Date:** 2026-09-26\n")
        w(f"**Runtime:** {elapsed:.1f}s\n")
        w(f"**Peak memory:** {peak_mem/(1024*1024):.1f} MB\n\n")

        # 1. Country blocking
        w("## 1. Country Blocking Recall\n\n")
        r = results[0]
        w(f"- **Overall recall:** {r.overall_recall:.4f} ({r.overall_recall*100:.2f}%)\n")
        w(f"- S2 recall: {r.s2_recall:.4f}\n")
        w(f"- S3 recall: {r.s3_recall:.4f}\n")
        w(f"- Entity full coverage: {r.entity_full_coverage:.4f}\n")
        w(f"- Avg candidates per S1: {r.avg_candidates:,.1f}\n")
        w(f"- Median candidates: {r.median_candidates:,.0f}\n")
        w(f"- P95 candidates: {r.p95_candidates:,.0f}\n")
        w(f"- Max candidates: {r.max_candidates:,}\n\n")

        w("### Country Match Verification\n\n")
        w(f"- Total GT pairs (with loaded entities): {country_stats['total_pairs']:,}\n")
        w(f"- Same country: {country_stats['same_country']:,} "
          f"({country_stats['same_country']/max(country_stats['total_pairs'],1)*100:.2f}%)\n")
        w(f"- Different country: {country_stats['diff_country']:,}\n")
        if country_stats["diff_examples"]:
            w("\n**Different-country examples:**\n\n")
            w("| S1 ID | Match ID | S1 Country | Match Country |\n")
            w("|---|---|---|---|\n")
            for s1id, mid, c1, c2 in country_stats["diff_examples"]:
                w(f"| {s1id} | {mid} | {c1} | {c2} |\n")
        else:
            w("\nNo different-country true matches found. Country blocking loses **zero** true pairs.\n")
        w("\n")

        # 2. Exact name recall
        w("## 2. Exact Name_Cleaned Recall\n\n")
        r = results[1]
        w(f"- **Overall recall:** {r.overall_recall:.4f} ({r.overall_recall*100:.2f}%)\n")
        w(f"- S2 recall: {r.s2_recall:.4f}\n")
        w(f"- S3 recall: {r.s3_recall:.4f}\n")
        w(f"- Entity full coverage: {r.entity_full_coverage:.4f}\n")
        w(f"- Avg candidates per S1: {r.avg_candidates:,.1f}\n")
        w(f"- Median candidates: {r.median_candidates:,.0f}\n")
        w(f"- P95 candidates: {r.p95_candidates:,.0f}\n")
        w(f"- Max candidates: {r.max_candidates:,}\n\n")

        # 3. Alphanumeric name recall
        w("## 3. Exact Name_Alphanumeric Recall\n\n")
        r = results[2]
        w(f"- **Overall recall:** {r.overall_recall:.4f} ({r.overall_recall*100:.2f}%)\n")
        w(f"- S2 recall: {r.s2_recall:.4f}\n")
        w(f"- S3 recall: {r.s3_recall:.4f}\n")
        w(f"- Entity full coverage: {r.entity_full_coverage:.4f}\n")
        w(f"- Avg candidates per S1: {r.avg_candidates:,.1f}\n")
        w(f"- Median candidates: {r.median_candidates:,.0f}\n")
        w(f"- P95 candidates: {r.p95_candidates:,.0f}\n")
        w(f"- Max candidates: {r.max_candidates:,}\n\n")

        # 4. Union recall
        w("## 4. Union Recall\n\n")
        r = results[3]
        w(f"- **Overall recall:** {r.overall_recall:.4f} ({r.overall_recall*100:.2f}%)\n")
        w(f"- S2 recall: {r.s2_recall:.4f}\n")
        w(f"- S3 recall: {r.s3_recall:.4f}\n")
        w(f"- Entity full coverage: {r.entity_full_coverage:.4f}\n")
        w(f"- Avg candidates per S1: {r.avg_candidates:,.1f}\n")
        w(f"- Median candidates: {r.median_candidates:,.0f}\n")
        w(f"- P95 candidates: {r.p95_candidates:,.0f}\n")
        w(f"- Max candidates: {r.max_candidates:,}\n\n")

        # 5. Candidate volume comparison
        w("## 5. Candidate Volume Statistics\n\n")
        w("| Route | Recall | Avg Cands | Median | P95 | Max |\n")
        w("|---|---|---|---|---|---|\n")
        for r in results:
            w(f"| {r.route_name} | {r.overall_recall:.4f} | {r.avg_candidates:,.1f} "
              f"| {r.median_candidates:,.0f} | {r.p95_candidates:,.0f} | {r.max_candidates:,} |\n")
        w("\n")

        # 6. S2 vs S3
        w("## 6. S2 vs S3 Comparison\n\n")
        w("| Route | S2 Recall | S3 Recall | S2 GT | S3 GT | S2 Retrieved | S3 Retrieved |\n")
        w("|---|---|---|---|---|---|---|\n")
        for r in results:
            w(f"| {r.route_name} | {r.s2_recall:.4f} | {r.s3_recall:.4f} "
              f"| {r.gt_s2_matches:,} | {r.gt_s3_matches:,} "
              f"| {r.retrieved_s2:,} | {r.retrieved_s3:,} |\n")
        w("\n")

        # 7. Common name explosion
        w("## 7. Common-Name Candidate Explosion\n\n")
        w("Top 30 most frequent `(country, name_cleaned)` keys in S2+S3:\n\n")
        w("| Rank | Country | Count | Name |\n")
        w("|---|---|---|---|\n")
        for i, cn in enumerate(common_names, 1):
            name_display = cn["name_cleaned"][:60]
            if len(cn["name_cleaned"]) > 60:
                name_display += "..."
            w(f"| {i} | {cn['country']} | {cn['count']:,} | {name_display} |\n")
        w("\n")
        if common_names:
            top = common_names[0]
            w(f"The most common name `{top['name_cleaned'][:40]}` ({top['country']}) "
              f"has **{top['count']:,}** records in S2+S3. "
              f"Any S1 entity with this exact name would generate {top['count']:,} candidates "
              f"from this key alone.\n\n")

        # 8. Runtime/memory
        w("## 8. Runtime and Memory\n\n")
        w(f"- **Total runtime:** {elapsed:.1f}s\n")
        w(f"- **Peak memory:** {peak_mem/(1024*1024):.1f} MB\n")
        w(f"- **S1 entities evaluated:** {results[0].s1_evaluated:,}\n")
        w(f"- **S2 entities loaded:** {len(s2_entities):,}\n")
        w(f"- **S3 entities loaded:** {len(s3_entities):,}\n")
        w(f"- **Total entities in memory:** {len(s1_entities) + len(s2_entities) + len(s3_entities):,}\n\n")

        w("| Route | Runtime |\n")
        w("|---|---|\n")
        for r in results:
            w(f"| {r.route_name} | {r.runtime_s:.2f}s |\n")
        w("\n")

        # 9. Recommendations
        w("## 9. Recommendations for Next Blocking Routes\n\n")
        w("*(To be filled after reviewing quantitative results)*\n\n")

        best_exact = max(results[1:], key=lambda r: r.overall_recall)
        country_r = results[0]

        w(f"**Country blocking** achieves {country_r.overall_recall:.4f} recall "
          f"but generates {country_r.avg_candidates:,.0f} avg candidates — "
          f"this is the upper bound for recall but too many candidates for pairwise comparison.\n\n")

        w(f"**Best exact-name route** (`{best_exact.route_name}`) achieves "
          f"{best_exact.overall_recall:.4f} recall with only "
          f"{best_exact.avg_candidates:,.1f} avg candidates. "
          f"This captures the easy matches with minimal candidate volume.\n\n")

        recall_gap = country_r.overall_recall - best_exact.overall_recall
        w(f"**Recall gap:** {recall_gap:.4f} ({recall_gap*100:.1f}% of true pairs) are missed "
          f"by exact-name blocking but retrievable within the same country. "
          f"These require fuzzy/token-overlap blocking to capture.\n\n")

        w("**Recommended next routes (not yet implemented):**\n\n")
        w("1. Token-overlap blocking (shared name tokens within same country)\n")
        w("2. N-gram blocking (character n-gram overlap)\n")
        w("3. Address-assisted blocking (same address tokens + country)\n")
        w("4. Phonetic blocking (Soundex/Metaphone keys)\n")
        w("5. DBA-aware blocking (split DBA names, block on each part)\n")


if __name__ == "__main__":
    main()
