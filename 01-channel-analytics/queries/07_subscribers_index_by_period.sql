-- Business question: How did subscribers gained per video change, as an INDEX
-- (Before = 100)? Relative only — no raw subscriber counts are returned.
SELECT
    period,
    ROUND(100.0 * AVG(subscribers_gained)
          / (SELECT AVG(subscribers_gained) FROM videos WHERE period = 'Before'), 0)
        AS subscribers_index_before_100
FROM videos
GROUP BY period
ORDER BY period DESC;
