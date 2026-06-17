-- =====================================================================
-- 10 — Sunset candidates: no engagement in the last 90 DAYS
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   Which subscribers have gone quiet recently — no opens AND no clicks in
--   the last 90 days? These are early "sunset candidates": people we should
--   try to win back, and (for deliverability) eventually suppress if they
--   stay cold, because mailing the unengaged hurts inbox placement.
--
-- LIST-HEALTH / DELIVERABILITY FRAMING: inbox providers watch how engaged a
-- sender's recipients are. Continuing to email people who never open drags
-- down deliverability for the WHOLE list, so identifying the disengaged is a
-- core list-hygiene task.
--
-- REFERENCE DATE: the synthetic data pins "today" to 2026-06-01, so the
-- 90-day window is date('2026-06-01', '-90 day') = 2026-03-03. (With real
-- data you would use date('now','-90 day') instead.)
--
-- TECHNIQUE (the key teaching point): LEFT JOIN to find the ABSENCE of
-- something. We LEFT JOIN every subscriber to ONLY their recent, engaged
-- rows (opened or clicked within 90 days). For subscribers who had no such
-- activity, the joined columns come back NULL — so "WHERE recent.subscriber_id
-- IS NULL" keeps exactly the people with no recent engagement. An INNER JOIN
-- could not do this: it would silently drop the very rows we want.
-- =====================================================================

SELECT
    sub.subscriber_id,
    sub.email,
    sub.source,
    sub.signup_date,
    sub.status
FROM subscribers sub
LEFT JOIN (
    -- Each subscriber who opened or clicked at least once in the last 90 days.
    SELECT DISTINCT e.subscriber_id
    FROM engagement e
    WHERE (e.opened = 1 OR e.clicked = 1)
      AND date(e.open_datetime) >= date('2026-06-01', '-90 day')
) recent
    ON sub.subscriber_id = recent.subscriber_id
-- Keep only subscribers with NO matching recent-engagement row (the NULLs).
WHERE recent.subscriber_id IS NULL
ORDER BY sub.signup_date ASC;
