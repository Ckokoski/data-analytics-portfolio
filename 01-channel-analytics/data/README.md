# Data — Content Channel Analytics

## What's committed here (and what isn't)

- **`sample_synthetic.csv`** — a tiny **synthetic** sample (12 fabricated videos) so the pipeline runs out of the box. The raw-looking columns (impressions, views, subscribers_gained) are **made up** for demonstration.
- **`data/private/`** — where your **real** channel-analytics exports go. This folder is **git-ignored** and never committed.
- The **SQLite database** built by the import script is also git-ignored (it rebuilds from the CSV any time).

## Privacy rule (repo-wide)

**Public = rates and percentages** (CTR %, % change, indexes). **Private = raw counts** (views, impressions, subscribers). Every committed query and chart shows rates only; raw counts stay in `data/private/` (git-ignored) and never enter the repo.

## How to export your data

These steps assume a YouTube channel (the export format the pipeline expects):

1. **Analytics → Advanced mode**, **Content** tab.
2. Set the date range to cover your before/after window.
3. Include: Video title, Video publish time, Impressions, Impressions click-through rate (%), Views, Average percentage viewed (%), Subscribers.
4. **Export → Comma-separated values (.csv)** into `data/private/` (it's git-ignored).
5. Match the headers to the table below (or adjust the column map in `import_to_sqlite.py`).

## Expected columns (what the import script reads)

| column | meaning |
|--------|---------|
| `video_title` | the video's title |
| `publish_date` | publish date (any parseable format) |
| `impressions` | times the thumbnail was shown (raw — stays local) |
| `ctr_percent` | impressions click-through rate (%) |
| `views` | views (raw — stays local) |
| `avg_percent_viewed` | average percentage of the video watched (%) |
| `subscribers_gained` | subscribers gained (raw — stays local) |

## Build the database

```bash
python import_to_sqlite.py                                              # synthetic sample
python import_to_sqlite.py data/private/your_export.csv --change-date 2025-10-01
```

`--change-date` sets the day the before/after split begins (e.g. the day the new thumbnails/titles went live).
