# Build Guide — Healthcare Quality Dashboard (Power BI Desktop)

This guide walks you through building a single-page Power BI dashboard from the
two cleaned CSV files in `data/`. It is written for an **advanced beginner** —
if you know KPI cards, column charts, slicers, and a little DAX, you can finish
this in about **90 minutes**.

**Before you start:** run the prep script once so the data exists.

```bash
python prep_data.py
```

That creates:
- `data/hospitals_clean.csv` (5,432 rows — one per hospital)
- `data/measures_clean.csv` (5,432 rows — quality-measure counts per hospital)

You will need **Power BI Desktop** (free from the Microsoft Store).

---

## Part 1 — Import the two CSVs with Power Query (about 20 min)

### 1.1 Load the hospitals file
1. Open Power BI Desktop → **Home** ribbon → **Get data** → **Text/CSV**.
2. Browse to `data/hospitals_clean.csv` and click **Open**.
3. In the preview window, click **Transform Data** (NOT "Load"). This opens the
   **Power Query Editor**, where we'll set data types.

### 1.2 Set data types on the hospitals query
In Power Query, the query on the left should be named `hospitals_clean`.
Click each column header, then use **Transform → Data type** (or the little
icon on the left of the column name) to set:

| Column | Set type to |
|---|---|
| `facility_id` | **Text** (important — keeps leading zeros like `010001`) |
| `facility_name`, `address`, `city`, `state`, `county`, `telephone` | Text |
| `zip_code` | **Text** (keeps leading zeros) |
| `hospital_type`, `hospital_ownership` | Text |
| `emergency_services`, `birthing_friendly` | Text |
| `overall_rating` | **Whole number** |
| `is_top_rated` | **True/False** |

> The script already converted "Not Available" to blanks, so unrated hospitals
> show as **null** in `overall_rating`. Leave them as null — do NOT replace
> them with 0, or you'll drag down your averages. Power BI's AVERAGE and COUNT
> automatically ignore nulls, which is exactly what we want.

### 1.3 Load the measures file
1. In Power Query, **Home → New Source → Text/CSV**.
2. Choose `data/measures_clean.csv` → **OK**.
3. Set data types on this query (`measures_clean`):

| Column | Set type to |
|---|---|
| `facility_id` | **Text** (must match the hospitals key type exactly) |
| all five `*_measure_count` columns | **Whole number** |

### 1.4 Apply
Click **Home → Close & Apply**. Power BI loads both tables. You'll see
`hospitals_clean` and `measures_clean` in the **Data** pane on the right.

---

## Part 2 — Build the data model (about 10 min)

We have two tables that describe the same hospitals, keyed by `facility_id`.
We'll relate them so the whole report filters together.

1. Click the **Model view** icon (the third icon on the far left toolbar — it
   looks like connected boxes).
2. You should see both tables as boxes. **Drag the `facility_id` field from
   `hospitals_clean` and drop it onto the `facility_id` field in
   `measures_clean`.** This creates a relationship line between them.
3. Double-click the relationship line to open its settings and confirm:
   - **Cardinality:** **One to one (1:1)** — each hospital appears exactly once
     in each table.
   - **Cross-filter direction:** **Both**.
   - **Make this relationship active:** ✔ checked.
4. Click **OK**.

> **Why this matters:** `hospitals_clean` is your main table (the "dimension"
> with names, states, types, rating). `measures_clean` holds extra facts about
> each hospital. The 1:1 relationship on `facility_id` lets a slicer on, say,
> *state* filter BOTH tables at once. This is the simplest possible star-style
> model and great practice.
>
> **Key joins to which:** `hospitals_clean[facility_id]` ⟶
> `measures_clean[facility_id]`, one-to-one.

---

## Part 3 — Create 5 starter DAX measures (about 20 min)

Measures are reusable calculations. Create each one via **Modeling → New
measure** (or right-click `hospitals_clean` in the Data pane → **New measure**),
then paste the DAX and press Enter. Put all five on the `hospitals_clean` table.

> Tip: type the name, then `=`, then paste. The text before `=` is the measure
> name that will show up in your visuals.

### 1) Hospital Count
```DAX
Hospital Count = COUNTROWS ( hospitals_clean )
```
*Counts the total number of hospitals (rows) currently in view. Powers your
headline KPI card and respects whatever slicers are applied.*

### 2) Avg Overall Star Rating
```DAX
Avg Overall Star Rating =
AVERAGE ( hospitals_clean[overall_rating] )
```
*Average of the 1–5 star rating. Nulls (unrated hospitals) are ignored
automatically, so this is the average among **rated** hospitals only.*

### 3) Rated Hospital Count
```DAX
Rated Hospital Count =
CALCULATE (
    COUNTROWS ( hospitals_clean ),
    NOT ISBLANK ( hospitals_clean[overall_rating] )
)
```
*How many hospitals actually have a star rating (the rest are "Not Available").
Useful context next to the average so viewers know the sample size.*

### 4) % Rated 4-5 Stars
```DAX
% Rated 4-5 Stars =
DIVIDE (
    CALCULATE (
        COUNTROWS ( hospitals_clean ),
        hospitals_clean[overall_rating] >= 4
    ),
    [Rated Hospital Count]
)
```
*Share of **rated** hospitals that earned 4 or 5 stars. `DIVIDE` safely returns
blank instead of an error if there are no rated hospitals in view. Format this
measure as a **Percentage** (see tip below).*

### 5) Avg Safety Measures
```DAX
Avg Safety Measures =
AVERAGE ( measures_clean[safety_measure_count] )
```
*Average number of safety-of-care measures CMS evaluated per hospital — pulled
from the second table to prove your relationship works. Swap in any of the other
`*_measure_count` columns to show mortality, readmission, etc.*

> **Formatting a measure:** click the measure in the Data pane, then use the
> **Measure tools** ribbon at the top. For `% Rated 4-5 Stars` set Format to
> **Percentage**, 0–1 decimals. For `Avg Overall Star Rating` set 1 decimal place.

---

## Part 4 — Lay out the single page (about 30 min)

Aim for this layout on one report page (landscape). Placement is a suggestion —
nudge to taste.

```
+----------------------------------------------------------------------+
|  HEALTHCARE QUALITY — U.S. HOSPITALS (CMS)        [ Title text box ] |
+----------------------------------------------------------------------+
|  [ KPI ]      [ KPI ]            [ KPI ]            [ KPI ]           |
|  Hospital     Avg Overall        % Rated           Rated Hospital    |
|  Count        Star Rating        4-5 Stars         Count             |
+----------------------------------------------------------------------+
|                                            |                         |
|   COLUMN CHART                             |   SLICER                |
|   Avg Overall Star Rating by State         |   State                 |
|   (or by Hospital Type)                    |   (list or dropdown)    |
|                                            |                         |
|                                            +-------------------------+
|                                            |   SLICER                |
|                                            |   Hospital Type         |
+--------------------------------------------+-------------------------+
|   COLUMN CHART                                                       |
|   Hospital Count by Hospital Ownership                               |
+----------------------------------------------------------------------+
```

### 4.1 Title (2 min)
- **Insert → Text box**, type `Healthcare Quality — U.S. Hospitals (CMS)`.
- Add a small subtitle: `Source: CMS Hospital General Information (public domain)`.

### 4.2 KPI cards row (8 min)
Add four **Card** visuals across the top. For each: click a blank spot on the
canvas, choose the **Card** visual in the Visualizations pane, then drag one
measure into its **Fields** well:
1. `Hospital Count`
2. `Avg Overall Star Rating`
3. `% Rated 4-5 Stars`
4. `Rated Hospital Count`

> Give each card a clear title via **Format visual → General → Title**.

### 4.3 Column chart #1 — rating by state (8 min)
- Add a **Clustered column chart**.
- **X-axis:** `hospitals_clean[state]`
- **Y-axis:** `Avg Overall Star Rating`
- Sort it: click the **… (More options)** on the visual → **Sort axis** →
  `Avg Overall Star Rating` → Descending. (Optional: use the visual's filter to
  show Top N states so it isn't too crowded.)
- *Alternative:* use `hospitals_clean[hospital_type]` on the X-axis if you'd
  rather compare rating by hospital type — fewer bars, very readable.

### 4.4 Column chart #2 — count by ownership (6 min)
- Add another **Clustered column chart**.
- **X-axis:** `hospitals_clean[hospital_ownership]`
- **Y-axis:** `Hospital Count`
- Sort Descending by `Hospital Count`.

### 4.5 Slicers (6 min)
- Add a **Slicer** → field `hospitals_clean[state]`. In **Format → Slicer
  settings** you can switch it to a **Dropdown** to save space.
- Add a second **Slicer** → field `hospitals_clean[hospital_type]`.
- Click a value and watch every KPI and chart update together — that's your 1:1
  model and cross-filtering at work.

### 4.6 Polish (a few minutes)
- Pick a consistent color theme (**View → Themes**).
- Make sure every visual has a descriptive title.
- **File → Save as** → save the `.pbix` into this project's `images/` folder
  (or the project root) so you can commit it.

---

## Part 5 — Sanity checks (5 min)

With **no slicers selected**, your cards should read approximately:

| Card | Expected value (June 2026 data) |
|---|---|
| Hospital Count | **5,432** |
| Rated Hospital Count | **3,182** |
| Avg Overall Star Rating | **~3.1** |
| % Rated 4-5 Stars | **~42%** (1,334 of 3,182 rated) |

If your numbers are wildly different, the most common cause is **null handling**
— make sure you did NOT replace blank ratings with 0. If they're close, you're
done. Take a screenshot for the README and write up what you see.

---

## What to do next
1. Save your `.pbix` and screenshot the dashboard (see `images/README.md`).
2. Add the screenshot to the project `README.md` — the **Findings** section already summarizes the data; drop your dashboard image in alongside it.
3. Use `TALKING_POINTS.md` to rehearse explaining the project in 2 minutes.
