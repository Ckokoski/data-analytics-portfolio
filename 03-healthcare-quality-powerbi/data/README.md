# Data — CMS Hospital General Information

This folder holds the cleaned data produced by [`../prep_data.py`](../prep_data.py).
The two CSV files here are generated from a single public dataset published by
the U.S. Centers for Medicare & Medicaid Services (CMS).

> Run `python prep_data.py` from the project folder to (re)create these files.
> They are small, so they are committed to the repo for convenience.

---

## Source dataset

| | |
|---|---|
| **Dataset name** | Hospital General Information |
| **Publisher** | U.S. Centers for Medicare & Medicaid Services (CMS) — Provider Data Catalog |
| **Dataset landing page** | https://data.cms.gov/provider-data/dataset/xubh-q36u |
| **Direct CSV used by the script** | https://data.cms.gov/provider-data/sites/default/files/resources/893c372430d9d71a1c52737d01239d47_1777413958/Hospital_General_Information.csv |
| **Dataset last updated (per CMS metadata)** | 2026-05-13 |
| **Downloaded for this project** | June 2026 |
| **Rows in the raw file** | 5,432 hospitals (38 columns) |

### What it is
A compilation of every Medicare-registered hospital in the United States and
its territories, including the hospital's name, address, type, ownership, and
its **overall quality star rating (1–5)** as calculated by CMS from dozens of
underlying quality measures (mortality, safety, readmission, patient
experience, and timely & effective care).

This is the same data that powers the public **Medicare Care Compare** website
that patients use to compare hospitals.

---

## License / usage terms

The data is a **work of the U.S. Government and is in the public domain.**
There are no copyright restrictions on reuse. Per CMS / HHS open-data policy,
attribution to CMS as the source is appreciated but not required.

- CMS Provider Data Catalog: https://data.cms.gov/provider-data/
- About the catalog: https://data.cms.gov/provider-data/about

This project cites CMS as the source and links the dataset page above.

> Note on accuracy: CMS refreshes this dataset periodically. If you re-download
> it later, the row counts and ratings may differ slightly from the numbers
> quoted in this repo. If CMS changes the direct file URL, open the dataset
> landing page above and use its **Download** button, or update `DATA_URL` near
> the top of `prep_data.py`.

---

## Cleaned files in this folder

The prep script splits the one wide raw file into **two tidy tables** that
share the key column `facility_id`. This makes a clean, beginner-friendly
2-table model in Power BI (join them 1-to-1 on `facility_id`).

### 1) `hospitals_clean.csv` — one row per hospital (5,432 rows, 14 columns)

| Column | Type | Meaning |
|---|---|---|
| `facility_id` | text | CMS Certification Number — the unique hospital ID. **Kept as text** to preserve leading zeros (e.g. `010001`). This is the join key. |
| `facility_name` | text | Hospital name. |
| `address` | text | Street address. |
| `city` | text | City / town. |
| `state` | text | 2-letter state or territory code (56 distinct values). |
| `zip_code` | text | ZIP code (text, to keep leading zeros). |
| `county` | text | County / parish. |
| `telephone` | text | Main phone number. |
| `hospital_type` | text | e.g. *Acute Care Hospitals*, *Critical Access Hospitals*, *Psychiatric*, *Childrens*. 8 distinct values. |
| `hospital_ownership` | text | e.g. *Voluntary non-profit – Private*, *Proprietary*, *Government – Local*. 12 distinct values. |
| `emergency_services` | text | `Yes` / `No` — whether the hospital offers emergency services. |
| `birthing_friendly` | text | `Y` / `N` — meets CMS criteria for birthing-friendly designation (blank if not reported). |
| `overall_rating` | whole number (nullable) | CMS overall hospital star rating, **1–5**. **Blank** when CMS lists the hospital as "Not Available" (not enough measures to rate). 3,182 of 5,432 hospitals are rated. |
| `is_top_rated` | true/false | Helper flag added by the script: `True` when `overall_rating` is 4 or 5. 1,334 hospitals are top-rated. |

### 2) `measures_clean.csv` — one row per hospital (5,432 rows, 6 columns)

These are the counts of how many individual quality measures CMS had available
for each hospital, grouped into the five categories that feed the overall star
rating. Blank when CMS marks the group "Not Available" for that hospital.

| Column | Type | Meaning |
|---|---|---|
| `facility_id` | text | Same hospital ID as above — the join key back to `hospitals_clean.csv`. |
| `mortality_measure_count` | whole number (nullable) | Number of **mortality** measures in the group for this hospital. |
| `safety_measure_count` | whole number (nullable) | Number of **safety of care** measures. |
| `readmission_measure_count` | whole number (nullable) | Number of **readmission** measures. |
| `patient_exp_measure_count` | whole number (nullable) | Number of **patient experience** measures. |
| `timely_effective_measure_count` | whole number (nullable) | Number of **timely & effective care** measures. |

---

## How the cleaning works (plain English)

`prep_data.py`:

1. Downloads the raw CSV directly from CMS (with a timeout and a friendly
   error message + manual-download instructions if the server is unreachable).
2. Converts the literal text `"Not Available"` and blank cells into real
   **nulls** (so they don't pollute averages or counts in Power BI).
3. Renames the long CMS column headers to short, clear `snake_case` names.
4. Sets correct data types — star rating and measure counts become whole
   numbers; IDs and ZIP codes stay as text to protect leading zeros.
5. Adds the `is_top_rated` helper flag.
6. Splits the data into the two tables above and writes them here.
