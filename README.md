# Amazon ML Challenge 2026: Business Entity Resolution

Given business records from 3 independent data sources with noisy and inconsistent fields, determine which records across sources refer to the same real-world business entity.

- **Source 1** is the deduplicated reference. For each S1 entity, find all matching records from Source 2 and Source 3.
- Evaluated on **F_0.5 (macro-averaged)** — precision is weighted 2x over recall.
- Training countries: US, India. Test additionally includes France (zero-shot).

---

## Project Structure

```
amazon-ml-challenge-2026/
│
├── database/                  # Original competition files (DO NOT MODIFY)
│   └── student_resource/
│       ├── dataset/
│       │   ├── train/         # train_source1/2/3.tsv, train_ground_truth.tsv
│       │   └── test/          # test_source1/2/3.tsv
│       ├── utils/             # validate_submission.py
│       ├── README.md          # Official problem statement
│       └── Documentation_template.md
│
├── dataset/                   # Symlink / shortcut to database/student_resource/dataset
│   ├── train/                 #   (use this path in code for cleaner imports)
│   └── test/
│
├── src/                       # Reusable solution code (the actual pipeline)
│   ├── preprocessing/         # Data loading, cleaning, normalization
│   ├── blocking/              # Candidate generation / blocking strategies
│   ├── features/              # Feature engineering for candidate pairs
│   ├── models/                # Training, inference, threshold tuning
│   ├── evaluation/            # F_0.5 scoring, validation splits, error analysis
│   └── submission/            # Output formatting, validation, packaging
│
├── experiments/               # Analysis and experiments (NOT part of final pipeline)
│   ├── dataset_understanding.md   # Completed dataset EDA
│   ├── dataset_summary.csv        # File-level statistics
│   ├── normalization/         # Name/address normalization experiments
│   ├── blocking/              # Blocking strategy experiments
│   ├── features/              # Feature selection experiments
│   ├── models/                # Model comparison experiments
│   └── error_analysis/        # False positive / false negative analysis
│
├── processed/                 # Generated intermediate data (gitignored, reproducible)
│                              #   e.g. normalized tables, blocked candidate pairs
│
├── models/                    # Trained model artifacts (gitignored, reproducible)
│
├── output/                    # Final submission files
│                              #   matching_results.tsv
│                              #   candidate_pairs.tsv
│
├── tests/                     # Unit and integration tests
│
├── notebooks/                 # Jupyter notebooks for exploration
│
├── .gitignore
├── requirements.txt
└── README.md
```

### Key distinctions

| Directory | Purpose | Tracked in git? |
|-----------|---------|-----------------|
| `database/` | Original competition files | Yes (read-only) |
| `dataset/` | Clean path alias to the data | Yes (gitkeep only) |
| `src/` | Final pipeline code | Yes |
| `experiments/` | Analysis and experiments | Yes |
| `processed/` | Generated intermediate data | No (large, reproducible) |
| `models/` | Trained model files | No (large, reproducible) |
| `output/` | Submission TSV files | Yes |
| `tests/` | Automated tests | Yes |

---

## Dataset Location

The actual dataset files live at:

```
database/student_resource/dataset/train/train_source1.tsv
database/student_resource/dataset/train/train_source2.tsv
database/student_resource/dataset/train/train_source3.tsv
database/student_resource/dataset/train/train_ground_truth.tsv
database/student_resource/dataset/test/test_source1.tsv
database/student_resource/dataset/test/test_source2.tsv
database/student_resource/dataset/test/test_source3.tsv
```

In all pipeline code, use this base path:

```python
DATA_DIR = "database/student_resource/dataset"
```

---

## Team Workflow

### Branching Strategy

- **`main`** is the stable branch. It contains only reviewed, working code.
- Each team member works on a **separate feature or experiment branch** (e.g., `feat/name-normalization`, `exp/tfidf-blocking`).
- **Do not push experimental work directly to `main`.**
- All changes to `main` go through a pull request reviewed by at least one other team member.

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature / pipeline work | `feat/<short-description>` | `feat/name-normalization` |
| Experiment | `exp/<short-description>` | `exp/tfidf-blocking` |
| Bug fix | `fix/<short-description>` | `fix/ground-truth-parsing` |

### Integration Rules

1. Experimental results in `experiments/` must be reviewed before the approach is integrated into `src/`.
2. Every pipeline module in `src/` should be reproducible: given the raw data in `database/`, running the pipeline regenerates `processed/`, `models/`, and `output/`.
3. Before merging to `main`, verify the submission passes `utils/validate_submission.py`.

---

## Evaluation

Submissions are scored with **F_0.5 (macro-averaged)**:

```
F_0.5 = (1.25 * Precision * Recall) / (0.25 * Precision + Recall)
```

- Precision is weighted 2x over recall — false merges are worse than missed matches.
- Singletons (no-match entities) score 1.0 when correctly left empty, 0.0 on any false match.

---

## Current Progress

- [x] Dataset understanding (see `experiments/dataset_understanding.md`)
- [ ] Data normalization
- [ ] Blocking / candidate generation
- [ ] Feature engineering
- [ ] Model training
- [ ] Threshold tuning
- [ ] Submission generation
