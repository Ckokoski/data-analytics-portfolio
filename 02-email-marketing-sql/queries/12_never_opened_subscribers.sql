-- =====================================================================
-- 12 — Subscribers who have NEVER opened a single email
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   Who on the list has never once opened any email we've ever sent them?
--   These "never-openers" are the deadest weight on the list — prime
--   suppression candidates and a red flag for how some channels were
--   acquired (e.g. low-quality signups).
--
-- DELIVERABILITY FRAMING: a pile of addresses that never open is exactly
-- what spam filters use to decide a sender is mailing people who don't want
-- it. Trimming never-openers is one of the highest-leverage list-hygiene moves.
--
-- TECHNIQUE: LEFT JOIN every subscriber to all of their engagement rows, then
-- aggregate per subscriber and keep only those whose total opens = 0. Using
-- COALESCE(SUM(e.opened), 0) handles subscribers who have NO engagement rows
-- at all (the SUM over zero rows is NULL) — they count as 0 opens, which is
-- correct: never sent to = never opened. We then also distinguish "was mailed
-- but never opened" from "was never even mailed".
-- =====================================================================

SELECT
    sub.source,
    COUNT(*)                                  AS subscribers,
    SUM(CASE WHEN emails_received = 0 THEN 1 ELSE 0 END) AS never_mailed,
    SUM(CASE WHEN emails_received > 0 THEN 1 ELSE 0 END) AS mailed_but_never_opened
FROM (
    -- Per subscriber: how many emails they received and how many they opened.
    SELECT
        sub.subscriber_id,
        sub.source,
        COUNT(e.engagement_id)        AS emails_received,
        COALESCE(SUM(e.opened), 0)    AS total_opens
    FROM subscribers sub
    LEFT JOIN engagement e
        ON sub.subscriber_id = e.subscriber_id
    GROUP BY sub.subscriber_id, sub.source
) sub
WHERE sub.total_opens = 0          -- never opened anything
GROUP BY sub.source
ORDER BY subscribers DESC;
