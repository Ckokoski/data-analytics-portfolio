# Demo data — SYNTHETIC

> **This data is not real.** It is randomly generated for demonstration only and describes no real company, campaign, or person.

`demo.csv` is produced by [`../generate_demo_data.py`](../generate_demo_data.py) with a fixed random seed, so it is fully reproducible — re-running the generator yields a byte-identical file.

## Shape

- ~1,600 rows — one row per channel × segment for each day that line was "active"
- 6 months: `2025-01-01` → `2025-06-30`
- 4 channels: Email, Paid Search, Social, Display
- 4 segments: New, Returning, VIP, Dormant

## Columns

| column | type | meaning |
|--------|------|---------|
| `date` | `YYYY-MM-DD` | campaign day |
| `channel` | text | marketing channel |
| `segment` | text | customer segment |
| `spend` | number | ad spend in dollars |
| `impressions` | integer | times an ad was shown |
| `clicks` | integer | clicks received |
| `conversions` | integer | completed conversions |
| `revenue` | number | revenue in dollars |

## How the realism works (and why it's honest)

The generator does **not** write ROAS or conversion rates directly. It gives each channel and segment plausible underlying economics — cost per impression, click rate, conversion rate, order value — and lets the headline metrics *emerge* from the funnel math. Real random noise is layered on top.

Two patterns were intentionally built in so there's something to find in the analysis:

- one channel is given cheap, low-intent traffic (so it tends toward ROAS < 1)
- one segment is given a much higher conversion rate and order value

The exact figures are whatever the seeded math produces — see [`../generate_demo_data.py`](../generate_demo_data.py) for the dials. Nothing here is presented as a real-world result.

## Regenerate

```bash
python ../generate_demo_data.py              # writes ./demo.csv
python ../generate_demo_data.py -o other.csv --seed 7
```
