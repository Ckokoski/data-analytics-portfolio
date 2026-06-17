# Data — YouTube Channel Analytics

## What's committed here (and what isn't)

- **`sample_synthetic.csv`** — a tiny **synthetic** sample (12 fabricated videos) so the pipeline runs out of the box. The raw-looking columns (impressions, views, subscribers_gained) are **made up** for demonstration.
- **`data/private/`** — where your **real** YouTube Studio exports go. This folder is **git-ignored** and never committed.
- **`youtube.db`** — the SQLite database built by the import script; also git-ignored (it rebuilds from the CSV any time).

## Privacy rule (repo-wide)

**Public = rates and percentages** (CTR %, % change, indexes). **Private = raw counts** (views, impressions, subscribers). Every committed query and chart shows rates only. Your absolute numbers live in your local private one-pager (see the repo root `PRIVATE_interview_onepager_TEMPLATE.md`) and are shown in interviews only.

## How to export from YouTube Studio

1. YouTube Studio → **Analytics** → **Advanced mode** (top-right).
2. **Content** tab → set the date range to cover your before/after window.
3. Include these columns: Video title, Video publish time, Impressions, Impressions click-through rate (%), Views, Average percentage viewed (%), Subscribers.
4. **Export → Comma-separated values (.csv)**.
5. Save it into `data/private/` (create the folder — it's git-ignored).
6. Make the headers match the table below (rename columns, or adjust the column map in `import_to_sqlite.py`).

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

`--change-date` is the day your before/after split begins. `>>> CHRISTOPHER:` set this to your actual change date.
