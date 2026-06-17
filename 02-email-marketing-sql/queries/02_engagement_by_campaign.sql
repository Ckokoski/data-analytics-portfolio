-- =====================================================================
-- 02 — Open rate, click rate, and CTOR BY CAMPAIGN
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   Which campaigns performed best and worst? For each campaign, what was
--   its open rate, click rate, and CTOR?
--
-- This is the core "campaign scorecard". Sort by open rate to see the
-- leaderboard from top to bottom.
--
-- METRICS:
--   open rate  = opens  / emails sent
--   click rate = clicks / emails sent
--   CTOR       = clicks / opens
--
-- TECHNIQUE: INNER JOIN engagement -> sends so each engagement row carries
-- its campaign name, then GROUP BY campaign. An INNER JOIN is correct here
-- because we only want engagement rows that belong to a real send (every
-- row does, but the JOIN makes that explicit).
-- =====================================================================

SELECT
    s.campaign_name,
    s.send_date,
    COUNT(*)                                    AS emails_sent,
    SUM(e.opened)                               AS opens,
    SUM(e.clicked)                              AS clicks,
    ROUND(100.0 * SUM(e.opened)  / COUNT(*), 1) AS open_rate_pct,
    ROUND(100.0 * SUM(e.clicked) / COUNT(*), 1) AS click_rate_pct,
    ROUND(100.0 * SUM(e.clicked) / NULLIF(SUM(e.opened), 0), 1) AS ctor_pct
FROM engagement e
INNER JOIN sends s
    ON e.send_id = s.send_id
GROUP BY s.campaign_name, s.send_date
ORDER BY open_rate_pct DESC;
