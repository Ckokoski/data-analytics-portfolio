-- =====================================================================
-- 04 — Click-to-open rate (CTOR) by campaign: creative & offer quality
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   Of the people who DID open, which campaigns persuaded the most of them
--   to click? CTOR isolates the strength of the email's content and offer
--   from the strength of the subject line (which mostly drives opens).
--
-- A campaign can have a great open rate but a weak CTOR (good subject line,
-- disappointing content) or vice-versa. Ranking by CTOR surfaces the
-- creative/offer winners.
--
-- METRIC:
--   CTOR = clicks / opens   (only counts subscribers who opened)
--
-- TECHNIQUE: INNER JOIN + GROUP BY, then a HAVING filter so we don't rank
-- campaigns on too few opens (a tiny send can post a misleadingly high or
-- low CTOR). HAVING filters AFTER aggregation; WHERE could not do this
-- because SUM(opened) does not exist until the rows are grouped.
-- =====================================================================

SELECT
    s.campaign_name,
    SUM(e.opened)                                              AS opens,
    SUM(e.clicked)                                             AS clicks,
    ROUND(100.0 * SUM(e.clicked) / SUM(e.opened), 1)          AS ctor_pct
FROM engagement e
INNER JOIN sends s
    ON e.send_id = s.send_id
GROUP BY s.campaign_name
-- Only keep campaigns with a meaningful number of opens to rank on.
HAVING SUM(e.opened) >= 30
ORDER BY ctor_pct DESC;
