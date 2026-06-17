-- =====================================================================
-- 06 — Acquisition sources ABOVE the overall average click rate
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   Which acquisition channels punch above their weight on CLICKS — i.e.
--   their click rate beats the list-wide average? Those are the channels
--   worth investing more acquisition budget in.
--
-- METRIC:
--   click rate = clicks / emails sent
--   benchmark  = overall list-wide click rate (subquery, one value)
--
-- TECHNIQUE: same pattern as query 05 but for SOURCES and CLICK rate, and
-- this time keeping the groups ABOVE the benchmark. The benchmark is again
-- a SUBQUERY in the HAVING clause; the comparison is done as fractions on
-- both sides.
-- =====================================================================

SELECT
    sub.source,
    COUNT(*)                                     AS emails_sent,
    SUM(e.clicked)                               AS clicks,
    ROUND(100.0 * SUM(e.clicked) / COUNT(*), 2)  AS click_rate_pct,
    ROUND(100.0 * (SELECT SUM(clicked) FROM engagement)
                / (SELECT COUNT(*)    FROM engagement), 2) AS overall_click_rate_pct
FROM engagement e
INNER JOIN subscribers sub
    ON e.subscriber_id = sub.subscriber_id
GROUP BY sub.source
-- Keep only sources whose click-rate fraction beats the overall fraction.
HAVING 1.0 * SUM(e.clicked) / COUNT(*)
       > (SELECT 1.0 * SUM(clicked) / COUNT(*) FROM engagement)
ORDER BY click_rate_pct DESC;
