"""
Smoke + unit tests for the Data-Quality Audit tool.

The headline test is the acceptance check from the brief: running the audit on a
demo CSV must complete with no error and produce a report file. A few small unit
tests pin down the core checks (null counting, duplicate detection, the verdict
logic) so a future change can't silently break them.

Run with:   pytest tests -v
"""
import subprocess
import sys
import pathlib

import pandas as pd

# conftest.py (one level up) puts the project folder on sys.path, so this works.
import audit

# The project root = the folder that contains audit.py (one level up from tests/).
ROOT = pathlib.Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# ACCEPTANCE: the CLI runs end-to-end on each committed demo CSV without error.
# ---------------------------------------------------------------------------

def test_cli_runs_on_customers_demo(tmp_path):
    """The customers demo should audit cleanly and write a report file."""
    csv = ROOT / "data" / "messy_customers.csv"
    assert csv.exists(), "demo CSV missing — run generate_demo_data.py first"

    result = subprocess.run(
        [
            sys.executable, str(ROOT / "audit.py"), str(csv),
            "--key", "customer_id",
            "--outdir", str(tmp_path),       # write the report into a temp folder
        ],
        capture_output=True,
        text=True,
    )

    # The script ran (didn't crash). Exit code 3 == FAIL verdict, which is the
    # *expected* outcome for this deliberately-broken file — not a program error.
    assert result.returncode == 3, result.stderr
    assert "VERDICT: FAIL" in result.stdout
    assert (tmp_path / "messy_customers_report.md").exists()


def test_cli_runs_on_orders_demo(tmp_path):
    """The orders demo should audit cleanly, with rules, and write a report."""
    csv = ROOT / "data" / "messy_orders.csv"
    rules = ROOT / "rules_example.json"
    assert csv.exists(), "demo CSV missing — run generate_demo_data.py first"

    result = subprocess.run(
        [
            sys.executable, str(ROOT / "audit.py"), str(csv),
            "--key", "order_id",
            "--rules", str(rules),
            "--outdir", str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )

    # Exit code 1 == REVIEW verdict, the expected outcome for this file.
    assert result.returncode == 1, result.stderr
    assert "VERDICT: REVIEW" in result.stdout
    assert (tmp_path / "messy_orders_report.md").exists()


# ---------------------------------------------------------------------------
# UNIT: the individual checks behave as documented.
# ---------------------------------------------------------------------------

def test_null_rates_counts_blanks_and_fake_blanks():
    """Empty strings and 'N/A'-style text should both count as missing."""
    df = pd.DataFrame({
        "a": ["x", "", "y", "N/A"],   # 2 of 4 missing -> 0.5
        "b": ["1", "2", "3", "4"],    # nothing missing -> 0.0
    })
    rates = audit.null_rates(df)
    assert rates["a"] == 0.5
    assert rates["b"] == 0.0


def test_looks_numeric_handles_currency_and_text():
    """Currency-decorated numbers are numeric; words are not."""
    assert audit.looks_numeric("$1,250.00") is True
    assert audit.looks_numeric("19.99") is True
    assert audit.looks_numeric("free") is False
    assert audit.looks_numeric("") is False


def test_duplicate_full_rows_counts_extra_copies():
    """Two identical rows -> exactly one counted as a duplicate."""
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    assert audit.duplicate_full_rows(df) == 1


def test_type_problems_flags_mostly_numeric_column():
    """A column that's 80%+ numeric with stray text should be flagged."""
    df = pd.DataFrame({
        # 4 of 5 numeric (80%) -> flagged, with 'free' as the bad example
        "price": ["10", "20", "30", "40", "free"],
    })
    issues = audit.type_problems(df)
    assert len(issues) == 1
    assert issues[0]["column"] == "price"
    assert "free" in issues[0]["bad_examples"]


def test_verdict_fails_on_half_empty_column():
    """A column over the 50% null line should force a FAIL verdict."""
    nulls = {"phone": 0.83, "name": 0.0}
    verdict, reasons = audit.decide_verdict(
        n_rows=20,
        nulls=nulls,
        dup_rows=0,
        dup_key_list=[],
        type_issues=[],
        range_issues=[],
    )
    assert verdict == "FAIL"
    assert any("phone" in r for r in reasons)


def test_verdict_passes_on_clean_data():
    """No issues at all -> PASS."""
    verdict, reasons = audit.decide_verdict(
        n_rows=100,
        nulls={"a": 0.0, "b": 0.0},
        dup_rows=0,
        dup_key_list=[],
        type_issues=[],
        range_issues=[],
    )
    assert verdict == "PASS"
