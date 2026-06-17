-- Business question: How did impressions-weighted CTR trend month by month?
-- (Helps separate a real step-change from gradual drift.)
SELECT
    substr(publish_date, 1, 7) AS month,                         -- YYYY-MM
    ROUND(SUM(impressions * ctr_percent) / SUM(impressions), 2) AS weighted_ctr_percent
FROM videos
GROUP BY month
ORDER BY month;
