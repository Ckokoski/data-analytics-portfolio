"""Smoke test for the Email Marketing SQL project.

The acceptance check from the brief:
  1. build_database.py builds a SQLite DB with the three expected tables,
  2. the engagement table has ~5,000 rows,
  3. the synthetic-data invariants hold (clicked => opened),
  4. EVERY queries/*.sql runs against the seeded DB with zero errors.

Everything runs against a throwaway database in a tmp_path so the committed
data/email_marketing.db is never touched by the tests.
"""
import sqlite3

import pytest

import build_database
import run_queries


@pytest.fixture(scope="module")
def temp_db(tmp_path_factory):
    """Build the synthetic DB once into a temp file and hand back its path."""
    db_path = tmp_path_factory.mktemp("emaildb") / "email_marketing.db"
    subscribers, sends, engagement = build_database.build(seed=build_database.SEED)
    build_database.write_db(db_path, subscribers, sends, engagement)
    return db_path


def test_tables_exist(temp_db):
    conn = sqlite3.connect(temp_db)
    try:
        names = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()
    assert {"subscribers", "sends", "engagement"}.issubset(names)


def test_engagement_row_count_is_about_5000(temp_db):
    conn = sqlite3.connect(temp_db)
    try:
        n = conn.execute("SELECT COUNT(*) FROM engagement").fetchone()[0]
    finally:
        conn.close()
    # "~5,000" per the brief -- allow a generous band around the target.
    assert 4000 <= n <= 6000, f"expected ~5000 engagement rows, got {n}"


def test_clicked_implies_opened(temp_db):
    """The core data rule: you cannot click an email you never opened."""
    conn = sqlite3.connect(temp_db)
    try:
        violations = conn.execute(
            "SELECT COUNT(*) FROM engagement WHERE clicked = 1 AND opened = 0"
        ).fetchone()[0]
        # click_datetime must be present exactly when clicked = 1
        click_dt_mismatch = conn.execute(
            "SELECT COUNT(*) FROM engagement "
            "WHERE (clicked = 1) <> (click_datetime IS NOT NULL)"
        ).fetchone()[0]
    finally:
        conn.close()
    assert violations == 0
    assert click_dt_mismatch == 0


def test_inactive_cohort_is_meaningful(temp_db):
    """There should be a non-trivial inactive cohort (the whole point of the
    sunset-candidate queries)."""
    conn = sqlite3.connect(temp_db)
    try:
        total = conn.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0]
        inactive = conn.execute(
            "SELECT COUNT(*) FROM subscribers WHERE status = 'inactive'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert inactive > 0
    # A meaningful cohort, but not the entire list.
    assert 0.1 < inactive / total < 0.9


def test_every_query_runs_without_error(temp_db):
    """Run all queries/*.sql against the seeded DB; none may raise."""
    sql_files = sorted(run_queries.QUERIES_DIR.glob("*.sql"))
    assert sql_files, "no .sql files found in queries/"

    conn = sqlite3.connect(temp_db)
    failures = []
    try:
        for path in sql_files:
            sql_text = path.read_text(encoding="utf-8")
            try:
                conn.execute(sql_text).fetchall()
            except sqlite3.Error as exc:  # pragma: no cover - failure path
                failures.append(f"{path.name}: {exc}")
    finally:
        conn.close()

    assert not failures, "queries errored:\n" + "\n".join(failures)


def test_every_query_has_business_question_header():
    """Each query file must document the business question it answers."""
    sql_files = sorted(run_queries.QUERIES_DIR.glob("*.sql"))
    missing = []
    for path in sql_files:
        text = path.read_text(encoding="utf-8")
        if "BUSINESS QUESTION" not in text:
            missing.append(path.name)
    assert not missing, f"files missing a BUSINESS QUESTION header: {missing}"


def test_exactly_two_window_function_files_flagged():
    """The brief allows ONE or TWO window-function files and requires each to
    carry a prominent '-- STRETCH (window function)' comment. Verify that the
    only files mentioning a window function are the flagged ones."""
    sql_files = sorted(run_queries.QUERIES_DIR.glob("*.sql"))
    flagged = []
    uses_window = []
    for path in sql_files:
        text = path.read_text(encoding="utf-8")
        upper = text.upper()
        if "STRETCH (WINDOW FUNCTION)" in upper:
            flagged.append(path.name)
        # A real window-function call always has 'OVER (' / 'OVER(' in the SQL.
        if "OVER (" in upper or "OVER(" in upper:
            uses_window.append(path.name)

    # 1 or 2 flagged files allowed by the brief; we ship 2.
    assert 1 <= len(flagged) <= 2, f"flagged window files: {flagged}"
    # Every file that actually uses a window function must be a flagged one.
    assert set(uses_window) == set(flagged), (
        f"window functions appear in unflagged files: "
        f"{set(uses_window) - set(flagged)}")
