"""
run_queries.py
==============

Run every .sql file in `queries/` against `data/youtube.db` and print the results,
so you can verify the whole pipeline end-to-end with one command.

PRIVACY: every query here returns rates, percentages, or indexes only — never raw
view / impression / subscriber counts. Safe to share the output.
"""
import sqlite3
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DB = HERE / "data" / "youtube.db"
QUERIES = HERE / "queries"


def business_question(sql_text: str) -> str:
    """Pull the '-- Business question:' line out of a .sql file's header."""
    for line in sql_text.splitlines():
        if "Business question" in line:
            return line.lstrip("- ").strip()
    return ""


def main() -> None:
    if not DB.exists():
        raise SystemExit("Database not found. Run `python import_to_sqlite.py` first.")

    con = sqlite3.connect(DB)
    for sql_file in sorted(QUERIES.glob("*.sql")):
        sql = sql_file.read_text(encoding="utf-8")
        print(f"\n=== {sql_file.name} ===")
        question = business_question(sql)
        if question:
            print(question)
        try:
            result = pd.read_sql_query(sql, con)
            print(result.to_string(index=False))
        except Exception as exc:  # surface a broken query loudly rather than silently skipping
            print(f"ERROR running {sql_file.name}: {exc}")
    con.close()


if __name__ == "__main__":
    main()
