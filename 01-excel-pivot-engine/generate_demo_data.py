"""
generate_demo_data.py
======================

Creates a SYNTHETIC multi-channel marketing-campaign dataset for the Pivot
Automation Engine demo.

    >>> THIS DATA IS NOT REAL. <<<
    It is randomly generated for demonstration only. The numbers do not describe
    any real company, campaign, or person. They are shaped to *look* realistic so
    there is something genuine to analyze.

How the realism works (and why it is honest)
--------------------------------------------
We do NOT write ROAS or conversion rates directly. Instead we give each channel
and segment plausible underlying economics (how much it costs to show an ad, how
often people click, how often clicks convert, how much a conversion is worth) and
then let pandas/Excel compute the headline metrics downstream. Patterns therefore
*emerge* from the math:

  * "Display" is given cheap, low-intent traffic, so its revenue tends to fall
    below its spend (ROAS < 1) -- a believable underperformer.
  * "VIP" customers are given a much higher conversion rate and order value, so
    that segment converts well above the others.

Because real random noise is layered on top, the exact figures shift run-to-run
in spirit -- but the seed is fixed, so the committed CSV is reproducible.

Usage
-----
    python generate_demo_data.py                 # writes data/demo.csv
    python generate_demo_data.py -o other.csv    # writes somewhere else
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Configuration -- the "dials" that shape the synthetic data.
# --------------------------------------------------------------------------- #

SEED = 42                       # fixed -> the generated CSV is reproducible
START_DATE = "2025-01-01"
END_DATE = "2025-06-30"         # six months
ACTIVE_PROBABILITY = 0.55       # chance a given channel x segment runs on a day

CHANNELS = ["Email", "Paid Search", "Social", "Display"]
SEGMENTS = ["New", "Returning", "VIP", "Dormant"]

# Per-channel economics:
#   mean_spend          typical daily spend for one channel x segment line ($)
#   impr_per_dollar     impressions bought per dollar (Display is cheap & broad)
#   ctr                 click-through rate (clicks / impressions)
#   base_cvr            base conversion rate (conversions / clicks) before segment
CHANNEL_PARAMS = {
    "Email":       {"mean_spend": 120, "impr_per_dollar": 80,  "ctr": 0.035, "base_cvr": 0.010},
    "Paid Search": {"mean_spend": 300, "impr_per_dollar": 28,  "ctr": 0.040, "base_cvr": 0.016},
    "Social":      {"mean_spend": 220, "impr_per_dollar": 130, "ctr": 0.010, "base_cvr": 0.008},
    "Display":     {"mean_spend": 180, "impr_per_dollar": 350, "ctr": 0.004, "base_cvr": 0.005},
}

# Per-segment behaviour:
#   cvr_multiplier  multiplies the channel's base conversion rate
#   aov             average order value -- revenue per conversion ($)
SEGMENT_PARAMS = {
    "New":       {"cvr_multiplier": 0.8, "aov": 55},
    "Returning": {"cvr_multiplier": 1.2, "aov": 80},
    "VIP":       {"cvr_multiplier": 2.2, "aov": 150},
    "Dormant":   {"cvr_multiplier": 0.5, "aov": 45},
}

COLUMNS = ["date", "channel", "segment",
           "spend", "impressions", "clicks", "conversions", "revenue"]

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "data" / "demo.csv"


def generate(seed: int = SEED) -> pd.DataFrame:
    """Build the synthetic campaign DataFrame.

    One row = one channel x segment line for one day (when that line was active).
    Returns a DataFrame with the COLUMNS above.
    """
    rng = np.random.default_rng(seed)
    days = pd.date_range(START_DATE, END_DATE, freq="D")
    rows = []

    # Loop in a fixed order (days, then channels, then segments) so the sequence
    # of random draws is identical on every run -> reproducible output.
    for day in days:
        for channel in CHANNELS:
            cp = CHANNEL_PARAMS[channel]
            for segment in SEGMENTS:
                sp = SEGMENT_PARAMS[segment]

                # Did this channel x segment line run today? (always draw, so the
                # random stream stays in lock-step run-to-run)
                if rng.random() >= ACTIVE_PROBABILITY:
                    continue

                # Spend: typical value with multiplicative noise (always positive).
                spend = round(cp["mean_spend"] * rng.lognormal(mean=0.0, sigma=0.30), 2)

                # Funnel: spend -> impressions -> clicks -> conversions -> revenue.
                impressions = int(rng.poisson(spend * cp["impr_per_dollar"]))
                clicks = int(rng.binomial(impressions, cp["ctr"]))

                conv_rate = min(cp["base_cvr"] * sp["cvr_multiplier"], 0.95)
                conversions = int(rng.binomial(clicks, conv_rate))

                revenue = round(conversions * sp["aov"] * rng.lognormal(0.0, 0.20), 2)

                rows.append([
                    day.strftime("%Y-%m-%d"), channel, segment,
                    spend, impressions, clicks, conversions, revenue,
                ])

    return pd.DataFrame(rows, columns=COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic campaign demo data.")
    parser.add_argument(
        "-o", "--output", type=Path, default=DEFAULT_OUTPUT,
        help=f"where to write the CSV (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--seed", type=int, default=SEED,
        help=f"random seed for reproducibility (default: {SEED})",
    )
    args = parser.parse_args()

    df = generate(seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Wrote {len(df):,} rows of SYNTHETIC campaign data to {args.output}")


if __name__ == "__main__":
    main()
