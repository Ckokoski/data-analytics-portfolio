-- Business question: What was the percent change in impressions-weighted CTR from
-- Before to After? (The single headline number, expressed as a percentage.)
SELECT
    ROUND(100.0 * (after_weighted - before_weighted) / before_weighted, 1) AS ctr_percent_change
FROM (
    SELECT
        SUM(CASE WHEN period = 'Before' THEN impressions * ctr_percent END)
            / SUM(CASE WHEN period = 'Before' THEN impressions END) AS before_weighted,
        SUM(CASE WHEN period = 'After'  THEN impressions * ctr_percent END)
            / SUM(CASE WHEN period = 'After'  THEN impressions END) AS after_weighted
    FROM videos
);
