SuburbIQ 📍
AI-Powered Franchise Site Intelligence — Data-driven decisions before the lease is signed.

SuburbIQ is a high-performance geospatial intelligence platform that helps franchise development managers and retail investors find the optimal Sydney suburb for expansion. By synthesizing 311,266 POIs with real-time LLM-driven market analysis, SuburbIQ identifies "Franchise Twins" and underserved commercial gaps.

v3.0!! (more like 2.5) so after getting our technicals, data, features, etc... right we have come to the realization that if our app wants to sell to real people and make an impact on them our need to be able to assist and cater to the user's needs and interest, thats why we decided to add a FAQ tab and REVAMP THE WHOLE UI OF OUR WEBSITE >:)

🌟 New in v2.0 (The Intelligence Update)
🤖 Integrated AI Co-Pilot (Powered by Llama 3)
We have moved beyond static charts. SuburbIQ now features an embedded AI Market Analyst that provides real-time, context-aware consultations.

Contextual Reasoning: The AI automatically ingests live dashboard metrics (Saturation, Foot Traffic, Category Gaps) to provide bespoke risk assessments.

Natural Language Queries: Users can ask complex questions like "Is the foot traffic here strong enough to offset the high competition?" and receive data-backed responses.

Executive Summaries: Generates instant Go/No-Go verdicts for board-level presentations.

🚫 Zero-State UX (Cascading Data Filters)
To provide a premium enterprise experience, we implemented Dependent Cascading Dropdowns.

The UI dynamically filters business categories based on the selected suburb.

Outcome: Users never encounter "No Data" screens. The platform only surfaces categories with actionable competitive intelligence.

🚀 Core Features
Saturation Score (0–100): Competitor density normalized against Sydney's 95th percentile, area-adjusted per km 
2
 .

Opportunity Score (0–100): A proprietary weighted metric: Saturation (60%) + Anchor Strength (25%) + Category Gaps (15%).

Interactive Competitor Mapping: Every competing business plotted with specialized markers for Corporate Chains vs. Independents.

Anchor Business Analysis: Real-time counts of foot-traffic generators (Offices, Transport, Hospitals, Schools) to validate demand.

Category Gap Insights: Identifies undersupplied retail categories compared to Sydney's regional averages.

Side-by-Side Comparison: Head-to-head analysis of two suburbs with synchronized maps and competitive benchmarks.

🛠️ Technical Stack
Layer	Technology
Intelligence	Groq (Llama-3.3-70B) — Sub-second AI inference
Data Processing	Polars + PyArrow — High-speed Parquet ingestion
Geospatial	GeoPandas + Shapely — Point-in-polygon spatial joins
Storage	SQLite — Pre-aggregated stats for ms query speeds
Frontend	Streamlit — Custom CSS & Chat-native UI
Visualization	Folium & Plotly — Interactive mapping and analytics
📈 Commercial Case & TAM
Site selection is a high-stakes capital expenditure. A single bad location can cost a franchise $200K–$2M. SuburbIQ targets the self-serve, mid-market tier:

Target Customers: Franchise Development Managers, Commercial Property Developers, and SMBs.

Monetization: SaaS model at $299/month per brand.

Market Opportunity: 1,300+ franchise systems in Australia alone.

🏗️ Deployment & Setup
Clone & Install:

Bash
git clone https://github.com/nova6709/suburbiq.git
cd suburbiq
pip install -r requirements.txt
API Configuration:
Create .streamlit/secrets.toml:

Ini, TOML
GROQ_API_KEY = "your_groq_key_here"
Run:

Bash
streamlit run app/app.py

final notes - big thank you to vanco and yu chien for joining my team and helping me with the slides, pitching and features for the hackathon project, another big thanks to comm-stem and sudata for organizing such a cool event for everyone - truely a learning experience, i never had so much fun locking in and building ever before lmao this will be my first hackathon of many many more in the future! final big thank you for nadh on discord for helping me with the team allocations too :). I hope you guys have more successful events in the future :) <3
-nova

Built for the SUDATA Data-Hack 2026 Theme 2: Foursquare Location Data · University of Sydney

