"""
import_to_sqlite.py
====================

Load a YouTube Studio per-video CSV export into a local SQLite database, tagging
each video as "Before" or "After" a content-change date (e.g. the day you started
new thumbnails/titles).

PRIVACY (read this):
    This script runs LOCALLY. Your REAL YouTube Studio exports belong in
    `data/private/` which is git-ignored — they never get committed or leave your
    machine. The only data committed to this repo is `data/sample_synthetic.csv`,
    which is fabricated for demonstration. Every query and chart in this project
    outputs RATES and PERCENTAGES only (CTR %, % change, indexes) — never raw
    views, impressions, or subscriber counts.

Usage:
    python import_to_sqlite.py                                  # uses the synthetic sample
    python import_to_sqlite.py data/private/my_export.csv       # your real export (local only)
    python import_to_sqlite.py data/private/my_export.csv --change-date 2025-10-01
"""
import argparse
import sqlite3
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DEFAULT_CSV = HERE / "data" / "sample_synthetic.csv"
DEFAULT_DB = HERE / "data" / "youtube.db"
DEFAULT_CHANGE_DATE = "2025-10-01"

# Columns we expect from a YouTube Studio per-video export (renamed for clarity).
EXPECTED_COLUMNS = [
    "video_title", "publish_date", "impressions", "ctr_percent",
    "views", "avg_percent_viewed", "subscribers_gained",
]


def load(csv_path: Path, db_path: Path, change_date: str) -> pd.DataFrame:
    """Read the CSV, tag Before/After by the change date, and write the `videos` table."""
    df = pd.read_csv(csv_path)
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise SystemExit(
            f"CSV is missing expected column(s): {', '.join(missing)}\n"
            f"Expected: {', '.join(EXPECTED_COLUMNS)}"
        )

    # Anything published on/after the change date is "After"; everything else "Before".
    published = pd.to_datetime(df["publish_date"])
    df["period"] = published.ge(pd.Timestamp(change_date)).map({True: "After", False: "Before"})
    df["publish_date"] = published.dt.strftime("%Y-%m-%d")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    df.to_sql("videos", con, if_exists="replace", index=False)
    con.close()
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a YouTube Studio CSV into SQLite.")
    parser.add_argument("csv", nargs="?", type=Path, default=DEFAULT_CSV,
                        help=f"input CSV (default: {DEFAULT_CSV.name})")
    parser.add_argument("-o", "--db", type=Path, default=DEFAULT_DB,
                        help=f"output SQLite DB (default: {DEFAULT_DB.name})")
    parser.add_argument("--change-date", default=DEFAULT_CHANGE_DATE,
                        help="YYYY-MM-DD split between Before/After (default: 2025-10-01)")
    args = parser.parse_args()

    df = load(args.csv, args.db, args.change_date)
    before = int((df["period"] == "Before").sum())
    after = int((df["period"] == "After").sum())
    print(f"Loaded {len(df)} videos into {args.db} "
          f"(Before={before}, After={after}; change date {args.change_date})")


if __name__ == "__main__":
    main()
