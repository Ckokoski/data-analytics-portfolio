"""Tests for the synthetic campaign-data generator.

We run the generator as a subprocess (the way a user would) and inspect the CSV
it writes, rather than importing internals. That keeps the test honest about the
real command-line behavior.
"""
import subprocess
import sys
import pathlib

import pandas as pd

# tests/ lives inside the project folder; parents[1] is 01-excel-pivot-engine/
ROOT = pathlib.Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "generate_demo_data.py"

EXPECTED_COLUMNS = [
    "date", "channel", "segment",
    "spend", "impressions", "clicks", "conversions", "revenue",
]


def _run_generator(out_path):
    subprocess.run(
        [sys.executable, str(GENERATOR), "-o", str(out_path)],
        check=True,
    )


def test_generator_produces_expected_shape(tmp_path):
    out = tmp_path / "demo.csv"
    _run_generator(out)
    df = pd.read_csv(out)

    assert list(df.columns) == EXPECTED_COLUMNS
    assert 1400 <= len(df) <= 1800, f"row count {len(df)} outside expected band"
    assert set(df["channel"]) == {"Email", "Paid Search", "Social", "Display"}
    assert set(df["segment"]) == {"New", "Returning", "VIP", "Dormant"}
    assert df["date"].min() >= "2025-01-01"
    assert df["date"].max() <= "2025-06-30"
    # No negative money/counts should ever appear.
    for col in ["spend", "impressions", "clicks", "conversions", "revenue"]:
        assert (df[col] >= 0).all(), f"negative values found in {col}"


def test_generator_is_reproducible(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    _run_generator(a)
    _run_generator(b)
    assert a.read_bytes() == b.read_bytes(), "seeded generator must be deterministic"
