-- =====================================================================
-- 09 — Rank campaigns by click rate (leaderboard with a rank number)
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   If we had to rank every campaign 1, 2, 3, ... by click rate, what's the
--   leaderboard? Which campaign drove the most clicks per email sent?
--
-- STRETCH (window function): this file uses the RANK() WINDOW FUNCTION, the
--   second (and final) window-function example in this project. RANK()
--   assigns 1 to the highest click rate, 2 to the next, and so on:
--       RANK() OVER (ORDER BY click_rate DESC)
--   Like the running total in query 08, RANK() looks across all the rows
--   (ordered by click rate) without collapsing them. Ties would share a rank
--   and then skip the next number (e.g. 1, 2, 2, 4) — that's RANK's defined
--   behaviour, versus ROW_NUMBER which would force a unique 1,2,3,4.
--   --> Christopher: window function #2 of 2. Every other query file is
--       deliberately free of window functions.
--
-- METRIC:
--   click rate = clicks / emails sent
--
-- TECHNIQUE: a subquery in FROM computes each campaign's click rate with a
-- plain INNER JOIN + GROUP BY (no window function), and the outer query just
-- adds the rank column on top.
-- =====================================================================

SELECT
    RANK() OVER (ORDER BY click_rate_pct DESC) AS click_rate_rank,
    campaign_name,
    emails_sent,
    clicks,
    click_rate_pct
FROM (
    -- inner query = click rate per campaign (core SQL only)
    SELECT
        s.campaign_name,
        COUNT(*)                                    AS emails_sent,
        SUM(e.clicked)                              AS clicks,
        ROUND(100.0 * SUM(e.clicked) / COUNT(*), 2) AS click_rate_pct
    FROM engagement e
    INNER JOIN sends s
        ON e.send_id = s.send_id
    GROUP BY s.campaign_name
)
ORDER BY click_rate_rank ASC;
