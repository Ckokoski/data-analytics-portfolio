"""
prep_data.py
============

Downloads the U.S. Centers for Medicare & Medicaid Services (CMS)
"Hospital General Information" dataset, cleans it, and writes two tidy
CSV files into the ./data folder so they are ready to load into Power BI.

What it produces
----------------
1) data/hospitals_clean.csv
   One row per hospital. Identity + location + type/ownership + the
   headline "overall star rating" (1-5, or blank when not rated).

2) data/measures_clean.csv
   One row per hospital, carrying the five "measure group" counts that CMS
   publishes (Mortality, Safety, Readmission, Patient Experience, Timely &
   Effective care). It shares the SAME key column (facility_id) as the
   hospitals table, so in Power BI you can join the two tables 1-to-1 and
   practice building a small data model.

Why two tables?
---------------
The raw file is one very wide table (38 columns). Splitting the "what is
this hospital" facts from the "how many quality measures" facts is a common,
realistic way to build a clean 2-table star-style model in Power BI without
overwhelming a beginner. Both tables join on facility_id.

How to run
----------
    python prep_data.py

Requirements: pandas + the Python standard library only. (We use urllib
for the download so you do NOT need to install the `requests` package.)

If the download URL ever stops working, the script prints the exact CMS
page to download the file from by hand. See the FALLBACK note below.
"""

# ---------------------------------------------------------------------------
# Imports - all standard library except pandas
# ---------------------------------------------------------------------------
import sys
import io
import urllib.request
import urllib.error

import pandas as pd


# ---------------------------------------------------------------------------
# Configuration  (edit these two values if CMS refreshes the file)
# ---------------------------------------------------------------------------

# Direct CSV download URL for the CMS "Hospital General Information" dataset.
# Verified working June 2026. This is the stable "resources" file that the
# dataset page (https://data.cms.gov/provider-data/dataset/xubh-q36u) links to.
DATA_URL = (
    "https://data.cms.gov/provider-data/sites/default/files/resources/"
    "893c372430d9d71a1c52737d01239d47_1777413958/Hospital_General_Information.csv"
)

# The human-friendly dataset page. If the automatic download fails, the user
# can open this page in a browser and click the "Download" / "CSV" button.
DATASET_PAGE = "https://data.cms.gov/provider-data/dataset/xubh-q36u"

# How long to wait (seconds) before giving up on the download.
TIMEOUT_SECONDS = 120


def download_csv(url: str) -> pd.DataFrame:
    """
    Download the CSV at `url` and return it as a pandas DataFrame.

    We read EVERY column as text (dtype=str) on purpose. The raw CMS file
    uses the literal words "Not Available" for missing values, which would
    confuse automatic number parsing. We convert those to real nulls and fix
    the data types ourselves in clean_data().
    """
    print(f"Downloading CMS Hospital General Information from:\n  {url}")

    # A User-Agent header makes some government servers happier.
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw_bytes = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as error:
        # Friendly, actionable error message instead of a raw stack trace.
        print("\n" + "=" * 70)
        print("ERROR: Could not download the dataset automatically.")
        print(f"Reason: {error}")
        print("\nWhat to do instead (takes ~1 minute):")
        print(f"  1. Open this page in your browser:\n     {DATASET_PAGE}")
        print("  2. Click the 'Download' button (CSV) near the top of the page.")
        print("  3. Save the file as 'Hospital_General_Information.csv'")
        print("     inside this project's folder.")
        print("  4. Re-run this script - it will read the local file if the")
        print("     download fails. (See read_local_fallback below.)")
        print("=" * 70)
        # Try the local fallback before giving up entirely.
        return read_local_fallback()

    # The CMS file is UTF-8 with a byte-order-mark (BOM); utf-8-sig strips it.
    text = raw_bytes.decode("utf-8-sig")
    # keep_default_na=False + na_values=["Not Available", ""] means: treat ONLY
    # blanks and the literal "Not Available" as missing - nothing else.
    frame = pd.read_csv(
        io.StringIO(text),
        dtype=str,
        keep_default_na=False,
        na_values=["Not Available", ""],
    )
    print(f"Downloaded OK - {len(frame):,} rows, {len(frame.columns)} columns.")
    return frame


def read_local_fallback() -> pd.DataFrame:
    """
    If the live download failed, try to read a manually-downloaded copy named
    'Hospital_General_Information.csv' sitting next to this script. If that is
    not present either, exit with a clear message.
    """
    local_name = "Hospital_General_Information.csv"
    try:
        frame = pd.read_csv(
            local_name,
            dtype=str,
            encoding="utf-8-sig",
            keep_default_na=False,
            na_values=["Not Available", ""],
        )
        print(f"Loaded local fallback file '{local_name}' "
              f"({len(frame):,} rows).")
        return frame
    except FileNotFoundError:
        print(f"\nNo local '{local_name}' found either. "
              "Please download it (see steps above) and re-run. Exiting.")
        sys.exit(1)


def clean_data(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Rename the messy CMS column headers to clear snake_case names, keep only
    the columns we care about, and fix data types.

    Returns ONE cleaned wide frame; we split it into two tables afterwards.
    """
    # Map: exact raw CMS header  ->  clean snake_case name.
    # (Only the columns we keep are listed here.)
    rename_map = {
        "Facility ID": "facility_id",
        "Facility Name": "facility_name",
        "Address": "address",
        "City/Town": "city",
        "State": "state",
        "ZIP Code": "zip_code",
        "County/Parish": "county",
        "Telephone Number": "telephone",
        "Hospital Type": "hospital_type",
        "Hospital Ownership": "hospital_ownership",
        "Emergency Services": "emergency_services",
        "Meets criteria for birthing friendly designation": "birthing_friendly",
        "Hospital overall rating": "overall_rating",
        # --- the five measure-group counts (go into measures_clean.csv) ---
        "MORT Group Measure Count": "mortality_measure_count",
        "Safety Group Measure Count": "safety_measure_count",
        "READM Group Measure Count": "readmission_measure_count",
        "Pt Exp Group Measure Count": "patient_exp_measure_count",
        "TE Group Measure Count": "timely_effective_measure_count",
    }

    # Keep only the columns we mapped, then rename them.
    columns_to_keep = [c for c in rename_map if c in raw.columns]
    frame = raw[columns_to_keep].rename(columns=rename_map)

    # --- Fix data types -----------------------------------------------------
    # overall_rating is 1-5 (or null). Use pandas' nullable integer type so a
    # missing rating stays missing instead of becoming a misleading 0 or NaN
    # float like 4.0.
    frame["overall_rating"] = pd.to_numeric(
        frame["overall_rating"], errors="coerce"
    ).astype("Int64")

    # The five measure-count columns are whole numbers (or null).
    measure_count_columns = [
        "mortality_measure_count",
        "safety_measure_count",
        "readmission_measure_count",
        "patient_exp_measure_count",
        "timely_effective_measure_count",
    ]
    for column in measure_count_columns:
        frame[column] = pd.to_numeric(
            frame[column], errors="coerce"
        ).astype("Int64")

    # Tidy up the text columns: strip stray spaces. Keep facility_id as TEXT
    # because some IDs have leading zeros (e.g. "010001") that we must not lose.
    text_columns = [
        "facility_id", "facility_name", "address", "city", "state",
        "zip_code", "county", "telephone", "hospital_type",
        "hospital_ownership", "emergency_services", "birthing_friendly",
    ]
    for column in text_columns:
        if column in frame.columns:
            frame[column] = frame[column].str.strip()

    # Add a tiny helper flag that is handy for Power BI cards:
    # is_top_rated = True when the hospital is rated 4 or 5 stars.
    frame["is_top_rated"] = frame["overall_rating"].isin([4, 5])

    # Drop any row missing a facility_id (cannot be used as a key).
    frame = frame.dropna(subset=["facility_id"])
    # Guard against duplicate IDs so the 1-to-1 join in Power BI stays valid.
    frame = frame.drop_duplicates(subset=["facility_id"], keep="first")

    return frame


def main() -> None:
    """Run the whole download -> clean -> split -> save pipeline."""
    # 1) Download (or fall back to a local copy).
    raw = download_csv(DATA_URL)

    # 2) Clean / rename / retype.
    clean = clean_data(raw)

    # 3) Split the single wide frame into the two model tables.
    #    Table A: hospital identity, location, type, rating.
    hospitals = clean[[
        "facility_id", "facility_name", "address", "city", "state",
        "zip_code", "county", "telephone", "hospital_type",
        "hospital_ownership", "emergency_services", "birthing_friendly",
        "overall_rating", "is_top_rated",
    ]].copy()

    #    Table B: the per-hospital quality-measure group counts.
    #    Shares facility_id with Table A for a 1-to-1 relationship.
    measures = clean[[
        "facility_id",
        "mortality_measure_count",
        "safety_measure_count",
        "readmission_measure_count",
        "patient_exp_measure_count",
        "timely_effective_measure_count",
    ]].copy()

    # 4) Write both CSVs into ./data (index=False = no extra numbering column).
    hospitals.to_csv("data/hospitals_clean.csv", index=False, encoding="utf-8")
    measures.to_csv("data/measures_clean.csv", index=False, encoding="utf-8")

    # 5) Print a friendly summary so the user knows it worked.
    rated = hospitals["overall_rating"].notna().sum()
    top = int(hospitals["is_top_rated"].sum())
    print("\nDONE. Clean files written:")
    print(f"  data/hospitals_clean.csv  -> {len(hospitals):,} rows, "
          f"{len(hospitals.columns)} columns")
    print(f"  data/measures_clean.csv   -> {len(measures):,} rows, "
          f"{len(measures.columns)} columns")
    print(f"  ({rated:,} hospitals have an overall star rating; "
          f"{top:,} are rated 4-5 stars.)")


# Standard Python entry point: only run main() when this file is executed
# directly (e.g. `python prep_data.py`), not when imported.
if __name__ == "__main__":
    main()
