"""
build_database.py
=================

Creates a SYNTHETIC email-marketing analytics database (SQLite) for the
Email Marketing SQL project.

    >>> THIS DATA IS NOT REAL. <<<
    Every email address, subscriber, campaign, and engagement event below is
    randomly generated for demonstration only. The numbers do not describe any
    real company, list, campaign, or person. They are shaped to *look* realistic
    so there is something genuine to analyze with SQL.

How the realism works (and why it is honest)
--------------------------------------------
We do NOT write "open rate = 32%" anywhere. Instead we give each campaign and
each acquisition source plausible underlying behaviour -- a base probability
that a given subscriber opens, and (given an open) a probability they click --
and then let the individual 0/1 events be drawn from those probabilities. The
headline metrics (open rate, click rate, CTOR) therefore *emerge* when you
aggregate the rows with SQL. Patterns built in on purpose:

  * Some acquisition sources (e.g. "Webinar", "Referral") attract more engaged
    subscribers than others (e.g. "Paid Social"), so their open rates run higher.
  * Engagement decays for subscribers who joined long ago and were never
    re-activated, which creates a believable INACTIVE / "sunset" cohort -- people
    with no opens or clicks in the last 90 / 180 days.
  * A "clicked" event can only happen on an email that was also "opened"
    (clicked implies opened), so CTOR = clicks / opens always makes sense.

Because the random seed is fixed, the generated database is reproducible:
re-running this script yields the same numbers every time.

What gets built
---------------
A SQLite file at  data/email_marketing.db  with three tables:

  subscribers (subscriber_id, email, signup_date, source, status)
  sends       (send_id, campaign_id, campaign_name, send_date, segment)
  engagement  (engagement_id, send_id, subscriber_id, opened, clicked,
               open_datetime, click_datetime)   -- ~5,000 rows

Usage
-----
    python build_database.py                 # writes data/email_marketing.db
    python build_database.py --seed 7        # different synthetic draw
    python build_database.py -o other.db     # write somewhere else
"""

import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------- #
# Configuration -- the "dials" that shape the synthetic data.
# Change these and re-run to get a different (still reproducible) dataset.
# --------------------------------------------------------------------------- #

SEED = 42                          # fixed -> the generated DB is reproducible

# The list spans ~12 months. "TODAY" is the analysis reference date; the
# inactive-cohort queries (90 / 180 day windows) are measured back from here.
# We pin it instead of using the real clock so the DB stays reproducible.
TODAY = datetime(2026, 6, 1)
LIST_START = TODAY - timedelta(days=365)   # subscribers can sign up from here

N_SUBSCRIBERS = 1200               # size of the email list
# We aim for ~5,000 engagement events. Per-send recipients = this / #sends.
# It is set a little above 5,000 because the earliest sends have a smaller
# eligible pool (few people had signed up yet), so they fall short and pull
# the grand total down toward ~5,000.
TARGET_ENGAGEMENT_ROWS = 6000

# Acquisition sources and how engaged the people from each tend to be.
#   weight    relative share of the list that comes from this source
#   open_mult multiplies a campaign's base open probability for these subs
#             (>1 = more engaged audience, <1 = colder audience)
SOURCE_PARAMS = {
    "Webinar":     {"weight": 0.18, "open_mult": 1.30},
    "Referral":    {"weight": 0.15, "open_mult": 1.20},
    "Organic":     {"weight": 0.27, "open_mult": 1.05},
    "Event":       {"weight": 0.15, "open_mult": 0.95},
    "Paid Social": {"weight": 0.25, "open_mult": 0.70},
}

# Campaigns sent over the year. Each has:
#   base_open  base probability a typical subscriber opens this send
#   base_ctor  probability they click GIVEN they opened (click-to-open rate)
#   segment    which audience the send targeted ("All List", a source, etc.)
# Open rate emerges as base_open x the subscriber's source open_mult x a decay
# factor for dormant subscribers; click rate emerges from there x base_ctor.
CAMPAIGNS = [
    {"name": "January Newsletter",      "base_open": 0.32, "base_ctor": 0.16, "segment": "All List"},
    {"name": "New Year Product Launch", "base_open": 0.38, "base_ctor": 0.22, "segment": "All List"},
    {"name": "February Newsletter",     "base_open": 0.30, "base_ctor": 0.14, "segment": "All List"},
    {"name": "Webinar Invite Q1",       "base_open": 0.41, "base_ctor": 0.27, "segment": "Webinar"},
    {"name": "Spring Sale",             "base_open": 0.35, "base_ctor": 0.24, "segment": "All List"},
    {"name": "March Newsletter",        "base_open": 0.29, "base_ctor": 0.13, "segment": "All List"},
    {"name": "Customer Case Study",     "base_open": 0.33, "base_ctor": 0.19, "segment": "Organic"},
    {"name": "April Newsletter",        "base_open": 0.28, "base_ctor": 0.12, "segment": "All List"},
    {"name": "Product Update May",      "base_open": 0.31, "base_ctor": 0.18, "segment": "All List"},
    {"name": "Re-engagement Nudge",     "base_open": 0.18, "base_ctor": 0.09, "segment": "Lapsed"},
    {"name": "Summer Promo",            "base_open": 0.34, "base_ctor": 0.21, "segment": "All List"},
    {"name": "Referral Program Push",   "base_open": 0.36, "base_ctor": 0.23, "segment": "Referral"},
]

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "data" / "email_marketing.db"


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #

def _build_subscribers(rng):
    """Return a list of subscriber tuples (subscriber_id, email, signup_date,
    source, status) plus a parallel dict of per-subscriber 'engagement profile'
    info the engagement step needs (their source multiplier and signup date)."""
    sources = list(SOURCE_PARAMS.keys())
    weights = np.array([SOURCE_PARAMS[s]["weight"] for s in sources])
    weights = weights / weights.sum()

    rows = []
    profiles = {}
    span_days = (TODAY - LIST_START).days

    for i in range(1, N_SUBSCRIBERS + 1):
        source = sources[rng.choice(len(sources), p=weights)]

        # Signup date: uniformly spread across the year-long window.
        signup = LIST_START + timedelta(days=int(rng.integers(0, span_days)))

        # Each subscriber gets a personal "affinity" wobble so people from the
        # same source are not identical -- keeps aggregates from looking fake.
        affinity = float(np.clip(rng.normal(1.0, 0.25), 0.3, 1.8))

        rows.append((
            i,
            f"user{i:04d}@example.com",          # fake / sanitized address
            signup.strftime("%Y-%m-%d"),
            source,
            "active",                            # provisional; finalized later
        ))
        profiles[i] = {
            "open_mult": SOURCE_PARAMS[source]["open_mult"] * affinity,
            "signup": signup,
        }

    return rows, profiles


def _build_sends(rng):
    """Return a list of send tuples (send_id, campaign_id, campaign_name,
    send_date, segment), one per campaign, spread across the year."""
    rows = []
    n = len(CAMPAIGNS)
    # Space the sends roughly evenly from ~11 months ago up to ~2 weeks ago.
    first = LIST_START + timedelta(days=20)
    last = TODAY - timedelta(days=14)
    total_span = (last - first).days

    for idx, camp in enumerate(CAMPAIGNS, start=1):
        offset = int(round(total_span * (idx - 1) / (n - 1)))
        send_date = first + timedelta(days=offset)
        rows.append((
            idx,                                 # send_id
            100 + idx,                           # campaign_id
            camp["name"],
            send_date.strftime("%Y-%m-%d"),
            camp["segment"],
        ))
    return rows


def _decay_factor(signup_date, send_date):
    """Older, un-touched subscribers engage less. Returns a multiplier in
    roughly [0.25, 1.0]: people who joined long before a send are likelier to
    have gone quiet by the time it goes out. This is what creates the inactive
    'sunset' cohort the queries look for."""
    tenure_days = (send_date - signup_date).days
    if tenure_days <= 0:
        return 0.0                               # not on the list yet
    # Half-life style decay: ~270 days to fall to ~0.5, floored at 0.25.
    factor = 0.5 ** (tenure_days / 270.0)
    return float(np.clip(0.25 + factor, 0.25, 1.0))


def _build_engagement(rng, subscribers, sends):
    """Draw the ~5,000 engagement events.

    For each send we choose a subset of the list as 'recipients' (only people who
    had already signed up before the send goes out), then for each recipient draw
    opened ~ Bernoulli(p_open) and, only if opened, clicked ~ Bernoulli(ctor).
    clicked therefore implies opened by construction.
    """
    n_sends = len(sends)
    # How many recipients per send so the grand total lands near the target.
    per_send = max(1, TARGET_ENGAGEMENT_ROWS // n_sends)

    rows = []
    eng_id = 0

    for send in sends:
        send_id, _campaign_id, _name, send_date_str, segment = send
        send_date = datetime.strptime(send_date_str, "%Y-%m-%d")
        camp = next(c for c in CAMPAIGNS if c["name"] == _name)

        # Only subscribers who joined BEFORE this send can receive it. Building
        # the eligible pool up front (instead of skipping later) keeps the row
        # count close to `per_send` for every send.
        eligible = [s[0] for s in subscribers
                    if SUB_PROFILES[s[0]]["signup"] <= send_date]
        if not eligible:
            continue

        # Pick recipients. "All List" / "Lapsed" sends sample broadly; segmented
        # sends bias toward subscribers whose source matches the segment.
        if segment in SOURCE_PARAMS:
            same = [sid for sid in eligible if subscribers[sid - 1][3] == segment]
            others = [sid for sid in eligible if subscribers[sid - 1][3] != segment]
            # 70% of recipients from the matching source, 30% from the rest.
            n_same = min(len(same), int(per_send * 0.7))
            n_other = min(len(others), per_send - n_same)
            chosen = list(rng.choice(same, size=n_same, replace=False)) + \
                     list(rng.choice(others, size=n_other, replace=False))
        else:
            size = min(len(eligible), per_send)
            chosen = list(rng.choice(eligible, size=size, replace=False))

        for sub_id in chosen:
            prof = SUB_PROFILES[int(sub_id)]
            decay = _decay_factor(prof["signup"], send_date)
            p_open = float(np.clip(camp["base_open"] * prof["open_mult"] * decay, 0.0, 0.95))
            opened = int(rng.random() < p_open)

            clicked = 0
            open_dt = None
            click_dt = None
            if opened:
                # Opened sometime in the 0-72h after the send.
                open_dt = send_date + timedelta(
                    hours=float(rng.uniform(0, 72)))
                clicked = int(rng.random() < camp["base_ctor"])
                if clicked:
                    # Clicked shortly AFTER opening (0-3h later).
                    click_dt = open_dt + timedelta(hours=float(rng.uniform(0, 3)))

            eng_id += 1
            rows.append((
                eng_id,
                int(send_id),
                int(sub_id),
                opened,
                clicked,
                open_dt.strftime("%Y-%m-%d %H:%M:%S") if open_dt else None,
                click_dt.strftime("%Y-%m-%d %H:%M:%S") if click_dt else None,
            ))

    return rows


def _finalize_status(subscribers, engagement):
    """Mark a subscriber 'inactive' if they have NO opens and NO clicks in the
    last 180 days (measured from TODAY). Everyone else stays 'active'. This is a
    convenience flag; the queries also derive cohorts directly from engagement
    so the logic is auditable in SQL, not hidden in Python."""
    cutoff = TODAY - timedelta(days=180)
    recent_active = set()
    for (_eid, _sid, sub_id, opened, clicked, open_dt, _click_dt) in engagement:
        if opened or clicked:
            # Use the open time if present (clicks always have an open).
            when = datetime.strptime(open_dt, "%Y-%m-%d %H:%M:%S")
            if when >= cutoff:
                recent_active.add(sub_id)

    finalized = []
    for (sub_id, email, signup, source, _status) in subscribers:
        status = "active" if sub_id in recent_active else "inactive"
        finalized.append((sub_id, email, signup, source, status))
    return finalized


# Module-level handle so the engagement builder can read subscriber profiles
# without threading them through every call. Populated in build().
SUB_PROFILES = {}


def build(seed: int = SEED):
    """Generate all three tables in memory and return them as lists of tuples:
    (subscribers, sends, engagement)."""
    global SUB_PROFILES
    rng = np.random.default_rng(seed)

    subscribers, SUB_PROFILES = _build_subscribers(rng)
    sends = _build_sends(rng)
    engagement = _build_engagement(rng, subscribers, sends)
    subscribers = _finalize_status(subscribers, engagement)

    return subscribers, sends, engagement


# --------------------------------------------------------------------------- #
# Schema + write
# --------------------------------------------------------------------------- #

SCHEMA = """
DROP TABLE IF EXISTS engagement;
DROP TABLE IF EXISTS sends;
DROP TABLE IF EXISTS subscribers;

CREATE TABLE subscribers (
    subscriber_id  INTEGER PRIMARY KEY,
    email          TEXT    NOT NULL,
    signup_date    TEXT    NOT NULL,   -- 'YYYY-MM-DD'
    source         TEXT    NOT NULL,   -- Webinar / Referral / Organic / Event / Paid Social
    status         TEXT    NOT NULL    -- 'active' or 'inactive'
);

CREATE TABLE sends (
    send_id        INTEGER PRIMARY KEY,
    campaign_id    INTEGER NOT NULL,
    campaign_name  TEXT    NOT NULL,
    send_date      TEXT    NOT NULL,   -- 'YYYY-MM-DD'
    segment        TEXT    NOT NULL    -- audience the send targeted
);

CREATE TABLE engagement (
    engagement_id  INTEGER PRIMARY KEY,
    send_id        INTEGER NOT NULL,
    subscriber_id  INTEGER NOT NULL,
    opened         INTEGER NOT NULL,   -- 0 / 1
    clicked        INTEGER NOT NULL,   -- 0 / 1  (clicked => opened)
    open_datetime  TEXT,               -- 'YYYY-MM-DD HH:MM:SS' or NULL
    click_datetime TEXT,               -- 'YYYY-MM-DD HH:MM:SS' or NULL
    FOREIGN KEY (send_id)       REFERENCES sends(send_id),
    FOREIGN KEY (subscriber_id) REFERENCES subscribers(subscriber_id)
);
"""


def write_db(path: Path, subscribers, sends, engagement) -> None:
    """Create the SQLite file at `path` and load the three tables."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT INTO subscribers VALUES (?, ?, ?, ?, ?)", subscribers)
        conn.executemany(
            "INSERT INTO sends VALUES (?, ?, ?, ?, ?)", sends)
        conn.executemany(
            "INSERT INTO engagement VALUES (?, ?, ?, ?, ?, ?, ?)", engagement)
        conn.commit()
    finally:
        conn.close()


def _print_summary(path, subscribers, sends, engagement) -> None:
    """Print a short, human-readable summary so a run is self-verifying."""
    n_sub = len(subscribers)
    n_send = len(sends)
    n_eng = len(engagement)
    opens = sum(r[3] for r in engagement)
    clicks = sum(r[4] for r in engagement)
    inactive = sum(1 for s in subscribers if s[4] == "inactive")

    open_rate = (opens / n_eng * 100) if n_eng else 0
    click_rate = (clicks / n_eng * 100) if n_eng else 0
    ctor = (clicks / opens * 100) if opens else 0

    print("=" * 60)
    print("  SYNTHETIC email-marketing database built")
    print("=" * 60)
    print(f"  File           : {path}")
    print(f"  Subscribers    : {n_sub:,}  ({inactive:,} inactive, "
          f"{n_sub - inactive:,} active)")
    print(f"  Sends/campaigns: {n_send:,}")
    print(f"  Engagement rows: {n_eng:,}")
    print(f"  Overall opens  : {opens:,}  ({open_rate:.1f}% open rate)")
    print(f"  Overall clicks : {clicks:,}  ({click_rate:.1f}% click rate)")
    print(f"  Overall CTOR   : {ctor:.1f}%  (clicks / opens)")
    print("-" * 60)
    print("  Reminder: this data is SYNTHETIC and describes no real list.")
    print("  Next: python run_queries.py")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the SYNTHETIC email-marketing SQLite database.")
    parser.add_argument(
        "-o", "--output", type=Path, default=DEFAULT_OUTPUT,
        help=f"where to write the .db (default: {DEFAULT_OUTPUT})")
    parser.add_argument(
        "--seed", type=int, default=SEED,
        help=f"random seed for reproducibility (default: {SEED})")
    args = parser.parse_args()

    subscribers, sends, engagement = build(seed=args.seed)
    write_db(args.output, subscribers, sends, engagement)
    _print_summary(args.output, subscribers, sends, engagement)


if __name__ == "__main__":
    main()
