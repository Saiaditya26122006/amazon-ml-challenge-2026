"""
Business Entity Resolution — Scalable Dataset Normalization

Reads competition TSV files row-by-row, applies normalization from
normalize.py, and writes enriched TSVs to processed/.  Memory usage
stays approximately constant regardless of file size.

Usage examples:

    # Single file
    python -m src.preprocessing.normalize_dataset \
        --input  database/student_resource/dataset/train/train_source1.tsv \
        --output processed/train/train_source1_normalized.tsv

    # Smoke test (first 100 000 rows only)
    python -m src.preprocessing.normalize_dataset \
        --input  database/student_resource/dataset/train/train_source1.tsv \
        --output processed/train/train_source1_normalized.tsv \
        --limit 100000

    # All training sources
    python -m src.preprocessing.normalize_dataset --train

    # All test sources
    python -m src.preprocessing.normalize_dataset --test

    # Everything
    python -m src.preprocessing.normalize_dataset --all
"""

from __future__ import annotations

import argparse
import os
import sys
import time

# ---------------------------------------------------------------------------
# Resolve project root and ensure src/ is importable.
# ---------------------------------------------------------------------------
_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SRC_DIR, os.pardir))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from preprocessing.normalize import (
    normalize_address,
    normalize_name,
    normalize_country,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(_PROJECT_ROOT, "database", "student_resource", "dataset")
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "processed")

INPUT_HEADER = ["entity_id", "business_name", "business_address", "country"]
NUM_INPUT_COLS = len(INPUT_HEADER)

DELIMITER = "\t"

# Output adds these columns *after* the four original ones.
DERIVED_COLUMNS = [
    "name_cleaned",
    "name_no_accents",
    "name_alphanumeric",
    "name_tokens",
    "addr_cleaned",
    "addr_no_accents",
    "addr_alphanumeric",
    "addr_tokens",
    "addr_numeric_tokens",
    "country_cleaned",
]

OUTPUT_HEADER = INPUT_HEADER + DERIVED_COLUMNS

# Batch of known source files used by --train / --test / --all.
_BATCH_SPECS: dict[str, list[tuple[str, str]]] = {
    "train": [
        (os.path.join(DATA_DIR, "train", f"train_source{i}.tsv"),
         os.path.join(OUTPUT_DIR, "train", f"train_source{i}_normalized.tsv"))
        for i in (1, 2, 3)
    ],
    "test": [
        (os.path.join(DATA_DIR, "test", f"test_source{i}.tsv"),
         os.path.join(OUTPUT_DIR, "test", f"test_source{i}_normalized.tsv"))
        for i in (1, 2, 3)
    ],
}

# Token-list separator inside TSV cells (space-join; avoids commas which
# appear in addresses and conflict with the ground-truth ID-list format).
_TOKEN_SEP = " "


# ---------------------------------------------------------------------------
# Core row processing
# ---------------------------------------------------------------------------

def normalize_row(entity_id: str, name: str, address: str, country: str) -> list[str]:
    """Return the full output row as a list of strings.

    The first four elements are the *unchanged* original columns.
    The remaining elements are the derived normalized columns.
    """
    nn = normalize_name(name)
    na = normalize_address(address)
    nc = normalize_country(country)

    return [
        entity_id,
        name,
        address,
        country,
        nn.cleaned,
        nn.no_accents,
        nn.alphanumeric,
        _TOKEN_SEP.join(nn.tokens),
        na.cleaned,
        na.no_accents,
        na.alphanumeric,
        _TOKEN_SEP.join(na.tokens),
        _TOKEN_SEP.join(na.numeric_tokens),
        nc.cleaned,
    ]


# ---------------------------------------------------------------------------
# Streaming file processor
# ---------------------------------------------------------------------------

def process_file(
    input_path: str,
    output_path: str,
    *,
    limit: int | None = None,
) -> dict:
    """Read *input_path* row-by-row, normalize, and write to *output_path*.

    Returns a summary dict with row counts, timing, and any errors.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    errors: list[str] = []
    rows_written = 0
    t0 = time.perf_counter()

    with (
        open(input_path, encoding="utf-8") as fin,
        open(output_path, "w", encoding="utf-8", newline="") as fout,
    ):
        # --- Validate header ---
        raw_header = fin.readline()
        if not raw_header:
            errors.append(f"{input_path}: file is empty")
            return _summary(input_path, output_path, 0, t0, errors)

        header_cols = raw_header.rstrip("\n").split(DELIMITER)
        if header_cols != INPUT_HEADER:
            errors.append(
                f"{input_path}: unexpected header {header_cols!r}; "
                f"expected {INPUT_HEADER!r}"
            )
            return _summary(input_path, output_path, 0, t0, errors)

        fout.write(DELIMITER.join(OUTPUT_HEADER) + "\n")

        # --- Stream rows ---
        for line_num, line in enumerate(fin, start=2):
            if limit is not None and rows_written >= limit:
                break

            stripped = line.rstrip("\n")
            if not stripped:
                continue

            parts = stripped.split(DELIMITER)
            if len(parts) != NUM_INPUT_COLS:
                errors.append(
                    f"{input_path} line {line_num}: expected {NUM_INPUT_COLS} "
                    f"columns, got {len(parts)}"
                )
                if len(parts) < NUM_INPUT_COLS:
                    continue
                # If extra columns, use only the first NUM_INPUT_COLS
                parts = parts[:NUM_INPUT_COLS]

            entity_id, name, address, country = parts
            out_row = normalize_row(entity_id, name, address, country)
            fout.write(DELIMITER.join(out_row) + "\n")
            rows_written += 1

    return _summary(input_path, output_path, rows_written, t0, errors)


def _summary(
    input_path: str,
    output_path: str,
    rows: int,
    t0: float,
    errors: list[str],
) -> dict:
    elapsed = time.perf_counter() - t0
    rate = rows / elapsed if elapsed > 0 else 0
    out_size = os.path.getsize(output_path) if os.path.isfile(output_path) else 0
    return {
        "input": input_path,
        "output": output_path,
        "rows_processed": rows,
        "elapsed_s": round(elapsed, 2),
        "rows_per_sec": round(rate),
        "output_size_mb": round(out_size / (1024 * 1024), 2),
        "errors": errors,
    }


def print_summary(s: dict) -> None:
    print(f"  Input:       {s['input']}")
    print(f"  Output:      {s['output']}")
    print(f"  Rows:        {s['rows_processed']:,}")
    print(f"  Time:        {s['elapsed_s']:.2f}s")
    print(f"  Rate:        {s['rows_per_sec']:,} rows/sec")
    print(f"  Output size: {s['output_size_mb']:.2f} MB")
    if s["errors"]:
        print(f"  Errors:      {len(s['errors'])}")
        for e in s["errors"][:10]:
            print(f"    - {e}")
    else:
        print(f"  Errors:      0")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Normalize competition TSV files (streaming, constant memory).",
    )
    # Single-file mode
    p.add_argument("--input", "-i", help="Path to a single input TSV file")
    p.add_argument("--output", "-o", help="Path for the output TSV file")

    # Batch modes
    p.add_argument("--train", action="store_true", help="Process all 3 training source files")
    p.add_argument("--test", action="store_true", help="Process all 3 test source files")
    p.add_argument("--all", action="store_true", help="Process all 6 source files (train + test)")

    # Options
    p.add_argument(
        "--limit", "-n", type=int, default=None,
        help="Process only the first N data rows per file (smoke test)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    jobs: list[tuple[str, str]] = []

    if args.input:
        if not args.output:
            parser.error("--output is required when --input is used")
        jobs.append((args.input, args.output))
    elif args.all:
        jobs.extend(_BATCH_SPECS["train"])
        jobs.extend(_BATCH_SPECS["test"])
    elif args.train:
        jobs.extend(_BATCH_SPECS["train"])
    elif args.test:
        jobs.extend(_BATCH_SPECS["test"])
    else:
        parser.error("Specify --input/--output, --train, --test, or --all")

    if not jobs:
        print("Nothing to do.")
        return 0

    limit_label = f" (limit {args.limit:,})" if args.limit else ""
    print(f"Normalizing {len(jobs)} file(s){limit_label}...\n")

    all_ok = True
    for inp, out in jobs:
        print(f"Processing: {os.path.basename(inp)}")
        s = process_file(inp, out, limit=args.limit)
        print_summary(s)
        if s["errors"]:
            all_ok = False
        print()

    if all_ok:
        print("All files processed successfully.")
    else:
        print("Some files had errors — see above.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
