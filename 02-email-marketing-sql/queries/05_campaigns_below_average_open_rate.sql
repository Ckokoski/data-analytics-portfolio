-- =====================================================================
-- 05 — Campaigns BELOW the overall average open rate (underperformers)
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   Which campaigns underperformed the list as a whole — i.e. their open
--   rate came in BELOW our overall average open rate? These are the sends
--   to learn from (subject line, timing, audience).
--
-- METRIC:
--   open rate = opens / emails sent
--   benchmark = the overall list-wide open rate (a single number computed
--               by the subquery in the HAVING clause)
--
-- TECHNIQUE (the key teaching point of this file):
--   * GROUP BY campaign to get each campaign's open rate.
--   * HAVING compares each group's open rate to a SUBQUERY BENCHMARK:
--     (SELECT 1.0*SUM(opened)/COUNT(*) FROM engagement) is the whole-list
--     open rate as a fraction. The subquery runs once and returns one value.
--   We keep the comparison as a fraction (no *100) on both sides so the
--   math is apples-to-apples.
-- =====================================================================

SELECT
    s.campaign_name,
    COUNT(*)                                    AS emails_sent,
    SUM(e.opened)                               AS opens,
    ROUND(100.0 * SUM(e.opened) / COUNT(*), 1)  AS open_rate_pct,
    -- show the benchmark next to each row for context
    ROUND(100.0 * (SELECT SUM(opened) FROM engagement)
                / (SELECT COUNT(*)   FROM engagement), 1) AS overall_open_rate_pct
FROM engagement e
INNER JOIN sends s
    ON e.send_id = s.send_id
GROUP BY s.campaign_name
-- Keep only campaigns whose open-rate fraction is below the overall fraction.
HAVING 1.0 * SUM(e.opened) / COUNT(*)
       < (SELECT 1.0 * SUM(opened) / COUNT(*) FROM engagement)
ORDER BY open_rate_pct ASC;
