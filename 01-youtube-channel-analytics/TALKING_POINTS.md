# Talking Points — YouTube Channel Analytics (flagship)

A 2-minute STAR walkthrough + 3 likely follow-ups. Method facts are filled; your real findings and numbers stay yours (`>>> CHRISTOPHER` + your private one-pager). **Talk in rates and multiples — never state raw audience counts out loud.**

## 2-minute walkthrough (STAR)

**Situation.** I changed the thumbnail/title approach on a content channel and wanted to know, honestly, whether click-through rate actually improved — not just eyeball it.

**Task.** Measure the before/after impact on CTR rigorously, weighting by reach, while controlling for the obvious confounds — and keep the channel's private numbers private.

**Action.** I exported the per-video data and built an **impressions-weighted CTR** model — `SUM(impressions × CTR) / SUM(impressions)` — in SQL, Excel, and Power BI (a custom DAX measure). Weighting matters because a high CTR on a barely-shown video shouldn't count as much as one on a heavily-shown video. I split videos Before/After the change date, charted the trend, and deliberately reported everything in rates and indexes so no raw audience numbers are exposed.

**Result.** `>>> CHRISTOPHER:` your headline in rate terms — e.g. "weighted CTR roughly doubled (~2×), with ~3× views per video, and average % viewed rose too." One or two sentences. Absolute numbers stay in your private one-pager.

## Likely follow-up questions

**1. "Why impressions-weighted instead of plain average CTR?"**
A simple average lets a tiny-reach video swing the number. Weighting by impressions gives the reach-honest CTR — the rate that actually reflects audience behavior. (On the synthetic sample simple and weighted are close; on real data with uneven reach they can diverge a lot.)

**2. "How do you know the change *caused* the lift — not something else?"**
I don't claim pure causation. `>>> CHRISTOPHER:` say how you handled the confounds — the data-detected split, a viral outlier, changing upload volume, and an AI-launch seasonality bump. The honest framing is "here's the lift, here's what I controlled for, and here's what I can't fully rule out."

**3. "Can I see the actual numbers?"**
The public repo shows rates and percentages only — the channel's raw counts are private. `>>> CHRISTOPHER:` "I keep the absolute figures in a one-pager I can walk you through" (your private PDF).
