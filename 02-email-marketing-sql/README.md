# 02 — Email Marketing Analytics with SQL

> Turn a year of synthetic email-campaign data into the answers a marketing
> team actually asks: which campaigns land, which channels bring engaged
> subscribers, and who should we stop emailing to protect deliverability.
> **SQLite + plain SQL.**

**Self-directed portfolio project.** All data is synthetic and labeled as such.

## Problem

Email marketing teams live and die by a handful of recurring questions, and the
answers all sit in the same place - the send and engagement logs:

- **Performance:** which campaigns got opened and clicked, and which flopped?
- **Acquisition quality:** which sources (Webinar, Referral, Paid Social, …)
  bring subscribers who actually engage, versus ones who go cold fast?
- **List health & deliverability:** who hasn't opened anything in 90 / 180 days?
  Mailbox providers punish senders who keep emailing people who never open, so
  finding and "sunsetting" the disengaged protects inbox placement for everyone
  else on the list.
- **Growth:** how fast is the list actually growing?

These are SQL questions. This project answers them with a small, readable query
library against a realistic (but synthetic) email database. The kind of thing an
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

Every address, campaign, and event is randomly generated
with a fixed seed, shaped to behave realistically so there's something genuine to
analyze. Two patterns are intentionally built in: some acquisition sources are
more engaged than others, and long-dormant subscribers form a believable
inactive cohort. The headline rates are never written directly. They **emerge**
from individual 0/1 events when you aggregate. One rule is enforced in the data:
**a click implies an open** (you can't click an email you never opened), so
**CTOR = clicks / opens** is always valid.

## Method

[`queries/`](queries/) holds **14 numbered, commented SQL files**. Every file
opens with a header stating the **business question** it answers and defining any
metric it uses. They stay at a deliberately readable level: `SELECT` / `WHERE` /
`GROUP BY` + aggregates / `HAVING` / `INNER JOIN` / `LEFT JOIN` / subqueries 
with exactly **two** clearly-flagged window-function "stretch" examples.

**Metric definitions used throughout:**

- **Open rate** = opens / emails sent
- **Click rate** = clicks / emails sent
- **CTOR** (click-to-open rate) = clicks / opens - of the people who opened, how
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

*This is my read of the included synthetic dataset. The short memo I'd hand a
marketing manager. Every claim ties to a numbered query above; run
`python build_database.py` then `python run_queries.py` to reproduce all of it.*

**Headline (Q01).** Across all 12 sends, this list runs a **30.9% open rate, 5.8%
click rate, and 18.9% CTOR** on 4,773 sends (1,475 opens, 279 clicks). Those are
the benchmarks I judge everything else against.

**What's working and what isn't (Q02, Q04, Q09).** The clear winner is the
**Webinar Invite Q1** send — it tops every metric at once: 41.1% open, 12.6% click,
and a 30.8% CTOR, and it ranks #1 on the click-rate leaderboard. The clear flop is
the **Re-engagement Nudge** (16.4% open / 1.4% click / 8.5% CTOR), but that one is
weak *by design* — it's the only send aimed at the lapsed segment, so a low open
rate is expected, not alarming. The flop I'd actually act on is the **April
Newsletter**: its open rate is healthy at 32.4% (above the 30.9% average), but its
**CTOR is the worst of any normal campaign at 8.0%** — roughly 162 people opened it
and only 13 clicked. That's not a subject-line problem, it's a **content/offer
problem**: the subject earned the open and then the email failed to convert it. The
lever there is the creative and the call-to-action, not the send time. The same
opens-vs-CTOR split separates the rest of the pack — the newsletters cluster low on
CTOR (March and February both ~12%) while the offer-driven sends (Spring Sale 24.8%,
Referral Program Push 26.6%) convert opens roughly 2–3x better.

**Acquisition quality (Q03, Q06, Q13).** Source matters a lot here. **Webinar and
Referral bring the engaged subscribers**: Webinar leads on opens (38.0%), and
Referral leads on the downstream metrics that pay the bills — 7.24% click rate (the
only source clearly above the 5.85% list average), a 21.8% CTOR, and **65.0% of its
subscribers still active**, the best retention of any channel. The cheap-but-rotting
volume is unmistakably **Paid Social**: despite being a quarter of the list, it
posts the *worst* number on every axis — 22.8% open, 4.4% click, and only **39.6%
still active**, meaning roughly 3 in 5 Paid Social signups have already gone cold.
If this were a live program I'd shift acquisition budget *away* from Paid Social and
*toward* Referral and Webinar, because those two bring people who keep opening
instead of inflating the headcount and then rotting.

**List health and the sunset plan (Q10–Q13).** The hygiene problem is real and
large. **847 subscribers (70.6% of the list) are 90-day sunset candidates** — no
open or click in the last 90 days — and **590 (49.2%) are 180-day candidates**, a
figure that exactly matches the 590 flagged `inactive`, which is a good internal
consistency check. On top of that, **456 subscribers (38.0%) have never opened a
single email** (296 were mailed and never opened, 160 were never mailed at all).
**Paid Social contributes the most dead weight at both cutoffs** — 246 of the 847
at 90 days and 180 of the 590 at 180 days — with Organic second; Referral is the
cleanest (only 64 at 180 days, and just 2 never-mailed). My plan would be the
standard two-stage one the queries are built around: at **90 days** (Q10) run a
re-engagement / win-back send to the early-warning cohort, then at **180 days**
(Q11) **suppress** whoever is still cold after that last attempt. Trimming them
isn't just tidiness — mailbox providers grade senders on recipient engagement, so
continuing to mail hundreds of people who never open **drags down inbox placement
for the entire list**. Cutting the dead weight is how the engaged subscribers who
remain keep landing in the inbox at all.

**Growth (Q07, Q08).** The list grows **steadily but flat** — roughly 85–110 new
signups every month (one bump to 129 in the final month), reaching 1,200 cumulative.
It is not accelerating. That's the worry when I put it next to the sunset cohort:
with ~49% of the list already 180-day-cold and only steady-state gross adds, raw
list size flatters a base that is **quietly rotting underneath**. Growth is keeping
the topline up, but it is not outrunning the disengagement.

**What I'd recommend next quarter.** (1) **Fix the newsletter, not its subject
line** — the April Newsletter pattern (good opens, dead clicks) says the issue is
content/offer, so I'd rework the CTA and creative and measure success as **CTOR
rising toward the ~25% the offer-driven sends already hit**, not as more opens.
(2) **Rebalance acquisition** away from Paid Social toward Referral/Webinar, and
judge each channel on **90-day active rate**, not signup volume — the goal is
subscribers who are still opening at 90 days, not a bigger number. (3) **Stand up
the 90/180-day sunset workflow** (Q10 re-engage → Q11 suppress) as a recurring job
and watch the **list-wide open rate after suppression** — trimming the cold tail
should *raise* it, which is the deliverability win.

*Caveat: this is clearly-labeled synthetic, seeded data, so the **method** is the
point, not the specific percentages. To confirm any of this on a real program I'd
want the signals this DB intentionally doesn't carry — **bounce, unsubscribe, and
spam-complaint data**, plus actual deliverability/inbox-placement metrics — since
those, not opens alone, are what truly justify suppressing an address.*

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
