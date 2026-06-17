-- =====================================================================
-- 03 — Open rate, click rate, and CTOR BY ACQUISITION SOURCE
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   Does where a subscriber came from (Webinar, Referral, Organic, Event,
--   Paid Social) affect how engaged they are? Which channels bring us the
--   subscribers who actually open and click?
--
-- This is a LIST-QUALITY question, not a campaign question: it tells us
-- which acquisition channels are worth more per subscriber.
--
-- METRICS:
--   open rate  = opens  / emails sent
--   click rate = clicks / emails sent
--   CTOR       = clicks / opens
--
-- TECHNIQUE: INNER JOIN engagement -> subscribers so each engagement row
-- carries the subscriber's source, then GROUP BY source.
-- =====================================================================

SELECT
    sub.source,
    COUNT(DISTINCT sub.subscriber_id)              AS subscribers_engaged,
    COUNT(*)                                        AS emails_sent,
    SUM(e.opened)                                   AS opens,
    SUM(e.clicked)                                  AS clicks,
    ROUND(100.0 * SUM(e.opened)  / COUNT(*), 1)     AS open_rate_pct,
    ROUND(100.0 * SUM(e.clicked) / COUNT(*), 1)     AS click_rate_pct,
    ROUND(100.0 * SUM(e.clicked) / NULLIF(SUM(e.opened), 0), 1) AS ctor_pct
FROM engagement e
INNER JOIN subscribers sub
    ON e.subscriber_id = sub.subscriber_id
GROUP BY sub.source
ORDER BY open_rate_pct DESC;
