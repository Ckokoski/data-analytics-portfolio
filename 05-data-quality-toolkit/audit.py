"""
audit.py — a CSV data-quality audit tool.

WHAT THIS DOES (in plain English)
---------------------------------
You point this script at ANY .csv file. It reads the file, runs a checklist of
data-quality checks (the kind of checks a careful analyst runs before trusting a
dataset), and writes a plain-language Markdown report you could hand to a manager.
It also prints a short summary to the screen and ends with a single verdict:

    PASS    — the data looks fit for analysis as-is.
    REVIEW  — usable, but there are issues a human should look at first.
    FAIL    — there are serious problems; don't analyze this until it's fixed.

HOW TO RUN IT
-------------
    python audit.py path/to/file.csv

    # optional flags:
    python audit.py data/messy_customers.csv --key customer_id
    python audit.py data/messy_orders.csv --rules rules_example.json

WHY THIS EXISTS
---------------
In a previous role I built QA checklists for email production — the human steps
that catch a broken link or a wrong merge field BEFORE it goes to a million
inboxes. This is that same QA instinct, written as code: a repeatable first-pass
check on any spreadsheet, so two people can't "eyeball" the same file and reach
two different conclusions about whether it's clean.

A NOTE FOR NON-ENGINEERS READING THE CODE
-----------------------------------------
This file is commented heavily on purpose. Each section is labelled, and the
checks are small, named functions so you can read them one at a time. You should
be able to follow the logic top to bottom without a programming background.
"""

# ---------------------------------------------------------------------------
# IMPORTS — the toolkits this script borrows from.
# ---------------------------------------------------------------------------
import argparse        # reads the command-line options the user types (the flags above)
import json            # reads the optional --rules file, which is written in JSON
import sys             # lets us exit with a status code the operating system understands
from pathlib import Path  # a friendly way to handle file paths on Windows or Mac
from datetime import datetime  # to timestamp the report

import pandas as pd    # the spreadsheet engine: it loads the CSV into a table ("DataFrame")


# ---------------------------------------------------------------------------
# TUNABLE THRESHOLDS — the "rules of thumb" that turn raw numbers into a verdict.
#
# These are deliberately gathered in one place and named, so a reviewer can see
# exactly where the PASS / REVIEW / FAIL line is drawn and disagree with it if
# they want. Nothing here is a law of nature — they're sensible defaults.
# ---------------------------------------------------------------------------

# A column missing MORE than this share of its values is a *serious* problem.
NULL_RATE_FAIL = 0.50      # 50%+ of a column is blank  -> counts toward FAIL
# A column missing more than this (but less than the FAIL line) is worth a look.
NULL_RATE_REVIEW = 0.05    # 5%+ of a column is blank   -> counts toward REVIEW

# If this share of full rows are exact duplicates, that's a serious problem.
DUP_ROW_FAIL = 0.10        # 10%+ of rows are duplicated -> counts toward FAIL

# When a column is *mostly* numbers but a few values aren't, how do we treat it?
# If at least this share of the non-blank values look numeric, we call the column
# "numeric-ish" and flag the stray text values as data-entry errors to fix.
NUMERIC_MAJORITY = 0.80    # 80%+ of values look like numbers -> treat column as numeric


# ===========================================================================
# SECTION 1 — SMALL HELPER CHECKS
# Each function below answers ONE question about the data and returns a small,
# plain result (a number, or a list of findings). They do not print anything;
# the report-building section decides how to present them.
# ===========================================================================


def looks_numeric(value) -> bool:
    """
    Return True if a single cell value could be read as a number.

    We strip common, harmless decorations first — a dollar sign, commas used as
    thousands separators, a trailing percent sign, surrounding spaces — because
    "$1,200" is really the number 1200 wearing a costume. If, after removing
    those, Python can turn it into a number, we say it "looks numeric".

    Truly blank cells return False here; blanks are counted separately as nulls,
    not as "non-numeric text", so we don't double-punish them.
    """
    # pandas marks missing cells as NaN ("not a number"); treat those as blank.
    if pd.isna(value):
        return False

    text = str(value).strip()
    if text == "":
        return False

    # Remove the common costume pieces a number might be wearing.
    cleaned = text.replace("$", "").replace(",", "").replace("%", "").strip()

    try:
        float(cleaned)   # if this succeeds, it really is a number
        return True
    except ValueError:
        return False     # e.g. "twelve", "N/A", "tbd" — not a number


def null_rates(df: pd.DataFrame) -> dict:
    """
    For every column, work out what share of its cells are blank (missing).

    Returns a dictionary like {"email": 0.12, "age": 0.0} meaning the 'email'
    column is 12% blank and 'age' has no blanks. We treat a few common
    "fake blanks" — the literal text "NA", "N/A", "null", "none", "-", or an
    empty string — as missing too, because in real exports those are blanks in
    disguise.
    """
    # Strings that humans use to mean "nothing here" but that import as text.
    fake_blanks = {"", "na", "n/a", "null", "none", "nan", "-", "--"}

    result = {}
    total_rows = len(df)

    for column in df.columns:
        if total_rows == 0:
            result[column] = 0.0
            continue

        # Start with the cells pandas already knows are missing.
        missing = df[column].isna()

        # Also count the "fake blank" text values, compared case-insensitively.
        as_text = df[column].astype(str).str.strip().str.lower()
        missing = missing | as_text.isin(fake_blanks)

        result[column] = missing.sum() / total_rows

    return result


def duplicate_full_rows(df: pd.DataFrame) -> int:
    """
    Count how many rows are EXACT copies of an earlier row (every column equal).

    pandas' .duplicated() marks the 2nd, 3rd, ... appearance of a repeated row as
    True (the first appearance is considered the "original" and is not counted),
    so the sum is the number of extra, redundant rows.
    """
    return int(df.duplicated().sum())


def duplicate_keys(df: pd.DataFrame, key: str) -> list:
    """
    For a column that is supposed to be a unique ID (like customer_id), find any
    ID values that show up on more than one row.

    Returns a list of (id_value, how_many_times_it_appears) pairs. An empty list
    means the key is clean (every value unique). If the named key column doesn't
    exist, we return the special value None so the caller can warn about it.
    """
    if key not in df.columns:
        return None

    counts = df[key].value_counts(dropna=True)   # how many times each value appears
    repeated = counts[counts > 1]                # keep only the ones appearing 2+ times
    return list(repeated.items())                # e.g. [("C001", 3), ("C014", 2)]


def type_problems(df: pd.DataFrame) -> list:
    """
    Find columns that look like they're meant to hold numbers but contain some
    text values — the classic "amount column with 'tbd' typed into one cell"
    problem that breaks every later calculation.

    For each text column we ask: of the non-blank values, what share look numeric?
      - If ALL of them are numeric, the column is fine (it's just stored as text,
        which is common in CSVs and harmless once we know it).
      - If MOST (>= NUMERIC_MAJORITY) are numeric but a few aren't, we flag it as
        a numeric column with stray non-numeric values, and list a few examples.
      - If it's a real mix or mostly text, we leave it alone — it's probably a
        genuine text column (names, categories) and not a data-quality bug.

    Returns a list of finding-dictionaries, one per problematic column.
    """
    findings = []

    for column in df.columns:
        series = df[column]

        # Columns pandas already parsed as numbers can't have stray text — skip.
        if pd.api.types.is_numeric_dtype(series):
            continue

        # Look only at non-blank cells; blanks are handled by the null check.
        non_blank = series.dropna()
        non_blank = non_blank[non_blank.astype(str).str.strip() != ""]
        if len(non_blank) == 0:
            continue  # column is entirely blank; the null check will catch that

        # Which non-blank values look like numbers?
        is_num = non_blank.apply(looks_numeric)
        numeric_share = is_num.mean()  # mean of True/False = share that are True

        # A fully-numeric-but-stored-as-text column is fine; don't flag it.
        if numeric_share == 1.0:
            continue

        # Mostly numeric with a few offenders -> this is the bug we care about.
        if numeric_share >= NUMERIC_MAJORITY:
            # Grab up to 5 example bad values to show the manager what to fix.
            offenders = non_blank[~is_num].unique().tolist()[:5]
            findings.append({
                "column": column,
                "numeric_share": numeric_share,
                "bad_examples": offenders,
            })

    return findings


def range_problems(df: pd.DataFrame, rules: dict) -> list:
    """
    Check numeric columns against simple min/max rules supplied by the user.

    `rules` looks like: {"age": {"min": 0, "max": 120}, "price": {"min": 0}}
    Meaning: ages must be between 0 and 120; prices must be at least 0.

    For each rule we count how many rows fall outside the allowed range and grab
    a couple of example offending values. We only check columns we can actually
    read as numbers; if a rule names a missing column we note that instead.

    Returns a list of finding-dictionaries, one per rule that found a problem
    (or that named a missing column).
    """
    findings = []

    for column, bounds in rules.items():
        # If the rule points at a column that isn't in the file, say so clearly.
        if column not in df.columns:
            findings.append({
                "column": column,
                "missing_column": True,
            })
            continue

        # Convert the column to numbers; anything non-numeric becomes blank (NaN)
        # here and is simply ignored by the range comparison (it's a *type*
        # problem, already caught above — not a *range* problem).
        as_numbers = pd.to_numeric(df[column], errors="coerce")

        low = bounds.get("min", None)   # may be absent -> no lower limit
        high = bounds.get("max", None)  # may be absent -> no upper limit

        # Build a True/False mask of rows that break the rule.
        too_low = as_numbers < low if low is not None else False
        too_high = as_numbers > high if high is not None else False
        out_of_range = (too_low | too_high)

        bad_count = int(out_of_range.sum())
        if bad_count > 0:
            examples = as_numbers[out_of_range].dropna().unique().tolist()[:5]
            findings.append({
                "column": column,
                "min": low,
                "max": high,
                "bad_count": bad_count,
                "bad_examples": examples,
            })

    return findings


# ===========================================================================
# SECTION 2 — THE VERDICT
# Take all the small findings and reduce them to one of PASS / REVIEW / FAIL,
# with a written list of the specific reasons. This is the "should I trust it?"
# call, made explicit instead of left to a gut feeling.
# ===========================================================================


def decide_verdict(
    n_rows,
    nulls,
    dup_rows,
    dup_key_list,
    type_issues,
    range_issues,
) -> tuple:
    """
    Weigh up every finding and return (verdict, reasons).

      verdict — the string "PASS", "REVIEW", or "FAIL".
      reasons — a list of plain-English sentences explaining the verdict.

    The logic, in words:
      * Anything that makes the data untrustworthy to actually analyze pushes the
        verdict toward FAIL (a half-empty column, lots of duplicate rows, a
        numeric column full of bad values, many out-of-range values).
      * Smaller blemishes that a human should glance at — a little missingness,
        a handful of duplicate IDs — push toward REVIEW.
      * If nothing trips either bar, it's a PASS.
    """
    fail_reasons = []     # serious problems
    review_reasons = []   # worth-a-look problems

    # An empty file is an automatic FAIL — there's nothing to analyze.
    if n_rows == 0:
        return "FAIL", ["The file has 0 data rows — there is nothing to analyze."]

    # --- Missing values, column by column. ---
    for column, rate in nulls.items():
        pct = rate * 100
        if rate >= NULL_RATE_FAIL:
            fail_reasons.append(
                f"Column '{column}' is {pct:.0f}% empty (over the "
                f"{NULL_RATE_FAIL*100:.0f}% serious-problem line)."
            )
        elif rate >= NULL_RATE_REVIEW:
            review_reasons.append(
                f"Column '{column}' is {pct:.0f}% empty — check whether those "
                f"blanks are expected."
            )

    # --- Exact duplicate rows. ---
    if n_rows > 0:
        dup_share = dup_rows / n_rows
        if dup_share >= DUP_ROW_FAIL:
            fail_reasons.append(
                f"{dup_rows} rows ({dup_share*100:.0f}%) are exact duplicates "
                f"(over the {DUP_ROW_FAIL*100:.0f}% line) — totals will be "
                f"double-counted."
            )
        elif dup_rows > 0:
            review_reasons.append(
                f"{dup_rows} exact-duplicate row(s) found — confirm these aren't "
                f"inflating your counts."
            )

    # --- Duplicate ID values in the key column (if a key was given). ---
    if dup_key_list:  # non-empty list means duplicates were found
        n_dupe_ids = len(dup_key_list)
        review_reasons.append(
            f"{n_dupe_ids} value(s) in the key column appear on more than one "
            f"row — the key is not unique."
        )

    # --- Numeric columns polluted with text. ---
    for issue in type_issues:
        review_reasons.append(
            f"Column '{issue['column']}' looks numeric but has stray "
            f"non-numeric value(s) such as {issue['bad_examples']} — these will "
            f"break calculations."
        )

    # --- Values outside the allowed range. ---
    for issue in range_issues:
        if issue.get("missing_column"):
            review_reasons.append(
                f"A range rule was given for column '{issue['column']}', but that "
                f"column isn't in the file."
            )
            continue
        # If a large share of a column is out of range, escalate to FAIL.
        share = issue["bad_count"] / n_rows
        sentence = (
            f"Column '{issue['column']}' has {issue['bad_count']} value(s) "
            f"outside the allowed range (e.g. {issue['bad_examples']})."
        )
        if share >= 0.10:
            fail_reasons.append(sentence + " That's over 10% of rows.")
        else:
            review_reasons.append(sentence)

    # --- Combine into a single verdict. ---
    if fail_reasons:
        # FAIL shows the serious reasons first, then the lesser ones for context.
        return "FAIL", fail_reasons + review_reasons
    if review_reasons:
        return "REVIEW", review_reasons
    return "PASS", ["No blocking data-quality issues were detected by these checks."]


# ===========================================================================
# SECTION 3 — BUILD THE MARKDOWN REPORT
# Turn all the findings into a tidy Markdown document a non-technical reader can
# skim: a verdict banner at the top, then the supporting detail in tables.
# ===========================================================================


def build_report(
    csv_path,
    df,
    nulls,
    dup_rows,
    dup_key_list,
    key,
    type_issues,
    range_issues,
    rules,
    verdict,
    reasons,
) -> str:
    """
    Assemble the full report as one big Markdown string and return it.
    (Writing it to disk happens back in main(); this function just builds text.)
    """
    n_rows = len(df)
    n_cols = len(df.columns)

    # A small visual cue so the verdict is impossible to miss at a glance.
    badge = {"PASS": "🟢 PASS", "REVIEW": "🟡 REVIEW", "FAIL": "🔴 FAIL"}[verdict]

    lines = []  # we collect lines, then join them with newlines at the end

    # --- Header ---------------------------------------------------------
    lines.append(f"# Data-Quality Audit — `{Path(csv_path).name}`")
    lines.append("")
    lines.append(
        f"_Generated by `audit.py` on "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}._"
    )
    lines.append("")

    # --- The verdict, front and centre ----------------------------------
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"### {badge}")
    lines.append("")
    lines.append("**Why:**")
    lines.append("")
    for reason in reasons:
        lines.append(f"- {reason}")
    lines.append("")
    lines.append(
        "> **How to read this:** **PASS** = safe to analyze as-is. "
        "**REVIEW** = usable, but check the points above first. "
        "**FAIL** = fix the serious problems before drawing any conclusions."
    )
    lines.append("")

    # --- At-a-glance overview ------------------------------------------
    lines.append("## Overview")
    lines.append("")
    lines.append("| Measure | Value |")
    lines.append("|---|---|")
    lines.append(f"| Rows of data | {n_rows:,} |")
    lines.append(f"| Columns | {n_cols} |")
    lines.append(f"| Exact-duplicate rows | {dup_rows:,} |")
    if key:
        if dup_key_list is None:
            key_note = f"key column '{key}' not found"
        elif len(dup_key_list) == 0:
            key_note = f"'{key}' is unique ✅"
        else:
            key_note = f"{len(dup_key_list)} repeated value(s) in '{key}' ⚠️"
        lines.append(f"| Key uniqueness | {key_note} |")
    lines.append("")

    # --- Missing-value table -------------------------------------------
    lines.append("## Missing values (per column)")
    lines.append("")
    lines.append(
        "Share of each column that is blank. We also count common stand-ins for "
        "blank — `NA`, `N/A`, `null`, `none`, `-` — as missing."
    )
    lines.append("")
    lines.append("| Column | % missing | Flag |")
    lines.append("|---|---|---|")
    # Show the emptiest columns first so the worst offenders are at the top.
    for column, rate in sorted(nulls.items(), key=lambda kv: kv[1], reverse=True):
        pct = rate * 100
        if rate >= NULL_RATE_FAIL:
            flag = "🔴 serious"
        elif rate >= NULL_RATE_REVIEW:
            flag = "🟡 review"
        else:
            flag = "—"
        lines.append(f"| {column} | {pct:.1f}% | {flag} |")
    lines.append("")

    # --- Duplicate keys detail (only if relevant) ----------------------
    if key and dup_key_list:
        lines.append(f"## Duplicate keys in `{key}`")
        lines.append("")
        lines.append(
            "These ID values appear on more than one row. If this column is "
            "meant to be a unique identifier, each of these is a data problem."
        )
        lines.append("")
        lines.append(f"| {key} | times it appears |")
        lines.append("|---|---|")
        for value, count in dup_key_list[:25]:  # cap the list so it stays readable
            lines.append(f"| {value} | {count} |")
        if len(dup_key_list) > 25:
            lines.append(f"| …and {len(dup_key_list) - 25} more | |")
        lines.append("")

    # --- Type problems --------------------------------------------------
    lines.append("## Type consistency")
    lines.append("")
    if type_issues:
        lines.append(
            "These columns look like they should hold numbers, but a few cells "
            "contain text. Those stray values silently break sums, averages, and "
            "charts until they're cleaned."
        )
        lines.append("")
        lines.append("| Column | % of values that are numeric | Example bad values |")
        lines.append("|---|---|---|")
        for issue in type_issues:
            share = issue["numeric_share"] * 100
            examples = ", ".join(f"`{v}`" for v in issue["bad_examples"])
            lines.append(f"| {issue['column']} | {share:.0f}% | {examples} |")
    else:
        lines.append("No numeric-looking columns were found with stray text values. ✅")
    lines.append("")

    # --- Range problems -------------------------------------------------
    lines.append("## Out-of-range values")
    lines.append("")
    if not rules:
        lines.append(
            "_No range rules were supplied (`--rules`), so this check was "
            "skipped. To enable it, pass a JSON file like_ "
            "`{\"age\": {\"min\": 0, \"max\": 120}}`."
        )
    elif range_issues:
        lines.append("Values that fall outside the limits you supplied via `--rules`:")
        lines.append("")
        lines.append("| Column | allowed range | # outside | example bad values |")
        lines.append("|---|---|---|---|")
        for issue in range_issues:
            if issue.get("missing_column"):
                lines.append(
                    f"| {issue['column']} | _(rule given)_ | — | "
                    f"column not found in file |"
                )
                continue
            lo = issue["min"] if issue["min"] is not None else "−∞"
            hi = issue["max"] if issue["max"] is not None else "∞"
            examples = ", ".join(f"`{v}`" for v in issue["bad_examples"])
            lines.append(
                f"| {issue['column']} | {lo} … {hi} | {issue['bad_count']} | "
                f"{examples} |"
            )
    else:
        lines.append("Every value checked fell within the supplied limits. ✅")
    lines.append("")

    # --- Footer / honesty note -----------------------------------------
    lines.append("---")
    lines.append("")
    lines.append(
        "_This is an automated first-pass check, not a guarantee of correctness. "
        "It flags the common, mechanical problems that make a dataset unsafe to "
        "analyze; it can't judge whether the numbers are *meaningful*. Treat a "
        "PASS as “clear to start,” not “certified true.”_"
    )
    lines.append("")

    return "\n".join(lines)


# ===========================================================================
# SECTION 4 — THE MAIN PROGRAM
# This is what runs when you type `python audit.py ...`. It reads the options,
# loads the file, calls every check, builds the report, writes it to disk, and
# prints the short summary + verdict to the screen.
# ===========================================================================


def main(argv=None):
    # --- 4a. Describe and read the command-line options. ---------------
    parser = argparse.ArgumentParser(
        description=(
            "Audit a CSV file for data-quality problems and write a Markdown "
            "report. Works on any CSV."
        )
    )
    parser.add_argument(
        "csv_path",
        help="Path to the CSV file to audit, e.g. data/messy_customers.csv",
    )
    parser.add_argument(
        "--key",
        default=None,
        help=(
            "Name of a column that is supposed to be a unique ID (e.g. "
            "customer_id). The audit will report any repeated values."
        ),
    )
    parser.add_argument(
        "--rules",
        default=None,
        help=(
            "Path to a JSON file of min/max range rules, e.g. "
            '{"age": {"min": 0, "max": 120}}. Optional.'
        ),
    )
    parser.add_argument(
        "--outdir",
        default="output",
        help="Folder to write the report into (default: output).",
    )
    args = parser.parse_args(argv)

    # --- 4b. Make sure the file exists before we do anything else. -----
    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"ERROR: file not found: {csv_path}")
        return 2  # a non-zero exit code tells the OS something went wrong

    # --- 4c. Load the optional range rules, if the user gave any. ------
    rules = {}
    if args.rules:
        rules_path = Path(args.rules)
        if not rules_path.exists():
            print(f"ERROR: --rules file not found: {rules_path}")
            return 2
        with open(rules_path, "r", encoding="utf-8") as fh:
            rules = json.load(fh)

    # --- 4d. Read the CSV into a table. --------------------------------
    # We read EVERYTHING as text first (dtype=str) on purpose: that way the
    # script — not pandas — decides what looks numeric, so a column with one bad
    # value isn't silently mangled before we get to inspect it.
    try:
        df = pd.read_csv(csv_path, dtype=str, keep_default_na=True)
    except Exception as exc:  # noqa: BLE001 - we want a friendly message for any failure
        print(f"ERROR: could not read CSV: {exc}")
        return 2

    # --- 4e. Run every check. ------------------------------------------
    nulls = null_rates(df)
    dup_rows = duplicate_full_rows(df)
    dup_key_list = duplicate_keys(df, args.key) if args.key else None
    type_issues = type_problems(df)
    range_issues = range_problems(df, rules)

    # --- 4f. Reduce all findings to a single verdict. ------------------
    # Note: duplicate_keys returns None if the key column is missing; for the
    # verdict we treat "missing key" as "no duplicate-key problem" (an empty list).
    dup_key_for_verdict = dup_key_list if dup_key_list else []
    verdict, reasons = decide_verdict(
        n_rows=len(df),
        nulls=nulls,
        dup_rows=dup_rows,
        dup_key_list=dup_key_for_verdict,
        type_issues=type_issues,
        range_issues=range_issues,
    )

    # --- 4g. Build the Markdown report and write it to disk. -----------
    report_text = build_report(
        csv_path=csv_path,
        df=df,
        nulls=nulls,
        dup_rows=dup_rows,
        dup_key_list=dup_key_list,
        key=args.key,
        type_issues=type_issues,
        range_issues=range_issues,
        rules=rules,
        verdict=verdict,
        reasons=reasons,
    )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)  # create output/ if it isn't there
    report_path = outdir / f"{csv_path.stem}_report.md"
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report_text)

    # --- 4h. Print a short summary to the screen. ----------------------
    # The full detail lives in the Markdown file; this is just the headline so a
    # person running it in a terminal gets instant feedback.
    print()
    print("=" * 60)
    print(f"  DATA-QUALITY AUDIT — {csv_path.name}")
    print("=" * 60)
    print(f"  Rows:    {len(df):,}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Exact-duplicate rows: {dup_rows:,}")
    if args.key:
        if dup_key_list is None:
            print(f"  Key '{args.key}': column not found")
        elif len(dup_key_list) == 0:
            print(f"  Key '{args.key}': unique (good)")
        else:
            print(f"  Key '{args.key}': {len(dup_key_list)} repeated value(s)")
    print("-" * 60)
    print(f"  VERDICT: {verdict}")
    for reason in reasons[:5]:  # show up to 5 reasons on screen; rest are in the file
        print(f"    - {reason}")
    if len(reasons) > 5:
        print(f"    ...and {len(reasons) - 5} more (see the report).")
    print("-" * 60)
    print(f"  Full report written to: {report_path}")
    print("=" * 60)
    print()

    # Exit code mirrors the verdict so this can be used in automated pipelines:
    #   0 = PASS, 1 = REVIEW, 3 = FAIL  (2 is reserved for "couldn't run" above).
    return {"PASS": 0, "REVIEW": 1, "FAIL": 3}[verdict]


# This standard Python line means: "only run main() if this file is executed
# directly (python audit.py ...), not if it's imported by another file (like a
# test)." sys.exit() passes our return code up to the operating system.
if __name__ == "__main__":
    sys.exit(main())
