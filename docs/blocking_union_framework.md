# Candidate Union Evaluation Framework

## Overview

This framework provides infrastructure to evaluate **unions of blocking routes** and analyze the **marginal contribution** of each route.

## Core Concepts

### Candidate Set

A `CandidateSet` represents the output of a single blocking route:

```
S1 ID -> set of candidate S2/S3 IDs
```

Key properties:
- Tracks which S1 entities retrieve which candidates
- Maintains S2/S3 separation
- Supports union operations
- Deduplicates automatically

### Route Contribution

For a union of routes, the framework computes:

1. **Total recall**: How many true pairs are retrieved by each route
2. **Unique pairs**: True pairs retrieved by this route ONLY
3. **Shared pairs**: True pairs retrieved by this route AND at least one other
4. **Marginal contribution**: How many NEW true pairs this route adds vs. all previous routes

### Union Evaluation

The framework supports evaluating arbitrary unions:

```
Route A only
Route B only
Route A + B
Route A + C
Route B + C
Route A + B + C
Route A + B + C + D + E
...
```

## Usage

### 1. Build Candidate Sets

For each blocking route, build a `CandidateSet`:

```python
from blocking.route_contribution import build_candidate_set

# Define your retriever function
def my_retriever(s1_entity):
    # Return set of candidate IDs for this S1 entity
    return {candidate_ids...}

# Build the candidate set
candidate_set = build_candidate_set(
    route_name="my_route",
    s1_entities=s1_entities,
    retriever=my_retriever
)
```

### 2. Analyze Union Contribution

Pass multiple candidate sets to analyze their union:

```python
from blocking.route_contribution import analyze_union_contribution

contrib = analyze_union_contribution(
    candidate_sets=[candidate_set_a, candidate_set_b, candidate_set_c],
    ground_truth=gt
)

print(f"Union recall: {contrib.overall_recall:.4f}")
print(f"Total retrieved: {contrib.total_retrieved:,}")

for c in contrib.contributions:
    print(f"{c.route_name}:")
    print(f"  Total recall: {c.recall:.4f}")
    print(f"  Marginal contribution: {c.marginal_true_pairs:,} pairs")
    print(f"  Unique pairs: {c.unique_true_pairs:,}")
    print(f"  Shared pairs: {c.shared_true_pairs:,}")
```

### 3. Print Formatted Report

```python
from blocking.route_contribution import print_union_contribution

print_union_contribution(contrib)
```

Output:
```
=== Union Contribution Analysis ===
Routes: exact_name + token_overlap + address_token
Total GT pairs: 10,000
Union retrieved: 8,500
Union recall: 0.8500

Per-route contributions:
Route                          Recall   Unique   Shared Marginal   Marg %
------------------------------------------------------------------------------------------
exact_name                     0.6000    2,000    4,000    6,000   0.6000
token_overlap                  0.7000      500    6,500    1,000   0.1000
address_token                  0.7500    1,000    6,500    1,500   0.1500

Pairwise overlap (shared true pairs):
  exact_name ∩ token_overlap: 4,000
  exact_name ∩ address_token: 4,500
  token_overlap ∩ address_token: 5,500
```

## Metrics Explained

### Recall

**Total recall** for a route = retrieved true pairs / total GT pairs

This measures how good the route is in isolation.

### Entity Full Coverage

Fraction of S1 entities where ALL true matches were retrieved.

This is stricter than recall — an entity with 3 true matches that retrieves 2 has partial recall but zero full coverage.

### Candidate Volume

- **avg_candidates**: Mean number of candidates per S1 entity
- **median_candidates**: Median (more robust to outliers)
- **p95_candidates**: 95th percentile (captures long tail)
- **max_candidates**: Worst-case explosion

### Unique vs. Shared

**Unique pairs**: Retrieved by this route ONLY, not by any other route in the union.

**Shared pairs**: Retrieved by this route AND at least one other route.

If a route has high unique pairs, it's capturing matches that other routes miss (high value).

If a route has low unique pairs, most of its matches are duplicates (low marginal value).

### Marginal Contribution

**Marginal pairs**: How many NEW true pairs this route adds vs. all previous routes in the union.

This depends on route order:
- Route A gets full credit (all its pairs are marginal)
- Route B only gets credit for pairs NOT already in A
- Route C only gets credit for pairs NOT already in A or B

Use this to measure **incremental value** of adding a route.

## Integration with Existing Code

### Existing evaluate_blocking() still works

The old `evaluate_blocking()` function is unchanged:

```python
from blocking.evaluate_blocking import evaluate_blocking

result = evaluate_blocking(
    route_name="my_route",
    s1_entities=s1_entities,
    ground_truth=gt,
    retriever=my_retriever
)

print(f"Recall: {result.overall_recall:.4f}")
print(f"Avg candidates: {result.avg_candidates:.1f}")
```

### New framework adds route contribution

The new framework **adds** route contribution analysis on top:

```python
# Old way: evaluate each route independently
result_a = evaluate_blocking("route_a", s1_entities, gt, retriever_a)
result_b = evaluate_blocking("route_b", s1_entities, gt, retriever_b)

# New way: analyze their union
cs_a = build_candidate_set("route_a", s1_entities, retriever_a)
cs_b = build_candidate_set("route_b", s1_entities, retriever_b)
contrib = analyze_union_contribution([cs_a, cs_b], gt)

# Now you can answer:
# - What is the recall of A + B union?
# - How many new pairs does B add vs. A?
# - Which pairs are unique to A? Which are shared?
```

## Example Workflow

### Scenario

We have 3 blocking routes:
- **Route A**: country + exact name
- **Route B**: country + alphanumeric name
- **Route C**: country + token overlap (to be implemented by Freebuff)

### Step 1: Build indices

```python
from blocking.exact_blocking import (
    build_country_name_cleaned_index,
    build_country_name_alphanumeric_index,
    retrieve_by_country_name_cleaned,
    retrieve_by_country_name_alphanumeric,
)

# Load data
s1_entities = load_source_normalized(S1_FILE, needed_ids=gt_ids)
s2s3_entities = {**load_source_normalized(S2_FILE), **load_source_normalized(S3_FILE)}

# Build indices
name_cleaned_idx = build_country_name_cleaned_index(s2s3_entities)
name_alnum_idx = build_country_name_alphanumeric_index(s2s3_entities)
# token_overlap_idx = build_token_overlap_index(s2s3_entities)  # Future
```

### Step 2: Build candidate sets

```python
from blocking.route_contribution import build_candidate_set

cs_a = build_candidate_set(
    "exact_name",
    s1_entities,
    lambda ent: retrieve_by_country_name_cleaned(ent, name_cleaned_idx)
)

cs_b = build_candidate_set(
    "alphanumeric_name",
    s1_entities,
    lambda ent: retrieve_by_country_name_alphanumeric(ent, name_alnum_idx)
)

# cs_c = build_candidate_set(
#     "token_overlap",
#     s1_entities,
#     lambda ent: retrieve_by_token_overlap(ent, token_overlap_idx)
# )  # Future
```

### Step 3: Evaluate unions

```python
from blocking.route_contribution import analyze_union_contribution

# A only
contrib_a = analyze_union_contribution([cs_a], gt)
print(f"A recall: {contrib_a.overall_recall:.4f}")

# B only
contrib_b = analyze_union_contribution([cs_b], gt)
print(f"B recall: {contrib_b.overall_recall:.4f}")

# A + B
contrib_ab = analyze_union_contribution([cs_a, cs_b], gt)
print(f"A+B recall: {contrib_ab.overall_recall:.4f}")
print(f"B adds {contrib_ab.contributions[1].marginal_true_pairs:,} new pairs")

# A + B + C (future)
# contrib_abc = analyze_union_contribution([cs_a, cs_b, cs_c], gt)
```

### Step 4: Interpret results

```
A recall: 0.6500
B recall: 0.6800
A+B recall: 0.7200

Route A: 6,500 pairs
Route B: 6,800 pairs
  - 6,100 shared with A
  - 700 unique to B
  - Marginal contribution: +700 pairs

Interpretation:
- A and B have high overlap (6,100 shared pairs)
- B only adds 700 new pairs (10% gain)
- We need a third route (token overlap, address, etc.) to close the gap
```

## Adding New Routes

When a new blocking route is ready (e.g., token-overlap from Freebuff):

### 1. Implement the retriever

```python
def build_token_overlap_index(entities):
    """Build inverted index: (country, token) -> set of entity IDs."""
    idx = defaultdict(set)
    for eid, ent in entities.items():
        if ent.country_cleaned and ent.name_cleaned:
            tokens = ent.name_cleaned.split()
            for token in tokens:
                key = (ent.country_cleaned, token)
                idx[key].add(eid)
    return dict(idx)

def retrieve_by_token_overlap(s1_entity, index, min_overlap=1):
    """Retrieve candidates with at least min_overlap shared name tokens."""
    if not s1_entity.country_cleaned or not s1_entity.name_cleaned:
        return set()
    
    s1_tokens = set(s1_entity.name_cleaned.split())
    candidate_votes = defaultdict(int)
    
    for token in s1_tokens:
        key = (s1_entity.country_cleaned, token)
        for cand_id in index.get(key, set()):
            candidate_votes[cand_id] += 1
    
    return {cand_id for cand_id, votes in candidate_votes.items() if votes >= min_overlap}
```

### 2. Build the candidate set

```python
token_overlap_idx = build_token_overlap_index(all_s2s3)

cs_token = build_candidate_set(
    "token_overlap",
    s1_entities,
    lambda ent: retrieve_by_token_overlap(ent, token_overlap_idx, min_overlap=2)
)
```

### 3. Evaluate the union

```python
contrib = analyze_union_contribution([cs_exact, cs_token], gt)

print_union_contribution(contrib)
```

### 4. Compare different configurations

```python
# Vary min_overlap threshold
for min_overlap in [1, 2, 3]:
    cs = build_candidate_set(
        f"token_overlap_{min_overlap}",
        s1_entities,
        lambda ent: retrieve_by_token_overlap(ent, token_overlap_idx, min_overlap=min_overlap)
    )
    
    result = evaluate_blocking(f"token_{min_overlap}", s1_entities, gt, cs)
    print(f"min_overlap={min_overlap}: recall={result.overall_recall:.4f}, avg_cands={result.avg_candidates:.1f}")
```

## Design Principles

### 1. Separation of Concerns

- **CandidateSet**: Tracks which S1 entities retrieve which candidates
- **evaluate_blocking()**: Computes recall and volume metrics
- **analyze_union_contribution()**: Computes marginal value across routes

Each component does one thing well.

### 2. Composability

All functions take standard inputs (`s1_entities`, `ground_truth`, `retriever`) and produce standard outputs (`CandidateSet`, `BlockingResult`, `UnionContribution`).

This makes it easy to mix and match routes.

### 3. No Assumptions

The framework **never assumes**:
- One-to-one matching
- S2 and S3 are the same
- Routes are independent
- Candidates are unique

It handles all combinations correctly.

### 4. Minimal Changes

The existing `evaluate_blocking()` and `candidate_union()` functions are **unchanged**.

New code is purely additive.

## Files

### Core Implementation

- `src/blocking/route_contribution.py` — NEW: Route contribution analysis
- `src/blocking/candidate_union.py` — Existing: Simple union function
- `src/blocking/evaluate_blocking.py` — Existing: Single-route evaluation
- `src/blocking/base.py` — Existing: Entity and data loading
- `src/blocking/exact_blocking.py` — Existing: Exact-match routes

### Tests

- `tests/test_route_contribution.py` — NEW: 18 tests for route contribution
- `tests/test_blocking.py` — Existing: 21 tests for core blocking

### Experiments

- `experiments/blocking/evaluate_route_unions.py` — NEW: Demo script
- `experiments/blocking/run_blocking.py` — Existing: Core blocking experiment

## Next Steps

### Immediate (STEP 3)

1. **Freebuff** completes token-overlap blocking
2. **Friend 2** completes address-token blocking
3. **Friend 1** completes name-variation experiments

### Integration (STEP 4)

Once all routes are ready:

1. Build candidate sets for all routes
2. Evaluate all unions:
   - Single routes
   - Pairs: A+B, A+C, A+D, B+C, ...
   - Triples: A+B+C, A+B+D, ...
   - Full union: A+B+C+D+E+F

3. Analyze:
   - Which routes have highest recall?
   - Which routes have lowest candidate volume?
   - Which combinations achieve best recall/volume tradeoff?
   - Which routes add the most marginal value?

4. Select the final blocking strategy:
   - Maybe: exact_name + token_overlap + address_token
   - Or: exact_name + token_overlap only (if address_token adds little)
   - Or: full union (if candidate volume is manageable)

### Documentation

This framework is ready for production use:
- 163 tests passing
- Full type hints
- Clear docstrings
- Example scripts
- Zero breaking changes

## Summary

The candidate-union evaluation framework provides:

✅ Generic candidate set representation  
✅ Union operations with deduplication  
✅ S2/S3 separation throughout  
✅ Recall metrics (pair, entity, source-specific)  
✅ Candidate volume metrics (avg, median, p95, max)  
✅ Route contribution analysis  
✅ Marginal value computation  
✅ Overlap matrices  
✅ Composable, reusable functions  
✅ Backward compatible with existing code  
✅ Comprehensive test coverage  

No ML models. No embeddings. No expensive processing. Just clean, fast, testable infrastructure for evaluating blocking routes.
