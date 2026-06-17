-- =====================================================================
-- 01 — Overall engagement summary (the list-wide benchmark)
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   Across every campaign we sent this year, how is the list performing
--   overall? What is our open rate, click rate, and CTOR?
--
-- These three list-wide numbers are the BENCHMARK the later queries
-- compare individual campaigns and sources against.
--
-- METRIC DEFINITIONS (used throughout this project):
--   open rate  = opens  / emails sent   (sent = one engagement row)
--   click rate = clicks / emails sent
--   CTOR       = clicks / opens         (click-to-open rate: of the people
--                who opened, how many clicked — a creative/offer quality signal)
--
-- DATA NOTE: every row in `engagement` is one email sent to one subscriber,
-- so COUNT(*) = emails sent. SYNTHETIC data — see data/README.md.
-- =====================================================================

SELECT
    COUNT(*)                               AS emails_sent,
    SUM(opened)                            AS total_opens,
    SUM(clicked)                           AS total_clicks,
    -- 100.0 (not 100) forces floating-point division so we get a real
    -- percentage instead of integer-truncated 0.
    ROUND(100.0 * SUM(opened)  / COUNT(*), 1)  AS open_rate_pct,
    ROUND(100.0 * SUM(clicked) / COUNT(*), 1)  AS click_rate_pct,
    -- Guard the CTOR denominator: if nobody opened, SUM(opened) is 0 and we
    -- would divide by zero, so fall back to NULL in that (here impossible) case.
    ROUND(100.0 * SUM(clicked) / NULLIF(SUM(opened), 0), 1) AS ctor_pct
FROM engagement;
