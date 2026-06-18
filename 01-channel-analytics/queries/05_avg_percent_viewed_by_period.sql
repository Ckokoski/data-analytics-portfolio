-- Business question: Did audience retention (average percentage of the video viewed)
-- change after the content change? Retention is already a rate, so it is safe to show.
SELECT
    period,
    ROUND(AVG(avg_percent_viewed), 1) AS avg_percent_viewed
FROM videos
GROUP BY period
ORDER BY period DESC;
