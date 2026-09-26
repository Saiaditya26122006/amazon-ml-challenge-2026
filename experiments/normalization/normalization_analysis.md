# Normalization Experiment Results

**Date:** 2026-09-26
**Runtime:** 2253.5s
**Peak memory:** 209.5 MB

## 1. Dataset and Sample

- **Source:** `database/student_resource/dataset/train/`
- **S1 entities sampled:** 50,000 (first 50,000 from ground truth)
- **Ground truth file:** `train_ground_truth.tsv`
- **Random seed:** 42

## 2. Pair Counts

- **True match pairs evaluated:** 172,731
- **Hard negative pairs evaluated:** 50,000
- Hard negatives: same country, not a ground-truth match

## 3. Name Experiment Results (True Matches)

| Experiment | Jaccard Mean | Jaccard Median | Char Sim Mean | Char Sim Median | Exact % | Jaccard Improved % | Jaccard Worse % | Jaccard Unchanged % |
|---|---|---|---|---|---|---|---|---|
| A_current | 0.6407 | 0.6667 | 0.7764 | 0.8621 | 25.5 | 0.0 | 0.0 | 100.0 |
| B_lower_punct | 0.6147 | 0.6667 | 0.7701 | 0.8571 | 21.7 | 0.0 | 6.4 | 93.6 |
| C_unicode_accent | 0.6407 | 0.6667 | 0.7764 | 0.8621 | 25.5 | 0.0 | 0.0 | 100.0 |
| D_legal_std | 0.6560 | 0.6667 | 0.7746 | 0.8571 | 28.4 | 3.8 | 0.0 | 96.2 |
| E_token_sort | 0.6407 | 0.6667 | 0.7799 | 0.8636 | 31.1 | 0.0 | 0.0 | 100.0 |
| F_combined | 0.6560 | 0.6667 | 0.7746 | 0.8571 | 28.4 | 3.8 | 0.0 | 96.2 |

## 4. Name Experiment Results (Non-Matches)

| Experiment | Jaccard Mean | Jaccard Median | Char Sim Mean | Exact % |
|---|---|---|---|---|
| A_current | 0.0300 | 0.0000 | 0.1329 | 0.0 |
| B_lower_punct | 0.0291 | 0.0000 | 0.1320 | 0.0 |
| C_unicode_accent | 0.0300 | 0.0000 | 0.1329 | 0.0 |
| D_legal_std | 0.0452 | 0.0000 | 0.1609 | 0.0 |
| E_token_sort | 0.0300 | 0.0000 | 0.1344 | 0.0 |
| F_combined | 0.0452 | 0.0000 | 0.1609 | 0.0 |

## 5. Name Discrimination Analysis

| Experiment | True Jaccard Mean | Non-Match Jaccard Mean | Gap | True Char Mean | Non-Match Char Mean | Gap |
|---|---|---|---|---|---|---|
| A_current | 0.6407 | 0.0300 | +0.6108 | 0.7764 | 0.1329 | +0.6434 |
| B_lower_punct | 0.6147 | 0.0291 | +0.5855 | 0.7701 | 0.1320 | +0.6381 |
| C_unicode_accent | 0.6407 | 0.0300 | +0.6108 | 0.7764 | 0.1329 | +0.6434 |
| D_legal_std | 0.6560 | 0.0452 | +0.6108 | 0.7746 | 0.1609 | +0.6137 |
| E_token_sort | 0.6407 | 0.0300 | +0.6108 | 0.7799 | 0.1344 | +0.6456 |
| F_combined | 0.6560 | 0.0452 | +0.6108 | 0.7746 | 0.1609 | +0.6137 |

## 6. Address Experiment Results (True Matches)

| Experiment | Jaccard Mean | Jaccard Median | Char Sim Mean | Exact % | Numeric Overlap | Jaccard Improved % | Jaccard Worse % |
|---|---|---|---|---|---|---|---|
| A_current | 0.6063 | 0.6429 | 0.7811 | 8.3 | 0.73289 | 0.0 | 0.0 |
| B_lower_punct | 0.5974 | 0.6250 | 0.7812 | 8.3 | 0.73289 | 0.0 | 9.2 |
| C_whitespace | 0.3001 | 0.2500 | 0.5361 | 2.3 | 0.73289 | 2.3 | 71.3 |
| D_abbrev | 0.6612 | 0.6667 | 0.8002 | 11.7 | 0.73289 | 25.5 | 0.1 |
| E_numeric | 0.7329 | 1.0000 | 0.7806 | 61.8 | 0.73289 | 58.6 | 22.5 |
| F_token_set | 0.6063 | 0.6429 | 0.7844 | 11.8 | 0.73289 | 0.0 | 0.0 |

## 7. Address Experiment Results (Non-Matches)

| Experiment | Jaccard Mean | Jaccard Median | Char Sim Mean | Exact % | Numeric Overlap |
|---|---|---|---|---|---|
| A_current | 0.0150 | 0.0000 | 0.1652 | 0.0 | 0.01168 |
| B_lower_punct | 0.0148 | 0.0000 | 0.1653 | 0.0 | 0.01168 |
| C_whitespace | 0.0059 | 0.0000 | 0.1378 | 0.0 | 0.01168 |
| D_abbrev | 0.0192 | 0.0000 | 0.1737 | 0.0 | 0.01168 |
| E_numeric | 0.0117 | 0.0000 | 0.0397 | 0.5 | 0.01168 |
| F_token_set | 0.0150 | 0.0000 | 0.1655 | 0.0 | 0.01168 |

## 8. Address Discrimination Analysis

| Experiment | True Jaccard Mean | Non-Match Jaccard Mean | Gap | True Char Mean | Non-Match Char Mean | Gap |
|---|---|---|---|---|---|---|
| A_current | 0.6063 | 0.0150 | +0.5913 | 0.7811 | 0.1652 | +0.6159 |
| B_lower_punct | 0.5974 | 0.0148 | +0.5825 | 0.7812 | 0.1653 | +0.6160 |
| C_whitespace | 0.3001 | 0.0059 | +0.2942 | 0.5361 | 0.1378 | +0.3983 |
| D_abbrev | 0.6612 | 0.0192 | +0.6420 | 0.8002 | 0.1737 | +0.6265 |
| E_numeric | 0.7329 | 0.0117 | +0.7212 | 0.7806 | 0.0397 | +0.7409 |
| F_token_set | 0.6063 | 0.0150 | +0.5913 | 0.7844 | 0.1655 | +0.6190 |

## 9. Collision Analysis (PART 3)

For each name experiment, we compare the true-match vs non-match similarity distributions.
A good transformation increases the **gap** between true and non-match similarity.
A dangerous transformation increases non-match similarity more than true-match similarity.

### Name: True-Match vs Non-Match Jaccard

- **A_current**: gap = 0.6108 (BASELINE)
- **B_lower_punct**: gap = 0.5855 (-0.0252 vs baseline) — NARROWER (risky)
- **C_unicode_accent**: gap = 0.6108 (+0.0000 vs baseline) — UNCHANGED
- **D_legal_std**: gap = 0.6108 (+0.0000 vs baseline) — UNCHANGED
- **E_token_sort**: gap = 0.6108 (+0.0000 vs baseline) — UNCHANGED
- **F_combined**: gap = 0.6108 (+0.0000 vs baseline) — UNCHANGED

### Address: True-Match vs Non-Match Jaccard

- **A_current**: gap = 0.5913 (BASELINE)
- **B_lower_punct**: gap = 0.5825 (-0.0087 vs baseline) — NARROWER (risky)
- **C_whitespace**: gap = 0.2942 (-0.2971 vs baseline) — NARROWER (risky)
- **D_abbrev**: gap = 0.6420 (+0.0507 vs baseline) — WIDER (good)
- **E_numeric**: gap = 0.7212 (+0.1299 vs baseline) — WIDER (good)
- **F_token_set**: gap = 0.5913 (+0.0000 vs baseline) — UNCHANGED

## 10. Examples Where Transformations Help

### Name Examples

- **S1-503957000** vs **S3-555791452** [D_legal_std]
  - S1: `AP Hospitality Inc` -> `ap hospitality incorporated`
  - Other: `AP AP Hospitality Incorporated` -> `ap ap hospitality incorporated`
  - Jaccard: 0.5000 -> 1.0000 (+0.5000)

- **S1-264156494** vs **S3-562014765** [D_legal_std]
  - S1: `Diksha Technologies Private Limited` -> `diksha technologies private limited`
  - Other: `Diksha Technologies Private Ltd` -> `diksha technologies private limited`
  - Jaccard: 0.6000 -> 1.0000 (+0.4000)

- **S1-567308588** vs **S3-595927967** [D_legal_std]
  - S1: `Zander Blue Co` -> `zander blue company`
  - Other: `Zander Blue Company` -> `zander blue company`
  - Jaccard: 0.5000 -> 1.0000 (+0.5000)

- **S1-9962387** vs **S3-13637230** [D_legal_std]
  - S1: `Systel Buildstructure (India) Private Limited` -> `systel buildstructure india private limited`
  - Other: `Systel Buildstructure Buildstructure (India) Private Ltd` -> `systel buildstructure buildstructure india private limited`
  - Jaccard: 0.6667 -> 1.0000 (+0.3333)

- **S1-818149988** vs **S2-489380965** [D_legal_std]
  - S1: `Vadyne Inc` -> `vadyne incorporated`
  - Other: `Vadyne Incorporated #34301` -> `vadyne incorporated 34301`
  - Jaccard: 0.2500 -> 0.6667 (+0.4167)

- **S1-67172650** vs **S3-520282171** [D_legal_std]
  - S1: `Apar Engineering (India) Private Limited` -> `apar engineering india private limited`
  - Other: `Apar Engineering (lndia) Private Ltd` -> `apar engineering lndia private limited`
  - Jaccard: 0.4286 -> 0.6667 (+0.2381)

- **S1-957102563** vs **S2-327669113** [D_legal_std]
  - S1: `Vadodara Industries Pvt Ltd` -> `vadodara industries private limited`
  - Other: `Vadodara Industries Pvt Limited` -> `vadodara industries private limited`
  - Jaccard: 0.6000 -> 1.0000 (+0.4000)

- **S1-161556164** vs **S2-709771917** [D_legal_std]
  - S1: `ZA Buildwell Private Limited` -> `za buildwell private limited`
  - Other: `ZA Buildwell Private Ltd` -> `za buildwell private limited`
  - Jaccard: 0.6000 -> 1.0000 (+0.4000)

- **S1-652339606** vs **S3-626670274** [D_legal_std]
  - S1: `Libra Service Limited` -> `libra service limited`
  - Other: `Libra Service Ltd` -> `libra service limited`
  - Jaccard: 0.5000 -> 1.0000 (+0.5000)

- **S1-654156225** vs **S2-775493531** [D_legal_std]
  - S1: `KBM Research Private Limited` -> `kbm research private limited`
  - Other: `Private KBM Research Ltd` -> `private kbm research limited`
  - Jaccard: 0.6000 -> 1.0000 (+0.4000)


### Address Examples (abbreviation expansion)

- **S1-102811957** vs **S2-478959098** [D_abbrev, US]
  - S1: `3315 Fremont Street, Peoria, IL` -> `3315 fremont street peoria il`
  - Other: `3315 FREMONT ST, PEORIA, IL` -> `3315 fremont street peoria il`
  - Jaccard: 0.6667 -> 1.0000 (+0.3333) — "ST" expanded to "street" creates exact match

- **S1-965667** vs **S3-11291185** [D_abbrev, US]
  - S1: `85 Wayne Avenue, Ticonderoga, NY` -> `85 wayne avenue ticonderoga ny`
  - Other: `Wayne Ave, Ticonderoga Townshiip, New York` -> `wayne avenue ticonderoga townshiip new york`
  - Jaccard: 0.2222 -> 0.3750 (+0.1528) — "Ave" expanded to "avenue"

- **S1-864861607** vs **S2-755275021** [D_abbrev, India]
  - S1: `H No- 94. Rd No-2, Chitra Takiyapar, Digha Road, Digha, Patna, Bihar` -> `h number 94 road number 2 chitra takiyapar digha road digha patna bihar`
  - Other: `PATNA, H NO- 94.. RD NO-2, Bihar, PATNA, null` -> `patna h number 94 road number 2 bihar patna`
  - Jaccard: 0.6364 -> 0.7000 (+0.0636) — "No" -> "number", "Rd" -> "road"

## 11. Examples Where Transformations Hurt

### Name Examples

- **S1-18526471** vs **S3-665674137** [D_legal_std]
  - S1: `Baus Corporation Corp` -> `baus corporation corporation`
  - Other: `BAUS CORPORATION CORP | www.bauscorpo.com` -> `baus corporation corporation www bauscorpo com`
  - Jaccard: 0.5000 -> 0.4000 (-0.1000)

- **S1-439499349** vs **S3-523495730** [D_legal_std]
  - S1: `Shree & Co Company` -> `shree company company`
  - Other: `Sri Shree & Có Company` -> `sri shree company company`
  - Jaccard: 0.7500 -> 0.6667 (-0.0833)

- **S1-439499349** vs **S3-425260148** [D_legal_std]
  - S1: `Shree & Co Company` -> `shree company company`
  - Other: `Company Schnbre & Co` -> `company schnbre company`
  - Jaccard: 0.5000 -> 0.3333 (-0.1667)

- **S1-439499349** vs **S3-107857514** [D_legal_std]
  - S1: `Shree & Co Company` -> `shree company company`
  - Other: `Haloavihalo a/k/a Shree & Co Company` -> `haloavihalo a k a shree company company`
  - Jaccard: 0.5000 -> 0.4000 (-0.1000)

- **S1-90545367** vs **S3-998012588** [D_legal_std]
  - S1: `Narsimha & Co Company` -> `narsimha company company`
  - Other: `Narsimha Co Company Services - 2385703984` -> `narsimha company company services 2385703984`
  - Jaccard: 0.6000 -> 0.5000 (-0.1000)


## 12. Country Consistency (PART 4)

- **Raw country match rate:** 100.0%
- **Normalized (lowercase) match rate:** 100.0%
- **No country mismatches** in true-match pairs.

## 13. Safe Transformations

Based on the discrimination analysis:

### Name: Legal form standardization (D_legal_std) — SAFE, MODERATE BENEFIT

- True-match Jaccard: 0.6407 -> 0.6560 (+0.0153, +2.4%)
- Non-match Jaccard: 0.0300 -> 0.0452 (+0.0152)
- **Discrimination gap unchanged** (0.6108 -> 0.6108)
- Improved 3.8% of true pairs, hurt 0.005% (essentially zero)
- Exact match rate: 25.5% -> 28.4% (+2.9 percentage points)
- Key examples: "Ltd" <-> "Limited", "Pvt" <-> "Private", "Inc" <-> "Incorporated", "Co" <-> "Company"
- **Verdict: Safe to add as a feature-engineering step.** The non-match Jaccard increase is proportional — legal form tokens ("limited", "private", etc.) appear in both true matches and non-matches, so standardizing them increases similarity equally in both groups. This preserves discrimination while increasing the number of exact-match pairs the system can identify with certainty.

### Name: Token sorting (E_token_sort) — SAFE FOR EXACT MATCH, NO JACCARD BENEFIT

- True-match Jaccard: unchanged (Jaccard is already order-invariant)
- True-match exact match rate: 25.5% -> 31.1% (+5.6pp)
- Char sim: 0.7764 -> 0.7799 (+0.0035)
- **Discrimination gap unchanged** (0.6108 -> 0.6108)
- **Verdict: Useful as an auxiliary representation for exact-match blocking.** Token order doesn't affect set-based similarity, but creating a canonical sorted form increases exact-match opportunities by +5.6pp. This is a pure win with zero collision risk for Jaccard/set-based comparisons.

### Address: Abbreviation expansion (D_abbrev) — SAFE, STRONG BENEFIT

- True-match Jaccard: 0.6063 -> 0.6612 (+0.0549, +9.1%)
- Non-match Jaccard: 0.0150 -> 0.0192 (+0.0042)
- **Discrimination gap WIDENS** (0.5913 -> 0.6420, +0.0507)
- Improved 25.5% of true pairs, hurt only 0.1%
- Exact match rate: 8.3% -> 11.7% (+3.4pp)
- **Verdict: The single strongest transformation tested.** This is the only name or address transform that meaningfully widens the discrimination gap. The non-match increase (+0.0042) is dwarfed by the true-match increase (+0.0549). Country-gated abbreviation expansion (st->street, rd->road, r.->rue, av->avenue, etc.) is clearly beneficial.

### Address: Numeric token extraction (E_numeric) — SAFE, VERY HIGH DISCRIMINATION

- True-match Jaccard: 0.6063 -> 0.7329 (+0.1266)
- Non-match Jaccard: 0.0150 -> 0.0117 (-0.0033, actually DECREASES)
- **Discrimination gap WIDENS dramatically** (0.5913 -> 0.7212, +0.1299)
- True-match exact rate: 8.3% -> 61.8% — most true matches share ALL numeric tokens
- Non-match exact rate: 0.5% — almost no false matches share all numeric tokens
- **Verdict: Extremely powerful feature. House numbers, postal codes, and other numeric tokens are the single most discriminative address feature.** Should be used as a separate matching feature, not a replacement for full address comparison. Note: 22.5% of true pairs have WORSE numeric similarity (one address has numbers the other doesn't — typically empty addresses), so this should be one signal among many.

### Address: Token set (F_token_set) — SAFE, MINOR BENEFIT

- True-match Jaccard: unchanged (already order-invariant)
- True-match exact match rate: 8.3% -> 11.8% (+3.5pp)
- **Discrimination gap unchanged** (0.5913 -> 0.5913)
- **Verdict: Same as name token sorting — useful for exact-match blocking, no Jaccard/discrimination impact.**


## 14. Transformations That Should NOT Be Added

### Name: Lowercase + punctuation only (B_lower_punct) — HARMFUL

- True-match Jaccard drops from 0.6407 to 0.6147 (-0.0260)
- Non-match Jaccard slightly decreases too (0.0300 -> 0.0291)
- **Discrimination gap narrows** (0.6108 -> 0.5855, -0.0253)
- This is WORSE than A_current because it lacks Unicode NFC normalization and Latin accent folding. The accented characters create token mismatches that A_current resolves.
- **Verdict: Never use plain lowercase+punctuation when Unicode/accent normalization is available.**

### Address: Whitespace-only normalization (C_whitespace) — DESTRUCTIVE

- True-match Jaccard collapses from 0.6063 to 0.3001 (-0.3062)
- **Discrimination gap collapses** (0.5913 -> 0.2942, -0.2971)
- 71.3% of true pairs get WORSE
- This happens because raw addresses have mixed case, punctuation, and formatting that create noise when compared without lowercasing/cleaning.
- **Verdict: Whitespace normalization alone is catastrophically insufficient. Always combine with lowercasing and punctuation normalization.**

### Name: Combined (F_combined) — IDENTICAL TO D_legal_std

- F_combined produces identical results to D_legal_std in this experiment.
- **Verdict: The current "combined" representation adds nothing beyond legal standardization. If we add more transforms in the future, this slot can be used for their combination.**


## 15. Recommendations for Production Normalizer

### Summary of Findings

The current `normalize.py` (Experiment A) is a strong baseline. The Unicode NFC normalization + Latin accent folding + Indic script preservation pipeline is demonstrably correct: it produces identical results to the explicit unicode_accent experiment (C) and significantly outperforms naive lowercase+punctuation (B).

### Discrimination-Improving Transforms (recommended for feature engineering)

| Transform | True Jaccard Gain | Gap Gain | Collision Risk | Priority |
|---|---|---|---|---|
| Address abbreviation expansion | +0.0549 | +0.0507 | Very low | **HIGH** |
| Address numeric extraction | +0.1266 | +0.1299 | None (decreases) | **HIGH** |
| Name legal form standardization | +0.0153 | +0.0000 | Neutral | **MEDIUM** |
| Name/addr token sorting | +0.0000 | +0.0000 | None | **LOW** (blocking only) |

### What should change in normalize.py?

**Nothing.** The production normalizer is correct as-is. All recommended transforms should be implemented as **additional feature-engineering columns** during the feature engineering phase (Step 3+), not as changes to the base normalizer. Reasons:

1. The base normalizer's job is to produce clean, lossless representations. It does this well.
2. Legal form standardization is domain-specific knowledge that belongs in feature engineering.
3. Address abbreviation expansion is country-specific and requires a mapping dictionary.
4. Numeric extraction is a derived feature, not a normalization.
5. Token sorting is a representation choice for blocking, not cleaning.

### Key insight: similarity vs discrimination

Legal form standardization improves true-match similarity (+0.0153 Jaccard) but the discrimination gap is unchanged (+0.0000). This means it helps recall but not precision. For our F_0.5 metric (which weights precision 2x), this is net positive only if the recall gain doesn't increase false positives proportionally.

Address abbreviation expansion is the clear winner: it improves true-match similarity (+0.0549) AND widens the discrimination gap (+0.0507). This helps both precision and recall.

Numeric token overlap is the most discriminative single feature: 61.8% of true matches share all numeric tokens, vs 0.5% of non-matches. This should be a high-weight feature in any model.

### What the experiments cannot tell us

- Cross-script matching (Devanagari/Tamil/Telugu <-> Latin): 0% character overlap, requires transliteration or multilingual embeddings. No normalization transform can solve this.
- DBA splitting: not tested in this experiment (would require DBA-specific transform).
- URL/domain name handling: not tested (would require domain-specific transform).
- These remain deferred to feature engineering / model design.


## Appendix: Runtime Statistics

- **Total runtime:** 2253.5s
- **True pairs evaluated:** 172,731
- **Negative pairs evaluated:** 50,000
- **Peak memory:** 209.5 MB
- **Sample:** First 50,000 S1 entities from ground truth
- **Random seed:** 42
