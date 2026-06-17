# Talking Points — Healthcare Quality Dashboard

Use this to explain the project in an interview or portfolio walkthrough.
The tool/process parts are filled in; the parts that depend on what your
finished dashboard reveals are marked `>>> CHRISTOPHER` for you to complete
after you build the `.pbix`.

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
- In **Power BI**, I built a **2-table model** joined one-to-one on that key,
  wrote **5 DAX measures** (hospital count, average star rating, count of rated
  hospitals, % rated 4–5 stars, and average safety measures), and designed a
  single page with **KPI cards, two column-chart breakdowns, and slicers** for
  state and hospital type so everything cross-filters together.

**Result.**
A clean, reproducible pipeline (anyone can re-run the script from a fresh clone
with just pandas) feeding a dashboard that compares hospital quality across the
country in seconds.
>>> CHRISTOPHER: Add 1–2 sentences with the headline numbers your dashboard
shows — e.g. "Across ~3,200 rated hospitals the average rating is about X, with
roughly 42% earning 4–5 stars, and [state/type] standing out as highest."

---

## Likely follow-up questions

**Q1. How did you handle missing data — the "Not Available" ratings?**
The raw file uses the literal text "Not Available" for hospitals CMS can't rate
(not enough underlying measures). My script converts those to true nulls so they
don't get counted as zeros. In Power BI, AVERAGE and my rating measures ignore
nulls automatically, so the "average star rating" reflects only **rated**
hospitals — and I added a separate "Rated Hospital Count" card so the audience
always sees the sample size behind the average.
>>> CHRISTOPHER: Add the actual rated-vs-unrated split from your dashboard
(roughly 3,182 rated out of 5,432 total in the June 2026 data).

**Q2. Why two tables and a relationship instead of one flat table?**
It's a simple, realistic star-style model: the hospitals table is the dimension
(names, location, type, rating) and the measures table holds extra per-hospital
facts. Joining them 1:1 on `facility_id` lets a single slicer filter both at
once, and it's good practice for the kind of modeling you do on bigger projects.
I kept it to two tables on purpose so the model stays readable.

**Q3. What would you add or change with more time?**
>>> CHRISTOPHER: Answer in your own words. Good directions: bring in a second
CMS dataset (e.g. HCAHPS patient-survey scores or readmission rates) for a
3-table model; add a map visual of average rating by state; add drill-through to
a hospital detail page; or schedule a refresh so the dashboard tracks CMS
updates over time.
