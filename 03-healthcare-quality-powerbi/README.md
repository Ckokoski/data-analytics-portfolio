# 03 — Healthcare Quality Dashboard (Power BI)

An interactive Power BI dashboard exploring the quality of U.S. hospitals using
the official CMS **Hospital General Information** dataset (the data behind
Medicare's public *Care Compare* site).

**Stack:** Python (pandas) for data prep · Power BI Desktop for the dashboard ·
DAX for measures.

---

## Problem

Patients, payers, and health systems want a quick, fair way to compare hospitals
on quality. CMS publishes an overall **1–5 star rating** for every
Medicare-registered hospital, but the raw file is one wide 38-column table mixing
addresses, footnotes, and dozens of measure counts — not easy to read at a
glance. **Which states and hospital types tend to score best? How many hospitals
are highly rated, and how many can't be rated at all?** This project turns the
raw CMS file into a clean model and a single-page dashboard that answers those
questions in seconds.

---

## Data

- **Dataset:** Hospital General Information — U.S. Centers for Medicare &
  Medicaid Services (CMS), Provider Data Catalog.
- **Landing page:** https://data.cms.gov/provider-data/dataset/xubh-q36u
- **Direct CSV used:** see [`prep_data.py`](prep_data.py) (`DATA_URL`).
- **Size:** 5,432 hospitals; the prep script keeps the columns that matter and
  splits them into two tidy tables.
- **License:** Public domain — a **work of the U.S. Government**, free to reuse;
  attribution to CMS appreciated. Full details and the per-column data
  dictionary are in [`data/README.md`](data/README.md).

---

## Method

1. **Prep ([`prep_data.py`](prep_data.py)).** Downloads the CMS CSV directly
   (stdlib `urllib`, with a timeout and a friendly manual-download fallback),
   converts `"Not Available"`/blanks to real nulls, renames columns to clear
   `snake_case`, fixes data types (keeping `facility_id`/`zip_code` as text so
   leading zeros survive), adds an `is_top_rated` flag, and writes two tidy
   tables to `data/`:
   - `hospitals_clean.csv` — one row per hospital (identity, location, type,
     ownership, star rating).
   - `measures_clean.csv` — per-hospital quality-measure group counts.
2. **Model + dashboard ([`BUILD_GUIDE.md`](BUILD_GUIDE.md)).** A step-by-step
   Power BI Desktop guide builds a 2-table model (joined 1:1 on `facility_id`),
   5 starter DAX measures (hospital count, average star rating, rated count,
   % rated 4–5, average safety measures), and a single-page layout with KPI
   cards, two column-chart breakdowns, and slicers. Followable in ~90 minutes.

---

## Findings

Reading the cleaned CMS data — the questions this dashboard is built to answer — a few things stand out:

- **Two in five hospitals can't be rated at all.** Of 5,432 hospitals, only **3,182 (59%) carry an overall star rating**; the other **41% are "Not Available,"** usually because CMS lacks enough underlying measures. That completeness gap is the first headline: any "average rating" describes a *rated subset*, not the whole country — so the dashboard shows the rated count beside every average and never hides the sample size.
- **Quality clusters in the middle.** Among rated hospitals the **average is 3.21 stars**, and the distribution is middle-heavy: 3 stars is the largest single group, only **25% of all hospitals (42% of rated) earn 4–5 stars**, and **27% of rated hospitals sit at 1–2 stars**.
- **Geography matters.** Average rating among rated hospitals ranges from **Utah (4.24), Colorado (3.96), and Wisconsin (3.78)** at the top to **Mississippi (2.33), Alabama (2.71), and Kentucky / West Virginia (~2.76)** at the bottom — about a two-star spread between the best and worst states.
- **Mostly non-profit, acute-care, ER-equipped.** Voluntary non-profit is the largest ownership group (~43%), acute-care the dominant type (~57%), and **83% offer emergency services** — context worth holding before reading too much into any single slice.

**So what:** "hospital quality" can't be read off one national average. The unrated 41% and the two-star state spread mean the honest analysis leads with *coverage and distribution*, then lets the user slice by state, ownership, and type — which is exactly what the dashboard's slicers are for.

*Data: public CMS "Hospital General Information" (June 2026 refresh); see [`data/README.md`](data/README.md). Figures shift slightly when CMS refreshes the dataset.*

> **Dashboard screenshots coming soon** — the `.pbix` is built in Power BI Desktop from [`BUILD_GUIDE.md`](BUILD_GUIDE.md); images land in [`images/`](images/).

---

## How to run

From this project folder (`03-healthcare-quality-powerbi/`):

```bash
# 1) Install the one dependency (pandas). requests is NOT needed — urllib is used.
pip install -r requirements.txt

# 2) Download + clean the CMS data. Writes data/hospitals_clean.csv and data/measures_clean.csv
python prep_data.py
```

Expected output on success:

```
Downloaded OK - 5,432 rows, 38 columns.

DONE. Clean files written:
  data/hospitals_clean.csv  -> 5,432 rows, 14 columns
  data/measures_clean.csv   -> 5,432 rows, 6 columns
  (3,182 hospitals have an overall star rating; 1,334 are rated 4-5 stars.)
```

Then open **Power BI Desktop** and follow [`BUILD_GUIDE.md`](BUILD_GUIDE.md) to
build the dashboard from the two CSVs.

> If the CMS download URL ever stops working, the script prints the exact CMS
> page to download the file from by hand, and you can update `DATA_URL` at the
> top of `prep_data.py`.
