"""Unit tests for the pure metric functions.

These use a tiny 3-row frame whose answers can be checked by hand, so a failing
test points at a real arithmetic bug rather than at noisy demo data.
"""
import pandas as pd
import pytest

from pivot_engine import (
    compute_kpis,
    channel_summary,
    segment_summary,
    monthly_trend,
    top_bottom_performers,
)


@pytest.fixture
def tiny():
    """3 rows with hand-computable totals.

    Email:   spend 200, revenue 600  -> ROAS 3.0
    Display: spend 100, revenue 50   -> ROAS 0.5  (underperformer)
    VIP:     20 conv / 200 clicks    -> 10% ; New: 1 / 100 -> 1%
    """
    return pd.DataFrame({
        "date": ["2025-01-01", "2025-01-01", "2025-02-01"],
        "channel": ["Email", "Display", "Email"],
        "segment": ["VIP", "New", "VIP"],
        "spend": [100, 100, 100],
        "impressions": [1000, 1000, 1000],
        "clicks": [100, 100, 100],
        "conversions": [10, 1, 10],
        "revenue": [300, 50, 300],
    })


def test_kpis_totals_and_rates(tiny):
    k = compute_kpis(tiny)
    assert k["total_spend"] == 300
    assert k["total_revenue"] == 650
    assert k["overall_roas"] == pytest.approx(650 / 300)
    assert k["conversion_rate"] == pytest.approx(21 / 300)   # conversions / clicks
    assert k["overall_ctr"] == pytest.approx(300 / 3000)     # clicks / impressions
    assert k["best_channel_by_roas"] == "Email"
    assert k["worst_channel_by_roas"] == "Display"


def test_channel_summary_roas(tiny):
    cs = channel_summary(tiny).set_index("channel")
    assert cs.loc["Email", "roas"] == pytest.approx(600 / 200)
    assert cs.loc["Display", "roas"] == pytest.approx(50 / 100)  # < 1


def test_segment_summary_conversion_rate(tiny):
    ss = segment_summary(tiny).set_index("segment")
    assert ss.loc["VIP", "conversion_rate"] == pytest.approx(0.10)
    assert ss.loc["New", "conversion_rate"] == pytest.approx(0.01)


def test_monthly_trend_one_row_per_month(tiny):
    mt = monthly_trend(tiny)
    assert len(mt) == 2                       # Jan + Feb 2025
    assert list(mt["month"]) == ["2025-01", "2025-02"]


def test_top_bottom_performers_ordering(tiny):
    top, bottom = top_bottom_performers(tiny, n=1)
    assert top.iloc[0]["roas"] >= bottom.iloc[0]["roas"]
    assert top.iloc[0]["channel"] == "Email" and top.iloc[0]["segment"] == "VIP"
