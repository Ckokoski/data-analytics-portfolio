-- =====================================================================
-- 13 — List health by source: active vs. inactive subscribers
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   For each acquisition source, how much of what it brought in is still
--   ACTIVE versus gone INACTIVE? Which channels deliver subscribers who
--   stay engaged, and which fill the list with people who quickly go cold?
--
-- This is the acquisition-quality scorecard for list health: a source can
-- look cheap per signup but be expensive if most of those signups rot.
--
-- METRIC:
--   active_pct = active subscribers / all subscribers from that source
--   (status comes from the subscribers table: 'inactive' = no opens/clicks
--    in the last 180 days; see data/README.md and query 11.)
--
-- TECHNIQUE: a single GROUP BY over subscribers with conditional SUMs
-- (CASE WHEN ... THEN 1 ELSE 0 END) to count actives and inactives side by
-- side. This "pivot with CASE" is a core-SQL pattern — no window functions.
-- =====================================================================

SELECT
    source,
    COUNT(*)                                                  AS total_subscribers,
    SUM(CASE WHEN status = 'active'   THEN 1 ELSE 0 END)      AS active_subscribers,
    SUM(CASE WHEN status = 'inactive' THEN 1 ELSE 0 END)      AS inactive_subscribers,
    ROUND(100.0 * SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END)
                / COUNT(*), 1)                                AS active_pct
FROM subscribers
GROUP BY source
ORDER BY active_pct DESC;
