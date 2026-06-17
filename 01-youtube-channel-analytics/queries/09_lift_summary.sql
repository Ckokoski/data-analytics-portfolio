-- Business question: One-line summary — Before vs After weighted CTR and the lift %.
-- This is the headline a hiring manager wants: two rates and the change between them.
SELECT
    ROUND(before_weighted, 2) AS before_weighted_ctr,
    ROUND(after_weighted, 2)  AS after_weighted_ctr,
    ROUND(100.0 * (after_weighted - before_weighted) / before_weighted, 1) AS lift_percent
FROM (
    SELECT
        SUM(CASE WHEN period = 'Before' THEN impressions * ctr_percent END)
            / SUM(CASE WHEN period = 'Before' THEN impressions END) AS before_weighted,
        SUM(CASE WHEN period = 'After'  THEN impressions * ctr_percent END)
            / SUM(CASE WHEN period = 'After'  THEN impressions END) AS after_weighted
    FROM videos
);
