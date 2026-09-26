# Token-Overlap Blocking Experiment Results

**Date:** 2026-09-26
**Runtime:** 742.1s
**Peak memory:** 0.0 MB
**S1 entities evaluated:** 94,406
**S2 entities loaded:** 5,034,616
**S3 entities loaded:** 5,285,603

## 1. Token Index and DF Distribution

- **(country, token) keys:** 1,483,762
- **Keys after max_df=1,000:** 1,480,770 (dropped 2,992, 0.20%)
- **Keys after max_df=5,000:** 1,482,934 (dropped 828, 0.06%)
- **Keys after max_df=20,000:** 1,483,466 (dropped 296, 0.02%)
- **Median df:** 1
- **P90 df:** 4 | **P95:** 15 | **P99:** 143
- **Max df:** 1,233,380
- **Total postings:** 37,023,660

## 2. Top 30 Tokens by Document Frequency

| Rank | Country | DF | Token |
|---|---|---|---|
| 1 | india | 1,233,380 | limited |
| 2 | india | 1,196,119 | private |
| 3 | us | 1,099,621 | llc |
| 4 | us | 846,946 | inc |
| 5 | india | 648,418 | ltd |
| 6 | india | 409,619 | pvt |
| 7 | india | 296,635 | लिमिटेड |
| 8 | us | 292,790 | center |
| 9 | us | 267,771 | partners |
| 10 | us | 266,460 | com |
| 11 | india | 246,472 | प्राइवेट |
| 12 | us | 245,692 | corp |
| 13 | us | 241,373 | and |
| 14 | us | 229,948 | s |
| 15 | india | 229,501 | india |
| 16 | us | 225,988 | c |
| 17 | us | 215,715 | group |
| 18 | us | 198,944 | co |
| 19 | us | 177,827 | ltd |
| 20 | india | 163,685 | services |
| 21 | us | 161,239 | care |
| 22 | us | 158,467 | l |
| 23 | us | 154,814 | services |
| 24 | us | 154,670 | of |
| 25 | india | 146,200 | com |
| 26 | us | 145,118 | holdings |
| 27 | india | 139,146 | llp |
| 28 | us | 132,212 | associates |
| 29 | india | 131,559 | center |
| 30 | us | 102,956 | health |

The most frequent token `limited` (india) appears in **1,233,380** records. Any S1 entity carrying this token pulls the entire posting list as candidates under min_overlap=1 — this is why a max_df filter matters.

## 3. Route Results

| Route | Recall | S2 Rec | S3 Rec | Full Cov | Avg Cands | Median | P95 | Max |
|---|---|---|---|---|---|---|---|---|
| token_overlap_min1_maxdf1k | 0.4387 | 0.4404 | 0.4370 | 0.3302 | 138.3 | 0 | 724 | 3,241 |
| token_overlap_min2_maxdf1k | 0.0881 | 0.0883 | 0.0879 | 0.0481 | 1.2 | 0 | 5 | 860 |
| token_overlap_min2_maxdf5k | 0.2410 | 0.2420 | 0.2400 | 0.1324 | 6.4 | 0 | 14 | 2,910 |
| token_overlap_min2_maxdf20k | 0.4044 | 0.4009 | 0.4076 | 0.2198 | 182.8 | 2 | 274 | 18,887 |
| union_alnum_token_min2_maxdf5k | 0.4107 | 0.4066 | 0.4145 | 0.1572 | 16.9 | 3 | 79 | 2,910 |

## 4. Comparison vs Exact-Name Baseline

| Route | Recall | Avg Cands | Source |
|---|---|---|---|
| country_name_cleaned | 0.1565 | 7.2 | core experiment |
| country_name_alphanumeric | 0.2561 | 11.2 | core experiment |
| token_overlap_min1_maxdf1k | 0.4387 | 138.3 | this experiment |
| token_overlap_min2_maxdf1k | 0.0881 | 1.2 | this experiment |
| token_overlap_min2_maxdf5k | 0.2410 | 6.4 | this experiment |
| token_overlap_min2_maxdf20k | 0.4044 | 182.8 | this experiment |
| union_alnum_token_min2_maxdf5k | 0.4107 | 16.9 | this experiment |

Best token route (`token_overlap_min1_maxdf1k`) recall = **0.4387** vs exact-alphanumeric baseline **0.2561** — +18.25 percentage points.

## 5. Observations

- **token_overlap_min1_maxdf1k:** recall 0.4387, avg 138.3 candidates, p95 724, max 3,241, runtime 1.9s
- **token_overlap_min2_maxdf1k:** recall 0.0881, avg 1.2 candidates, p95 5, max 860, runtime 5.5s
- **token_overlap_min2_maxdf5k:** recall 0.2410, avg 6.4 candidates, p95 14, max 2,910, runtime 40.5s
- **token_overlap_min2_maxdf20k:** recall 0.4044, avg 182.8 candidates, p95 274, max 18,887, runtime 310.0s
- **union_alnum_token_min2_maxdf5k:** recall 0.4107, avg 16.9 candidates, p95 79, max 2,910, runtime 48.1s

## 6. Runtime and Memory

- **Total runtime:** 742.1s
- **Peak memory:** 0.0 MB

| Route | Runtime |
|---|---|
| token_overlap_min1_maxdf1k | 1.86s |
| token_overlap_min2_maxdf1k | 5.51s |
| token_overlap_min2_maxdf5k | 40.52s |
| token_overlap_min2_maxdf20k | 309.97s |
| union_alnum_token_min2_maxdf5k | 48.06s |

## 7. Recommendations for Next Steps

*(To be filled after reviewing quantitative results)*

Candidate follow-ups: n-gram blocking (character-level typos), address-assisted blocking, phonetic keys, and DBA-aware splitting. Route-union contribution analysis can quantify how much each token route adds on top of exact-name blocking.
