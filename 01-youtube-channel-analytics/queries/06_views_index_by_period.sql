-- Business question: Roughly how many more views per video did the After period earn,
-- expressed as an INDEX with Before = 100? (An index keeps this privacy-safe: it shows
-- the relative multiple without ever exposing a raw view count.)
SELECT
    period,
    ROUND(100.0 * AVG(views) / (SELECT AVG(views) FROM videos WHERE period = 'Before'), 0)
        AS views_index_before_100
FROM videos
GROUP BY period
ORDER BY period DESC;
