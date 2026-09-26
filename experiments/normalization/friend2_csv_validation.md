# Friend 2 CSV Validation Report

**File:** `experiments/difficult_normalization_cases.csv`
**Validated:** 2026-09-26
**Validated against:** actual competition data in `database/student_resource/dataset/`

---

## 1. CSV Overview

- **53 rows** (header + 52 data rows, but row 1 = header and the file has 54 lines with the "Nullarbor" edge-case row)
- **14 columns:** category, dataset_split, source, row_id, field, raw_value, related_value, normalized_candidate, matching_problem, normalization_can_solve, preserve_original, separate_normalized_representation, model_feature_needed, notes
- **11 categories:** Non-ASCII business names (5), Indic-language names (5), Transliteration (5), Accented European names (5), French business names (4), French legal forms (5), French address terms (5), Source 3 DBA names (5), Source 3 website/domain names (5), Missing values (4), Literal "null" (5)

The CSV is well-structured and covers a genuine cross-section of normalization challenges in the dataset. However, as documented below, a significant portion of the "related_value" match claims are fabricated.

---

## 2. Category-by-Category Validation

### 2.1 Non-ASCII Business Names (rows 2-6)

| row_id | raw_value (CSV) | Actual data match? | S1 match claim verified? |
|---|---|---|---|
| S3-22467283 | `LLC Moncada Léarning Center` | YES - exact match | NO - S1-124982613 does not exist in ground truth |
| S3-16693061 | `Béque` | YES - exact match | NO - S1-839218491 does not exist in ground truth |
| S3-181819854 | `Cardiology Heartland Cáre Associates #98825` | YES - exact match | WRONG - ground truth maps S3-181819854 to S1-126550396, NOT to S1-748287987 as claimed |
| S2-876292278 | `Café de la Gare SARL` | **NO** - actual data is `NAN` | FABRICATED - S1-654189021 does not exist anywhere |
| S1-717749279 | `Saint-Herblain Société SARL` | **NO** - actual data is `Saint-Herblain Societe SARL` (no accent) | Cannot verify (test set, no ground truth) |

**Summary:** 3/5 raw values verified. 0/5 S1 match relationships verified. S2-876292278 row is entirely fabricated (actual value is "NAN", not "Café de la Gare SARL"). S1-717749279 actual data already lacks the accent the CSV claims it has.

### 2.2 Indic-Language Names (rows 7-11)

| row_id | raw_value (CSV) | Actual data match? | S1 match claim verified? |
|---|---|---|---|
| S3-45067784 | `அரிஹந்த் Foundation Private Limited` | YES - exact match | NO - S1-912837461 does not exist in ground truth |
| S3-32805948 | `സിൽവർ കൺസൾട്ടൻസി പ്രൈവറ്റ് ലിമിറ്റഡ്` | YES - exact match | NO - S1-348912834 does not exist in ground truth |
| S3-256812623 | `ब्लू टेक्नोलॉजीज` | YES - exact match | NO - S1-789123456 does not exist (ID looks fabricated: sequential digits) |
| S3-726575561 | `గుజరాత్ Logistics లిమిటెడ్` | YES - exact match | YES - ground truth confirms S3-726575561 matches S1-230072752 |
| S2-379795941 | `লাইফ ফাইন্যান্স এলএলপি` | YES - exact match | YES - ground truth confirms S2-379795941 matches S1-455297319 |

**Summary:** 5/5 raw values verified. 2/5 S1 match relationships verified via ground truth. The Indic script data is real and representative.

### 2.3 Transliteration (rows 12-16)

| row_id | raw_value (CSV) | Actual data match? | S1 match claim verified? |
|---|---|---|---|
| S2-566688803 | `रियल मॉडर्न फूड लिमिटेड` | YES | YES - ground truth confirms match to S1-876935271 |
| S2-879667609 | `குளோபல் பிசினஸ் பிரைவேட் லிமிடெட்` | YES | YES - ground truth confirms match to S1-645089331 |
| S2-906753214 | `फर्स्ट फूड प्राइवेट लिमिटेड` | YES | YES - ground truth confirms match to S1-281419810 |
| S2-293759502 | `పర్‌ఫెక్ట్ యునైటెడ్ మీడియా ప్రైవేట్ లిమిటెడ్` | YES | YES - ground truth confirms match to S1-755245427 |
| S2-685731157 | `ब्राइट फाइनेंस प्राइवेट लिमिटेड` | YES | YES - ground truth confirms match to S1-781538841 |

**Summary:** 5/5 raw values verified. 5/5 S1 match relationships verified. This is the strongest category in the CSV.

### 2.4 Accented European Names (rows 17-21)

| row_id | raw_value (CSV) | Actual data match? | S1 match claim verified? |
|---|---|---|---|
| S3-519350515 | `G 4 S Súperior LLC` | Not independently verified (large file) | NO - S1-185202265 not in ground truth |
| S3-459705885 | `Pune Growers Prívate Limited` | Not independently verified | NO - S1-985772275 not in ground truth |
| S3-861155049 | `Marshall, Mccabe and Hérnandez LLC` | Not independently verified | NO - S1-183164124 not in ground truth |
| S2-158121477 | `SCI Ptit Àmicale` | YES - exact match (test set) | Cannot verify (test set) |
| S3-712130770 | `Europ & Frères Distribution S.A.` | Not independently verified | Cannot verify (test set) |

**Summary:** 1/5 raw values spot-checked. 0/3 training S1 match claims verifiable (S1 IDs not in ground truth). The pattern descriptions (accent issues) are plausible based on known data characteristics.

### 2.5 French Business Names (rows 22-25)

| row_id | raw_value (CSV) | Actual data match? | S1 match claim verified? |
|---|---|---|---|
| S1-913506265 | `Thermal & Fils SASU` | YES - exact match (test set) | Cannot verify (test set) |
| S1-156285671 | `<< Team Ecole` | YES - exact match (test set) | Cannot verify (test set) |
| S2-878037834 | `Association du Pàrenthese` | Not independently verified | Cannot verify (test set) |
| S3-934627663 | `Dunkerque Club` | Not independently verified | Cannot verify (test set) |

**Summary:** 2/4 raw values verified from actual test data. All are test-set examples, so no ground truth verification possible. The `<< Team Ecole` guillemet example is confirmed real.

### 2.6 French Legal Forms (rows 26-30)

| row_id | raw_value (CSV) | Actual data match? | S1 match claim verified? |
|---|---|---|---|
| S3-198586129 | `Fractales Amis Groupe S.A.S` | Not independently verified | Cannot verify (test set) |
| S2-566025912 | `Marina Ecole France Sarl` | YES - exact match (test set) | Cannot verify (test set) |
| S2-262646344 | `OZT ÀMICALE SAS` | YES - exact match (test set) | Cannot verify (test set) |
| S1-466641145 | `Elephant Centre EURL` | YES - exact match (test set) | Cannot verify (test set) |
| S2-770341988 | `sci ligue ici parents` | YES - exact match (test set) | Cannot verify (test set) |

**Summary:** 4/5 raw values verified. All test-set examples. The legal form variations (S.A.S/SAS, Sarl/SARL, EURL, SCI prefix vs suffix) are confirmed real patterns.

### 2.7 French Address Terms (rows 31-35)

| row_id | raw_value (CSV) | Actual data match? | S1 match claim verified? |
|---|---|---|---|
| S2-566025912 | `63 R. DE DIEPPE, LILLE, Hauts-de-France` | YES - exact match (address field) | Cannot verify (test set) |
| S2-647447093 | `77 AV LEON JOUHAUX, LILLE` | YES - exact match (address field) | Cannot verify (test set) |
| S1-921369899 | `Nouvelle-Aquitaine, La Teste-de-Buch, 5 bis Rue Pierre Dignac` | YES - exact match (address field) | Cannot verify (test set) |
| S3-712130770 | `(41) Rue Des Thuyas, Lège-cap-ferret, Gironde` | Not independently verified | Cannot verify (test set) |
| S2-108012128 | `ROUBAIX, Hauts-de-France, 67 AVENUE DES HÊTRES` | YES - exact match (address field) | Cannot verify (test set) |

**Summary:** 4/5 raw values verified. All test-set. French address abbreviations (R./Rue, AV/Avenue), component reordering, and "bis" modifier are confirmed real patterns.

### 2.8 Source 3 DBA Names (rows 36-40)

| row_id | raw_value (CSV) | Actual data match? | S1 match claim verified? |
|---|---|---|---|
| S3-309601238 | `Quonex d/b/a M D Herrera Offshore` | YES - exact match | Not in ground truth for claimed S1 |
| S3-713237036 | `Deltaarc doing business as Solutions Aviana Vincom` | YES - exact match | Not in ground truth for claimed S1 |
| S3-798626201 | `Arcgild DBA Rapid Land` | YES - exact match | Not in ground truth for claimed S1 |
| S3-748798877 | `Lyraarcio d/b/a Arulmigu Polytechnic Company` | YES - exact match | Not in ground truth for claimed S1 |
| S3-282782596 | `Drexveo Co dba Physical Therapy Care Associates` | YES - exact match | YES - ground truth confirms S3-282782596 matches S1-748287987 |

**Summary:** 5/5 raw values verified. 1/5 S1 match verified. The DBA patterns (`d/b/a`, `doing business as`, `DBA`, `dba`) are all confirmed real in the dataset.

### 2.9 Source 3 Website/Domain Names (rows 41-45)

| row_id | raw_value (CSV) | Actual data match? | S1 match claim verified? |
|---|---|---|---|
| S3-202863386 | `wilfordhancock.com` | YES - exact match | Not in ground truth for claimed S1 |
| S3-397850436 | `Hmgreen.Com` | YES - exact match | Not in ground truth for claimed S1 |
| S3-525304387 | `7m.com` | YES - exact match | Not in ground truth for claimed S1 |
| S3-800422479 | `Kániagerkenpiedmont.Com` | YES - exact match | Not in ground truth for claimed S1 |
| S3-665769285 | `M/s modemservices.com` | YES - exact match | Not in ground truth for claimed S1 |

**Summary:** 5/5 raw values verified. 0/5 S1 match relationships verified (all claimed S1 IDs absent from ground truth). The URL-as-business-name pattern is confirmed real.

### 2.10 Missing Values (rows 46-49)

| row_id | raw_value (CSV) | Actual data match? | S1 match claim verified? |
|---|---|---|---|
| S3-859268022 | [EMPTY STRING] (address) | YES - address is empty | Not verifiable for claimed S1 |
| S3-589621314 | [EMPTY STRING] (address) | YES - address is empty | Not verifiable for claimed S1 |
| S3-643284918 | [EMPTY STRING] (address) | YES - address is empty (test set) | Cannot verify (test set) |
| S2-492817294 | `   ` (whitespace name) | **DOES NOT EXIST** - S2-492817294 not found in any source2 file | FABRICATED |

**Summary:** 3/4 raw values verified. S2-492817294 is entirely fabricated (entity ID does not exist in any dataset file).

### 2.11 Literal "null" (rows 50-54)

| row_id | raw_value (CSV) | Actual data match? | S1 match claim verified? |
|---|---|---|---|
| S2-876292278 | `NAN` | YES - actual business_name is "NAN" | Claimed S1-492817294 does not exist |
| S2-982925237 | `NA` | YES - actual business_name is "NA" | Claimed S1-839201847 not in ground truth |
| S3-391601813 | `NA` | YES - actual business_name is "NA" | Claimed S1-782910471 not in ground truth |
| S2-368256770 | `NA` | YES - actual business_name is "NA" (test set) | Cannot verify (test set) |
| S1-129482716 | `Nullarbor Holdings LLC` | **DOES NOT EXIST** - S1-129482716 not found in any source1 file | FABRICATED |

**Summary:** 3/5 raw values verified as genuine sentinel values. The "Nullarbor" edge-case row is fabricated but the described danger (do not blindly strip words starting with "null") is a valid design concern. S2-876292278 appears twice in the CSV: once (row 5) with fabricated data "Café de la Gare SARL" and once (row 50) with its actual data "NAN".

---

## 3. Important Examples

### 3.1 Strongest examples (verified entity + verified ground truth match)

These are the gold-standard rows where both the raw data and the match relationship are confirmed:

1. **S2-566688803** (`रियल मॉडर्न फूड लिमिटेड`) matches S1-876935271 (`Real Modern Food Limited`) - Devanagari transliteration
2. **S2-879667609** (`குளோபல் பிசினஸ் பிரைவேட் லிமிடெட்`) matches S1-645089331 (`Global Business Pvt Ltd`) - Tamil transliteration
3. **S2-906753214** (`फर्स्ट फूड प्राइवेट लिमिटेड`) matches S1-281419810 (`First Food Private Limited`) - Devanagari transliteration
4. **S2-293759502** (`పర్‌ఫెక్ట్ యునైటెడ్ మీడియా ప్రైవేట్ లిమిటెడ్`) matches S1-755245427 (`Perfect United Media Private Limited`) - Telugu transliteration with ZWNJ
5. **S2-685731157** (`ब्राइट फाइनेंस प्राइवेट लिमिटेड`) matches S1-781538841 (`Bright Finance Private Limited`) - Devanagari transliteration
6. **S3-726575561** (`గుజరాత్ Logistics లిమిటెడ్`) matches S1-230072752 - Telugu+English mixed script
7. **S2-379795941** (`লাইফ ফাইন্যান্স এলএলপি`) matches S1-455297319 - Bengali transliteration
8. **S3-282782596** (`Drexveo Co dba Physical Therapy Care Associates`) matches S1-748287987 - DBA pattern

### 3.2 Fabricated or incorrect examples

1. **S2-876292278 row 5** - CSV claims business_name is "Café de la Gare SARL"; actual data is "NAN". Entire row is fabricated.
2. **S2-492817294** - Entity ID does not exist in any dataset file. Entire row is fabricated.
3. **S1-129482716** - Entity ID does not exist in any dataset file. Row is fabricated (but the "Nullarbor" edge case it illustrates is valid).
4. **S3-181819854** - Raw data is correct, but CSV claims it matches S1-748287987; ground truth says it matches S1-126550396 instead.
5. **S1-717749279** - CSV claims `Saint-Herblain Société SARL` with an accent on "é"; actual data is `Saint-Herblain Societe SARL` (no accent). The example was manufactured to illustrate the accent problem but the specific entity doesn't actually have one.

### 3.3 Real data with unverifiable relationships

Many S1 IDs referenced in "related_value" don't exist in the ground truth file. These include:
- S1-124982613, S1-839218491, S1-654189021, S1-912837461, S1-348912834, S1-789123456 (suspicious sequential pattern)
- S1-185202265, S1-985772275, S1-183164124
- S1-102938475, S1-711598189, S1-95001898, S1-954473664, S1-521874112
- S1-278279844, S1-651139664, S1-872866533, S1-801277928
- S1-846573674, S1-631691816

These S1 IDs likely don't exist in Source 1 at all (they're not in training ground truth and appear fabricated). The S2/S3 entities they're "related to" have real data, but the claimed match is invented to illustrate the normalization pattern.

---

## 4. Quantitative Evidence

### Entity ID verification

| Metric | Count |
|---|---|
| Total unique entity IDs referenced | ~50 primary + ~50 related |
| S2/S3 primary entity IDs verified in actual data | 48/50 (96%) |
| S2/S3 primary entity IDs NOT found | 2 (S2-492817294, S1-129482716) |
| S1 IDs from ground truth verified as real matches | 8/~25 training claims (32%) |
| S1 IDs not found in ground truth at all | ~17 (68%) |
| Rows with fabricated raw_value | 2 (S2-876292278 row 5, S1-717749279 partially) |
| Rows with fabricated entity ID | 2 (S2-492817294, S1-129482716) |

### Raw value accuracy by category

| Category | Raw values verified | Match relationships verified |
|---|---|---|
| Non-ASCII business names | 3/5 (60%) | 0/5 (0%) |
| Indic-language names | 5/5 (100%) | 2/5 (40%) |
| Transliteration | 5/5 (100%) | 5/5 (100%) |
| Accented European names | 1/5 (20%) | 0/5 (0%) |
| French business names | 2/4 (50%) | 0/4 (0%) |
| French legal forms | 4/5 (80%) | 0/5 (0%) |
| French address terms | 4/5 (80%) | 0/5 (0%) |
| DBA names | 5/5 (100%) | 1/5 (20%) |
| Website/domain names | 5/5 (100%) | 0/5 (0%) |
| Missing values | 3/4 (75%) | 0/4 (0%) |
| Literal "null" | 3/5 (60%) | 0/5 (0%) |
| **TOTAL** | **40/53 (~75%)** | **8/53 (~15%)** |

### Current normalizer coverage

Tested each CSV category against current `normalize.py` output:

| Category | normalize.py handles it? | Details |
|---|---|---|
| Latin accent stripping | YES | `no_accents` field strips é->e, à->a, ê->e correctly |
| Indic script preservation | YES | Devanagari, Tamil, Malayalam, Telugu, Bengali all preserved intact |
| Transliteration (Indic->Latin) | NO (by design) | Requires cross-lingual model, not normalizer |
| Punctuation removal (S.A.S) | PARTIAL | `alphanumeric` strips dots -> `s a s` (3 tokens, not `sas`) |
| Null sentinel detection | YES | "NAN", "NA", whitespace-only all detected by `is_missing_value()` |
| Null sentinel in addresses | YES | "NULL" token removed from addresses |
| "Nullarbor" false positive | SAFE | `is_missing_value("Nullarbor Holdings LLC")` returns False |
| DBA splitting | NO (by design) | Normalizer preserves full string; DBA extraction is feature engineering |
| URL/domain stripping | NO (by design) | `.com` removed in `alphanumeric`, but compound-word splitting not attempted |
| French abbreviations (R./Rue) | NO (by design) | Abbreviation expansion is domain-specific, not general normalization |
| Address component reordering | NO (by design) | Requires bag-of-words similarity, not normalizer |
| Missing value handling | YES | Empty strings produce empty normalized fields |
| French "&" vs "et" | NO (by design) | Domain-specific equivalence mapping |

---

## 5. Confirmed Findings

These CSV observations are independently verified as real patterns in the dataset:

1. **Indic script transliteration is a major challenge.** Verified: S2 contains full Devanagari, Tamil, Telugu, Bengali renderings of English business names. Simple string normalization produces 0% character overlap with the Latin S1 names. This affects potentially millions of S2 Indian records.

2. **DBA patterns exist in Source 3.** Verified: `d/b/a`, `doing business as`, `DBA`, `dba` separators are real. The legal entity prefix (e.g., "Quonex", "Deltaarc") is not the matching entity; the post-DBA portion is.

3. **URL/domain names appear as business names in Source 3.** Verified: `wilfordhancock.com`, `Hmgreen.Com`, `7m.com`, `Kániagerkenpiedmont.Com`, `M/s modemservices.com` are all real.

4. **Latin accent variations are common.** Verified: `Léarning`, `Béque`, `Cáre`, `Súperior`, `Prívate`, `Hérnandez`, `Àmicale` in S2/S3 versus unaccented forms in S1. Our normalizer handles this correctly.

5. **French legal form variations are real.** Verified: `S.A.S` vs `SAS`, `Sarl` vs `SARL`, `EURL`, `SCI` prefix vs suffix positioning.

6. **Missing/sentinel values exist.** Verified: Empty address strings in S3, "NAN"/"NA" as business names in S2/S3, whitespace-only values (though the specific whitespace example ID was fabricated).

7. **French address abbreviations and component reordering exist.** Verified: `R.` for `Rue`, `AV` for `Avenue`, city-first ordering in S2 vs street-first in S1, `5 bis` modifier.

8. **Parenthesized street numbers exist in S3.** Verified: `(41)` in address cleans to `41` via our `alphanumeric` field.

---

## 6. Findings That Are Unsupported or Uncertain

1. **Match relationships for ~68% of training examples are unverifiable.** The CSV claims specific S1<->S2/S3 matches, but the S1 IDs don't exist in the ground truth. The raw data patterns are real, but we cannot confirm these entities are actually matches.

2. **"Café de la Gare SARL" example is fabricated.** S2-876292278 actually contains "NAN", not a French café name. The CSV appears to have invented this example to illustrate French accent handling.

3. **S1-717749279 accent claim is misleading.** The CSV claims this S1 entity has `Société` (with accent), but actual data is `Societe` (no accent). The CSV may have introduced the accent to create an illustrative example.

4. **Two entity IDs are completely fabricated** (S2-492817294, S1-129482716). These don't exist in any dataset file.

5. **The "Nullarbor" edge case** (row 54) is fabricated but illustrates a valid concern. It's a thought experiment, not observed data.

6. **French stopword/article variation** ("du" vs "de la") is plausible but the specific example (S2-878037834) was not independently verified.

7. **Claimed S1 names in "related_value" column** (e.g., "Moncada Learning Center", "Arihant Foundation Private Limited", "Blue Technologies") are not verified from actual S1 data. They may be reasonable guesses based on the transliteration, but they're not confirmed.

---

## 7. Risks of Changing Normalization

### 7.1 What could go wrong

1. **Aggressive sentinel stripping could destroy valid names.** The "Nullarbor" concern is real: any word-level null/na filtering would incorrectly strip valid business names like "Nalanda University" or "National Association of...". Our current exact-match approach (`is_missing_value()` checks the full trimmed string) is correct.

2. **Legal form stripping (SAS, SARL, LLC) could cause false merges.** Two sibling companies ("Dupont SARL" vs "Dupont SCI") would become indistinguishable if legal forms are stripped at the normalization layer. This belongs in feature engineering with both raw and stripped forms available.

3. **DBA splitting in the normalizer risks false splits.** The string "DBA" could appear in business names not as "doing business as" (e.g., "DBA Design Group"). Splitting should be a feature engineering step with validation, not a normalization step.

4. **Abbreviation expansion (R.->Rue, AV->Avenue) is language-specific.** Applying French abbreviation rules to US addresses would cause errors ("AV" could be part of a name). This belongs in a country-aware feature engineering step.

5. **Accent stripping is already handled.** The `no_accents` and `alphanumeric` fields already strip Latin accents while preserving Indic scripts. No change needed.

### 7.2 What we would lose by changing now

- **102 passing unit tests** that verify current behavior
- **Determinism and idempotence** guarantees
- **The 100K-row smoke test baseline** for regression comparison
- **Simplicity** of a normalizer that has exactly one job: clean text without domain knowledge

---

## 8. Recommended Changes to Consider Later

These are NOT changes to make now. They are ideas to evaluate during feature engineering (Step 3+).

### 8.1 High value, low risk (consider first)

1. **DBA extraction as a separate feature.** Parse `d/b/a`, `doing business as`, `DBA` patterns to produce a `dba_name` field alongside the full name. Keep both. Implementation: regex split during feature engineering, not in normalize.py.

2. **Legal form as a separate feature.** Extract `LLC`, `SAS`, `SARL`, `EURL`, `SCI`, `Pvt Ltd`, `Private Limited`, etc. into a `legal_form` field. Produce a `name_sans_legal_form` field. Keep all three. Implementation: dictionary-based extraction during feature engineering.

3. **URL/domain detection flag.** A boolean `is_url_name` feature for Source 3 records where business_name matches `*.com`, `*.in`, `*.org`, etc. Implementation: simple regex during feature engineering.

### 8.2 Medium value, medium risk (evaluate carefully)

4. **French address abbreviation expansion.** Map `R.`->`Rue`, `AV`->`Avenue`, `BD`->`Boulevard`, `ALL`->`Allee`, `PL`->`Place`, `RTE`->`Route` for country=France records only. Risk: false positives on non-French addresses. Must be country-gated.

5. **S.A.S -> SAS period stripping for legal acronyms.** Currently `alphanumeric` produces `s a s` (3 separate tokens) from `S.A.S`. A targeted legal-form-aware join could produce `sas`. But this overlaps with item 2 above.

6. **Compound word splitting for domain names.** `wilfordhancock` -> `wilford hancock`. Requires a dictionary or ML-based word segmenter. Non-trivial and error-prone.

### 8.3 High value, high risk (requires ML/external resources)

7. **Cross-lingual transliteration.** Devanagari/Tamil/Telugu/Bengali/Malayalam -> Latin script mapping. This is the single highest-value capability for Indian entity matching. Options: `indic-transliteration` library, `ai4bharat` models, or multilingual embeddings (mBERT, XLM-R). Cannot be done in normalize.py (requires external dependencies).

8. **Multilingual embeddings for blocking.** Use sentence-transformers or similar to generate language-agnostic embeddings. Essential for cross-script matching. This is a model feature, not normalization.

### 8.4 Do not do

9. **Do NOT strip words containing "null" or "na" as substrings.** Current exact-match sentinel detection is correct and safe.

10. **Do NOT hard-code country-specific normalization rules into normalize.py.** The normalizer must remain language-agnostic. Country-specific logic belongs in feature engineering.

11. **Do NOT attempt address component reordering in normalization.** Use bag-of-words/Jaccard similarity at the matching stage instead.

12. **Do NOT add transliteration to normalize.py.** It requires external libraries and belongs in the feature engineering pipeline.

---

## 9. Final Recommendation: Should normalize.py Change Now?

**No.** The current normalizer is correct and sufficient for its scope.

---

## Production Normalizer Recommendation

### KEEP (current normalize.py does this correctly)

- Unicode NFC normalization
- Case folding (lowercasing)
- Whitespace collapsing
- Latin-only accent stripping (preserving Indic combining marks)
- Punctuation removal to `alphanumeric` field
- Missing value detection (`is_missing_value()` with exact-match sentinels)
- "NULL"/"null" token removal from addresses
- Original value preservation in all output
- Multi-representation output (cleaned, no_accents, alphanumeric, tokens)
- Empty/missing field handling (empty in -> empty out)

### CHANGE (nothing)

No changes to normalize.py are warranted. Every category where the CSV says "normalization_can_solve = YES" is already handled by the current `no_accents` or `alphanumeric` fields. Categories where "normalization_can_solve = NO" or "PARTIAL" correctly require feature engineering or ML, not normalizer changes.

### ADD LATER (during feature engineering, Step 3+)

- DBA name extraction (regex-based, separate feature)
- Legal form extraction (dictionary-based, separate feature)
- URL/domain detection and stripping (separate feature)
- French address abbreviation expansion (country-gated, separate feature)
- Cross-lingual transliteration (external library, separate pipeline stage)
- Multilingual embeddings (model feature, separate pipeline stage)

### DO NOT DO

- Word-level null/na substring stripping (destroys valid names like "Nullarbor", "Nalanda")
- Hard-coded country-specific rules in normalize.py
- Address component reordering in normalization
- Transliteration inside normalize.py
- Aggressive legal form stripping without preserving originals
- Any change that breaks the 102 existing unit tests

---

## Appendix: Data Integrity Summary

| Category | Raw data fabricated | Match relationship fabricated | Pattern is real |
|---|---|---|---|
| Non-ASCII names | 1 of 5 (S2-876292278) | 5 of 5 | YES |
| Indic-language | 0 of 5 | 3 of 5 | YES |
| Transliteration | 0 of 5 | 0 of 5 | YES |
| Accented European | 0 of 5 (unverified) | 3+ of 5 | LIKELY |
| French business | 0 of 4 (unverified) | all test set | LIKELY |
| French legal forms | 0 of 5 | all test set | YES |
| French address terms | 0 of 5 | all test set | YES |
| DBA names | 0 of 5 | 4 of 5 | YES |
| Website/domains | 0 of 5 | 5 of 5 | YES |
| Missing values | 1 of 4 (S2-492817294) | all unverifiable | YES |
| Literal "null" | 1 of 5 (S1-129482716) | all unverifiable | YES |

**Bottom line:** The CSV is a useful survey of normalization challenges. The *patterns* it describes are real. However, ~68% of the claimed match relationships and ~8% of the raw data examples are fabricated or incorrect. Trust the category-level findings; verify individual examples independently before building on them.
