# 02 — Email Marketing Analytics with SQL

> Turn a year of synthetic email-campaign data into the answers a marketing
> team actually asks: which campaigns land, which channels bring engaged
> subscribers, and who should we stop emailing to protect deliverability.
> **SQLite + plain SQL.**

**Self-directed portfolio project.** All data is synthetic and labeled as such.

## Problem

Email marketing teams live and die by a handful of recurring questions, and the
answers all sit in the same place — the send and engagement logs:

- **Performance:** which campaigns got opened and clicked, and which flopped?
- **Acquisition quality:** which sources (Webinar, Referral, Paid Social, …)
  bring subscribers who actually engage, versus ones who go cold fast?
- **List health & deliverability:** who hasn't opened anything in 90 / 180 days?
  Mailbox providers punish senders who keep emailing people who never open, so
  finding and "sunsetting" the disengaged protects inbox placement for everyone
  else on the list.
- **Growth:** how fast is the list actually growing?

These are SQL questions. This project answers them with a small, readable query
library against a realistic (but synthetic) email database — the kind of thing an
analyst would hand a marketing manager.

## Data

A **synthetic**, seeded SQLite database (`data/email_marketing.db`) covering
**~12 months**, built by [`build_database.py`](build_database.py). Full schema and
the "how the realism works" notes are in [`data/README.md`](data/README.md).
Three tables:

| table | grain | key columns |
|-------|-------|-------------|
| `subscribers` | one row per person | `subscriber_id`, `email` (fake `user0001@example.com`), `signup_date`, `source`, `status` |
| `sends` | one row per campaign send | `send_id`, `campaign_id`, `campaign_name`, `send_date`, `segment` |
| `engagement` | one row per subscriber × send (~4,800 rows) | `send_id`, `subscriber_id`, `opened` (0/1), `clicked` (0/1), `open_datetime`, `click_datetime` |

```
subscribers (1) ───< engagement >─── (1) sends
```

It is **not real** — every address, campaign, and event is randomly generated
with a fixed seed, shaped to behave realistically so there's something genuine to
analyze. Two patterns are intentionally built in: some acquisition sources are
more engaged than others, and long-dormant subscribers form a believable
inactive cohort. The headline rates are never written directly — they **emerge**
from individual 0/1 events when you aggregate. One rule is enforced in the data:
**a click implies an open** (you can't click an email you never opened), so
**CTOR = clicks / opens** is always valid.

## Method

[`queries/`](queries/) holds **14 numbered, commented SQL files**. Every file
opens with a header stating the **business question** it answers and defining any
metric it uses. They stay at a deliberately readable level — `SELECT` / `WHERE` /
`GROUP BY` + aggregates / `HAVING` / `INNER JOIN` / `LEFT JOIN` / subqueries —
with exactly **two** clearly-flagged window-function "stretch" examples.

**Metric definitions used throughout:**

- **Open rate** = opens / emails sent
- **Click rate** = clicks / emails sent
- **CTOR** (click-to-open rate) = clicks / opens — of the people who opened, how
  many clicked; a signal of creative/offer quality, independent of the subject
  line that mostly drives opens
- **Sunset candidate** = a subscriber with no opens **and** no clicks in the last
  N days (90 = early re-engagement; 180 = suppress candidate)

**What the query set covers:**

| # | file | what it answers | techniques |
|---|------|-----------------|------------|
| 01 | `01_overall_engagement_summary.sql` | list-wide open / click / CTOR (the benchmark) | aggregates |
| 02 | `02_engagement_by_campaign.sql` | open / click / CTOR **by campaign** | INNER JOIN, GROUP BY |
| 03 | `03_engagement_by_source.sql` | open / click / CTOR **by source** | INNER JOIN, GROUP BY |
| 04 | `04_ctor_by_campaign_quality.sql` | which campaigns convert opens to clicks best | GROUP BY, HAVING |
| 05 | `05_campaigns_below_average_open_rate.sql` | campaigns under the overall open rate | HAVING + **subquery benchmark** |
| 06 | `06_sources_above_average_click_rate.sql` | sources beating the overall click rate | HAVING + **subquery benchmark** |
| 07 | `07_subscriber_growth_by_month.sql` | new signups per month | GROUP BY on a date |
| 08 | `08_cumulative_subscribers_by_month.sql` | running list size over time | **window function (STRETCH)** |
| 09 | `09_rank_campaigns_by_click_rate.sql` | campaign leaderboard by click rate | **window function (STRETCH)** |
| 10 | `10_sunset_candidates_90_days.sql` | no engagement in 90 days | LEFT JOIN (find the absence) |
| 11 | `11_sunset_candidates_180_days.sql` | no engagement in 180 days, by source | LEFT JOIN (find the absence) |
| 12 | `12_never_opened_subscribers.sql` | who has never opened anything | LEFT JOIN, CASE |
| 13 | `13_list_health_by_source.sql` | active vs. inactive share per source | GROUP BY, CASE pivot |
| 14 | `14_subscriber_engagement_profile.sql` | per-subscriber opens/clicks (incl. never-mailed) | LEFT JOIN keeps NULLs |

The **two window-function files are 08 and 09** — each carries a prominent
`-- STRETCH (window function): ...` comment so they're easy to study deliberately.
Every other file is intentionally free of window functions.

[`run_queries.py`](run_queries.py) executes all 14 files in one command and prints
each file's business question plus a few result rows — so "every query runs
against the seeded DB" is verifiable instantly.

## Findings

>>> CHRISTOPHER: This is the part interviewers care about most — your read of the
> data, in your own words. Run `python build_database.py` then
> `python run_queries.py`, look at the outputs, and write the short memo you'd
> send the marketing team. Prompts to work through (then delete them):
>
> - **Performance:** From queries 02 and 04 — which campaign was the clear
>   winner, and which was the clear flop? Is the flop weak on *opens* (subject
>   line / timing) or on *CTOR* (content / offer)? Name the lever you'd pull.
> - **Acquisition quality:** From queries 03, 06, and 13 — which source brings the
>   most engaged subscribers, and which one looks like cheap-but-rotting volume?
>   Would you shift acquisition budget? Which way?
> - **List health / deliverability:** From queries 10–13 — roughly how much of the
>   list is a sunset candidate at 90 vs. 180 days, and which source contributes
>   the most dead weight? What's your re-engagement-then-suppress plan, and why
>   does trimming the unengaged actually *help* the subscribers who remain?
> - **Growth:** From queries 07–08 — is the list growing steadily, accelerating,
>   or stalling? Does growth offset the churn you see in the sunset cohort?
> - **The recommendation:** In 3–4 sentences, what 2–3 actions would you push the
>   marketing team to take next quarter, and what would you measure to know they
>   worked?
> - **Honesty caveat:** one line noting this is synthetic data, so the *method* is
>   the point — name what you'd want from the real system to confirm it (e.g.
>   bounce/unsubscribe/spam-complaint data this DB doesn't include).

## How to run

```bash
# from this folder (02-email-marketing-sql/)
pip install -r requirements.txt          # numpy only; sqlite3 is stdlib
python build_database.py                 # writes data/email_marketing.db (+ prints a summary)
python run_queries.py                    # runs all 14 queries, prints Q + sample rows
```

Both scripts finish in a second or two. Useful flags:

```bash
python build_database.py --seed 7        # a different (still reproducible) synthetic draw
python run_queries.py --rows 10          # show more result rows per query
```

### Run a single query with the `sqlite3` CLI

If you have the `sqlite3` command-line tool installed:

```bash
sqlite3 data/email_marketing.db                       # open the DB
sqlite> .headers on
sqlite> .mode column
sqlite> .read queries/02_engagement_by_campaign.sql   # run one query file
sqlite> .quit
```

### Running the tests (optional)

```bash
pip install -r requirements-dev.txt
pytest tests -v
```

The test suite builds a throwaway database, checks the synthetic-data invariants
(including "a click implies an open"), and runs **every** query with zero errors.
