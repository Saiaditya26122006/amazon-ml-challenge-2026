# Token-Overlap Blocking Experiment — COMPLETE

**Date**: 2026-09-26  
**Status**: ✅ COMPLETE  
**Runtime**: 706.5s (~12 minutes)  
**Evaluation**: VERIFIED CORRECT

---

## Files Inspected/Changed

### Inspected (Freebuff's work):
- ✅ `src/blocking/token_blocking.py` — Token-overlap implementation (135 lines)
- ✅ `tests/test_token_blocking.py` — 31 tests (ALL PASSING)
- ✅ `experiments/blocking/run_token_blocking.py` — Experiment script (473 lines)
- ✅ `src/blocking/__init__.py` — Exports added
- ✅ `src/blocking/evaluate_blocking.py` — Evaluation logic (verified correct)

### Created by experiment:
- ✅ `experiments/blocking/token_blocking_results.csv`
- ✅ `experiments/blocking/token_blocking_analysis.md`
- ✅ `experiments/blocking/token_blocking_run.log`

### Changed:
- **NONE** — No code changes made, only ran the experiment

---

## Exact Command Used

```bash
cd "C:\Users\TALLURI SAI ADITYA\OneDrive\Desktop\projects\ML challenge dataset"
python experiments/blocking/run_token_blocking.py
```

---

## Evaluation Verification

### ✅ VERIFIED CORRECT

**Checked**:
1. ✅ **Same GT denominator across all routes**:
   - Core blocking: `gt_s2=167,009`, `gt_s3=178,988`, `s1_evaluated=94,406`
   - Token blocking: `gt_s2=167,009`, `gt_s3=178,988`, `s1_evaluated=94,406`
   - **All routes evaluated against identical GT population**

2. ✅ **No denominator manipulation**:
   - `evaluate_blocking()` iterates over `s1_entities` and accumulates GT counts
   - Denominators are fixed for all routes (lines 57-72, 96-98 in `evaluate_blocking.py`)

3. ✅ **Country partitioning applied**:
   - Index keys are `(country, token)` tuples
   - Retrieval only looks up `(s1_entity.country_cleaned, token)`
   - No cross-country candidates

4. ✅ **Duplicate candidates removed**:
   - `retrieve_by_token_overlap()` returns a `set[str]`
   - Automatic deduplication

5. ✅ **GT never used during candidate generation**:
   - Token index built from full S2/S3 pools (lines 207-208)
   - Retrieval uses only token index, not ground truth
   - GT only used in evaluation (lines 66-85 of `evaluate_blocking.py`)

6. ✅ **DF filtering working correctly**:
   - `max_df=1,000`: dropped 2,992 keys (0.20%)
   - `max_df=5,000`: dropped 828 keys (0.06%)
   - `max_df=20,000`: dropped 296 keys (0.02%)
   - Postings shared (not copied) — efficient

7. ✅ **No silent candidate caps or filtering**:
   - All candidates returned by retrieval are evaluated
   - No post-retrieval filtering

---

## Results Summary

### Evaluation Population

- **S1 entities evaluated**: 94,406
- **S2 entities in pool**: 5,034,616
- **S3 entities in pool**: 5,285,603
- **Total S2+S3**: 10,320,219
- **Total GT pairs**: 345,997 (S2: 167,009 | S3: 178,988)

### Token Index Statistics

- **(country, token) keys**: 1,483,762
- **Median df**: 1
- **P90 df**: 4 | **P95**: 15 | **P99**: 143
- **Max df**: 1,233,380 (token: "limited", country: "india")
- **Total postings**: 37,023,660

**Top problematic tokens** (corporate suffixes):
- `limited` (india): 1,233,380 entities
- `private` (india): 1,196,119 entities
- `llc` (us): 1,099,621 entities
- `inc` (us): 846,946 entities
- `ltd` (india): 648,418 entities

These tokens appear in so many entities that `min_overlap=1` without df filtering would generate millions of candidates.

### Route Results

| Route | Overall Recall | S2 Recall | S3 Recall | Avg Cands | Median | P95 | Max | Runtime |
|---|---|---|---|---|---|---|---|---|
| **token_overlap_min1_maxdf1k** | **0.4387** | 0.4404 | 0.4370 | 138.3 | 0 | 724 | 3,241 | 1.7s |
| token_overlap_min2_maxdf1k | 0.0881 | 0.0883 | 0.0879 | 1.2 | 0 | 5 | 860 | 5.4s |
| token_overlap_min2_maxdf5k | 0.2410 | 0.2420 | 0.2400 | 6.4 | 0 | 14 | 2,910 | 41.8s |
| token_overlap_min2_maxdf20k | 0.4044 | 0.4009 | 0.4076 | 182.8 | 2 | 274 | 18,887 | 326.7s |
| **union_alnum_token_min2_maxdf5k** | **0.4107** | 0.4066 | 0.4145 | **16.9** | 3 | 79 | 2,910 | 67.1s |

### Comparison vs Exact-Name Baseline

| Route | Overall Recall | Source |
|---|---|---|
| country_name_cleaned | 0.1565 | core experiment |
| country_name_alphanumeric | 0.2561 | core experiment |
| **token_overlap_min1_maxdf1k** | **0.4387** | token experiment |
| **union_alnum_token_min2_maxdf5k** | **0.4107** | token experiment |

**Best token route gain**: +18.25 percentage points vs exact-alphanumeric baseline.

---

## Important Findings

### 1. Token-overlap significantly outperforms exact-match blocking

- **Exact alphanumeric**: 0.2561 recall
- **Token min1 max_df=1k**: 0.4387 recall (**+71% relative improvement**)
- **Union alnum + token**: 0.4107 recall

Token-overlap captures ~70% more true pairs than exact matching.

### 2. min_overlap vs max_df tradeoff

**min_overlap=1** (any shared token):
- High recall (0.4387)
- High candidate volume (avg 138, max 3,241)
- Requires aggressive df filtering (max_df=1k)
- Fast (1.7s)

**min_overlap=2** (at least 2 shared tokens):
- Lower recall (0.0881-0.4044 depending on max_df)
- Lower candidate volume (avg 1.2-182.8)
- Less sensitive to df filtering
- Slower (5.4s-326.7s depending on max_df)

**Tradeoff**: min1 gets more recall with controlled volume, min2 requires higher max_df to recover recall but generates more candidates.

### 3. Union route is the practical winner

**union_alnum_token_min2_maxdf5k**:
- Recall: 0.4107 (93.6% of best token route)
- Avg candidates: 16.9 (8.2× fewer than min1)
- P95 candidates: 79 (9.1× fewer than min1)
- Max candidates: 2,910 (same as standalone token route)
- Runtime: 67.1s (reasonable)

This union:
- Captures exact matches efficiently (alphanumeric)
- Recovers fuzzy matches (token-overlap with min2)
- Keeps candidate volume practical
- **Recommended for production**

### 4. median=0 indicates many S1 entities retrieve nothing

For all token routes, `median_candidates=0` or close to 0.

This means:
- ~50% of S1 entities retrieve ZERO candidates from token-overlap alone
- These entities either:
  - Have no name tokens (empty names)
  - Have only high-df tokens (filtered out)
  - Have tokens not present in S2/S3 within their country
- **This is why the union with exact-match is crucial** — exact-match covers many entities that token-overlap misses

### 5. S2 vs S3 recall is balanced

All routes show similar recall for S2 and S3:
- S2 recall: 0.088-0.440
- S3 recall: 0.088-0.437
- Difference: < 1 percentage point

No systematic bias toward either source.

### 6. Entity full coverage is low

Even the best route (`token_overlap_min1_maxdf1k`) has:
- **Entity full coverage: 0.3302**

This means only 33% of S1 entities with GT matches retrieve ALL their true matches.

Remaining 67% retrieve some but not all matches — indicating:
- Name variations (typos, abbreviations, reorderings)
- Partial name matches
- Need for additional blocking routes (address, phonetic, n-gram)

### 7. Corporate suffix tokens dominate high-df keys

Top 10 tokens are all corporate suffixes:
- limited, private, llc, inc, ltd, pvt, लिमिटेड, center, partners, com

These tokens appear in >100k-1M entities each.

Without df filtering, `min_overlap=1` would generate millions of candidates for any entity with these suffixes.

**Aggressive df filtering is essential for token-overlap blocking.**

### 8. Performance scales with max_df

Runtime grows dramatically with max_df:
- max_df=1k, min2: 5.4s
- max_df=5k, min2: 41.8s
- max_df=20k, min2: 326.7s

Higher max_df means:
- Larger posting lists to union
- More candidates to count/evaluate
- More true pairs retrieved (0.0881 → 0.4044)

**For production, max_df=5k with min_overlap=2 offers the best recall/speed tradeoff.**

---

## Evaluation Caveats

### 1. Sample size

- Evaluated on first 100K S1 training entities
- Only 94,406 had GT matches
- Represents ~10% of full training set
- Results may vary slightly on full dataset

### 2. No cross-dataset evaluation

- Evaluated on training set only
- No validation/test set results yet
- May overfit to training distribution

### 3. No address/numeric blocking yet

Current results are name-based blocking only:
- Exact name (cleaned, alphanumeric)
- Token-overlap name

Address-token and numeric blocking routes are still pending:
- Friend 2: address-token experiments
- Friend 1: name-variation experiments

The union recall will likely improve when these routes are added.

### 4. No parameter tuning for production

The experiment swept `max_df ∈ {1k, 5k, 20k}` and `min_overlap ∈ {1, 2}`.

Production deployment may benefit from:
- Intermediate max_df values (e.g., 2k, 3k, 10k)
- Variable min_overlap by S1 entity (e.g., min1 for short names, min2 for long names)
- Hybrid routes (min1 for rare tokens, min2 for common tokens)

### 5. No end-to-end pairwise evaluation

These are **blocking** (candidate generation) results only.

Final performance depends on:
- Pairwise comparison model quality
- Classification threshold tuning
- Production latency constraints

---

## Ready for Candidate-Union Framework

✅ **YES** — The token-blocking results are ready to feed into the candidate-union evaluation framework.

### Next Steps

1. **Import token routes into union framework**:
   ```python
   from blocking.token_blocking import build_country_token_index, filter_index_by_df, retrieve_by_token_overlap
   
   # Build indices
   token_idx = build_country_token_index(all_s2s3)
   token_idx_5k = filter_index_by_df(token_idx, max_df=5_000)
   
   # Create candidate sets
   cs_exact = build_candidate_set("exact_alnum", s1_entities, exact_retriever)
   cs_token = build_candidate_set("token_min2_5k", s1_entities, 
       lambda ent: retrieve_by_token_overlap(ent, token_idx_5k, min_overlap=2))
   
   # Analyze union
   contrib = analyze_union_contribution([cs_exact, cs_token], ground_truth)
   print_union_contribution(contrib)
   ```

2. **Wait for Friend 1 and Friend 2 routes**:
   - Friend 1: Name-variation blocking
   - Friend 2: Address-token blocking

3. **Evaluate all route combinations**:
   - exact_name
   - token_overlap
   - address_token
   - name_variation
   - All pairs (exact+token, exact+address, token+address, ...)
   - All triples (exact+token+address, ...)
   - Full union

4. **Analyze marginal contributions**:
   - Which routes add the most unique true pairs?
   - Which routes have high overlap?
   - What is the optimal route subset?

5. **Select final blocking strategy for production**

---

## Recommendations

### For Production Deployment

**Recommended route**: `union_alnum_token_min2_maxdf5k`
- Recall: 0.4107
- Avg candidates: 16.9
- P95 candidates: 79
- Max candidates: 2,910
- Runtime: 67s (for 94K entities)

**Why this route**:
- High recall (41% of GT pairs)
- Manageable candidate volume (avg 17, p95 79)
- Captures both exact and fuzzy matches
- Fast enough for production

**For even higher recall** (if candidate volume permits):
- Use `token_overlap_min1_maxdf1k`
- Recall: 0.4387 (+2.8 pp)
- Avg candidates: 138 (8× higher)
- P95 candidates: 724 (9× higher)

**Tradeoff**: +2.8 pp recall costs 8× more candidates.

### For Next Experiments

1. **Sweep intermediate max_df values**:
   - Try max_df ∈ {2k, 3k, 7k, 10k, 15k}
   - Find optimal recall/volume point

2. **Adaptive min_overlap**:
   - Short names (1-2 tokens): use min_overlap=1
   - Long names (3+ tokens): use min_overlap=2
   - May improve recall without exploding candidates

3. **Token weighting**:
   - Downweight high-df tokens in overlap counting
   - E.g., "limited" overlap counts as 0.1, rare tokens count as 1.0
   - May improve precision

4. **Address-augmented blocking**:
   - Add address-token route from Friend 2
   - Analyze union contribution
   - May recover entities with name variations but matching addresses

---

## Summary

✅ Token-overlap blocking experiment **complete and verified correct**  
✅ **+71% relative recall improvement** vs exact-alphanumeric baseline  
✅ **union_alnum_token_min2_maxdf5k** recommended for production (0.4107 recall, 16.9 avg candidates)  
✅ Results ready for candidate-union framework  
✅ No code changes made — Freebuff's implementation is solid  
✅ No evaluation issues found — denominator consistent across all routes  

**Waiting for**:
- Friend 1: Name-variation blocking
- Friend 2: Address-token blocking

**Then**: Evaluate all route combinations using the candidate-union framework.
