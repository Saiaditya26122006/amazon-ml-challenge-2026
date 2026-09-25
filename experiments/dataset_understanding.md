# Amazon ML Challenge 2026: Business Entity Resolution
# Complete Dataset Understanding Report

**Date:** 2026-09-25
**Purpose:** Exploratory data analysis only. No models, no code, no external data.

---

## PART 1: DATASET STRUCTURE

### 1.1 What Each File Represents

The dataset is organized into **training** and **test** splits, each containing records from 3 independent data sources:

| File | Description |
|------|-------------|
| `train_source1.tsv` | Deduplicated reference source (S1) for training |
| `train_source2.tsv` | Second independent source (S2) for training |
| `train_source3.tsv` | Third independent source (S3) for training |
| `train_ground_truth.tsv` | Known matches between S1 and S2/S3 for training |
| `test_source1.tsv` | Deduplicated reference source (S1) for testing |
| `test_source2.tsv` | Second independent source (S2) for testing |
| `test_source3.tsv` | Third independent source (S3) for testing |

### 1.2 Why Source 1 Is Different from Source 2 and Source 3

**Source 1 is the deduplicated reference source.** It contains cleaner, more standardized records:
- **Zero missing addresses** (0% empty) vs 3.3% empty in S2/S3
- **Zero non-ASCII characters in names** (0%) vs 15% in S2 and 11% in S3
- Addresses use full words more often (e.g., "Street" instead of "St", "Avenue" instead of "Ave")
- Names typically include full legal suffixes ("Private Limited" instead of "Pvt Ltd")
- Source 1 has **no `null` strings** in addresses while S2 has 2.62% and S3 has 2.48%

**Source 2 and Source 3** are noisy, partial, independently-collected records:
- Both contain records in Indic scripts (Hindi, Tamil, Bengali, etc.)
- Both have missing addresses (~3.3%)
- Both use abbreviated street names (St, Ave, Rd, Dr, Ln, Blvd)
- Both contain the literal string "null" in addresses
- Both contain typos, accented characters, word-order variations
- Source 3 additionally contains DBA (doing-business-as) names and website URLs as names

### 1.3 What `entity_id` Means

`entity_id` is a **unique identifier** for each record. Every entity ID is unique within its file and across all files. There are zero duplicate IDs anywhere in the dataset.

### 1.4 What the S1-, S2-, S3- Prefixes Mean

The prefix encodes which **source** the record comes from:
- `S1-` = Source 1 (the deduplicated reference)
- `S2-` = Source 2 (noisy independent source)
- `S3-` = Source 3 (noisy independent source)

There is no separate "source" column; the prefix is the only indicator.

### 1.5 What Each Column Means

| Column | Meaning |
|--------|---------|
| `entity_id` | Unique record ID with source prefix (S1-/S2-/S3-) |
| `business_name` | Name of the business, may include abbreviations, legal suffixes, typos, transliterations, DBA names, or website URLs |
| `business_address` | Physical address, may be partial, reordered, abbreviated, use landmarks, or contain "null" |
| `country` | Country label: "US", "India" in training; "US", "India", "France" in test |

### 1.6 Relationship Between the Three Sources

The three sources represent **independent databases** describing the same real-world businesses. They share **no common identifiers** -- only overlapping (but noisy) attribute values (name, address, country). The task is to determine which records across sources refer to the same real-world business.

Source 1 is the anchor: we match S2 and S3 records **to** S1 entities.

### 1.7 What `train_ground_truth.tsv` Represents

It contains one row per S1 training entity. The `matched_entity_ids` column lists all S2 and S3 entity IDs that refer to the same real-world business. If the list is empty, the S1 entity has **no known counterpart** in S2 or S3 (a "singleton").

### 1.8 Concrete Example

**Entity: "Raj Investments LLP" (S1-55344266)**

| Source | entity_id | business_name | business_address | country |
|--------|-----------|---------------|------------------|---------|
| S1 | S1-55344266 | Raj Investments LLP | 6(29), C.I.T. Colony, 2Nd Main Road Mylapore, Chennai, Tamil Nadu | India |
| S2 | S2-249013014 | ராஜ் இன்வெஸ்ட்மெண்ட்ஸ் எல்எல்பி | 6(29), C.I.T. COLONY, 2ND MAIN ROAD MYLAPORE, CHENNAI, Tamil Nadu | India |
| S2 | S2-197070651 | (Tamil transliteration) | (variation of same address) | India |
| S3 | S3-478195123 | Raj Investments எல்எல்பி | 6(29), C.i.t. Colony, 2Nd Main Road Mylapore, Chennai, TN | India |
| S3 | S3-384364074 | ராஜ் இன்வெஸ்ட்மெண்ட்ஸ் எல்எல்பி | 6(29), C.i.t. Colony, 2Nd Main Road Mylapore, Chennai, தமிழ்நாடு | India |

Ground truth row: `S1-55344266  S2-249013014,S2-197070651,S3-478195123,S3-384364074`

Notice the variations:
- English name vs Tamil script transliteration
- Mixed English + Tamil ("Raj Investments எல்எல்பி")
- Case differences (Colony vs COLONY)
- State abbreviation (Tamil Nadu vs TN vs தமிழ்நாடு)

---

## PART 2: DATASET SIZE

| File | Rows | Columns | Column Names | Unique IDs |
|------|------|---------|-------------|------------|
| train_source1.tsv | 2,206,821 | 4 | entity_id, business_name, business_address, country | 2,206,821 |
| train_source2.tsv | 5,034,616 | 4 | entity_id, business_name, business_address, country | 5,034,616 |
| train_source3.tsv | 5,285,603 | 4 | entity_id, business_name, business_address, country | 5,285,603 |
| train_ground_truth.tsv | 2,206,821 | 2 | source1_entity_id, matched_entity_ids | 2,206,821 |
| test_source1.tsv | 1,732,544 | 4 | entity_id, business_name, business_address, country | 1,732,544 |
| test_source2.tsv | 4,887,273 | 4 | entity_id, business_name, business_address, country | 4,887,273 |
| test_source3.tsv | 5,082,316 | 4 | entity_id, business_name, business_address, country | 5,082,316 |

**Key observations:**
- All data types are strings (object dtype)
- All IDs are unique within every file -- zero duplicates
- S2 and S3 are each ~2.3x larger than S1
- Ground truth has exactly the same number of rows as train_source1 (every S1 entity has a row)
- Total training records: ~12.5M; total test records: ~11.7M
- The naive comparison space for test is 1.7M x (4.9M + 5.1M) = ~17 billion pairs

---

## PART 3: DATA QUALITY

### 3.1 Missing Values

| File | entity_id empty | business_name empty | business_address empty | country empty |
|------|----------------|--------------------|-----------------------|---------------|
| train_source1 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| train_source2 | 0 (0.00%) | 0 (0.00%) | 168,967 (3.36%) | 0 (0.00%) |
| train_source3 | 0 (0.00%) | 0 (0.00%) | 175,916 (3.33%) | 0 (0.00%) |
| test_source1 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| test_source2 | 0 (0.00%) | 0 (0.00%) | 129,408 (2.65%) | 0 (0.00%) |
| test_source3 | 0 (0.00%) | 0 (0.00%) | 136,098 (2.68%) | 0 (0.00%) |

**Whitespace-only values:** Zero across all files and columns.

### 3.2 Duplicate Rows and IDs

All files have **zero duplicate rows** and **zero duplicate entity IDs**.

### 3.3 Non-ASCII Characters in Names

| File | Names with non-ASCII | Percentage |
|------|---------------------|------------|
| train_source1 | 0 | 0.00% |
| train_source2 | 764,608 | 15.19% |
| train_source3 | 606,737 | 11.48% |
| test_source1 | 40,789 | 2.35% |
| test_source2 | 928,158 | 18.99% |
| test_source3 | 737,515 | 14.51% |

**Critical finding:** Source 1 training has **zero** non-ASCII names but Source 1 test has 2.35% non-ASCII names (likely French characters: accents, cedillas). This is a distribution shift.

### 3.4 Name and Address Length Extremes

| File | Name min | Name max | Name mean | Addr min | Addr max | Addr mean | Names>100 | Addr>200 |
|------|----------|----------|-----------|----------|----------|-----------|-----------|----------|
| train_source1 | 3 | 105 | 24.0 | 11 | 256 | 52.1 | 2 | 52 |
| train_source2 | 2 | 104 | 25.1 | 0 | 249 | 46.2 | 3 | 53 |
| train_source3 | 2 | 123 | 25.2 | 0 | 240 | 46.7 | 3 | 58 |
| test_source1 | 3 | 92 | 23.8 | 11 | 268 | 57.2 | 0 | 63 |
| test_source2 | 2 | 102 | 25.7 | 0 | 269 | 50.4 | 1 | 126 |
| test_source3 | 2 | 103 | 25.7 | 0 | 267 | 48.7 | 3 | 108 |

### 3.5 "null" Strings in Addresses

| File | Count | Percentage |
|------|-------|------------|
| train_source1 | 43 | 0.00% |
| train_source2 | 131,794 | 2.62% |
| train_source3 | 130,844 | 2.48% |

These are literal "null" strings in the data, not actual NULL/NaN values. Example: `"5Th Floor, Bbr Avenue, null, KANSAS CITY, MO"`.

### 3.6 Implications for Entity Resolution

1. **Missing addresses in S2/S3 (~3.3%)** means name-only matching is required for ~170K records per source
2. **Transliterated names (15% in S2)** means string similarity on raw text will fail -- need script-aware approaches
3. **"null" strings** must be stripped/handled to avoid false address similarity
4. **Source 1 is cleaner** -- it's the reference; S2/S3 are the noisy candidates
5. **No missing names** -- every record has a business name, making it the most reliable matching signal
6. **Very few extreme-length outliers** -- name/address length distributions are well-behaved

---

## PART 4: BUSINESS NAME ANALYSIS

### 4.1 Unique Names and Duplicates

| File | Total | Unique | Duplicates | Dup % |
|------|-------|--------|------------|-------|
| train_source1 | 2,206,821 | 1,539,229 | 667,592 | 30.25% |
| train_source2 | 5,034,616 | 4,402,009 | 632,607 | 12.57% |
| train_source3 | 5,285,603 | 4,651,609 | 633,994 | 11.99% |

**30% of S1 names are not unique!** This means name alone is insufficient for matching -- many different businesses share the same name.

### 4.2 Most Repeated Names

**Source 1 top repeated names:**
| Name | Count |
|------|-------|
| Primary Care Group | 253 |
| Ear Nose & Throat Group | 251 |
| Pediatric Group | 222 |
| Womens Health Group | 220 |
| Physical Therapy Group | 218 |
| Pediatric Dental Group | 216 |
| Behavioral Health Group | 215 |
| Chiropractic Group | 209 |
| Orthopedic Group | 208 |
| Eye Group | 207 |

These are generic medical practice names that appear across many different physical locations. Each is a **different real-world business** at a different address.

**Source 2 top repeated names:** "Primary Care" (320), "Physical Therapy" (307), "Womens Health" (297), "Urgent Care" (297). Note: S2 often **drops the word "Group"** from S1 names.

**Source 3 top repeated names:** "Primary Care" (421), "Physical Therapy" (399), "Pediatric Dental" (393). Same pattern as S2.

### 4.3 Name Length Statistics

| File | Min | Max | Mean | Median |
|------|-----|-----|------|--------|
| train_source1 | 3 | 105 | 24.0 | 24 |
| train_source2 | 2 | 104 | 25.1 | 25 |
| train_source3 | 2 | 123 | 25.2 | 25 |

Shortest names: "Raa", "Beo", "Dao" (S1); "MT", "CS" (S2); "GM", "AC" (S3)

Longest name (S1): "164/B-43 Vinayaka.Plaza 2Nd Floor 24Th Cross Ro Ad 6Th Block Jayanagar Bangalore 560082 Breweries Pvt Ltd" (105 chars -- an address embedded in the name field)

### 4.4 Legal Suffix Patterns

| Pattern | S1 Count | S2 Count | S3 Count |
|---------|----------|----------|----------|
| Corp | 34,738 | 141,773 | 140,236 |
| Corporation | 14,372 | 62,623 | 58,097 |
| Pvt | 121,462 | 189,270 | 220,353 |
| Private | 432,394 | 528,131 | 639,861 |
| Ltd | 148,598 | 398,464 | 427,781 |
| Limited | 522,340 | 528,795 | 673,480 |
| LLC | 355,736 | 528,303 | 571,362 |
| Inc | 238,309 | 400,229 | 419,917 |
| & | 111,897 | 209,076 | 216,937 |
| and | 57,296 | 118,201 | 122,220 |
| dba | 6 | 16 | 31,629 |

**Key patterns:**
- S1 prefers full forms ("Private Limited"), S2/S3 often abbreviate ("Pvt Ltd")
- `dba` appears almost exclusively in S3 (31,629 occurrences) -- "doing business as" trade names
- `&` and "and" are used interchangeably across sources

### 4.5 Observed Name Variation Patterns (with real examples)

**Corp vs Corporation:**
```
S1: 'Pretty Constructions Corporation'
S2: 'Smt PRETTY CONSTRUCTIONS (CORP)'

S1: 'Legacy Business Corporation'
S2: 'Legacy Business Corp Corp'
```

**Ltd vs Limited:**
```
S1: 'Diksha Technologies Private Limited'
S2: 'Diksha Technologies Private Ltd'

S1: 'Apar Engineering (India) Private Limited'
S2: 'Apar Engineering (lndia) Private Ltd'     <-- note: lowercase L instead of I in "lndia"
```

**Transliteration (English to Indic script):**
```
S1: 'Raj Investments LLP'
S2: 'ராஜ் இன்வெஸ்ட்மெண்ட்ஸ் எல்எல்பி'  (Tamil script)

S1: 'Ss Food Private Limited'
S2: 'एसएस फूड प्राइवेट लिमिटेड'  (Hindi/Devanagari script)
```

**Mixed script:**
```
S1: 'Raj Investments LLP'
S3: 'Raj Investments எல்எல்பி'  (English + Tamil for "LLP")
```

**DBA / trade names (Source 3):**
```
S1: 'Pawan Pharmaceuticals Clinic'
S3: 'Jaxfaye DBA: Pawan Pharmaceuticals Clinic'

S1: 'Aguilar Diversified LLC'
S3: 'Nexnovi DBA Aguilar Diversified LLC'
```

**Website URLs as business names (Source 3):**
```
S1: 'Maure Williams Colombier Inc'
S3: 'maurewilliamscolombier.com'

S1: 'Summit Health LLC'
S3: 'summithealth.com'
```

**Typos:**
```
S1: 'Payne Enterprises'
S2: 'Payne Enterpires'         (missing 's', swapped letters)
S2: 'PAYNE-ENRTPRMISES'        (scrambled letters, hyphenated)
S3: 'Payne Etrepndiels'        (heavily corrupted)
```

**Accented characters:**
```
S1: 'Payne Enterprises'
S2: 'Payne Énterprises'        (accented E)
```

**Word-order changes:**
```
S1: 'Dahlia Power Reliable Scientific LLC'
S2: 'Dahlia Power Reliable'                (dropped words)
S2: 'Dahlia Power Reliable Scientific'     (dropped "LLC")
```

**Added/removed suffixes:**
```
S1: 'Payne Enterprises'
S3: 'Payne Enterprises  LLC'   (added LLC with extra space)

S1: 'Maure Williams Colombier Inc'
S3: 'Maure Williams Inc Center' (reordered + added word)
```

**Completely different name for same entity (nickname/alias):**
```
S1: 'Maure Williams Colombier Inc'
S3: 'Dréxkor'                              (totally different name, same address)
```

---

## PART 5: ADDRESS ANALYSIS

### 5.1 Missing Addresses

| File | Empty | Percentage |
|------|-------|------------|
| train_source1 | 0 | 0.00% |
| train_source2 | 168,967 | 3.36% |
| train_source3 | 175,916 | 3.33% |
| test_source1 | 0 | 0.00% |
| test_source2 | 129,408 | 2.65% |
| test_source3 | 136,098 | 2.68% |

Source 1 always has addresses. S2/S3 are missing ~3% of the time.

### 5.2 Address Uniqueness

| File | Total | Unique | Repeated |
|------|-------|--------|----------|
| train_source1 | 2,206,821 | 2,130,606 | 76,215 |
| train_source2 | 5,034,616 | 4,337,262 | 697,354 |
| train_source3 | 5,285,603 | 4,632,765 | 652,838 |

### 5.3 Street Abbreviation Patterns

Source 1 overwhelmingly uses **full street type names**, while S2/S3 split roughly 50/50 between full and abbreviated:

| Pattern | S1 | S2 | S3 |
|---------|-----|-----|-----|
| Street | 309,331 (14.0%) | 337,310 (6.7%) | 357,143 (6.8%) |
| St | 16,162 (0.7%) | 333,485 (6.6%) | 331,436 (6.3%) |
| Road | 461,781 (20.9%) | 669,292 (13.3%) | 619,124 (11.7%) |
| Rd | 19,722 (0.9%) | 330,958 (6.6%) | 326,238 (6.2%) |
| Avenue | 189,785 (8.6%) | 193,632 (3.9%) | 212,211 (4.0%) |
| Ave | 3,180 (0.1%) | 224,070 (4.5%) | 224,220 (4.2%) |
| Drive | 221,544 (10.0%) | 215,965 (4.3%) | 241,783 (4.6%) |
| Dr | 8,330 (0.4%) | 283,537 (5.6%) | 281,587 (5.3%) |
| Lane | 107,929 (4.9%) | 118,512 (2.4%) | 124,994 (2.4%) |
| Ln | 1,294 (0.1%) | 115,505 (2.3%) | 116,402 (2.2%) |

### 5.4 PIN/ZIP Codes

| File | 6-digit PIN | 5-digit ZIP |
|------|-------------|-------------|
| train_source1 | 1,656 (0.08%) | 145,601 (6.60%) |
| train_source2 | 41,851 (0.83%) | 327,300 (6.50%) |
| train_source3 | 42,140 (0.80%) | 343,630 (6.50%) |

PIN/ZIP codes are present in a minority of records. S2/S3 have more Indian PIN codes than S1.

### 5.5 Landmark References

"Near" keyword (Indian-style landmark references): S1 2.59%, S2 2.21%, S3 1.69%.

### 5.6 Address Variation Examples (from matched pairs)

**Case difference + prefix removal:**
```
S1: 'No. 35, Brentwood Apartments, Defence Colony, 2Nd Main, Indiranagar, Bangalore, Karnataka'
S2: '35 , BRENTWOOD APARTMENTS, DEFENCE COLONY, 2ND MAIN, INDIRANAGAR, BANGALORE, Karnataka'
```

**Abbreviation + removal of house number:**
```
S1: '5604 Brooklyn Avenue, Kansas City, MO'
S2: 'BROOKLYN AVENUE, KANSAS CITY, MO'                  (house number removed)
```

**State full name vs abbreviation:**
```
S1: '8 Forman Road, Currie, MN'
S3: '8 Forman Rd, Curie, Minnesota'                     (Rd vs Road, MN vs Minnesota, typo in "Curie")
```

**Component reordering:**
```
S1: '216 Metropolitan Drive, NY, Rochester'
S2: '1 METROPOLITAN DR, ROCHESTER, NY'                  (different house number!)

S1: 'MN, Madison, 2476 261st Avenue'
S3: '##2476 261st Ave, Madison, Minnesota'               (## prefix, Ave vs Avenue)
```

**Partial addresses:**
```
S1: 'C/O Gurnav Singh Saluja, Beside Zudio, Kultapara, Sadar, Sambalpur, Orissa'
S2: 'C/O GURNAV SINGH SALUJA, SADAR, Odisha'            (many components dropped, state name changed)
```

**Typos in addresses:**
```
S1: '4604 Charleston Street, Broken Arrow, OK'
S2: '4604 CHARLESTON ST, BROKE NARROW CDP, OK'           ("Broken Arrow" -> "BROKE NARROW CDP")
```

---

## PART 6: COUNTRY ANALYSIS

### 6.1 Training Data Countries

| Source | US | India |
|--------|------|--------|
| train_source1 | 1,323,633 (60.0%) | 883,188 (40.0%) |
| train_source2 | 3,016,817 (59.9%) | 2,017,799 (40.1%) |
| train_source3 | 3,170,056 (60.0%) | 2,115,547 (40.0%) |

Training data contains **only US and India**, with a ~60/40 split.

### 6.2 Test Data Countries

| Source | India | US | France |
|--------|-------|------|--------|
| test_source1 | 809,986 (46.8%) | 663,106 (38.3%) | 259,452 (15.0%) |
| test_source2 | 2,312,565 (47.3%) | 1,871,330 (38.3%) | 703,378 (14.4%) |
| test_source3 | 2,405,000 (47.3%) | 1,945,701 (38.3%) | 731,615 (14.4%) |

### 6.3 Key Differences

1. **France is new in the test set** -- ~15% of test entities are French, with zero French training data
2. **Country distribution shift:** Training is 60/40 US/India; test is 47/38/15 India/US/France
3. India becomes the largest segment in test (47.3%) vs second-largest in training (40%)
4. Country match rate in ground truth is **100%** (all matched pairs share the same country)

### 6.4 French Entity Characteristics

From test set samples:
- French legal suffixes: SARL, SAS, SASU, SCI, EURL, S.A., S.A.S
- French address patterns: "Rue", "Boulevard", "Avenue", "Allée", accented characters (é, è, ê, à)
- Region names: Nouvelle-Aquitaine, Hauts-de-France, etc.
- Department names: Gironde, Nord, Loire-Atlantique
- Accent variations between sources (e.g., "Àmicale" vs "Amicale")

---

## PART 7: GROUND TRUTH ANALYSIS

### 7.1 Match Distribution

| Metric | Value |
|--------|-------|
| Total S1 entities | 2,206,821 |
| Zero matches (singletons) | 123,247 (5.58%) |
| Exactly one match | 119,157 (5.40%) |
| More than one match | 1,964,417 (89.02%) |
| Average matches per entity | 3.46 |
| Maximum matches for one entity | 11 |

### 7.2 Match Count Distribution

| Matches | Count | Percentage |
|---------|-------|------------|
| 0 | 123,247 | 5.58% |
| 1 | 119,157 | 5.40% |
| 2 | 375,212 | 17.00% |
| 3 | 530,841 | 24.05% |
| 4 | 484,115 | 21.94% |
| 5 | 321,957 | 14.59% |
| 6 | 164,868 | 7.47% |
| 7 | 63,968 | 2.90% |
| 8 | 18,680 | 0.85% |
| 9 | 4,205 | 0.19% |
| 10 | 534 | 0.02% |
| 11 | 37 | 0.00% |

The **most common case is 3 matches** (24%). The distribution peaks at 3-4 matches and falls off quickly after 6.

### 7.3 S2 vs S3 Match Breakdown

| Metric | Count |
|--------|-------|
| Total S2 match references | 3,693,619 |
| Total S3 match references | 3,944,746 |
| Entities matching BOTH S2 and S3 | 1,776,047 (80.5% of matched entities) |
| Entities matching only S2 | 143,029 (6.5%) |
| Entities matching only S3 | 164,498 (7.5%) |

S3 has slightly more matches than S2. The vast majority (80.5%) of matched entities have counterparts in **both** S2 and S3.

### 7.4 Real Examples

**Singleton (zero matches):**
```
S1-302869473 -> (none)
S1-262997549 -> (none)
S1-508022910 -> (none)
```

**Single match:**
```
S1-116043204 -> S3-85523430
S1-473377609 -> S3-433876173
```

**Multi-match (5 matches):**
```
S1-965667 -> S2-681193310, S2-743505751, S3-775321672, S3-11291185, S3-860443364
Entity: 'Maure Williams Colombier Inc' | '85 Wayne Avenue, Ticonderoga, NY'
  Matches include:
    S2: 'Maure Wilblims Colombier Inc' (typo)
    S2: 'Maure Williams Colombier' (dropped suffix)
    S3: 'Dréxkor' (completely different name!)
    S3: 'maurewilliamscolombier.com' (URL)
    S3: 'Maure Williams Inc Center' (reordered + added word)
```

**Maximum matches (11):**
```
S1-765235386: 'Vijay Ace Business' | Pune, Maharashtra
  Has 5 S2 matches + 6 S3 matches
  S2 variants include Hindi transliteration: 'विजय एस बिजनेस'
  S2 word-order swap: 'VIJAY BUSINESS ACE'
```

---

## PART 8: MATCH QUALITY / NOISE ANALYSIS

Based on analysis of 182,932 true-match pairs from the first 50,000 matched S1 entities:

### 8.1 Name Similarity in True Matches

| Metric | Value |
|--------|-------|
| Exact name match | 4.64% |
| Normalized name match (lowercase + strip) | 10.78% |
| Mean name length difference | 3.8 characters |
| Median name length difference | 2 characters |
| Max name length difference | 67 characters |
| Mean name token Jaccard | 0.561 |
| Median name token Jaccard | 0.600 |
| Jaccard = 0 (zero token overlap) | 28,872 pairs (15.8%) |
| Jaccard = 1 (perfect token overlap) | 37,395 pairs (20.4%) |
| Jaccard >= 0.5 | 129,637 pairs (70.9%) |

### 8.2 By Source

| Metric | S1 <-> S2 | S1 <-> S3 |
|--------|-----------|-----------|
| Pairs sampled | 88,396 | 94,536 |
| Exact name match | 4.69% | 4.60% |
| Normalized name match | 11.14% | 10.45% |
| Name Jaccard mean | 0.553 | 0.569 |
| Address Jaccard mean | 0.587 | 0.463 |

S3 has slightly higher name similarity but **lower address similarity** than S2. This suggests S3 has noisier/more partial addresses.

### 8.3 Address Similarity in True Matches

| Metric | Value |
|--------|-------|
| Exact address match | 2.28% |
| Mean address token Jaccard | 0.523 |
| Median address token Jaccard | 0.500 |

### 8.4 Country Match in True Matches

**100%** of true-match pairs share the same country. This is a critical blocking signal.

### 8.5 What These Numbers Mean

- **Only 4.6% exact name match** -- raw string comparison is nearly useless
- **Only 10.8% match after lowercasing** -- case normalization helps but is far from sufficient
- **15.8% zero name token overlap** -- a significant fraction of true matches have completely different name tokens (transliterations, URLs, nicknames)
- **70.9% have Jaccard >= 0.5** -- the majority of matches do share some name tokens
- **Only 2.3% exact address match** -- addresses are heavily varied
- **100% country match** -- country is a perfect blocking key for known matches

---

## PART 9: NEGATIVE / HARD-NEGATIVE ANALYSIS

### 9.1 Same Name, Different Business (NOT a match)

These are records that share the **exact same business name** but are **different entities** at different addresses:

```
NOT matched:
  S1: S1-133037285 | 'Christ Chapel' | '2100 Cameron Drive, Dundalk, MD' | US
  S2: S2-980137130 | 'Christ Chapel' | '3565 BAXTER DR, MT, HELNA' | US

NOT matched:
  S1: S1-865131206 | 'Helios' | '66 Edgewood Street, Bridgeport, CT' | US
  S2: S2-209746679 | 'HELIOS' | 'WINSTON-SALEM, 517 OAK SUMMIT ROAD, NC' | US

NOT matched:
  S1: S1-791217329 | 'Indian Brothers Private Limited' | '#17/1, Lalbagh Road, Bangalore, Karnataka' | India
  S2: S2-903446816 | 'indian brothers private limited' | 'পশ্চিমবঙ্গ, DOOR NO 49...' | India

NOT matched:
  S1: S1-514155563 | 'Horizon LLC' | '2025 Sterigere Street, West Norriton, PA' | US
  S2: S2-668189279 | 'Horizon Llc' | '7019 GEOGRIA AVE, WASHINGTON, DC' | US
```

### 9.2 Generic/Common Business Names

Names like "Primary Care Group" appear **253 times in S1** alone, each at a different address:
```
'Primary Care Group' (15 S1 instances):
  S1-162593001 | '8190 Tr 73, Old Fort, OH'
  S1-754988004 | '277 Whitehall Road, Hempstead, NY'
  S1-389422044 | '142 Autumn Ridge Drive, Daniels, WV'
```

These are entirely different businesses that happen to share the same name. Matching on name alone would produce massive false positives.

### 9.3 Why These Are Difficult

1. **Name collision is common:** 30% of S1 names are non-unique. A name match alone has high false positive risk.
2. **Same name + same country:** "Christ Chapel" appears multiple times in US, "Indian Brothers Private Limited" appears multiple times in India. Country doesn't disambiguate.
3. **Address is the key differentiator** for these cases, but addresses are themselves noisy and partial.
4. **Generic names amplify the problem:** Medical practice names ("Primary Care", "Pediatric Dental") appear hundreds of times, requiring precise address matching.

---

## PART 10: TRAIN VS TEST DIFFERENCES

### 10.1 Size Differences

| Source | Train Rows | Test Rows | Ratio |
|--------|-----------|-----------|-------|
| Source 1 | 2,206,821 | 1,732,544 | 0.79x |
| Source 2 | 5,034,616 | 4,887,273 | 0.97x |
| Source 3 | 5,285,603 | 5,082,316 | 0.96x |

Test S1 is ~21% smaller than training S1, but S2/S3 are roughly the same size.

### 10.2 Country Distribution Shift

| Country | Train (S1) | Test (S1) |
|---------|-----------|-----------|
| US | 60.0% | 38.3% |
| India | 40.0% | 46.8% |
| France | 0.0% | 15.0% |

This is a **major distribution shift**: US drops from 60% to 38%, India goes from 40% to 47%, and France appears at 15%.

### 10.3 Non-ASCII Names Shift

| File | Train non-ASCII % | Test non-ASCII % |
|------|-------------------|-------------------|
| Source 1 | 0.00% | 2.35% |
| Source 2 | 15.19% | 18.99% |
| Source 3 | 11.48% | 14.51% |

Train Source 1 has **zero** non-ASCII names; test Source 1 has 2.35% (French characters). This means any pipeline that assumes S1 names are ASCII-only will break.

### 10.4 Address Length Shift

Test addresses are slightly longer on average:
- S1 train mean: 52.1, test mean: 57.2 (+5.1)
- S2 train mean: 46.2, test mean: 50.4 (+4.2)

This likely reflects French addresses being longer (full words, region names).

### 10.5 Missing Address Rates

Test has slightly **fewer** missing addresses than training:
- S2: train 3.36% vs test 2.65%
- S3: train 3.33% vs test 2.68%

### 10.6 Potential Failure Modes

1. **France (zero-shot):** No French training data exists. Models must generalize to French legal suffixes (SARL, SAS, SASU, SCI, EURL), French address patterns (Rue, Boulevard, Allée), and French accented characters.
2. **Non-ASCII in Source 1:** Training S1 is pure ASCII; test S1 has accented French characters. Any ASCII-normalization applied to S1 in training may need adjustment.
3. **Country-dependent features:** Features tuned for US (ZIP codes, state abbreviations) or India (PIN codes, landmark-based addresses) may not transfer to France.
4. **Hard-coding countries:** The README explicitly warns against hard-coding `{US, India}`. The pipeline must treat country as an open set.
5. **Transliteration landscape changes:** Training has Hindi, Tamil, Bengali, etc. Test additionally has French accented text. The non-ASCII rate increases across all sources.

---

## PART 11: IMPORTANT OBSERVATIONS

### A. What We Know With Certainty

1. **Country is a perfect blocking key** for true matches (100% match rate in ground truth).
2. **Source 1 is the cleanest source** with zero missing values, zero non-ASCII names (in training), and full-form naming.
3. **89% of S1 entities have multiple matches** (2+ matches in S2/S3), averaging 3.46 matches.
4. **5.58% are singletons** with zero matches -- and correctly predicting these earns a full 1.0 per entity.
5. **Only 4.6% of true matches have exactly the same name.** Name normalization/similarity is critical.
6. **15.8% of true matches have zero token overlap in names** (transliterations, URLs, nicknames).
7. **France has zero training data** but represents 15% of test entities.
8. **30% of S1 business names are not unique** -- the same name can refer to different businesses.
9. **F_0.5 is precision-heavy** -- false positives are penalized more than false negatives.
10. **All entity IDs are globally unique** -- no duplicate IDs exist anywhere.
11. **"null" is a literal string in ~2.5% of S2/S3 addresses**, not a missing value indicator.
12. **DBA names appear almost exclusively in S3** (31,629 occurrences).

### B. What Appears Difficult

1. **Transliteration matching:** English "Raj Investments LLP" must match Tamil "ராஜ் இன்வெஸ்ட்மெண்ட்ஸ் எல்எல்பி". Token overlap is zero; character-level similarity is zero.
2. **Generic name disambiguation:** "Primary Care Group" appears 253 times at different addresses. Address matching becomes critical and addresses are themselves noisy.
3. **Alias/nickname matching:** "Maure Williams Colombier Inc" matches "Dréxkor" (a completely different name) -- only the address connects them.
4. **URL-to-name matching:** "maurewilliamscolombier.com" must match "Maure Williams Colombier Inc".
5. **French entities with no training signal:** All French matching must work zero-shot.
6. **Scale:** 1.7M x 10M comparison space requires effective blocking to be computationally feasible.
7. **Address noise:** Typos ("Broke Narrow" for "Broken Arrow"), reordering, partial addresses, "null" strings.
8. **Mixed-script names:** "Raj Investments எல்எல்பி" has both English and Tamil tokens.

### C. What the Dataset Suggests We Should Investigate

1. **Blocking strategies:** Country-based blocking reduces the space by ~2-3x immediately. Beyond that, investigate phonetic encoding, n-gram based, and TF-IDF based blocking on names.
2. **Transliteration handling:** Need a way to bridge Indic scripts to Latin script. Investigate transliteration libraries or embedding-based approaches that handle multilingual text.
3. **Name normalization pipeline:** Strip/normalize legal suffixes (Pvt/Private, Ltd/Limited, Corp/Corporation, LLC, Inc), handle "&" vs "and", handle DBA prefixes, handle URL-to-name conversion.
4. **Address normalization:** Abbreviation expansion (St->Street, Rd->Road, etc.), "null" removal, case normalization, state abbreviation standardization.
5. **Singleton detection:** Since singletons score 1.0 when correctly identified and 0.0 on any false match, a confident "no match" prediction is valuable.
6. **French-specific patterns:** French legal suffixes (SARL, SAS, etc.), French address structure, accent handling.
7. **Token-level and character-level similarity features:** Jaccard, Levenshtein, Jaro-Winkler, and others for both name and address.

### D. What We Should NOT Assume

1. **Do NOT assume name match implies entity match.** 30% of names are shared by multiple different businesses.
2. **Do NOT assume all names are in Latin script.** 15-19% of S2/S3 names are in Indic or other scripts.
3. **Do NOT assume S1 names are ASCII.** Test S1 has 2.35% non-ASCII names (French).
4. **Do NOT assume the training country set covers all test countries.** France is absent from training.
5. **Do NOT assume addresses are consistently formatted.** Components can be reordered, partial, or contain "null".
6. **Do NOT assume "null" means missing.** It appears as a literal string in addresses.
7. **Do NOT assume high name similarity means a match.** "Christ Chapel" at different addresses = different businesses.
8. **Do NOT assume a match always has overlapping name tokens.** 15.8% of true matches have zero name token overlap.
9. **Do NOT assume that one match type (S2 vs S3) is harder.** Both have similar noise profiles but different characteristics (DBA mostly in S3, etc.).
10. **Do NOT assume equal match counts.** The distribution peaks at 3 but ranges from 0 to 11.

---

## PART 12: TEAM-FRIENDLY SUMMARY

### What is this challenge about?

Imagine three separate phone books of businesses. Each phone book was written independently -- they don't share any ID numbers. Some businesses appear in all three books, some in two, some in only one. The spellings, addresses, and even the languages used may differ between books. **Your job: figure out which entries across the three phone books refer to the same real-world business.**

### 1. What goes in?

Three TSV files per split (train/test), each with 4 columns: entity_id, business_name, business_address, country. Plus a ground truth file for training.

### 2. What comes out?

A file listing, for each Source 1 entity, all the matching Source 2 and Source 3 entities. Some S1 entities may have zero matches (singletons).

### 3. What is Source 1?

The **clean reference database.** In training, it has 2.2M records, all with complete addresses, English-only names, and full legal forms ("Private Limited" not "Pvt Ltd"). Think of it as the "gold standard" list.

### 4. What are Source 2 and Source 3?

**Noisy, independently-collected databases** (~5M records each). They have:
- Missing addresses (~3.3%)
- Names in Hindi, Tamil, Bengali, and other scripts (11-15%)
- Abbreviations, typos, and word-order changes
- Literal "null" strings in addresses
- Source 3 uniquely has DBA names ("Nexnovi DBA Aguilar Diversified LLC") and website URLs as names ("summithealth.com")

### 5. What does the ground truth tell us?

For each S1 entity, it lists all matching S2 and S3 entity IDs. Example:

```
S1-55344266    S2-249013014,S2-197070651,S3-478195123,S3-384364074
```

This means the business "Raj Investments LLP" (S1-55344266) has 2 records in Source 2 and 2 records in Source 3 that refer to the same company.

### 6. What makes matching difficult?

Real examples from our data:

| Challenge | S1 Record | S2/S3 Record |
|-----------|-----------|-------------|
| **Transliteration** | Raj Investments LLP | ராஜ் இன்வெஸ்ட்மெண்ட்ஸ் எல்எல்பி |
| **Typos** | Payne Enterprises | Payne Enterpires |
| **Heavy corruption** | Payne Enterprises | PAYNE-ENRTPRMISES |
| **Abbreviation** | Diksha Technologies Private Limited | Diksha Technologies Private Ltd |
| **URL as name** | Summit Health LLC | summithealth.com |
| **DBA prefix** | Aguilar Diversified LLC | Nexnovi DBA Aguilar Diversified LLC |
| **Alias** | Maure Williams Colombier Inc | Dréxkor |
| **Address reorder** | 630 45th Terrace, Kansas City, MO | 45ND TERRACE, null, KANSAS CITY, MO |
| **Same name, different biz** | Christ Chapel (Dundalk, MD) | Christ Chapel (Helena, MT) |

### 7. What does a correct match look like?

```
S1: 'Payne Enterprises' | '3315 Fremont Street, Peoria, IL' | US
S2: 'Payne Énterprises' | '3315 FREMONT ST, PEORIA, IL' | US
```

Same business: name is nearly identical (accented E), address matches (Street vs St, same number and city), same country.

### 8. What does a singleton look like?

```
S1-302869473 -> (no matches)
```

This S1 entity has no counterpart in S2 or S3. Correctly predicting this earns a full 1.0 for this entity. **5.58% of entities are singletons.**

### 9. What are the major challenges visible in OUR actual data?

1. **Scale:** 1.7M query entities x 10M candidate entities. Need efficient blocking.
2. **Multilingual names:** 15-19% of S2/S3 names are in Indic scripts. Pure string matching fails.
3. **France is zero-shot:** 15% of test is French, with zero French training data.
4. **Name ambiguity:** "Primary Care Group" appears 253 times -- address is the tiebreaker.
5. **Extreme noise:** Some true matches have zero name overlap (aliases, transliterations).
6. **Precision matters more:** F_0.5 penalizes false merges 2x more than missed matches.
7. **Singletons matter:** 5.58% of entities have no match. Getting them right is free points.

---

*End of Dataset Understanding Report*
