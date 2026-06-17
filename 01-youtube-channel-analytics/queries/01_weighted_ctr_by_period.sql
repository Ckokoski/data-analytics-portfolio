-- Business question: After the content change, did click-through rate improve when we
-- weight each video by how often it was shown (impressions)?
--
-- Weighted CTR = SUM(impressions * ctr_percent) / SUM(impressions).
-- Weighting matters because a high CTR on a video almost nobody saw shouldn't count
-- the same as a high CTR on a heavily-shown video.
-- PRIVACY: only the weighted RATE is returned, never the underlying impression counts.
SELECT
    period,
    ROUND(SUM(impressions * ctr_percent) / SUM(impressions), 2) AS weighted_ctr_percent
FROM videos
GROUP BY period
ORDER BY period DESC;   -- Before, then After
