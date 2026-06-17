# Talking Points — Healthcare Quality Dashboard

Use this to explain the project in an interview or portfolio walkthrough. The data prep and dashboard design are done; once you build the `.pbix` from the guide, switch the Power BI lines to first person and add a screenshot.

---

## 2-Minute Pitch (STAR)

**Situation.**
CMS publishes an overall 1–5 star quality rating for every Medicare-registered
hospital in the U.S. — over 5,400 of them — but it ships as one wide, messy
38-column CSV that's hard to read and full of "Not Available" placeholders.
There was no quick way to see how hospital quality varies across states,
ownership types, and facility types.

**Task.**
Turn that raw public dataset into a clean, trustworthy data model and a
single-page interactive dashboard that answers "who's highly rated, and where?"
at a glance.

**Action.**
- I wrote a small **Python (pandas)** script that downloads the dataset straight
  from data.cms.gov, converts "Not Available"/blanks into real nulls, renames
  the cryptic columns to clear names, fixes data types (keeping hospital IDs and
  ZIP codes as text so leading zeros survive), and splits the data into **two
  tidy tables** — hospital facts and quality-measure counts — sharing a
  `facility_id` key.
- On the **Power BI** side, the build guide stands up a **2-table model** joined
  one-to-one on that key, **5 DAX measures** (hospital count, average star rating,
  count of rated hospitals, % rated 4–5 stars, and average safety measures), and a
  single page with **KPI cards, two column-chart breakdowns, and slicers** for
  state and hospital type so everything cross-filters together.

**Result.**
A clean, reproducible pipeline — anyone can re-run the prep script from a fresh
clone with just pandas — plus a build guide that stands the data up as a
single-page Power BI dashboard. The data already answers the headline question:
across the **3,182 rated hospitals** the average is **3.21 stars**, only **42% of
them (25% of all hospitals) earn 4–5 stars**, and a notable **41% of hospitals are
unrated** — so coverage is as much the story as quality. Utah, Colorado, and
Wisconsin top the state rankings; Mississippi and Alabama sit at the bottom.

---

## Likely follow-up questions

**Q1. How did you handle missing data — the "Not Available" ratings?**
The raw file uses the literal text "Not Available" for hospitals CMS can't rate
(not enough underlying measures). My script converts those to true nulls so they
don't get counted as zeros. In Power BI, AVERAGE and my rating measures ignore
nulls automatically, so the "average star rating" reflects only **rated**
hospitals — and I added a separate "Rated Hospital Count" card so the audience
always sees the sample size behind the average.
Concretely: **3,182 of 5,432 hospitals are rated (59%)** in the June 2026 data, so 2,250 (41%) are excluded from any rating average — which is why I surface the rated count as its own KPI card.

**Q2. Why two tables and a relationship instead of one flat table?**
It's a simple, realistic star-style model: the hospitals table is the dimension
(names, location, type, rating) and the measures table holds extra per-hospital
facts. Joining them 1:1 on `facility_id` lets a single slicer filter both at
once, and it's good practice for the kind of modeling you do on bigger projects.
I kept it to two tables on purpose so the model stays readable.

**Q3. What would you add or change with more time?**
With more time I'd bring in a second CMS dataset — HCAHPS patient-survey scores or 30-day readmission rates — for a three-table model; add a **map visual** of average rating by state (the geographic spread is striking); add drill-through to a per-hospital detail page; and schedule a refresh so the dashboard tracks CMS updates instead of being a one-time snapshot.
