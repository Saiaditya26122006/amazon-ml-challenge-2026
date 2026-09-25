"""
Unit tests for src/preprocessing/normalize_dataset.py

Run from the project root:
    python -m pytest tests/test_normalize_dataset.py -v
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from preprocessing.normalize_dataset import (
    DELIMITER,
    INPUT_HEADER,
    OUTPUT_HEADER,
    normalize_row,
    process_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_tsv(path: str, rows: list[list[str]]) -> None:
    """Write a list of rows (each a list of strings) as a TSV file."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        for row in rows:
            f.write(DELIMITER.join(row) + "\n")


def _read_tsv(path: str) -> list[list[str]]:
    """Read a TSV file and return rows (each a list of strings)."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            rows.append(line.rstrip("\n").split(DELIMITER))
    return rows


def _make_input(tmpdir: str, data_rows: list[list[str]]) -> str:
    """Create a well-formed input TSV with the standard header."""
    path = os.path.join(tmpdir, "input.tsv")
    _write_tsv(path, [INPUT_HEADER] + data_rows)
    return path


# ---------------------------------------------------------------------------
# Tests for normalize_row
# ---------------------------------------------------------------------------


class TestNormalizeRow:

    def test_returns_correct_length(self):
        row = normalize_row("S1-001", "Acme Inc", "123 Main St, NY", "US")
        assert len(row) == len(OUTPUT_HEADER)

    def test_original_columns_preserved(self):
        row = normalize_row("S1-42", "HELLO World", "1 Elm Ave, TX", "India")
        assert row[0] == "S1-42"
        assert row[1] == "HELLO World"
        assert row[2] == "1 Elm Ave, TX"
        assert row[3] == "India"

    def test_name_normalized(self):
        row = normalize_row("S2-1", "  Payne  Énterprises  ", "addr", "US")
        # row[4] = name_cleaned
        assert row[4] == "payne énterprises"
        # row[5] = name_no_accents
        assert row[5] == "payne enterprises"
        # row[6] = name_alphanumeric
        assert row[6] == "payne enterprises"
        # row[7] = name_tokens
        assert row[7] == "payne enterprises"

    def test_address_null_removed(self):
        row = normalize_row("S2-2", "Biz", "123 ST, NULL, CITY, KY", "US")
        # row[8] = addr_cleaned — "null" should be gone
        assert "null" not in row[8].split()

    def test_address_numeric_tokens(self):
        row = normalize_row("S1-3", "Biz", "1795 Elm Drive, Suite 200", "US")
        # row[12] = addr_numeric_tokens
        assert "1795" in row[12]
        assert "200" in row[12]

    def test_country_cleaned(self):
        row = normalize_row("S1-4", "Biz", "addr", "  France  ")
        # row[13] = country_cleaned
        assert row[13] == "france"

    def test_missing_address(self):
        row = normalize_row("S3-5", "Biz", "", "India")
        # addr_cleaned should be empty
        assert row[8] == ""
        # addr_tokens should be empty
        assert row[11] == ""
        # addr_numeric_tokens should be empty
        assert row[12] == ""

    def test_devanagari_name(self):
        row = normalize_row("S2-6", "राम मार्केटिंग", "addr", "India")
        # name_cleaned should preserve Devanagari
        assert "राम" in row[4]
        assert "मार्केटिंग" in row[4]
        # name_tokens should have 2 tokens
        assert len(row[7].split()) == 2


# ---------------------------------------------------------------------------
# Tests for process_file
# ---------------------------------------------------------------------------


class TestProcessFile:

    def test_basic_processing(self, tmp_path):
        inp = _make_input(str(tmp_path), [
            ["S1-001", "Acme Inc", "123 Main St", "US"],
            ["S1-002", "Beta Ltd", "456 Oak Ave", "India"],
        ])
        out = os.path.join(str(tmp_path), "out.tsv")
        result = process_file(inp, out)

        assert result["rows_processed"] == 2
        assert result["errors"] == []

        rows = _read_tsv(out)
        assert rows[0] == OUTPUT_HEADER
        assert len(rows) == 3  # header + 2 data rows

    def test_original_columns_in_output(self, tmp_path):
        inp = _make_input(str(tmp_path), [
            ["S1-999", "Hello World", "789 Pine Ln", "France"],
        ])
        out = os.path.join(str(tmp_path), "out.tsv")
        process_file(inp, out)

        rows = _read_tsv(out)
        data = rows[1]
        assert data[0] == "S1-999"
        assert data[1] == "Hello World"
        assert data[2] == "789 Pine Ln"
        assert data[3] == "France"

    def test_normalized_columns_added(self, tmp_path):
        inp = _make_input(str(tmp_path), [
            ["S1-001", "UPPER Name", "100 Elm St", "US"],
        ])
        out = os.path.join(str(tmp_path), "out.tsv")
        process_file(inp, out)

        rows = _read_tsv(out)
        data = rows[1]
        assert len(data) == len(OUTPUT_HEADER)
        # name_cleaned (index 4) should be lowercase
        assert data[4] == "upper name"

    def test_entity_id_never_modified(self, tmp_path):
        ids = ["S1-000001", "S2-999999", "S3-123ABC"]
        inp = _make_input(str(tmp_path), [
            [eid, "Name", "Addr", "US"] for eid in ids
        ])
        out = os.path.join(str(tmp_path), "out.tsv")
        process_file(inp, out)

        rows = _read_tsv(out)
        for i, eid in enumerate(ids):
            assert rows[i + 1][0] == eid

    def test_missing_address_handled(self, tmp_path):
        inp = _make_input(str(tmp_path), [
            ["S3-001", "Biz Name", "", "India"],
        ])
        out = os.path.join(str(tmp_path), "out.tsv")
        result = process_file(inp, out)

        assert result["rows_processed"] == 1
        assert result["errors"] == []

        rows = _read_tsv(out)
        data = rows[1]
        assert data[2] == ""  # original empty address preserved

    def test_unicode_roundtrip(self, tmp_path):
        inp = _make_input(str(tmp_path), [
            ["S2-001", "राम मार्केटिंग", "DELHI, Delhi", "India"],
        ])
        out = os.path.join(str(tmp_path), "out.tsv")
        process_file(inp, out)

        rows = _read_tsv(out)
        data = rows[1]
        assert data[1] == "राम मार्केटिंग"
        assert "राम" in data[4]

    def test_address_with_numbers(self, tmp_path):
        inp = _make_input(str(tmp_path), [
            ["S1-001", "Biz", "KH NO. -570/13, NEW DELHI", "India"],
        ])
        out = os.path.join(str(tmp_path), "out.tsv")
        process_file(inp, out)

        rows = _read_tsv(out)
        data = rows[1]
        # addr_numeric_tokens (index 12)
        assert "570" in data[12]
        assert "13" in data[12]

    def test_multiple_rows(self, tmp_path):
        data_rows = [[f"S1-{i:03d}", f"Name {i}", f"Addr {i}", "US"] for i in range(50)]
        inp = _make_input(str(tmp_path), data_rows)
        out = os.path.join(str(tmp_path), "out.tsv")
        result = process_file(inp, out)

        assert result["rows_processed"] == 50
        rows = _read_tsv(out)
        assert len(rows) == 51  # header + 50

    def test_limit(self, tmp_path):
        data_rows = [[f"S1-{i:03d}", f"Name {i}", f"Addr {i}", "US"] for i in range(100)]
        inp = _make_input(str(tmp_path), data_rows)
        out = os.path.join(str(tmp_path), "out.tsv")
        result = process_file(inp, out, limit=10)

        assert result["rows_processed"] == 10
        rows = _read_tsv(out)
        assert len(rows) == 11  # header + 10

    def test_limit_larger_than_file(self, tmp_path):
        data_rows = [["S1-001", "Name", "Addr", "US"]]
        inp = _make_input(str(tmp_path), data_rows)
        out = os.path.join(str(tmp_path), "out.tsv")
        result = process_file(inp, out, limit=999999)

        assert result["rows_processed"] == 1

    def test_bad_header_reports_error(self, tmp_path):
        path = os.path.join(str(tmp_path), "bad.tsv")
        _write_tsv(path, [["col_a", "col_b"]])
        out = os.path.join(str(tmp_path), "out.tsv")
        result = process_file(path, out)

        assert result["rows_processed"] == 0
        assert len(result["errors"]) > 0

    def test_empty_file_reports_error(self, tmp_path):
        path = os.path.join(str(tmp_path), "empty.tsv")
        with open(path, "w") as f:
            pass
        out = os.path.join(str(tmp_path), "out.tsv")
        result = process_file(path, out)

        assert result["rows_processed"] == 0
        assert len(result["errors"]) > 0

    def test_output_dir_created(self, tmp_path):
        inp = _make_input(str(tmp_path), [
            ["S1-001", "Name", "Addr", "US"],
        ])
        out = os.path.join(str(tmp_path), "deep", "nested", "out.tsv")
        result = process_file(inp, out)

        assert result["rows_processed"] == 1
        assert os.path.isfile(out)

    def test_summary_fields(self, tmp_path):
        inp = _make_input(str(tmp_path), [
            ["S1-001", "Name", "Addr", "US"],
        ])
        out = os.path.join(str(tmp_path), "out.tsv")
        result = process_file(inp, out)

        assert "input" in result
        assert "output" in result
        assert "rows_processed" in result
        assert "elapsed_s" in result
        assert "rows_per_sec" in result
        assert "output_size_mb" in result
        assert "errors" in result
