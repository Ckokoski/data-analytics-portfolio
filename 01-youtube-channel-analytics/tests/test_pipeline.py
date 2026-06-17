"""Smoke test + privacy guard for the YouTube pipeline.

1. The import + every query runs on the synthetic sample with no error.
2. No query OUTPUT exposes a raw-count column (views / impressions / subscribers) —
   this enforces the repo's "rates public, raw counts private" rule in code.
"""
import subprocess
import sys
import sqlite3
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW_COUNT_COLUMNS = {"views", "impressions", "subscribers_gained", "subscribers"}


def test_pipeline_runs_and_outputs_are_rates_only(tmp_path):
    db = tmp_path / "youtube.db"
    subprocess.run(
        [sys.executable, str(ROOT / "import_to_sqlite.py"), "-o", str(db)],
        check=True,
    )

    con = sqlite3.connect(db)
    sql_files = sorted((ROOT / "queries").glob("*.sql"))
    assert len(sql_files) >= 10, "expected the full set of template queries"

    for sql_file in sql_files:
        df = pd.read_sql_query(sql_file.read_text(encoding="utf-8"), con)
        leaked = RAW_COUNT_COLUMNS.intersection({c.lower() for c in df.columns})
        assert not leaked, f"{sql_file.name} exposes raw-count column(s): {leaked}"
    con.close()
