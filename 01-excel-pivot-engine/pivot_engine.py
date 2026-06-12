"""
pivot_engine.py
===============

Turn a raw multi-channel marketing-campaign CSV into a formatted, multi-sheet
Excel workbook of the summaries a marketing team actually asks for.

This file is organized in three readable layers:

  1. METRIC FUNCTIONS  -- pure pandas: take a DataFrame, return a summary.
                          No file reading, no Excel. Easy to read and to test.
  2. WORKBOOK WRITER   -- takes those summaries and formats them with openpyxl.
  3. COMMAND LINE      -- glues 1 and 2 together: read CSV -> compute -> write.

Usage:
    python pivot_engine.py demo.csv
    python pivot_engine.py demo.csv -o my_report.xlsx
"""

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Metric definitions -- ONE place, reused in the workbook so a reviewer always
# sees exactly how each number was calculated.
# --------------------------------------------------------------------------- #
METRIC_DEFINITIONS = {
    "ROAS": "Return on ad spend = revenue / spend",
    "CTR": "Click-through rate = clicks / impressions",
    "Conversion rate": "conversions / clicks",
    "CPA": "Cost per acquisition = spend / conversions",
    "Revenue per conversion": "revenue / conversions",
}


# --------------------------------------------------------------------------- #
# Layer 1: metric functions (pure -- no I/O)
# --------------------------------------------------------------------------- #
def _safe_div(numerator, denominator):
    """Divide, but return NaN instead of infinity when dividing by zero.

    Works for single numbers and for whole pandas columns (Series). This keeps
    an empty channel/segment from blowing up the report with 'inf'.
    """
    if isinstance(numerator, pd.Series) or isinstance(denominator, pd.Series):
        with np.errstate(divide="ignore", invalid="ignore"):
            result = numerator / denominator
        return result.replace([np.inf, -np.inf], np.nan)
    if denominator == 0:
        return float("nan")
    return numerator / denominator


def channel_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Spend, revenue, ROAS, conversions and CPA grouped by channel.

    Sorted best-to-worst by ROAS so the top of the table is the winner.
    """
    g = df.groupby("channel", as_index=False).agg(
        spend=("spend", "sum"),
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        conversions=("conversions", "sum"),
        revenue=("revenue", "sum"),
    )
    g["roas"] = _safe_div(g["revenue"], g["spend"])
    g["cpa"] = _safe_div(g["spend"], g["conversions"])
    g["conversion_rate"] = _safe_div(g["conversions"], g["clicks"])
    return g.sort_values("roas", ascending=False, ignore_index=True)


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Clicks, conversions, conversion rate and revenue grouped by segment.

    Sorted best-to-worst by conversion rate.
    """
    g = df.groupby("segment", as_index=False).agg(
        clicks=("clicks", "sum"),
        conversions=("conversions", "sum"),
        revenue=("revenue", "sum"),
        spend=("spend", "sum"),
    )
    g["conversion_rate"] = _safe_div(g["conversions"], g["clicks"])
    g["revenue_per_conversion"] = _safe_div(g["revenue"], g["conversions"])
    g["roas"] = _safe_div(g["revenue"], g["spend"])
    return g.sort_values("conversion_rate", ascending=False, ignore_index=True)


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Month-by-month spend, revenue, ROAS and the month-over-month change.

    `mom_revenue_change` is the fractional change in revenue vs the prior month
    (e.g. 0.10 = up 10%). The first month is NaN because it has no prior month.
    """
    d = df.copy()
    d["month"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m")
    g = d.groupby("month", as_index=False).agg(
        spend=("spend", "sum"),
        revenue=("revenue", "sum"),
        clicks=("clicks", "sum"),
        conversions=("conversions", "sum"),
    )
    g = g.sort_values("month", ignore_index=True)
    g["roas"] = _safe_div(g["revenue"], g["spend"])
    g["mom_revenue_change"] = g["revenue"].pct_change()
    return g


def top_bottom_performers(df: pd.DataFrame, n: int = 5):
    """Rank every channel x segment combination by ROAS.

    Returns a (top_n, bottom_n) tuple of DataFrames -- the best and worst
    performing combinations, each sorted from highest ROAS to lowest within
    its group.
    """
    g = df.groupby(["channel", "segment"], as_index=False).agg(
        spend=("spend", "sum"),
        clicks=("clicks", "sum"),
        conversions=("conversions", "sum"),
        revenue=("revenue", "sum"),
    )
    g["roas"] = _safe_div(g["revenue"], g["spend"])
    g = g.sort_values(["roas", "revenue"], ascending=False, ignore_index=True)
    top = g.head(n).reset_index(drop=True)
    bottom = (
        g.tail(n)
        .sort_values(["roas", "revenue"], ascending=False, ignore_index=True)
    )
    return top, bottom


def compute_kpis(df: pd.DataFrame) -> dict:
    """One-page headline numbers for the whole dataset."""
    total_spend = df["spend"].sum()
    total_revenue = df["revenue"].sum()
    total_impressions = df["impressions"].sum()
    total_clicks = df["clicks"].sum()
    total_conversions = df["conversions"].sum()

    channels = channel_summary(df)
    segments = segment_summary(df)

    return {
        "total_spend": total_spend,
        "total_revenue": total_revenue,
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "overall_roas": _safe_div(total_revenue, total_spend),
        "overall_ctr": _safe_div(total_clicks, total_impressions),
        "conversion_rate": _safe_div(total_conversions, total_clicks),
        "cpa": _safe_div(total_spend, total_conversions),
        "revenue_per_conversion": _safe_div(total_revenue, total_conversions),
        "best_channel_by_roas": channels.loc[channels["roas"].idxmax(), "channel"],
        "worst_channel_by_roas": channels.loc[channels["roas"].idxmin(), "channel"],
        "best_segment_by_conversion": segments.loc[
            segments["conversion_rate"].idxmax(), "segment"
        ],
    }
