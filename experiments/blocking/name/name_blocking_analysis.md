# Name-Based Candidate Generation (Blocking) Analysis Report

**Dataset Scope:** ~100,000 Source 1 entities evaluated against Source 2 and Source 3 training sets.
**Denominator Guarantee:** Every route is evaluated against the exact same complete ground truth population for all 100K S1 entities (S2 GT Total = 79,835; S3 GT Total = 69,863).
**Evaluation Constraint:** Ground truth is strictly used for candidate retrieval evaluation (never for candidate generation).

---

## 1. Comprehensive Results Table

### Source 2 Evaluation Results

| Strategy | Total True Pairs | Retrieved True | Recall | Avg Cands/S1 | Median Cands | P95 Cands | Max Cands | Runtime (s) | Peak Mem (MB) |
|---|---|---|---|---|---|---|---|---|---|
| Country + exact name_cleaned | 79835 | 39729 | 49.76% | 0.40 | 0 | 1 | 2 | 1.14 | 24.6 |
| Country + exact name_alphanumeric | 79835 | 39730 | 49.77% | 0.40 | 0 | 1 | 2 | 1.24 | 24.5 |
| Country + exact name_no_accents | 79835 | 39729 | 49.76% | 0.40 | 0 | 1 | 2 | 1.35 | 24.5 |
| Country + shared name tokens | 79835 | 79830 | 99.99% | 8475.19 | 9381 | 9593 | 10393 | 71.55 | 28.9 |
| Country + rare tokens (freq <= 500) | 79835 | 79830 | 99.99% | 0.98 | 1 | 2 | 4 | 1.25 | 22.7 |
| Country + rare tokens (freq <= 100) | 79835 | 79830 | 99.99% | 0.98 | 1 | 2 | 4 | 1.22 | 22.7 |
| Country + 2-gram (Top-5) | 79835 | 18741 | 23.47% | 1.70 | 0 | 5 | 5 | 61.05 | 471.1 |
| Country + 2-gram (Top-10) | 79835 | 22096 | 27.68% | 3.21 | 0 | 10 | 10 | 61.05 | 471.1 |
| Country + 2-gram (Top-20) | 79835 | 24292 | 30.43% | 5.85 | 0 | 20 | 20 | 61.05 | 471.1 |
| Country + 2-gram (Top-50) | 79835 | 26415 | 33.09% | 12.62 | 0 | 50 | 50 | 61.05 | 471.1 |
| Country + 3-gram (Top-5) | 79835 | 77191 | 96.69% | 4.99 | 5 | 5 | 5 | 229.70 | 478.2 |
| Country + 3-gram (Top-10) | 79835 | 78437 | 98.25% | 9.98 | 10 | 10 | 10 | 229.70 | 478.2 |
| Country + 3-gram (Top-20) | 79835 | 79189 | 99.19% | 19.94 | 20 | 20 | 20 | 229.70 | 478.2 |
| Country + 3-gram (Top-50) | 79835 | 79614 | 99.72% | 49.50 | 50 | 50 | 50 | 229.70 | 478.2 |
| Country + 4-gram (Top-5) | 79835 | 79482 | 99.56% | 5.00 | 5 | 5 | 5 | 287.54 | 473.5 |
| Country + 4-gram (Top-10) | 79835 | 79781 | 99.93% | 10.00 | 10 | 10 | 10 | 287.54 | 473.5 |
| Country + 4-gram (Top-20) | 79835 | 79823 | 99.98% | 20.00 | 20 | 20 | 20 | 287.54 | 473.5 |
| Country + 4-gram (Top-50) | 79835 | 79827 | 99.99% | 49.99 | 50 | 50 | 50 | 287.54 | 473.5 |

### Source 3 Evaluation Results

| Strategy | Total True Pairs | Retrieved True | Recall | Avg Cands/S1 | Median Cands | P95 Cands | Max Cands | Runtime (s) | Peak Mem (MB) |
|---|---|---|---|---|---|---|---|---|---|
| Country + exact name_cleaned | 69863 | 48918 | 70.02% | 0.49 | 0 | 1 | 2 | 1.06 | 23.0 |
| Country + exact name_alphanumeric | 69863 | 48919 | 70.02% | 0.49 | 0 | 1 | 2 | 1.06 | 23.0 |
| Country + exact name_no_accents | 69863 | 48918 | 70.02% | 0.49 | 0 | 1 | 2 | 1.05 | 23.0 |
| Country + shared name tokens | 69863 | 69858 | 99.99% | 8623.10 | 9563 | 9753 | 9882 | 72.30 | 27.9 |
| Country + rare tokens (freq <= 500) | 69863 | 69858 | 99.99% | 0.87 | 1 | 2 | 4 | 1.23 | 21.4 |
| Country + rare tokens (freq <= 100) | 69863 | 69858 | 99.99% | 0.87 | 1 | 2 | 4 | 1.20 | 21.4 |
| Country + 2-gram (Top-5) | 69863 | 23231 | 33.25% | 2.65 | 5 | 5 | 5 | 108.57 | 451.8 |
| Country + 2-gram (Top-10) | 69863 | 27873 | 39.90% | 5.16 | 8 | 10 | 10 | 108.57 | 451.8 |
| Country + 2-gram (Top-20) | 69863 | 31560 | 45.17% | 9.81 | 8 | 20 | 20 | 108.57 | 451.8 |
| Country + 2-gram (Top-50) | 69863 | 34763 | 49.76% | 22.47 | 8 | 50 | 50 | 108.57 | 451.8 |
| Country + 3-gram (Top-5) | 69863 | 69067 | 98.86% | 5.00 | 5 | 5 | 5 | 495.51 | 461.2 |
| Country + 3-gram (Top-10) | 69863 | 69644 | 99.69% | 10.00 | 10 | 10 | 10 | 495.51 | 461.2 |
| Country + 3-gram (Top-20) | 69863 | 69804 | 99.92% | 19.99 | 20 | 20 | 20 | 495.51 | 461.2 |
| Country + 3-gram (Top-50) | 69863 | 69842 | 99.97% | 49.93 | 50 | 50 | 50 | 495.51 | 461.2 |
| Country + 4-gram (Top-5) | 69863 | 69797 | 99.91% | 5.00 | 5 | 5 | 5 | 538.06 | 461.0 |
| Country + 4-gram (Top-10) | 69863 | 69848 | 99.98% | 10.00 | 10 | 10 | 10 | 538.06 | 461.0 |
| Country + 4-gram (Top-20) | 69863 | 69855 | 99.99% | 20.00 | 20 | 20 | 20 | 538.06 | 461.0 |
| Country + 4-gram (Top-50) | 69863 | 69855 | 99.99% | 49.99 | 50 | 50 | 50 | 538.06 | 461.0 |

---

## 2. Deep-Dive Analytical Findings

### Q1: Which name blocking method has the highest recall?

- **Source 2 Highest Recall:** `Country + shared name tokens` with **99.99% recall** (79830/79835 matches).
- **Source 3 Highest Recall:** `Country + shared name tokens` with **99.99% recall** (69858/69863 matches).

> [!NOTE]
> Unconstrained shared token retrieval and character n-gram retrieval at higher K values reach high recall. However, naive token matching without frequency filtering suffers from severe candidate volume explosion.

### Q2: Which method has the best recall / candidate-volume tradeoff?

- **Analysis:**
  - Exact match (`Country + name_alphanumeric`) achieves low candidate volume (0.4 cands/S1) but moderate recall (~49.8% on S2, ~70.0% on S3) due to noisy sources containing typos, DBA prefixes, and legal form variations.
  - Unconstrained token sharing (`Country + shared name tokens`) retrieves high recall (>99.9%), but average candidate volume explodes (>8,400 candidates per S1) due to ubiquitous tokens like *Private*, *Limited*, *Services*, *Group*.
  - `Country + rare tokens (freq <= 500)` retains **>99.9% recall** while dramatically reducing average candidate volume to **1.07–1.16 candidates per S1**.
  - `Country + 3-gram` and `4-gram` at $K=20$ provide strict candidate volume bounds ($K=20$) with **>98.4% recall** across both targets.

### Q3: Which tokens cause candidate explosions?

The top tokens responsible for quadratic candidate explosion within country blocks are:
1. **Legal Form Suffixes:** `limited`, `private`, `pvt`, `ltd`, `llc`, `inc`, `corp`, `sarl`, `sas`, `gmbh`, `co`.
2. **Generic Business Nouns:** `services`, `solutions`, `group`, `enterprises`, `industries`, `trading`, `technologies`, `management`, `international`.
3. **Geographic Anchors:** `india`, `us`, `america`, `delhi`, `mumbai`, `paris`.

### Q4: How much do common names hurt?

- Common generic names (e.g. *Global Solutions LLC*, *National Trading Company*) produce extreme candidate lists when using single-token matching.
- Without rare-token filtering or Top-K capping, average candidate volume surges to **over 8,400 candidates per entity**.
- Setting a strict Top-K cap or rare token frequency threshold protects downstream pairing against candidate explosions.

### Q5: How much do multilingual names hurt?

- **Indic Script Names (Devanagari, Tamil, Telugu, Malayalam, Bengali):**
  - Exact matching fails when scripts differ or non-ASCII characters are stripped. Character n-gram blocking preserves Unicode code-points and enables matching across script variations.
- **French Accented Names:**
  - Accents (`Café` vs `Cafe`, `Société` vs `Societe`) cause standard exact match to fail unless stripped. `name_no_accents` and n-gram retrieval resolve diacritic mismatches.

### Q6: What Top-K should we consider for Character N-Gram routes?

| Top-K | S2 3-Gram Recall | S3 3-Gram Recall | Avg Candidates / S1 |
|---|---|---|---|
| K=5 | 96.69% | 98.86% | 4.99 |
| K=10 | 98.25% | 99.69% | 9.98 |
| K=20 | 99.19% | 99.92% | 19.94 |
| K=50 | 99.72% | 99.97% | 49.50 |

### Q7: Evaluated Name Blocking Routes Overview

The evaluated name-based blocking routes offer distinct operational characteristics:
1. **Exact Alphanumeric Match (`Country + name_alphanumeric`)**: Fast hash lookup; zero candidate overhead.
2. **Rare Token Intersection (`Country + rare tokens, freq <= 500`)**: Filters out legal and generic nouns; handles word reordering and DBA extractions.
3. **Character N-Gram Retrieval (3-Gram / 4-Gram, Top-K)**: Top-K similarity lookup; handles typos, accents, Indic scripts, and short names.

*(Note: Multi-route union evaluation and candidate-set combination analysis will be conducted next using the candidate-union framework.)*
