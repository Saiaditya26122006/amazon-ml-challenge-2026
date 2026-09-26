# Core Blocking Experiment Results

**Date:** 2026-09-26
**Runtime:** ~1,580s (data loading dominated)
**S1 entities evaluated:** 94,406
**S2 entities loaded:** 5,034,616
**S3 entities loaded:** 5,285,603
**Total entities in memory:** 10,414,625

## 1. Country Blocking Recall

- **Overall recall:** 1.0000 (100.00%)
- S2 recall: 1.0000
- S3 recall: 1.0000
- Entity full coverage: 1.0000
- Avg candidates per S1: 5,362,121
- Median candidates: 6,186,873
- P95 candidates: 6,186,873
- Max candidates: 6,186,873

### Country Match Verification

- Total GT pairs (with loaded entities): 345,997
- Same country: 345,997 (100.00%)
- Different country: 0

No different-country true matches found. Country blocking loses **zero** true pairs. However, the dataset has only **2 distinct country values** after normalization, so country blocking provides almost no selectivity — each S1 entity retrieves either the full US or India pool.

## 2. Exact Name_Cleaned Recall

- **Overall recall:** 0.1565 (15.65%)
- S2 recall: 0.1560
- S3 recall: 0.1570
- Entity full coverage: 0.0180 (1.8%)
- Avg candidates per S1: 7.2
- Median candidates: 1
- P95 candidates: 41
- Max candidates: 378

Exact `name_cleaned` matching captures only 15.65% of true matches. This indicates that the majority of true matches have different cleaned names — consistent with noisy S2/S3 data having misspellings, abbreviations, and transliteration differences.

## 3. Exact Name_Alphanumeric Recall

- **Overall recall:** 0.2561 (25.61%)
- S2 recall: 0.2510
- S3 recall: 0.2609
- Entity full coverage: 0.0371 (3.7%)
- Avg candidates per S1: 11.2
- Median candidates: 2
- P95 candidates: 70
- Max candidates: 501

Alphanumeric normalization (removing punctuation/special chars) improves recall by **64%** relative to name_cleaned (25.61% vs 15.65%). The candidate volume increases modestly (11.2 vs 7.2 avg), which is an excellent tradeoff.

## 4. Union Recall

- **Overall recall:** 0.2561 (25.61%)
- S2 recall: 0.2510
- S3 recall: 0.2609
- Entity full coverage: 0.0371 (3.7%)
- Avg candidates per S1: 11.2
- Median candidates: 2
- P95 candidates: 70
- Max candidates: 501

The union of name_cleaned + name_alphanumeric has **identical** recall to name_alphanumeric alone. This confirms that name_alphanumeric is a strict superset of name_cleaned for blocking — every entity pair that shares an exact `name_cleaned` also shares an exact `name_alphanumeric` (since alphanumeric normalization only removes characters, it can only merge groups, never split them).

## 5. Candidate Volume Statistics

| Route | Recall | Avg Cands | Median | P95 | Max |
|---|---|---|---|---|---|
| country_only | 1.0000 | 5,362,121 | 6,186,873 | 6,186,873 | 6,186,873 |
| country_name_cleaned | 0.1565 | 7.2 | 1 | 41 | 378 |
| country_name_alphanumeric | 0.2561 | 11.2 | 2 | 70 | 501 |
| union_name_cleaned_alphanumeric | 0.2561 | 11.2 | 2 | 70 | 501 |

The median candidate count of 1-2 for exact-name routes means most S1 entities either have a single match or no match in S2/S3 by exact name. The long tail (max 378-501) represents common business names shared by many entities.

## 6. S2 vs S3 Comparison

| Route | S2 Recall | S3 Recall | S2 GT | S3 GT | S2 Retrieved | S3 Retrieved |
|---|---|---|---|---|---|---|
| country_only | 1.0000 | 1.0000 | 167,009 | 178,988 | 167,009 | 178,988 |
| country_name_cleaned | 0.1560 | 0.1570 | 167,009 | 178,988 | 26,046 | 28,102 |
| country_name_alphanumeric | 0.2510 | 0.2609 | 167,009 | 178,988 | 41,924 | 46,690 |
| union_name_cleaned_alphanumeric | 0.2510 | 0.2609 | 167,009 | 178,988 | 41,924 | 46,690 |

S2 and S3 recall are very similar across all routes (~1% difference), suggesting both sources have comparable name noise levels.

## 7. Key Observations

1. **Only 2 country values**: After normalization, the entire dataset has just 2 distinct countries (likely "us" and "india"). This makes country-only blocking useless as a standalone strategy — it provides zero selectivity.

2. **Name_alphanumeric dominates name_cleaned**: The alphanumeric variant is strictly better (64% more recall at modest candidate volume increase). This means punctuation and special character differences account for a significant fraction of exact-match failures.

3. **74.4% of true matches are NOT captured by exact name blocking**: Even the best exact strategy (name_alphanumeric) misses 74.4% of true pairs. These missed pairs require fuzzy matching strategies — the names are genuinely different between S1 and S2/S3.

4. **Extremely low entity full coverage (3.7%)**: Only 3.7% of S1 entities have ALL their true matches captured by exact name blocking. This means 96.3% of entities have at least one true match with a different name.

5. **Candidate volume is manageable**: Exact-name blocking produces very small candidate sets (median 1-2, P95 41-70), making pairwise comparison feasible. The challenge is recall, not volume.

## 8. Runtime and Memory

- **Total runtime:** ~1,580s (loading dominated by S2+S3 normalization)
- **S1 load:** 12.5s (94,406 entities, filtered from 2.2M rows)
- **S2 load:** 388.6s (5,034,616 entities, name+country normalization only)
- **S3 load:** 390.4s (5,285,603 entities, name+country normalization only)
- **Index building:** ~777s total (3 indices)
- **Route evaluation:** ~356s total (4 routes)

| Route | Runtime |
|---|---|
| country_only | 49.09s |
| country_name_cleaned | 72.70s |
| country_name_alphanumeric | 72.88s |
| union_name_cleaned_alphanumeric | 161.77s |

## 9. Recommendations for Next Blocking Routes

**Country blocking** achieves 1.0000 recall but generates 5,362,121 avg candidates — this is the upper bound for recall but too many candidates for pairwise comparison.

**Best exact-name route** (`country_name_alphanumeric`) achieves 0.2561 recall with only 11.2 avg candidates. This captures the easy matches with minimal candidate volume.

**Recall gap:** 0.7439 (74.4% of true pairs) are missed by exact-name blocking but retrievable within the same country. These require fuzzy/token-overlap blocking to capture.

**Recommended next routes (not yet implemented):**

1. **Token-overlap blocking** (shared name tokens within same country) — highest priority. Most name differences are word-level: abbreviations ("inc" vs "incorporated"), missing words, reorderings. Sharing even 1-2 tokens should dramatically increase recall.

2. **N-gram blocking** (character n-gram overlap) — captures typos and transliteration differences that token matching misses.

3. **Address-assisted blocking** (same address tokens + country) — uses address as a secondary signal. Two entities at the same address are likely the same business even with different names.

4. **Phonetic blocking** (Soundex/Metaphone keys) — captures phonetic similarities for misspelled names.

5. **DBA-aware blocking** (split "doing business as" names, block on each part) — businesses with DBA names appear under multiple names.

**Priority order**: Token-overlap > Address-assisted > N-gram > Phonetic > DBA
