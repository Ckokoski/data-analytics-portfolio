-- Business question: Did the higher-CTR period also hold attention better? Compares
-- average CTR against average retention (% viewed) for each period — both rates.
SELECT
    period,
    ROUND(AVG(ctr_percent), 2)        AS avg_ctr_percent,
    ROUND(AVG(avg_percent_viewed), 1) AS avg_percent_viewed
FROM videos
GROUP BY period
ORDER BY period DESC;
