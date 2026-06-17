-- =====================================================================
-- 07 — Subscriber growth: new signups by month
-- ---------------------------------------------------------------------
-- BUSINESS QUESTION:
--   How fast is the list growing? How many NEW subscribers joined in each
--   month over the past year?
--
-- This is the raw acquisition trend (new joins per month). Query 08 turns
-- it into a running cumulative list size.
--
-- TECHNIQUE: strftime('%Y-%m', signup_date) truncates each signup date to
-- its year-month, and GROUP BY that bucket counts joins per month. No JOIN
-- needed — this lives entirely in the subscribers table.
-- =====================================================================

SELECT
    strftime('%Y-%m', signup_date)  AS signup_month,
    COUNT(*)                        AS new_subscribers
FROM subscribers
GROUP BY signup_month
ORDER BY signup_month ASC;
