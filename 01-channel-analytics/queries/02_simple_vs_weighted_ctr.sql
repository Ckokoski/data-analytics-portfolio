-- Business question: How does a simple (unweighted) average CTR compare with the
-- impressions-weighted CTR for each period? (Shows why the weighting choice matters.)
-- video_count is the number of videos, not an audience count.
SELECT
    period,
    ROUND(AVG(ctr_percent), 2)                                   AS simple_avg_ctr_percent,
    ROUND(SUM(impressions * ctr_percent) / SUM(impressions), 2)  AS weighted_ctr_percent,
    COUNT(*)                                                     AS video_count
FROM videos
GROUP BY period
ORDER BY period DESC;
