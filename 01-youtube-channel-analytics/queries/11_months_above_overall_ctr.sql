-- Business question: Which months beat the overall impressions-weighted CTR?
-- Uses HAVING with a subquery benchmark (the all-time weighted CTR).
SELECT
    substr(publish_date, 1, 7) AS month,
    ROUND(SUM(impressions * ctr_percent) / SUM(impressions), 2) AS weighted_ctr_percent
FROM videos
GROUP BY month
HAVING SUM(impressions * ctr_percent) / SUM(impressions)
       > (SELECT SUM(impressions * ctr_percent) / SUM(impressions) FROM videos)
ORDER BY month;
