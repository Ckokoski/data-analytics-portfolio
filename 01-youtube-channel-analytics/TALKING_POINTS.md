# Talking Points — YouTube Channel Analytics (flagship)

A 2-minute STAR walkthrough + 3 likely follow-ups, in rate terms. **Talk in rates and multiples — never state raw audience counts out loud;** the absolute numbers stay in the private one-pager.

## 2-minute walkthrough (STAR)

**Situation.** I changed the thumbnail/title approach on a content channel and wanted to know, honestly, whether click-through rate actually improved — not just eyeball it.

**Task.** Measure the before/after impact on CTR rigorously, weighting by reach, while controlling for the obvious confounds — and keep the channel's private numbers private.

**Action.** I exported the per-video data and built an **impressions-weighted CTR** model — `SUM(impressions × CTR) / SUM(impressions)` — in SQL, Excel, and Power BI (a custom DAX measure). Weighting matters because a high CTR on a barely-shown video shouldn't count as much as one on a heavily-shown video. I split videos Before/After the change date, charted the trend, and deliberately reported everything in rates and indexes so no raw audience numbers are exposed.

**Result.** Impressions-weighted CTR roughly **doubled — about 3.5% to 6.9%, a ~96% lift** — after the change, and average % viewed rose alongside it, which suggests the new packaging drew better-matched viewers rather than just more clicks. I keep this rates-only in public; the absolute counts live in my private one-pager.

## Likely follow-up questions

**1. "Why impressions-weighted instead of plain average CTR?"**
A simple average lets a tiny-reach video swing the number. Weighting by impressions gives the reach-honest CTR — the rate that actually reflects audience behavior. (On the synthetic sample simple and weighted are close; on real data with uneven reach they can diverge a lot.)

**2. "How do you know the change *caused* the lift — not something else?"**
I don't claim pure causation — I'm explicit about the confounds: the before/after split was data-detected rather than pre-registered, a viral outlier can skew averages (impressions-weighting tempers that), my upload volume changed across the window, and an AI-launch seasonality bump landed around the same time. So the honest framing is "here's a ~96% weighted-CTR lift, here's what I controlled for by weighting, and here's what I can't fully rule out."

**3. "Can I see the actual numbers?"**
The public repo shows rates and percentages only — the channel's raw counts are private. I keep the absolute figures in a one-pager I can walk you through in the room.
