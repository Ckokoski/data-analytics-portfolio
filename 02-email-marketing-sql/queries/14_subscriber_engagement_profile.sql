-- =====================================================================
-- 14 — Per-subscriber engagement profile (incl. people who never engaged)
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   For each subscriber, how many emails have they received, how many did
--   they open, and how many did they click? We want EVERY subscriber listed
--   — including ones who received mail but never opened, and even ones who
--   were never mailed at all — so nobody silently disappears from the count.
--
-- This per-person profile is the building block a marketer would export to
-- build re-engagement segments (e.g. "opened 0 of 5").
--
-- TECHNIQUE (why LEFT JOIN matters here): we LEFT JOIN subscribers -> their
-- engagement rows. A subscriber with no engagement rows still appears, with
-- COUNT(e.engagement_id) = 0 and their open/click sums coalesced to 0. Swap
-- LEFT JOIN for INNER JOIN and those never-mailed subscribers would VANISH
-- from the result — which is exactly the bug LEFT JOIN avoids.
--
-- NOTE: limited to 25 rows just so the runner prints a readable sample; the
-- pattern is what matters, not the row count. Ordered to surface the least-
-- engaged first (the people a re-engagement campaign would target).
-- =====================================================================

SELECT
    sub.subscriber_id,
    sub.source,
    sub.status,
    COUNT(e.engagement_id)        AS emails_received,
    COALESCE(SUM(e.opened),  0)   AS opens,
    COALESCE(SUM(e.clicked), 0)   AS clicks
FROM subscribers sub
LEFT JOIN engagement e
    ON sub.subscriber_id = e.subscriber_id
GROUP BY sub.subscriber_id, sub.source, sub.status
-- Least-engaged first: fewest opens, then fewest clicks.
ORDER BY opens ASC, clicks ASC, emails_received DESC
LIMIT 25;
