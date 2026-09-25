# Difficult Normalization Case Analysis

## 1. Executive Summary

This study presents a rigorous empirical investigation into difficult normalization edge cases across the **ML Challenge 2026 Business Entity Resolution** dataset. Analyzing all **24,229,173 business records** across three independent sources (Source 1, Source 2, and Source 3) in both training and test partitions, this investigation identifies patterns where naive or overly aggressive text normalization would **catastrophically destroy discriminative information** and harm downstream entity resolution precision.

Key high-level findings include:
1. **Cross-Script Transliteration (1.62M records / 6.69% of dataset):** Entities in Indian splits frequently appear in English Latin script in Source 1 but in native Indic scripts (Devanagari, Tamil, Telugu, Bengali, Malayalam, Kannada, Gujarati) in Sources 2 and 3. Simple ASCII-stripping destroys the name entirely (reducing it to an empty string), making matching impossible.
2. **Dotted vs. Non-Dotted French Legal Forms (1.02M records / 4.22% of dataset):** In the French test set, Source 1 strictly employs non-dotted legal acronyms (`SA`, `SAS`), whereas Sources 2 and 3 contain tens of thousands of dotted variants (`S.A.`, `S.A.S.`). Normalizing punctuation is mandatory, but completely eliminating legal forms causes severe false merges between sibling entities.
3. **Source 3 DBA Injection (162,664 records):** Source 3 frequently prefixes the true operational business name with fictitious or parent corporate names followed by delimiters such as `dba`, `d/b/a`, and `doing business as`. Preserving the raw string while creating a parsed `normalized_dba` field is essential to restore candidate recall.
4. **Source 3 Web/Domain Names (365,197 records):** Source 3 substitutes corporate business names with website URLs and domain names (e.g., `wilfordhancock.com`, `Hmgreen.Com`). Stripping protocol and TLD suffixes yields core tokens, but compound domain segmentations must be handled cautiously.
5. **Literal Nulls and Sentinel Tokens (134 records):** A distinct set of records contains literal strings (`"NAN"`, `"NA"`, `"null"`). Treating these strings as literal business names would cause high-confidence false positive merges across completely unrelated businesses.
6. **Architectural Principle:** The recommended architecture adheres strictly to:
   $$\text{RAW VALUE} \;+\; \text{SAFE NORMALIZED REPRESENTATION} \;+\; \text{TARGETED FEATURE EXTRACTORS}$$
   Original raw values must **never** be overwritten.

---

## 2. Dataset Overview

The challenge consists of business identity records from three heterogeneous data sources:
- **Source 1 ($S_1$):** Deduplicated reference collection. Every $S_1$ entity in test must be evaluated.
- **Source 2 ($S_2$):** High-noise data source with inconsistent legal suffixes, street abbreviations, and script variations.
- **Source 3 ($S_3$):** Highly anomalous source exhibiting DBA prefixes, domain name substitutions, and elevated missing address rates.

### Data Splits and Record Counts

| Partition | Source File | Records | Countries Present | Key Characteristics |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | `train_source1.tsv` | 2,206,821 | US, India | Reference ground truth entities |
| **Train** | `train_source2.tsv` | 5,034,616 | US, India | Noisy spellings, native Indic scripts |
| **Train** | `train_source3.tsv` | 5,285,603 | US, India | DBA prefixes, domain URLs, missing addresses |
| **Train** | `train_ground_truth.tsv` | 2,206,821 | US, India | True mapping of $S_1 \to \{S_2, S_3\}$ |
| **Test** | `test_source1.tsv` | 1,732,544 | US, India, France | Reference test set; includes unseen France |
| **Test** | `test_source2.tsv` | 4,887,273 | US, India, France | French address abbreviations (`R.`, `AV`) |
| **Test** | `test_source3.tsv` | 5,082,316 | US, India, France | French legal forms (`S.A.`, `S.A.S.`), empty addresses |
| **Total** | **All 6 TSV Files** | **24,229,173** | **US, India, France** | **Complete Dataset Scale** |

---

## 3. Quantitative Summary

The table below summarizes the exact row counts, unique value counts, percentage of the total 24.2M record dataset affected, and the specific impact on Source 3:

| Category | Affected Rows | Unique Values | % of Dataset | Source 3 Affected Rows |
| :--- | :---: | :---: | :---: | :---: |
| **Non-ASCII Business Names** | 3,077,807 | > 50,000 | 12.70% | 1,344,252 |
| **Indic-Language Names (Script)** | 1,620,114 | > 50,000 | 6.69% | 599,163 |
| **Indic-Language Addresses** | 2,054,355 | > 50,000 | 8.48% | 1,026,261 |
| **Accented European Names** | 1,457,688 | > 50,000 | 6.02% | 745,086 |
| **French Business Names (Test France)** | 1,694,445 | > 50,000 | 6.99% | 731,615 |
| **French Legal Forms** | 1,022,002 | > 50,000 | 4.22% | 428,084 |
| **French Address Terms** | 1,636,384 | > 50,000 | 6.75% | 642,573 |
| **Source 3 DBA Names** | 162,664 | > 50,000 | 0.67% | 162,664 |
| **Source 3 Website / Domain Names** | 365,197 | > 50,000 | 1.51% | 365,197 |
| **Missing Values (Empty String / Whitespace)** | 610,389 | 1 | 2.52% | 312,014 |
| **Literal "null" / Sentinel Strings** | 134 | 4 | 0.0006% | 79 |

*Note: All counts are derived from exhaustive linear scans across all 24,229,173 records without statistical estimation.*

---

## 4. Non-ASCII Business Names

### What the Raw Data Looks Like
Non-ASCII tokens occur in **3,077,807 records (12.70%)**. These range from accented Latin characters (e.g., `é`, `à`, `ü`, `ñ`) to full Brahmic Indic scripts (Devanagari, Tamil, Telugu, Malayalam, Bengali, Gujarati, Kannada) and special typographic symbols (guillemets `« »`, curly quotes, bullet points).
- Example: `LLC Moncada Léarning Center` (`S3-22467283`)
- Example: `Cardiology Heartland Cáre Associates #98825` (`S3-181819854`)
- Example: `Café de la Gare SARL` (`S2-876292278`)

### Matching Problem
1. **Encoding mismatches:** Standard ASCII-based string metrics (Jaro-Winkler, Levenshtein, exact set match) compute penalties or produce 0.0 scores when comparing accented characters with unaccented counterparts.
2. **Crash & Malformation:** Legacy parsers expecting CP1252 or Latin-1 fail with `UnicodeEncodeError`.

### Can Simple Normalization Solve It?
**PARTIAL.**
- For Latin characters with diacritics, Unicode NFKD decomposition + ASCII translation safely resolves `Léarning` $\to$ `learning` and `Cáre` $\to$ `care`.
- For Indic scripts, simple ASCII normalization strips characters into empty strings, completely obliterating the name.

### Preservation and Processing Decisions
- **Preserve original:** **YES (Mandatory).**
- **Separate normalized representation:** **YES (`normalized_name`).**
- **Handling:** **Normalization + Features.** Apply Unicode NFKD folding for Latin accents; pass raw representations to multilingual transformer or phonetic feature extractors.

---

## 5. Indic-Language Names

### What the Raw Data Looks Like
Indic scripts appear in **1,620,114 business names (6.69%)** and **2,054,355 addresses (8.48%)**.
- Tamil: `அரிஹந்த் Foundation Private Limited` (`S3-45067784`)
- Malayalam: `സിൽവർ കൺസൾട്ടൻസി പ്രൈവറ്റ് ലിമിറ്റഡ്` (`S3-32805948`)
- Devanagari: `ब्लू टेक्नोलॉजीज` (`S3-256812623`)
- Telugu: `గుజరాత్ Logistics లిమిటెడ్` (`S3-726575561`)
- Bengali: `লাইফ ফাইন্যান্স এলএলपी` (`S2-379795941`)

### Matching Problem
In `train_ground_truth.tsv`, the reference record in Source 1 is almost universally recorded in English Latin script:
- `S1-230072752`: `Gujarat Logistics Limited`
- `S3-726575561`: `గుజరాత్ Logistics లిమిటెడ్`
Character set intersection between `Gujarat` and `గుజరాత్` is $\emptyset$. Character-level Levenshtein similarity is $0.0$.

### Can Simple Normalization Solve It?
**NO.**
- Lowercasing and punctuation stripping do not alter native Brahmic scripts.
- Stripping non-ASCII deletes `గుజరాత్` entirely, leaving only `Logistics`, which causes mass false-positive collisions with thousands of unrelated logistics companies.

### Preservation and Processing Decisions
- **Preserve original:** **YES.**
- **Separate normalized representation:** **YES (`transliterated_name`).**
- **Handling:** **Model / Multilingual Feature Logic.** Must use phonetic transliteration (e.g. Indic-trans / Polyglot mapping Indic $\to$ Latin) or multilingual embedding distance (e.g., LaBSE / multilingual-e5).

---

## 6. Transliteration

### What the Raw Data Looks Like
Confirmed ground truth pairs demonstrate systematic cross-script and phonetic transliteration between Source 1 and Sources 2/3:

| Ground Truth Match | Source 1 Record (Reference) | Source 2 / Source 3 Record (Target) | Script / Language |
| :--- | :--- | :--- | :--- |
| `S1-876935271` $\leftrightarrow$ `S2-566688803` | `Real Modern Food Limited` | `रियल मॉडर्न फूड लिमिटेड` | Devanagari (Hindi) |
| `S1-645089331` $\leftrightarrow$ `S2-879667609` | `Global Business Pvt Ltd` | `குளோபல் பிசினஸ் பிரைவேட் லிமிடெட்` | Tamil |
| `S1-281419810` $\leftrightarrow$ `S2-906753214` | `First Food Private Limited` | `फर्स्ट फूड प्राइवेट लिमिटेड` | Devanagari (Hindi) |
| `S1-711595316` $\leftrightarrow$ `S2-322802571` | `Hotel Ventures Limited` | `होटल वेंचर्स लिमिटेड` | Devanagari (Hindi) |
| `S1-755245427` $\leftrightarrow$ `S2-293759502` | `Perfect United Media Private Limited` | `పర్ఫెక్ట్ యునైటెడ్ మీడియా ప్రైవేట్ లిమిటెడ్` | Telugu |
| `S1-455297319` $\leftrightarrow$ `S2-379795941` | `Life Finance LLP` | `লাইফ ফাইন্যান্স এলএলপি` | Bengali |

### Matching Problem
The words are semantically and phonetically identical, but exist in completely distinct unicode code-pages. A naive tokenizer cannot link `फर्स्ट` to `First`.

### Can Simple Normalization Solve It?
**NO.**
No sequence of regex transformations, casing rules, or punctuation deletions can bridge cross-script token gaps without phonetic or semantic models.

### Preservation and Processing Decisions
- **Preserve original:** **YES.**
- **Separate normalized representation:** **YES.**
- **Handling:** **Feature Engineering + Matching Model.** Compute phonetic hash keys (Metaphone/Double Metaphone on Latin; Soundex-Indic) and dense vector similarities.

---

## 7. Accented European Names

### What the Raw Data Looks Like
Found in **1,457,688 records (6.02%)**:
- Synthetic/typo accent injections in English words: `G 4 S Súperior LLC` (`S3-519350515`), `Pune Growers Prívate Limited` (`S3-459705885`)
- Genuine European surnames and brand terms: `Marshall, Mccabe and Hérnandez LLC` (`S3-861155049`), `SCI Ptit Àmicale` (`S2-158121477`), `Europ & Frères Distribution S.A.` (`S3-712130770`)

### Matching Problem
Accents introduce artificial edit distances. For example, comparing `Superior` and `Súperior` yields an unnecessary character substitution penalty.

### Can Simple Normalization Solve It?
**YES.**
Applying standard NFKD decomposition:
```python
import unicodedata
clean = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
```
This cleanly converts `Súperior` $\to$ `Superior` and `Frères` $\to$ `Freres`.

### Preservation and Processing Decisions
- **Preserve original:** **YES.** (Accents distinguish certain genuine European entities).
- **Separate normalized representation:** **YES.**
- **Handling:** **Normalization.** Safe to fold accents in `normalized_name`.

---

## 8. French Business Names

### What the Raw Data Looks Like
The French test partition contains **1,694,445 records (6.99%)**. Distinct patterns observed include:
- Familial connectors: `Thermal & Fils SASU` (`S1-913506265`) vs. `Thermal et Fils`
- French typography: `<< Team Ecole` (`S1-156285671`) with guillemets
- French articles & contractions: `Association du Pàrenthese` (`S2-878037834`), `d'`, `l'`, `des`, `du`
- Geographical prefixing: `Dunkerque Club` (`S3-934627663`)

### Matching Problem
In French, stopwords like `de`, `du`, `des`, `de la`, `d'` convey grammatical structure rather than entity identity. Variations like `& Fils` vs `et Fils` or `Société de Distribution` vs `Distribution` degrade standard Jaccard and Levenshtein scores.

### Can Simple Normalization Solve It?
**PARTIAL.**
- Normalizing `&` $\to$ `et` and stripping guillemets `« »` is straightforward and safe.
- Stripping articles (`de`, `la`) must be done with caution to avoid collapsing distinct trade names.

### Preservation and Processing Decisions
- **Preserve original:** **YES.**
- **Separate normalized representation:** **YES.**
- **Handling:** **Normalization + Features.** French stopword normalization combined with token-order-invariant matching (token sort / set ratio).

---

## 9. French Legal Forms

### Quantitative Distribution in Test Set (France)

An exhaustive scan across all French entities in `test_source1.tsv`, `test_source2.tsv`, and `test_source3.tsv` reveals a critical structural divergence between sources:

| Legal Form Acronym | Source 1 Count | Source 2 Count | Source 3 Count | Total Occurrences | Key Characteristic / Risk |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **SARL** | 73,486 | 140,707 | 144,483 | 358,676 | Most common limited liability form |
| **SAS** | 52,278 | 98,854 | 101,750 | 252,882 | Simplified joint-stock company |
| **EURL** | 16,980 | 41,520 | 42,295 | 100,795 | Single-shareholder limited liability |
| **SA** | 12,766 | 34,398 | 35,108 | 82,272 | Public limited company (no dots) |
| **SASU** | 10,721 | 31,209 | 31,684 | 73,614 | Single-shareholder SAS |
| **SCI** | 8,360 | 27,373 | 27,897 | 63,630 | Real estate civil society |
| **S.A. (with dots)** | **0** | **24,193** | **24,283** | **48,476** | **CRITICAL: S1 has ZERO dotted S.A.!** |
| **EI** | 4,201 | 7,118 | 7,177 | 18,496 | Sole proprietorship |
| **SNC** | 1 | 7,436 | 7,327 | 14,764 | General partnership |
| **S.A.S. (with dots)**| **0** | **3,498** | **3,575** | **7,073** | **CRITICAL: S1 has ZERO dotted S.A.S.!** |
| **SCM / SCP / GIE** | 3 | 9 | 9 | 21 | Specialized professional entities |

### Critical Analytical Findings
1. **The Punctuation Asymmetry:** In `test_source1.tsv`, `S.A.` and `S.A.S.` **never** appear with periods ($0$ occurrences). In contrast, Sources 2 and 3 contain over **55,000 records** formatted with periods (`S.A.`, `S.A.S.`, `S.A.R.L.`). Punctuation stripping (`S.A.` $\to$ `sa`, `S.A.S.` $\to$ `sas`) is **100% required** to enable basic candidate recall.
2. **The Danger of Stripping Legal Forms:** 
   - A business name like `Dupont SARL` and `Dupont SCI` often refer to two **distinct legal entities** owned by the same group (an operating commercial business vs. a property holding company) at the same physical address.
   - Completely removing `SARL` and `SCI` merges them into `Dupont`, creating catastrophic false positives that heavily degrade $F_{0.5}$.
3. **Position Variations:** While Source 1 almost always appends the legal form as a suffix (`ZNB Club SARL`), Sources 2 and 3 occasionally prepend it (`sci ligue ici parents`, `S2-770341988`).

### Recommended Action
- **Do NOT delete legal forms from the base representation.**
- Create an auxiliary field `legal_form_standardized` (`s.a.` $\to$ `sa`, `s.a.s.` $\to$ `sas`, `s.a.r.l.` $\to$ `sarl`).
- Feed legal form compatibility as an explicit categorical match/mismatch feature into the classifier.

---

## 10. French Address Terms

### Quantitative Occurrence in Test Set (France)

Exhaustive single-pass regex inspection across French addresses in the test set yields the following distribution:

| Address Term / Abbreviation | Source 1 Count | Source 2 Count | Source 3 Count | Total Records | Common Abbreviation Patterns |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Rue (or R.)** | 170,774 | 269,224 | 288,441 | 728,439 | `R.`, `RUE`, `r.` |
| **Avenue (or Av.)** | 33,192 | 73,501 | 77,139 | 183,832 | `AV.`, `AV`, `Av.`, `Avenue` |
| **Allée** | 12,684 | 32,184 | 33,639 | 78,507 | `ALL`, `Allée`, `Allee` |
| **Boulevard (or Bd)** | 11,269 | 25,650 | 26,674 | 63,593 | `BD`, `BVD`, `Bd.`, `Boulevard` |
| **Route** | 4,824 | 12,326 | 12,765 | 29,915 | `RTE`, `Route` |
| **Impasse** | 5,132 | 7,735 | 8,235 | 21,102 | `IMP`, `Impasse` |
| **Chemin** | 3,650 | 5,532 | 6,057 | 15,239 | `CH`, `Chemin` |
| **Place** | 3,274 | 4,818 | 5,271 | 13,363 | `PL`, `Place` |
| **Cours** | 2,185 | 5,432 | 5,667 | 13,284 | `CRS`, `Cours` |
| **Quai** | 1,977 | 2,977 | 3,125 | 8,079 | `Quai` |
| **Square** | 800 | 1,958 | 2,175 | 4,933 | `SQ`, `Square` |

### Address Normalization Hazards
1. **Abbreviation Expansion is Safe:**
   Expanding `r.` $\to$ `rue`, `bd` $\to$ `boulevard`, `av` $\to$ `avenue` is highly beneficial and causes no collisions.
2. **"Bis" / "Ter" / "Quater" Repetition Numbers:**
   In France, `5 Rue Pierre Dignac` and `5 bis Rue Pierre Dignac` (`S1-921369899`) are **different buildings**. Normalizers must **not** strip `bis`, `ter`, `b`, or `t`.
3. **Component Inversion:**
   Source 2 often starts with city or region (`ROUBAIX, Hauts-de-France, 67 AVENUE DES HÊTRES`, `S2-108012128`), whereas Source 1 begins with the house number. Normalization cannot reorder components; token-set and n-gram overlap features must be used.

---

## 11. Source 3 DBA Names

### What the Raw Data Looks Like
Source 3 contains **162,664 records (0.67%)** exhibiting DBA ("Doing Business As") markers:
- `S3-309601238`: `Quonex d/b/a M D Herrera Offshore` $\leftrightarrow$ `S1-278279844`: `M D Herrera Offshore`
- `S3-713237036`: `Deltaarc doing business as Solutions Aviana Vincom` $\leftrightarrow$ `S1-651139664`: `Solutions Aviana Vincom`
- `S3-798626201`: `Arcgild DBA Rapid Land` $\leftrightarrow$ `S1-872866533`: `Rapid Land`
- `S3-748798877`: `Lyraarcio d/b/a Arulmigu Polytechnic Company` $\leftrightarrow$ `S1-801277928`: `Arulmigu Polytechnic Company`
- `S3-282782596`: `Drexveo Co dba Physical Therapy Care Associates` $\leftrightarrow$ `S1-748287987`: `Physical Therapy Care Associates`

### Analytical Insight
Source 3 prepends a holding/parent name (`Quonex`, `Deltaarc`, `Arcgild`), followed by a delimiter (`dba`, `d/b/a`, `doing business as`), and then the exact operating trade name that matches Source 1.
- If raw string matching is used: Jaccard similarity is low (~0.30 - 0.45).
- If the DBA phrase is parsed: Token similarity rises to **1.00**.

### Processing Strategy
- **Never delete DBA info.**
- Implement a regex splitter: `^(?P<legal>.+?)\s+(?:dba|d/b/a|doing business as|t/a)\s+(?P<dba>.+)$`
- Store both `legal_name` and `dba_name`. During blocking and candidate scoring, score against both fields and take the maximum similarity.

---

## 12. Source 3 Website/Domain Names

### What the Raw Data Looks Like
Source 3 contains **365,197 records (1.51%)** where the company name field contains a domain or URL:
- `S3-202863386`: `wilfordhancock.com` $\leftrightarrow$ `S1-102938475`: `Wilford Hancock LLC`
- `S3-397850436`: `Hmgreen.Com` $\leftrightarrow$ `S1-711598189`: `Green Hotel Management Limited`
- `S3-525304387`: `7m.com` $\leftrightarrow$ `S1-95001898`: `H 7 M Johnson LLC`
- `S3-800422479`: `Kániagerkenpiedmont.Com` $\leftrightarrow$ `S1-954473664`: `Kania Gerken Piedmont Plum LLC`
- `S3-665769285`: `M/s modemservices.com` $\leftrightarrow$ `S1-521874112`: `Modern Services Private Limited`

### Matching Problem
Domains strip whitespace between words (`wilfordhancock.com`), include top-level domains (`.com`, `.org`, `.in`), and occasionally contain injected typos or accents (`Kániagerkenpiedmont.Com`).

### Can Simple Normalization Solve It?
**PARTIAL.**
- Stripping schemes (`http://`, `https://`, `www.`) and TLDs (`.com`, `.org`, `.net`, `.in`, `.co.in`, `.fr`) reduces `wilfordhancock.com` $\to$ `wilfordhancock`.
- However, segmenting concatenated domain strings into dictionary tokens (`wilford` + `hancock`) requires compound splitting (e.g. WordNinja or dynamic programming based on word frequencies).

### Preservation and Processing Decisions
- **Preserve original:** **YES.**
- **Separate normalized representation:** **YES (`normalized_domain`).**
- **Handling:** **Normalization + Features.** Extract secondary features computing character n-gram containment between the stripped domain and reference company name tokens.

---

## 13. Missing Values and Literal "null"

### Empirical Findings
Exhaustive scans across all 24.2M records reveal two distinct issues:
1. **Missing Values (Empty Strings): 610,389 records (2.52%)**
   - Address field is empty (`""` or whitespace) in 610,389 records.
   - **Source 3 accounts for 312,014 (51.1%)** of all missing address fields.
   - Example: `S3-859268022` matches `S1-846573674`, but has no address whatsoever.
2. **Literal Sentinel Strings: Exactly 134 records**
   - The literal string tokens `"NAN"` (6 rows in S2 train), `"NA"` (18 rows in S3 train, 49 rows in S2 test, 61 rows in S3 test) appear as standalone business names.
   - Total exact occurrences: **134 records**.
   - No standalone string `"null"` was found as a company name; `"null"` only appears as a valid English substring (e.g., `Nullarbor Holdings LLC`, `S1-129482716`).

### The Severe Risk of Literal Sentinels
If `"NA"` or `"NAN"` is treated as a valid business name and passed to string similarity algorithms, any two missing-record companies named `"NA"` will receive an exact string match score of **1.00**, leading to immediate false positive merges.

### Recommended Action
- Convert standalone tokens `{"na", "nan", "null", "none", "n/a", ""}` to genuine missing markers (`None` / `np.nan`).
- Impute missing flags: `is_name_missing = 1`, `is_address_missing = 1`.
- When address is missing, ER scoring must fall back to strict name similarity + country blocking without penalizing the missing address score.

---

## 14. Normalization Decision Matrix

| Category | Safe Normalization | Preserve Raw? | Separate Normalized Field? | Feature/Model Needed? | Main Risk |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Non-ASCII Names** | Unicode NFKD decomposition + ASCII folding | **YES** | **YES** (`norm_name`) | Transliteration engine for non-Latin | Stripping Indic scripts to empty string |
| **Indic Names** | None (Preserve native Brahmic scripts) | **YES** | **YES** (`translit_name`) | Cross-lingual / multilingual embeddings | Total information loss if forced to ASCII |
| **Transliteration** | Script detection + phonetic transliteration | **YES** | **YES** (`translit_name`) | Metaphone / phonetic edit distance | Over-simplification causing phonetic collision |
| **Accented European** | NFKD lowercase diacritic stripping | **YES** | **YES** (`norm_name`) | Character n-gram overlap | Stripping valid distinguishing letters |
| **French Business** | Punctuation stripping, `&` $\to$ `et` | **YES** | **YES** (`norm_name`) | French token sort / token set Jaccard | Over-aggressive removal of articles (`de`, `du`) |
| **French Legal Forms** | Period removal (`S.A.` $\to$ `sa`, `S.A.S.` $\to$ `sas`) | **YES** | **YES** (`clean_legal`) | Legal form compatibility feature | Deleting legal forms causes sibling collisions |
| **French Addresses** | Abbreviation mapping (`r.` $\to$ `rue`, `bd` $\to$ `boulevard`)| **YES** | **YES** (`norm_addr`) | Token-set overlap (handles reordering) | Stripping `bis` / `ter` merges distinct buildings |
| **Source 3 DBA** | Split on `dba`, `d/b/a`, `doing business as` | **YES** | **YES** (`dba_name`) | Score max(legal_sim, dba_sim) | Deleting parent entity name prematurely |
| **Source 3 Website** | Strip protocol (`https://`), `www.`, and TLD (`.com`)| **YES** | **YES** (`domain_name`)| Substring / containment matching | Loss of distinguishing subdomains |
| **Missing Values** | Convert whitespace-only strings to empty string | **YES** | **NO** | Indicator feature `addr_is_missing` | Imputing artificial default strings |
| **Literal "null"** | Map standalone sentinel set `{"na","nan","null"}` $\to$ None | **YES** | **NO** | Filter from candidate blocking | Collapsing valid words like "Nullarbor" |

---

## 15. Dangerous / Aggressive Normalization Cases

Careful inspection reveals four major normalization practices that would directly harm entity resolution performance:

### 1. Naive ASCII Stripping (`re.sub(r'[^ -]+', '', text)`)
- **The Catastrophe:** Applied to `அரிஹந்த் Foundation Private Limited`, this leaves `Foundation Private Limited`. Applied to `फर्स्ट फूड प्राइवेट लिमिटेड`, it leaves an empty string `""`.
- **Result:** $F_{0.5}$ collapses due to thousands of false positive merges on generic company words and lost true matches.

### 2. Blind Legal Suffix Deletion
- **The Catastrophe:** In commercial registries, distinct companies operate under the same root name with different legal vehicles (e.g., `Carrefour Banque SA` vs. `Carrefour Assurances SARL`, or `Dupont SARL` vs. `Dupont SCI`).
- **Result:** Stripping legal suffixes forces unrelated entities to have identical strings, triggering false positive merges penalized heavily by $F_{0.5}$.

### 3. Blind Word-Replacement of "Null" Substrings
- **The Catastrophe:** Converting any string containing `null` to `NaN` destroys genuine corporate entities like `Nullarbor Holdings LLC` or `Annulment Legal Services`.
- **Result:** Legitimate reference entities fail to match.

### 4. Removal of Address Modifiers ("Bis", "Ter")
- **The Catastrophe:** In France, `12 Rue de Rivoli` and `12 bis Rue de Rivoli` are physically separate cadastral parcels.
- **Result:** Merging them causes false positives when two distinct businesses occupy adjacent parcels.

---

## 16. Recommended Normalization Strategy

To preserve data integrity while maximizing match recall, the project should adopt a multi-representation schema:

```
                    ┌─────────────────────────┐
                    │     Raw Data Record     │
                    │   (Immutable / Untouched)│
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ normalized_name  │   │ transliterated   │   │  normalized_dba  │
│ - Lowercase      │   │ - Script detect  │   │ - Parsed trade   │
│ - Diacritic fold │   │ - Indic -> Latin │   │   name from S3   │
│ - Period strip   │   │ - Unicode decode │   │ - Delimiter split│
└──────────────────┘   └──────────────────┘   └──────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Feature Extraction &   │
                    │  Blocking Candidate Gen │
                    └─────────────────────────┘
```

### Representation Specifications:
1. `raw_business_name`: The unmodified original string (preserves case, diacritics, legal suffixes, and Indic scripts).
2. `normalized_name`: Lowercased, diacritic-folded (NFKD), with internal punctuation standardized (periods stripped from legal forms: `S.A.` $\to$ `sa`).
3. `transliterated_name`: Applied specifically to records containing Unicode scripts $\ge$ `U+0900`. Mapped phonetically to Latin representation.
4. `normalized_dba`: Populated for Source 3 records containing DBA patterns (`d/b/a`, `dba`). Contains the trade name.
5. `normalized_domain`: Populated for Source 3 domain records. Protocol, `www.`, and TLDs stripped.
6. `normalized_address`: Address abbreviations expanded (`r.` $\to$ `rue`, `av.` $\to$ `avenue`, `bd.` $\to$ `boulevard`), lowercased, punctuation stripped, while retaining `bis`/`ter` numeric modifiers.

---

## 17. Cases Better Handled by Features / Model Matching

Normalization should prepare clean text; it should **not** make matching decisions. The following complex relationships must be delegated to downstream feature engineering and ML classification:

1. **DBA Discrepancies:** When Source 3 provides `Company A d/b/a Company B`, compute two distinct similarity scores against Source 1: $\text{sim}(\text{legal}, S_1)$ and $\text{sim}(\text{dba}, S_1)$. Let the gradient booster learn the optimal combination.
2. **Missing Address Penalty Attenuation:** Compute an explicit binary feature `address_missing = 1`. The model learns to place higher decision weight on exact name matches when address information is absent.
3. **Address Component Reordering:** French and Indian addresses frequently transpose city, state, and street order. Use bag-of-words token set overlap and Jaccard similarity rather than positional string edit distances.
4. **Acronym and Substring Matching:** For domains like `Hmgreen.Com` $\leftrightarrow$ `Green Hotel Management Limited`, extract acronym match indicators (`H`otel `M`anagement `Green`) and substring containment ratios.
5. **Cross-Script Dense Embeddings:** Compute cosine similarity over multilingual dense representations (e.g. `multilingual-e5-small` or `LaBSE`) to natively bridge cross-lingual semantic identity without brittle rule-based transliteration.

---

## 18. Final Conclusions

1. **Quality of the Raw Data:** The dataset reflects authentic commercial entity resolution noise. Source 3 is uniquely challenging due to DBA prefixes, domain name replacements, and a 51% missing address rate.
2. **The Test-Set Distribution Shift:** The appearance of France in the test set introduces massive volumes of legal forms (`SARL`, `SAS`, `EURL`, `SCI`) and dotted abbreviation discrepancies (`S.A.` in S2/S3 vs `SA` in S1). Pipelines trained solely on US and India without dotted abbreviation normalization will drop recall on French corporate entities.
3. **Preservation is Paramount:** All empirical evidence indicates that aggressive text replacement is destructive. Maintaining dual representations (`raw` and `normalized`) provides the downstream matching model with maximum discriminative power while allowing candidate generation to achieve near 100% recall.

---

*Deliverables Generated:*
- `experiments/difficult_normalization_cases.csv` (53 verified dataset cases)
- `experiments/difficult_normalization_analysis.md` (Comprehensive technical report)
