# Email-marketing data — SYNTHETIC

> **This data is not real.** Every email address, subscriber, campaign, and
> engagement event is randomly generated for demonstration only. It describes no
> real company, list, campaign, or person. Email addresses are all of the form
> `user0001@example.com` — `example.com` is the reserved, non-deliverable domain
> from RFC 2606, so none of these addresses can reach anyone.

`email_marketing.db` is a SQLite database produced by
[`../build_database.py`](../build_database.py) with a fixed random seed, so it is
fully reproducible — re-running the generator yields the same numbers every time.

## Shape

- **~12 months** of activity. The analysis reference date ("today") is pinned to
  `2026-06-01` so the inactive-cohort queries (last 90 / 180 days) are
  reproducible instead of drifting with the real clock.
- **1,200 subscribers** across 5 acquisition sources.
- **12 campaigns / sends** spread across the year.
- **~4,800 engagement rows** (one row per subscriber per send they received).

## Tables

### `subscribers`

One row per person on the list.

| column          | type | meaning |
|-----------------|------|---------|
| `subscriber_id` | INTEGER (PK) | unique subscriber id |
| `email`         | TEXT | fake/sanitized address, e.g. `user0042@example.com` |
| `signup_date`   | TEXT `YYYY-MM-DD` | when they joined the list |
| `source`        | TEXT | how they were acquired: `Webinar`, `Referral`, `Organic`, `Event`, `Paid Social` |
| `status`        | TEXT | `active` or `inactive` (see below) |

`status` is set to `inactive` when a subscriber has **no opens and no clicks in
the last 180 days** (measured from the reference date), otherwise `active`. This
is a convenience flag — the queries also re-derive the inactive cohorts directly
from `engagement` so the logic is auditable in SQL, not hidden in Python.

### `sends`

One row per campaign send.

| column          | type | meaning |
|-----------------|------|---------|
| `send_id`       | INTEGER (PK) | unique send id |
| `campaign_id`   | INTEGER | campaign identifier |
| `campaign_name` | TEXT | human-readable name, e.g. `Spring Sale` |
| `send_date`     | TEXT `YYYY-MM-DD` | the day the campaign went out |
| `segment`       | TEXT | audience the send targeted (`All List`, a source name, or `Lapsed`) |

### `engagement`

One row per subscriber per send they received — the fact table.

| column           | type | meaning |
|------------------|------|---------|
| `engagement_id`  | INTEGER (PK) | unique row id |
| `send_id`        | INTEGER (FK → `sends`) | which send this is about |
| `subscriber_id`  | INTEGER (FK → `subscribers`) | which subscriber |
| `opened`         | INTEGER | `1` if they opened, else `0` |
| `clicked`        | INTEGER | `1` if they clicked, else `0` |
| `open_datetime`  | TEXT `YYYY-MM-DD HH:MM:SS` or NULL | when they opened (NULL if never opened) |
| `click_datetime` | TEXT `YYYY-MM-DD HH:MM:SS` or NULL | when they clicked (NULL if never clicked) |

**Key rule baked into the data: `clicked = 1` implies `opened = 1`.** You cannot
click an email you never opened, so every clicked row also has `opened = 1` and a
non-null `open_datetime`. This is why **CTOR = clicks / opens** is always a valid
ratio.

## Entity relationships

```
subscribers (1) ───< engagement >─── (1) sends
   subscriber_id        send_id
```

`engagement` is the bridge: each row links one subscriber to one send and records
whether that subscriber opened and/or clicked.

## How the realism works (and why it's honest)

The generator does **not** write "open rate = 32%" anywhere. Instead it gives
each campaign and each acquisition source plausible underlying behaviour — a base
probability that a subscriber opens, and (given an open) a probability they click
— and then draws each individual `opened` / `clicked` event from those
probabilities. The headline metrics **emerge** only when you aggregate with SQL.

Patterns intentionally built in so there's something to find:

- **Source quality varies.** People acquired via `Webinar` and `Referral` are
  more engaged (higher open rates) than people from `Paid Social`.
- **Engagement decays.** Subscribers who joined long ago and were never
  re-activated open less and less, which produces a believable **inactive /
  "sunset" cohort** — people with no opens or clicks in the last 90 / 180 days.
- **A deliberately weak send.** The `Re-engagement Nudge` campaign targets lapsed
  subscribers and (realistically) underperforms, so there's a clear low outlier.

The exact figures are whatever the seeded math produces — see
[`../build_database.py`](../build_database.py) for the dials. Nothing here is
presented as a real-world result.

## Regenerate

```bash
python ../build_database.py                 # writes ./email_marketing.db
python ../build_database.py --seed 7        # a different synthetic draw
python ../build_database.py -o other.db     # write somewhere else
```

## Poke at it directly (sqlite3 CLI)

If you have the `sqlite3` command-line tool:

```bash
sqlite3 email_marketing.db
sqlite> .tables
sqlite> .schema subscribers
sqlite> SELECT COUNT(*) FROM engagement;
sqlite> .read ../queries/01_overall_engagement_summary.sql
sqlite> .quit
```
