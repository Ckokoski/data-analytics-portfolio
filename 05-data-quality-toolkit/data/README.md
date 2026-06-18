# Demo data — SYNTHETIC and DELIBERATELY MESSY

> **This data is not real.** Every name, email, and value here is invented for
> demonstration only. It describes no real person, customer, or company. The
> files are intentionally broken so the audit tool has genuine problems to find.

Both files are produced by [`../generate_demo_data.py`](../generate_demo_data.py)
with a fixed random seed, so they are fully reproducible — re-running the
generator yields identical files every time.

---

## `messy_customers.csv` — built to earn a **FAIL**

A small fake customer list. Columns: `customer_id`, `name`, `email`, `phone`,
`city`, `signup_date`.

**Problems baked in on purpose:**

| Problem | What it looks like | Why it matters |
|---|---|---|
| Nearly-empty column | `phone` is blank on ~83% of rows | A field someone added but never backfilled — useless for analysis as-is. This crosses the audit's 50% "serious" line. |
| Duplicate full rows | 4 rows are exact copies of earlier rows (~17%) | As if the file was appended to itself; every total would be double-counted. Crosses the 10% "serious" line. |
| Missing values | Some `email`, `city`, `signup_date` cells blank; a couple use the text `"N/A"` | Real exports use blanks *and* fake-blank text like `N/A`; the audit treats both as missing. |
| Duplicate keys | `customer_id` values `C001`, `C003`, `C005` each appear twice | A unique ID that isn't actually unique silently breaks any join or per-customer rollup. Caught with `--key customer_id`. |

**Audit result:** `FAIL` — driven by the half-empty `phone` column and the
duplicate-row share, with the missing values and duplicate keys listed as
supporting issues.

---

## `messy_orders.csv` — built to earn a **REVIEW**

A small fake order list. Columns: `order_id`, `customer_id`, `price`,
`quantity`, `discount_pct`.

**Problems baked in on purpose:**

| Problem | What it looks like | Why it matters |
|---|---|---|
| Bad types | `price` holds the words `"free"` and `"TBD"`; `quantity` holds `"two"` | Text hiding in a numeric column silently breaks every sum, average, and chart. |
| Out-of-range values | a negative `quantity` (`-2`), a `price` of `0`, a `discount_pct` of `150`, and a `price` typo of `999999.99` | Impossible values that pass unnoticed unless something checks the ranges. Caught with `--rules ../rules_example.json`. |
| Currency formatting (NOT an error) | a couple of prices written as `"$19.99"` and `"1,250.00"` | Included on purpose to show the audit correctly recognises these as numbers, not mistakes. |

**Audit result:** `REVIEW` — the type and range issues are real and listed, but
none individually crosses the "serious" line, so the file is usable once a human
addresses the flagged points.

---

## Regenerate

```bash
python ../generate_demo_data.py     # rewrites both CSVs into this folder
```
