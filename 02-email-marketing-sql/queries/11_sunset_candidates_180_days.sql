-- =====================================================================
-- 11 — Sunset candidates: no engagement in the last 180 DAYS (suppress list)
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   Which subscribers have been cold for a full 180 days — no opens AND no
--   clicks in the last six months? This is the harder cutoff: people this
--   disengaged are strong candidates to SUPPRESS (stop mailing) to protect
--   deliverability, after one last win-back attempt.
--
-- Compare to query 10 (90 days): the 90-day list is the early-warning
-- "re-engage" cohort; this 180-day list is the "sunset / suppress" cohort.
-- The 180-day cohort should be SMALLER than the 90-day one (a longer window
-- is easier to have SOME activity in). This query's result also matches the
-- subscribers flagged status = 'inactive' by the generator.
--
-- REFERENCE DATE: data pins "today" to 2026-06-01, so the 180-day window is
-- date('2026-06-01', '-180 day') = 2025-12-03. (Real data: date('now','-180 day').)
--
-- TECHNIQUE: identical LEFT JOIN "find the absence" pattern as query 10, with
-- a 180-day window. We also break the result down by source so we can see
-- WHERE the dead weight came from.
-- =====================================================================

SELECT
    sub.source,
    COUNT(*) AS sunset_candidates_180d
FROM subscribers sub
LEFT JOIN (
    -- Each subscriber who opened or clicked at least once in the last 180 days.
    SELECT DISTINCT e.subscriber_id
    FROM engagement e
    WHERE (e.opened = 1 OR e.clicked = 1)
      AND date(e.open_datetime) >= date('2026-06-01', '-180 day')
) recent
    ON sub.subscriber_id = recent.subscriber_id
WHERE recent.subscriber_id IS NULL
GROUP BY sub.source
ORDER BY sunset_candidates_180d DESC;
