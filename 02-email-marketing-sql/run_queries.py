"""
run_queries.py
==============

Runs EVERY .sql file in queries/ against the SYNTHETIC email-marketing
database and prints, for each file:

  * the file name,
  * the BUSINESS QUESTION it answers (pulled straight from the file's comment
    header), and
  * a few result rows.

This is the one-command acceptance check: if this script finishes without an
error, every query in the project runs cleanly against the seeded DB.

Usage
-----
    python build_database.py     # first, to create data/email_marketing.db
    python run_queries.py        # then run all queries
    python run_queries.py --rows 10        # show more rows per query
    python run_queries.py --db other.db    # point at a different database
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# Make stdout robust no matter how this script is launched (direct, piped to
# another tool, or redirected to a file). On Windows the default console code
# page is cp1252, which raises OSError/UnicodeEncodeError when output is piped.
# Reconfiguring to UTF-8 with errors="replace" keeps the runner from ever
# crashing on a stray character. (No-op on platforms that already use UTF-8.)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):  # pragma: no cover - very old Python only
    pass

HERE = Path(__file__).resolve().parent
DEFAULT_DB = HERE / "data" / "email_marketing.db"
QUERIES_DIR = HERE / "queries"

MAX_COL_WIDTH = 22          # truncate wide text columns when printing


def extract_business_question(sql_text: str) -> str:
    """Pull the 'BUSINESS QUESTION:' block out of a query file's header.

    The convention (see any file in queries/) is:

        -- BUSINESS QUESTION:
        --   line one of the question
        --   line two ...
        --
        -- (next labelled section, e.g. METRIC / TECHNIQUE / STRETCH)

    We return everything between 'BUSINESS QUESTION:' and the next blank
    comment line or the next ALL-CAPS label, with the leading '-- ' stripped.
    """
    lines = sql_text.splitlines()
    collecting = False
    out = []
    for raw in lines:
        line = raw.strip()
        if not line.startswith("--"):
            # First non-comment line ends the header for sure.
            if collecting:
                break
            continue
        # Strip the leading dashes and one optional space.
        content = line[2:].lstrip()

        if not collecting:
            if content.upper().startswith("BUSINESS QUESTION"):
                collecting = True
            continue

        # We are inside the question block. Stop at a blank comment line
        # (just '--') or at the next labelled section like 'METRIC:' / 'TECHNIQUE'.
        if content == "":
            break
        stripped_label = content.rstrip(":")
        if (content.endswith(":") and stripped_label.isupper()) or \
           content.upper().startswith(("METRIC", "TECHNIQUE", "STRETCH",
                                        "DATA NOTE", "REFERENCE DATE",
                                        "DELIVERABILITY", "LIST-HEALTH",
                                        "LIST QUALITY", "NOTE")):
            break
        out.append(content)

    return " ".join(out).strip() or "(no BUSINESS QUESTION header found)"


def _fmt(value) -> str:
    """Format one cell for printing: None -> 'NULL', wide text truncated."""
    if value is None:
        return "NULL"
    text = str(value)
    if len(text) > MAX_COL_WIDTH:
        return text[: MAX_COL_WIDTH - 3] + "..."
    return text


def print_result(cursor, max_rows: int) -> int:
    """Print up to `max_rows` rows from an executed cursor as a small table.
    Returns the number of rows actually fetched from the DB (capped at
    max_rows + 1 so we can tell the user there were 'more')."""
    columns = [d[0] for d in cursor.description] if cursor.description else []
    rows = cursor.fetchmany(max_rows + 1)

    if not columns:
        print("    (query returned no columns)")
        return 0
    if not rows:
        print("    (0 rows)")
        return 0

    # Header
    header = " | ".join(_fmt(c).ljust(MAX_COL_WIDTH) for c in columns)
    print("    " + header)
    print("    " + "-" * len(header))

    shown = rows[:max_rows]
    for row in shown:
        print("    " + " | ".join(_fmt(v).ljust(MAX_COL_WIDTH) for v in row))

    if len(rows) > max_rows:
        print(f"    ... (more rows; showing first {max_rows})")

    return len(shown)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run every queries/*.sql against the synthetic DB.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB,
                        help=f"path to the SQLite DB (default: {DEFAULT_DB})")
    parser.add_argument("--rows", type=int, default=6,
                        help="result rows to show per query (default: 6)")
    args = parser.parse_args()

    if not args.db.exists():
        print(f"ERROR: database not found at {args.db}\n"
              f"Run  python build_database.py  first.", file=sys.stderr)
        return 1

    sql_files = sorted(QUERIES_DIR.glob("*.sql"))
    if not sql_files:
        print(f"ERROR: no .sql files found in {QUERIES_DIR}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(args.db)
    failures = []

    print("#" * 70)
    print(f"  Running {len(sql_files)} queries against {args.db.name}")
    print(f"  (SYNTHETIC data — numbers are illustrative, not real)")
    print("#" * 70)

    for path in sql_files:
        sql_text = path.read_text(encoding="utf-8")
        question = extract_business_question(sql_text)

        print()
        print("=" * 70)
        print(f"  {path.name}")
        print("=" * 70)
        print(f"  Q: {question}")
        print("-" * 70)

        try:
            cur = conn.execute(sql_text)
            print_result(cur, args.rows)
        except sqlite3.Error as exc:
            failures.append((path.name, str(exc)))
            print(f"    !! ERROR: {exc}")

    conn.close()

    print()
    print("#" * 70)
    if failures:
        print(f"  FAILED: {len(failures)} of {len(sql_files)} queries errored:")
        for name, err in failures:
            print(f"    - {name}: {err}")
        print("#" * 70)
        return 1

    print(f"  SUCCESS: all {len(sql_files)} queries ran with no errors.")
    print("#" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
