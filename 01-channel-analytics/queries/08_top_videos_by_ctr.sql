-- Business question: Which videos had the highest click-through rate? (Rate only.)
-- On the synthetic sample these are fake titles; on your real export this stays local.
SELECT
    video_title,
    period,
    ctr_percent
FROM videos
ORDER BY ctr_percent DESC
LIMIT 5;
