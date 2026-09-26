"""
Token-overlap blocking experiment — evaluate shared-token retrieval routes.

Routes (all use a df-filtered index; see token_blocking_run.log for why):
    1. token_overlap_min1_maxdf1k      (tokens with df > 1k dropped)
    2. token_overlap_min2_maxdf1k
    3. token_overlap_min2_maxdf5k
    4. token_overlap_min2_maxdf20k
    5. union_alnum_token_min2_maxdf5k  (exact alnum + route 3)

The first run of this experiment stalled on unfiltered min_overlap=1:
median df is 1, but corporate-suffix tokens ("limited", "private", "llc",
"inc") have posting lists of ~1M entities, and max_df=50k only dropped
65 keys — so every S1 entity unions million-element postings. Lower max_df
thresholds bound posting size at query time.

Usage:
    python experiments/blocking/run_token_blocking.py
"""

from __future__ import annotations

import csv
import io
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from blocking.base import Entity, load_ground_truth, DATA_DIR, DELIMITER
from blocking.exact_blocking import (
    build_country_name_alphanumeric_index,
    retrieve_by_country_name_alphanumeric,
)
from blocking.token_blocking import (
    build_country_token_index,
    filter_index_by_df,
    retrieve_by_token_overlap,
    top_tokens_by_df,
    df_percentiles,
)
from blocking.candidate_union import candidate_union
from blocking.evaluate_blocking import evaluate_blocking, BlockingResult
from preprocessing.normalize import normalize_name, normalize_country


# ---------------------------------------------------------------------------
# Loaders (same pattern as run_blocking.py — name + country only)
# ---------------------------------------------------------------------------

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
    """Load entities normalizing only name + country (skip address)."""
    entities: dict[str, Entity] = {}
    with open(filepath, encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split(DELIMITER)
            if len(parts) < 4:
                continue
            eid, raw_name, raw_country = parts[0], parts[1], parts[3]
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
MAX_DF_SWEEP = (1_000, 5_000, 20_000)
TRAIN_DIR = os.path.join(DATA_DIR, "train")

S1_FILE = os.path.join(TRAIN_DIR, "train_source1.tsv")
S2_FILE = os.path.join(TRAIN_DIR, "train_source2.tsv")
S3_FILE = os.path.join(TRAIN_DIR, "train_source3.tsv")
GT_FILE = os.path.join(TRAIN_DIR, "train_ground_truth.tsv")

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def _get_process_memory_mb() -> float:
    """Get current process peak RSS in MB (Windows + Unix)."""
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

    print("=== Token-Overlap Blocking Experiment ===")
    print(f"Sample: first {SAMPLE_S1:,} S1 entities")
    print(f"max_df sweep: {MAX_DF_SWEEP}\n")

    # ------------------------------------------------------------------
    # Step 1: Load ground truth
    # ------------------------------------------------------------------
    print("Loading ground truth...", flush=True)
    t0 = time.perf_counter()
    gt = load_ground_truth(GT_FILE, limit=SAMPLE_S1)
    print(f"  {len(gt):,} S1 entries, {time.perf_counter()-t0:.1f}s")

    s1_ids_needed = set(gt.keys())
    total_gt = sum(len(v) for v in gt.values())
    print(f"  Total GT pairs: {total_gt:,}")

    # ------------------------------------------------------------------
    # Step 2: Load S1 (GT only) + full S2/S3 pools
    # ------------------------------------------------------------------
    print("\nLoading S1 entities...", flush=True)
    t0 = time.perf_counter()
    s1_entities = load_blocking_keys_needed(S1_FILE, s1_ids_needed)
    print(f"  {len(s1_entities):,} loaded, {time.perf_counter()-t0:.1f}s")

    print("Loading S2 entities (blocking keys only)...", flush=True)
    t0 = time.perf_counter()
    s2_entities = load_blocking_keys_only(S2_FILE)
    print(f"  {len(s2_entities):,} loaded, {time.perf_counter()-t0:.1f}s")

    print("Loading S3 entities (blocking keys only)...", flush=True)
    t0 = time.perf_counter()
    s3_entities = load_blocking_keys_only(S3_FILE)
    print(f"  {len(s3_entities):,} loaded, {time.perf_counter()-t0:.1f}s")

    all_s2s3 = {**s2_entities, **s3_entities}
    print(f"\nMemory after load: {_get_process_memory_mb():.1f} MB")

    # ------------------------------------------------------------------
    # Step 3: Build (country, token) index — single pass, unfiltered
    # ------------------------------------------------------------------
    print("\n--- Building Token Index ---", flush=True)
    t0 = time.perf_counter()
    token_idx = build_country_token_index(all_s2s3)
    print(f"  {len(token_idx):,} (country, token) keys, {time.perf_counter()-t0:.1f}s")
    print(f"  Memory: {_get_process_memory_mb():.1f} MB")

    # df distribution analysis
    stats = df_percentiles(token_idx)
    print("\n--- Token DF Distribution ---")
    print(f"  Keys: {stats['keys']:,}")
    print(f"  Median df: {stats['median']:.0f}")
    print(f"  P90 df: {stats['p90']:,}  P95: {stats['p95']:,}  P99: {stats['p99']:,}")
    print(f"  Max df: {stats['max']:,}")
    print(f"  Total postings: {stats['total_postings']:,}")

    top_tokens = top_tokens_by_df(token_idx, top_n=30)
    print(f"\n  Top 30 tokens by df:")
    print(f"  {'Country':<10} {'DF':>10}  Token")
    print(f"  {'-'*10} {'-'*10}  {'-'*40}")
    for t in top_tokens:
        print(f"  {t['country']:<10} {t['df']:>10,}  {t['token'][:40]}")

    # ------------------------------------------------------------------
    # Step 4: df-filtered views (postings shared, not copied)
    # ------------------------------------------------------------------
    token_idx_by_df: dict[int, dict] = {}
    for max_df in MAX_DF_SWEEP:
        print(f"\n--- Filtering Index (max_df={max_df:,}) ---", flush=True)
        t0 = time.perf_counter()
        token_idx_by_df[max_df] = filter_index_by_df(token_idx, max_df=max_df)
        kept = len(token_idx_by_df[max_df])
        dropped = len(token_idx) - kept
        print(f"  Kept {kept:,} keys, dropped {dropped:,} "
              f"({dropped/max(len(token_idx),1)*100:.2f}%), {time.perf_counter()-t0:.2f}s")

    # ------------------------------------------------------------------
    # Step 5: Exact-alphanumeric index (for union route)
    # ------------------------------------------------------------------
    print("\n--- Building Exact Alphanumeric Index ---", flush=True)
    t0 = time.perf_counter()
    name_alnum_idx = build_country_name_alphanumeric_index(all_s2s3)
    print(f"  {len(name_alnum_idx):,} keys, {time.perf_counter()-t0:.1f}s")

    # ------------------------------------------------------------------
    # Step 6: Evaluate routes
    # ------------------------------------------------------------------
    print("\n--- Evaluating Token-Overlap Routes ---", flush=True)
    results: list[BlockingResult] = []

    def _run(name, fn):
        print(f"\n{name}...", flush=True)
        t0 = time.perf_counter()
        r = evaluate_blocking(name, s1_entities, gt, fn)
        r.runtime_s = time.perf_counter() - t0
        results.append(r)
        _print_result(r)
        return r

    def _run_token(name, index, min_overlap):
        return _run(
            name,
            lambda ent: retrieve_by_token_overlap(ent, index, min_overlap=min_overlap),
        )

    _run_token("token_overlap_min1_maxdf1k", token_idx_by_df[1_000], min_overlap=1)
    _run_token("token_overlap_min2_maxdf1k", token_idx_by_df[1_000], min_overlap=2)
    _run_token("token_overlap_min2_maxdf5k", token_idx_by_df[5_000], min_overlap=2)
    _run_token("token_overlap_min2_maxdf20k", token_idx_by_df[20_000], min_overlap=2)
    _run(
        "union_alnum_token_min2_maxdf5k",
        lambda ent: candidate_union(ent, [
            lambda e: retrieve_by_country_name_alphanumeric(e, name_alnum_idx),
            lambda e: retrieve_by_token_overlap(e, token_idx_by_df[5_000], min_overlap=2),
        ]),
    )

    # ------------------------------------------------------------------
    # Step 7: Write CSV results
    # ------------------------------------------------------------------
    csv_path = os.path.join(OUTPUT_DIR, "token_blocking_results.csv")
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
    # Step 8: Write analysis report
    # ------------------------------------------------------------------
    elapsed_total = time.perf_counter() - t_total
    peak_mem_mb = _get_process_memory_mb()

    report_path = os.path.join(OUTPUT_DIR, "token_blocking_analysis.md")
    print(f"\nWriting report: {report_path}", flush=True)
    _write_report(
        report_path, results, stats, top_tokens,
        len(token_idx), token_idx_by_df,
        len(s1_entities), len(s2_entities), len(s3_entities),
        elapsed_total, peak_mem_mb,
    )

    print("\n=== Done ===")
    print(f"  Total runtime: {elapsed_total:.1f}s")
    print(f"  Peak memory: {peak_mem_mb:.1f} MB")


def _print_result(r: BlockingResult):
    print(f"  S1 evaluated: {r.s1_evaluated:,}")
    print(f"  GT: S2={r.gt_s2_matches:,} S3={r.gt_s3_matches:,}")
    print(f"  Retrieved: S2={r.retrieved_s2:,} S3={r.retrieved_s3:,}")
    print(f"  Recall: S2={r.s2_recall:.4f} S3={r.s3_recall:.4f} overall={r.overall_recall:.4f}")
    print(f"  Entity full coverage: {r.entity_full_coverage:.4f}")
    print(f"  Candidates: avg={r.avg_candidates:.1f} median={r.median_candidates:.0f} "
          f"p95={r.p95_candidates:.0f} max={r.max_candidates:,}")
    print(f"  Runtime: {r.runtime_s:.2f}s", flush=True)


def _load_core_baseline() -> dict[str, dict]:
    """Read-only load of core_blocking_results.csv for comparison."""
    path = os.path.join(OUTPUT_DIR, "core_blocking_results.csv")
    rows: dict[str, dict] = {}
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows[row["route_name"]] = row
    return rows


def _write_report(
    path, results, stats, top_tokens,
    n_keys, token_idx_by_df,
    n_s1, n_s2, n_s3, elapsed, peak_mem,
):
    baseline = _load_core_baseline()

    with open(path, "w", encoding="utf-8") as f:
        w = f.write

        w("# Token-Overlap Blocking Experiment Results\n\n")
        w("**Date:** 2026-09-26\n")
        w(f"**Runtime:** {elapsed:.1f}s\n")
        w(f"**Peak memory:** {peak_mem:.1f} MB\n")
        w(f"**S1 entities evaluated:** {n_s1:,}\n")
        w(f"**S2 entities loaded:** {n_s2:,}\n")
        w(f"**S3 entities loaded:** {n_s3:,}\n\n")

        # 1. Token index & df distribution
        w("## 1. Token Index and DF Distribution\n\n")
        w(f"- **(country, token) keys:** {n_keys:,}\n")
        for max_df, idx in token_idx_by_df.items():
            kept = len(idx)
            w(f"- **Keys after max_df={max_df:,}:** {kept:,} "
              f"(dropped {n_keys - kept:,}, "
              f"{(n_keys - kept)/max(n_keys,1)*100:.2f}%)\n")
        w(f"- **Median df:** {stats['median']:.0f}\n")
        w(f"- **P90 df:** {stats['p90']:,} | **P95:** {stats['p95']:,} | "
          f"**P99:** {stats['p99']:,}\n")
        w(f"- **Max df:** {stats['max']:,}\n")
        w(f"- **Total postings:** {stats['total_postings']:,}\n\n")

        # 2. Top tokens
        w("## 2. Top 30 Tokens by Document Frequency\n\n")
        w("| Rank | Country | DF | Token |\n")
        w("|---|---|---|---|\n")
        for i, t in enumerate(top_tokens, 1):
            w(f"| {i} | {t['country']} | {t['df']:,} | {t['token'][:50]} |\n")
        w("\n")
        if top_tokens:
            top = top_tokens[0]
            w(f"The most frequent token `{top['token']}` ({top['country']}) appears in "
              f"**{top['df']:,}** records. Any S1 entity carrying this token pulls "
              f"the entire posting list as candidates under min_overlap=1 — "
              f"this is why a max_df filter matters.\n\n")

        # 3. Route results
        w("## 3. Route Results\n\n")
        w("| Route | Recall | S2 Rec | S3 Rec | Full Cov | Avg Cands | Median | P95 | Max |\n")
        w("|---|---|---|---|---|---|---|---|---|\n")
        for r in results:
            w(f"| {r.route_name} | {r.overall_recall:.4f} | {r.s2_recall:.4f} | "
              f"{r.s3_recall:.4f} | {r.entity_full_coverage:.4f} | "
              f"{r.avg_candidates:,.1f} | {r.median_candidates:,.0f} | "
              f"{r.p95_candidates:,.0f} | {r.max_candidates:,} |\n")
        w("\n")

        # 4. Comparison vs exact baseline
        w("## 4. Comparison vs Exact-Name Baseline\n\n")
        if baseline:
            w("| Route | Recall | Avg Cands | Source |\n")
            w("|---|---|---|---|\n")
            for name in ("country_name_cleaned", "country_name_alphanumeric"):
                if name in baseline:
                    b = baseline[name]
                    w(f"| {name} | {float(b['overall_recall']):.4f} | "
                      f"{float(b['avg_candidates']):,.1f} | core experiment |\n")
            for r in results:
                w(f"| {r.route_name} | {r.overall_recall:.4f} | "
                  f"{r.avg_candidates:,.1f} | this experiment |\n")
            w("\n")
            if "country_name_alphanumeric" in baseline:
                base_rec = float(baseline["country_name_alphanumeric"]["overall_recall"])
                best = max(results, key=lambda r: r.overall_recall)
                w(f"Best token route (`{best.route_name}`) recall = "
                  f"**{best.overall_recall:.4f}** vs exact-alphanumeric baseline "
                  f"**{base_rec:.4f}** — "
                  f"{'+' if best.overall_recall >= base_rec else ''}"
                  f"{(best.overall_recall - base_rec)*100:.2f} percentage points.\n\n")
        else:
            w("*(core_blocking_results.csv not found — baseline comparison skipped)*\n\n")

        # 5. Per-route interpretation
        w("## 5. Observations\n\n")
        for r in results:
            w(f"- **{r.route_name}:** recall {r.overall_recall:.4f}, "
              f"avg {r.avg_candidates:,.1f} candidates, "
              f"p95 {r.p95_candidates:,.0f}, max {r.max_candidates:,}, "
              f"runtime {r.runtime_s:.1f}s\n")
        w("\n")

        # 6. Runtime
        w("## 6. Runtime and Memory\n\n")
        w(f"- **Total runtime:** {elapsed:.1f}s\n")
        w(f"- **Peak memory:** {peak_mem:.1f} MB\n\n")
        w("| Route | Runtime |\n")
        w("|---|---|\n")
        for r in results:
            w(f"| {r.route_name} | {r.runtime_s:.2f}s |\n")
        w("\n")

        # 7. Recommendations
        w("## 7. Recommendations for Next Steps\n\n")
        w("*(To be filled after reviewing quantitative results)*\n\n")
        w("Candidate follow-ups: n-gram blocking (character-level typos), "
          "address-assisted blocking, phonetic keys, and DBA-aware splitting. "
          "Route-union contribution analysis can quantify how much each token "
          "route adds on top of exact-name blocking.\n")


if __name__ == "__main__":
    main()
