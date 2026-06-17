-- =====================================================================
-- 08 — Cumulative list size by month (running total)
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   How big has the list grown to by the end of each month? Instead of just
--   "new joins this month" (query 07), show the running TOTAL — the list
--   size cumulatively over time.
--
-- STRETCH (window function): this file uses a WINDOW FUNCTION, which is one
--   step beyond the core SQL in the rest of this project. The running total
--   is produced by:
--       SUM(new_subscribers) OVER (ORDER BY signup_month)
--   A window function does a calculation ACROSS a set of rows that are
--   related to the current row, WITHOUT collapsing them into one row the way
--   GROUP BY does. Here, "OVER (ORDER BY signup_month)" tells SQLite: for each
--   month's row, add up new_subscribers for that month and every earlier
--   month. That cumulative sum is the list size at that point in time.
--   --> Christopher: this is the ONE technique to study deliberately here.
--       Compare it to query 07: same data, but 07 stops at per-month counts
--       and 08 accumulates them.
--
-- TECHNIQUE: a subquery in FROM first rolls signups up to per-month counts
-- (exactly query 07), then the outer query lays the running total beside it.
-- =====================================================================

SELECT
    signup_month,
    new_subscribers,
    -- Running total: this month's joins plus all earlier months' joins.
    SUM(new_subscribers) OVER (ORDER BY signup_month) AS cumulative_subscribers
FROM (
    -- inner query = "new signups by month" (same logic as query 07)
    SELECT
        strftime('%Y-%m', signup_date) AS signup_month,
        COUNT(*)                       AS new_subscribers
    FROM subscribers
    GROUP BY signup_month
)
ORDER BY signup_month ASC;
