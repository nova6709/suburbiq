# SuburbIQ — Demo Script

## Hook (0:00)
Every year, franchise owners sign leases on locations that fail within 18 months.
Not because their product was bad — because they picked the wrong suburb.
SuburbIQ fixes that.

## Intro (0:12)
SuburbIQ is an AI-powered franchise site intelligence platform.
Give it a suburb and a business category — it tells you whether that location
is worth opening in, backed by 311,000 real Sydney POIs from Foursquare's open dataset.

## Single suburb demo (0:25)
Select Newtown + Café, click Analyse.

I'm a franchise development manager looking at Newtown for a new café.
Instantly I get five metrics — Opportunity score, Saturation, Competitor count,
Density per km², and Anchor businesses.

High competition — 115 cafés in Newtown. But strong foot traffic — 183 anchor
businesses nearby. 32.5 cafés per km² versus Sydney's average of 8.
Recommendation: premium differentiation required.

Every competitor is pinned on this live interactive map.
This used to take a consultant a week.

The category gaps panel surfaces what's undersupplied — Bubble Tea Shop, Korean Restaurant.
Lower-competition alternatives: Marrickville scores 34, Erskineville scores 28.

## AI Co-Pilot (1:45)
Type: "Should I open here?"

The AI Co-Pilot powered by Llama 3 ingests all live dashboard data —
saturation, foot traffic, gaps — and gives a contextual Go/No-Go verdict.
This used to cost $5,000 in consultant fees.

## Comparison demo (2:30)
Compare tab — Parramatta vs Chatswood for Gym.

Parramatta: 43 gyms, saturation 72.
Chatswood: 31 gyms, saturation 58.
Verdict: Chatswood has the stronger opportunity.

This is a $500,000 lease decision answered in 30 seconds.

## Data strategy (3:15)
100 million global POIs filtered to Sydney.
Point-in-polygon spatial join against ABS suburb boundaries — 99.4% assignment rate.
Pre-aggregated to SQLite for millisecond queries.
Saturation score = density per km² normalised against Sydney 95th percentile.

## Commercial case (3:35)
Placer.ai raised $100M for location intelligence.
SuburbIQ is the POI-native self-serve tier.
$299/month per franchise brand.
1,300+ franchise systems in Australia.

## Close (3:50)
SuburbIQ. Find the right suburb before you sign the lease.
github.com/nova6709/suburbiq
