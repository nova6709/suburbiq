import streamlit as st
import sqlite3
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import plotly.graph_objects as go
from pathlib import Path
import io
from fpdf import FPDF
from datetime import datetime
from groq import Groq
import os
import gdown

DB_PATH = Path("data/suburbiq.db")
if not DB_PATH.exists():
    os.makedirs("data", exist_ok=True)
    gdown.download("https://drive.google.com/uc?id=1KubUO7AL3PdT91mk68b4iLb2JEqaa_F_", str(DB_PATH), quiet=False)
DB = DB_PATH

st.set_page_config(
    page_title="SuburbIQ — Franchise Site Intelligence",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import base64 as _b64
_logo_path = Path(__file__).parent / "logo.png"
_LOGO_B64 = _b64.b64encode(_logo_path.read_bytes()).decode() if _logo_path.exists() else ""

try:
    _GROQ_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    _GROQ_KEY = ""

_GROQ_MODEL = "llama-3.3-70b-versatile"

def _chat_stream(history, new_message, system_ctx):
    """Stream a Groq response. Rebuilds client on every call — safe across Streamlit reruns."""
    client = Groq(api_key=_GROQ_KEY)
    messages = [{"role": "system", "content": system_ctx}] + history + [{"role": "user", "content": new_message}]
    stream = client.chat.completions.create(
        model=_GROQ_MODEL,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        text = chunk.choices[0].delta.content
        if text:
            yield text

# ── CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base & Reset ─────────────────────────────────────── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.stApp { background: #F4F6F8 !important; }
[data-testid="stAppViewContainer"] { background: #F4F6F8 !important; }
[data-testid="stMain"] { background: #F4F6F8 !important; }

/* Force all text dark on light bg */
.stApp, .stApp p, .stApp div, .stApp span, .stApp label,
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #111827 !important; }

/* Hide Streamlit chrome */
#MainMenu, footer, header, .stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

/* Content container */
[data-testid="stAppViewBlockContainer"] {
    max-width: 1440px !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
}

/* ── Header / Nav ─────────────────────────────────────── */
.siq-header {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 1rem 1.75rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid #E5E7EB;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.04);
}
.siq-header * { color: #111827 !important; }
.siq-logo img { background: transparent !important; border: none !important; box-shadow: none !important; }
.siq-header [data-testid="stMarkdownContainer"],
.siq-header [data-testid="element-container"] {
    background: transparent !important; border: none !important;
    padding: 0 !important; box-shadow: none !important;
}
.siq-badge {
    background: #F3F4F6;
    border: 1px solid #E5E7EB;
    border-radius: 9999px;
    padding: 0.3rem 0.85rem;
    color: #6B7280 !important;
    font-size: 0.73rem;
    font-weight: 500;
    letter-spacing: 0.02em;
}

/* ── White Cards ──────────────────────────────────────── */
.siq-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 1.25rem 1.4rem;
    border: 1px solid #E5E7EB;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 4px 6px rgba(0,0,0,0.04);
    margin-bottom: 1rem;
}

/* ── Metric Cards ─────────────────────────────────────── */
div[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 4px 6px rgba(0,0,0,0.04) !important;
}
div[data-testid="stMetric"] label {
    color: #6B7280 !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] div {
    color: #111827 !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
}
.opp-metric div[data-testid="stMetric"] {
    border: 2px solid #BFDBFE !important;
    box-shadow: 0 2px 12px rgba(59,130,246,0.1) !important;
}

/* ── Pill Badges ──────────────────────────────────────── */
.pill {
    display: inline-block;
    border-radius: 9999px;
    padding: 0.2rem 0.7rem;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    line-height: 1.6;
}
.pill-green  { background: #D1FAE5; color: #065F46 !important; }
.pill-amber  { background: #FEF3C7; color: #92400E !important; }
.pill-red    { background: #FEE2E2; color: #991B1B !important; }
.pill-blue   { background: #DBEAFE; color: #1E40AF !important; }
.pill-gray   { background: #F3F4F6; color: #374151 !important; }

/* ── Section Labels ───────────────────────────────────── */
.siq-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #9CA3AF;
    margin-bottom: 0.55rem;
    margin-top: 0.15rem;
}

/* ── Scoreboard ───────────────────────────────────────── */
.scoreboard-wrap {
    background: #EEF2FF;
    border: 1px solid #C7D2FE;
    border-radius: 14px;
    padding: 1rem 1.25rem 0.85rem;
    margin-bottom: 0.5rem;
}

/* ── Verdict Cards ────────────────────────────────────── */
.verdict-label { font-weight: 600; color: #111827; font-size: 0.88rem; }
.verdict-detail { color: #6B7280; font-size: 0.82rem; margin-top: 2px; line-height: 1.45; }

.rec-banner {
    background: linear-gradient(135deg, #1D4ED8, #2563EB);
    border-radius: 10px;
    padding: 0.85rem 1.1rem;
    font-weight: 600;
    font-size: 0.86rem;
    margin-top: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    box-shadow: 0 4px 14px rgba(29,78,216,0.25);
}
.rec-banner, .rec-banner * { color: white !important; }

/* ── Winner / Loser / Tie Boxes ───────────────────────── */
.winner-box {
    background: #ECFDF5; border: 1.5px solid #6EE7B7;
    border-radius: 10px; padding: 0.65rem 1rem;
    text-align: center; font-weight: 700; color: #065F46; font-size: 0.88rem;
}
.loser-box {
    background: #FFF1F2; border: 1px solid #FECDD3;
    border-radius: 10px; padding: 0.65rem 1rem;
    text-align: center; font-weight: 600; color: #BE123C; font-size: 0.88rem;
}
.tie-box {
    background: #FFFBEB; border: 1px solid #FDE68A;
    border-radius: 10px; padding: 0.65rem 1rem;
    text-align: center; font-weight: 600; color: #92400E; font-size: 0.88rem;
}

/* ── Alt Card ─────────────────────────────────────────── */
.alt-card {
    background: #FFFFFF;
    border: 1px solid #DBEAFE;
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin-bottom: 7px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

/* ── Score Bar ────────────────────────────────────────── */
.score-bar-wrap {
    height: 7px; background: #F3F4F6;
    border-radius: 9999px; overflow: hidden; margin-top: 6px;
}
.score-bar-fill { height: 100%; border-radius: 9999px; transition: width 0.6s ease; }

/* ── Tabs ─────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #E5E7EB;
    gap: 3px;
    margin-bottom: 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 600 !important;
    color: #6B7280 !important;
    font-size: 0.85rem !important;
    padding: 0.45rem 1.3rem !important;
    transition: all 0.15s ease !important;
}
.stTabs [aria-selected="true"] {
    background: #1D4ED8 !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(29,78,216,0.25) !important;
}

/* ── Buttons ──────────────────────────────────────────── */
.stButton > button {
    background: #1D4ED8 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1.75rem !important;
    letter-spacing: 0.01em !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 2px 8px rgba(29,78,216,0.28) !important;
}
.stButton > button:hover {
    background: #1E40AF !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(29,78,216,0.35) !important;
}
.stButton > button p, .stButton > button div,
.stButton > button span { color: white !important; }

.stDownloadButton > button {
    background: #FFFFFF !important;
    color: #1D4ED8 !important;
    border: 1.5px solid #BFDBFE !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    transition: all 0.18s ease !important;
}
.stDownloadButton > button:hover {
    background: #EFF6FF !important;
    border-color: #93C5FD !important;
}

/* ── Selectbox ────────────────────────────────────────── */
.stSelectbox label {
    font-size: 0.73rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: #374151 !important;
}
.stSelectbox > div > div {
    background: #F9FAFB !important;
    border: 1.5px solid #E5E7EB !important;
    border-radius: 9px !important;
    font-weight: 500 !important;
    color: #111827 !important;
    transition: border-color 0.15s ease !important;
}
.stSelectbox > div > div:focus-within {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
}

/* ── AI Chat ──────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    border-radius: 12px !important;
    padding: 0.75rem 1rem !important;
    margin-bottom: 0.5rem !important;
    border: none !important;
    box-shadow: none !important;
}
/* User bubble */
[data-testid="stChatMessage"][data-testid*="user"],
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #EFF6FF !important;
    border-left: 3px solid #3B82F6 !important;
}
/* AI / assistant bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}
[data-testid="stChatInput"] > div {
    border-radius: 10px !important;
    border: 1.5px solid #E5E7EB !important;
    background: #FFFFFF !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
}

/* ── Empty State ──────────────────────────────────────── */
.empty-state { text-align: center; padding: 3.5rem 2rem; color: #9CA3AF; }
.empty-icon { font-size: 3rem; margin-bottom: 0.85rem; }
.empty-title { font-size: 1.1rem; font-weight: 700; color: #6B7280; }
.empty-sub { font-size: 0.85rem; margin-top: 0.3rem; color: #9CA3AF; }

/* ── Map ──────────────────────────────────────────────── */
.map-wrap {
    border-radius: 12px; overflow: hidden;
    border: 1px solid #E5E7EB;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* ── Radio ────────────────────────────────────────────── */
.stRadio > div { flex-direction: row !important; gap: 0.5rem; }
.stRadio label { font-size: 0.82rem !important; font-weight: 500 !important; }
.stRadio { margin-top: 0 !important; margin-bottom: 0.25rem !important; }

/* ── Reduce Streamlit vertical gaps ──────────────────── */
[data-testid="stVerticalBlock"] > [data-testid="element-container"] { margin-bottom: 0 !important; }

/* ── Footer ───────────────────────────────────────────── */
.siq-footer {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    font-size: 0.7rem;
    color: #9CA3AF;
    font-style: italic;
    border-top: 1px solid #E5E7EB;
    margin-top: 2rem;
}

/* ── Misc ─────────────────────────────────────────────── */
.stSpinner > div { border-top-color: #1D4ED8 !important; }
.stAlert { border-radius: 10px !important; }
hr { border-color: #F3F4F6 !important; margin: 0.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

CHART_CFG = {"displayModeBar": False, "staticPlot": False}

# ── Data helpers ──────────────────────────────────────────
COMMERCIAL_CATS = {
    'Airport Ticket Counter', 'Plane', 'Airport Gate', 'Airport Lounge',
    'Bus Line', 'Train', 'Road', 'City', 'Country', 'State',
    'Neighborhood', 'Island', 'Town', 'Village', 'Moving Target',
    'Intersection', 'Platform', 'Tree', 'Polling Place'
}

@st.cache_data
def get_categories():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT DISTINCT category FROM suburb_stats ORDER BY category", conn)
    conn.close()
    return [c for c in df["category"].tolist() if c not in COMMERCIAL_CATS]

@st.cache_data
def get_categories_for_suburb(suburb):
    conn = sqlite3.connect(DB)
    df = pd.read_sql(
        "SELECT DISTINCT category FROM suburb_stats WHERE suburb=? ORDER BY category",
        conn, params=(suburb,))
    conn.close()
    return [c for c in df["category"].tolist() if c not in COMMERCIAL_CATS]

@st.cache_data
def get_suburbs():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT DISTINCT suburb FROM suburb_stats ORDER BY suburb", conn)
    conn.close()
    return df["suburb"].tolist()

@st.cache_data
def query(suburb, category):
    conn = sqlite3.connect(DB)
    stats = pd.read_sql("SELECT * FROM suburb_stats WHERE suburb=? AND category=?",
                        conn, params=(suburb, category))
    pois = pd.read_sql("SELECT * FROM pois WHERE SAL_NAME21=? AND category_name=?",
                       conn, params=(suburb, category))
    anchor_cats = ('Gym', 'Supermarket', 'Train Station', 'Shopping Mall',
                   'Office', 'University', 'Hospital', 'School')
    anchors = pd.read_sql(
        f"SELECT category, raw_count FROM suburb_stats WHERE suburb=? "
        f"AND category IN ({','.join('?'*len(anchor_cats))}) ORDER BY raw_count DESC",
        conn, params=(suburb, *anchor_cats))
    top = pd.read_sql("SELECT category, raw_count, saturation_score FROM suburb_stats "
                      "WHERE suburb=? ORDER BY raw_count DESC LIMIT 8", conn, params=(suburb,))
    conn.close()
    return stats, pois, anchors, top

@st.cache_data
def get_gaps(suburb):
    EXCLUDE = {
        'Airport Ticket Counter', 'Plane', 'Airport Gate', 'Airport Lounge',
        'Bus Line', 'Train', 'Road', 'City', 'Country', 'State', 'Neighborhood',
        'Island', 'Town', 'Village', 'Moving Target', 'Intersection', 'Platform',
        'Tree', 'Polling Place', 'Structure', 'Miscellaneous Store',
        'Business and Professional Services', 'Building'
    }
    conn = sqlite3.connect(DB)
    local = pd.read_sql("SELECT category, raw_count FROM suburb_stats WHERE suburb=?",
                        conn, params=(suburb,))
    sydney_avg = pd.read_sql(
        "SELECT category, AVG(raw_count) as avg_count, COUNT(*) as suburb_count "
        "FROM suburb_stats GROUP BY category HAVING suburb_count > 10", conn)
    conn.close()
    merged = sydney_avg.merge(local, on="category", how="left")
    merged["raw_count"] = merged["raw_count"].fillna(0)
    merged["gap"] = merged["avg_count"] - merged["raw_count"]
    return (merged[
        ~merged["category"].isin(EXCLUDE) &
        (merged["avg_count"] < 50) & (merged["avg_count"] > 1) & (merged["gap"] > 1)
    ].sort_values("gap", ascending=False).head(5))

@st.cache_data
def get_alternatives(suburb, category):
    conn = sqlite3.connect(DB)
    df = pd.read_sql("""
        SELECT s.suburb, s.saturation_score
        FROM suburb_stats s
        JOIN (SELECT suburb, SUM(raw_count) as total FROM suburb_stats GROUP BY suburb) t
        ON s.suburb = t.suburb
        WHERE s.category=? AND s.suburb != ? AND t.total > 500
        ORDER BY s.saturation_score ASC LIMIT 3
    """, conn, params=(category, suburb))
    conn.close()
    return df

@st.cache_data
def get_dominant(suburb, category):
    JUNK = {
        'vicinity', 'google', 'foursquare', 'unknown', 'n/a', 'none', 'closed',
        'unnamed', 'null', 'the', 'and', 'a', 'an', 'my', 'your', 'our',
        'new', 'old', 'big', 'little', 'great', 'good', 'best', 'top',
        'shop', 'store', 'cafe', 'coffee', 'restaurant', 'bar', 'gym'
    }
    conn = sqlite3.connect(DB)
    df = pd.read_sql("""
        SELECT name, COUNT(*) as cnt FROM pois
        WHERE SAL_NAME21=? AND category_name=?
        GROUP BY name ORDER BY cnt DESC LIMIT 20
    """, conn, params=(suburb, category))
    conn.close()
    df = df[df['name'].str.len() > 4]
    df = df[~df['name'].str.lower().str.strip().isin(JUNK)]
    df = df[df['cnt'] >= 2]
    df = df[~df['name'].str.lower().str.contains('vicinity|google|apple|maps|unnamed|unknown', na=False)]
    return df.iloc[0] if len(df) > 0 else None

@st.cache_data
def classify_competitors(suburb, category):
    """Tag each local POI as chain (appears in 3+ suburbs) or independent."""
    conn = sqlite3.connect(DB)
    pois_local = pd.read_sql(
        "SELECT name, latitude, longitude FROM pois WHERE SAL_NAME21=? AND category_name=?",
        conn, params=(suburb, category))
    chain_names = pd.read_sql("""
        SELECT name FROM pois WHERE category_name=?
        GROUP BY name HAVING COUNT(DISTINCT SAL_NAME21) >= 3
    """, conn, params=(category,))
    conn.close()
    if len(pois_local) == 0:
        return pois_local, 0, 0
    chain_set = set(chain_names['name'].str.lower())
    pois_local['is_chain'] = pois_local['name'].str.lower().isin(chain_set)
    return pois_local, int(pois_local['is_chain'].sum()), int((~pois_local['is_chain']).sum())

def score_color(score):
    if score >= 75: return "#ef4444", "#fef2f2"
    if score >= 40: return "#f59e0b", "#fffbeb"
    return "#10b981", "#f0fdf4"

def make_map(pois, classified=None):
    tiles = "CartoDB positron"
    if len(pois) == 0:
        return folium.Map(location=[-33.8688, 151.2093], zoom_start=12, tiles=tiles)
    m = folium.Map(location=[pois["latitude"].mean(), pois["longitude"].mean()],
                   zoom_start=14, tiles=tiles)
    for _, r in pois.iterrows():
        color = "#4f46e5"
        if classified is not None and 'is_chain' in classified.columns:
            row_c = classified[classified['name'] == r['name']]
            color = "#dc2626" if (len(row_c) > 0 and row_c.iloc[0]['is_chain']) else "#10b981"
        folium.CircleMarker(
            location=[r["latitude"], r["longitude"]],
            radius=7, color=color, fill=True,
            fill_color=color, fill_opacity=0.85, weight=1.5,
            popup=folium.Popup(
                f"<div style='font-family:Inter,sans-serif;font-size:12px;min-width:120px'>"
                f"<b style='color:#0f172a'>{r['name']}</b><br>"
                f"<span style='color:#64748b'>{r['category_name']}</span></div>",
                max_width=220)
        ).add_to(m)
    return m

def make_heatmap_map(pois):
    tiles = "CartoDB positron"
    if len(pois) == 0:
        return folium.Map(location=[-33.8688, 151.2093], zoom_start=12, tiles=tiles)
    m = folium.Map(location=[pois["latitude"].mean(), pois["longitude"].mean()],
                   zoom_start=14, tiles=tiles)
    heat_data = [[r["latitude"], r["longitude"]] for _, r in pois.iterrows()]
    HeatMap(heat_data, radius=22, blur=18, min_opacity=0.35,
            gradient={0.3: "#10b981", 0.6: "#f59e0b", 1.0: "#ef4444"}).add_to(m)
    return m

def verdict_data(score, count, suburb, category, anchor_total):
    sc, sbg = score_color(score)
    if score >= 75:
        comp_label, comp_detail = "High competition", f"{count:,} {category.lower()} locations competing in {suburb}"
    elif score >= 40:
        comp_label, comp_detail = "Moderate competition", f"{count:,} {category.lower()} locations — room for the right concept"
    else:
        comp_label, comp_detail = "Low competition", f"Only {count:,} {category.lower()} locations — strong greenfield signal"
    if anchor_total >= 10:
        fc, foot_label, foot_detail = "#10b981", "Strong foot traffic", f"{anchor_total:,} anchor businesses driving consistent demand"
    elif anchor_total >= 3:
        fc, foot_label, foot_detail = "#f59e0b", "Moderate foot traffic", f"{anchor_total:,} anchor businesses nearby"
    else:
        fc, foot_label, foot_detail = "#ef4444", "Weak foot traffic", f"Only {anchor_total} anchor businesses — demand risk"
    if score >= 75:
        rec = "This market is crowded — premium positioning or a differentiated concept required"
    elif score >= 40:
        rec = "Viable opportunity — success depends on concept quality and execution"
    else:
        rec = "Strong greenfield opportunity — low competition, consider moving quickly"
    return sc, sbg, comp_label, comp_detail, fc, foot_label, foot_detail, rec

def _pdf_safe(text):
    """Replace Unicode chars that Helvetica (Latin-1) can't encode."""
    return (str(text)
            .replace("\u2014", " - ")   # em dash
            .replace("\u2013", " - ")   # en dash
            .replace("\u00b7", ".")     # middle dot
            .replace("\u2019", "'")     # right single quote
            .replace("\u2018", "'")     # left single quote
            .replace("\u201c", '"')     # left double quote
            .replace("\u201d", '"')     # right double quote
            .encode("latin-1", errors="replace").decode("latin-1"))

def generate_pdf(suburb, category, score, count, anchor_total,
                 density_per_km, opp_score, chain_count, indie_count,
                 gaps, dominant, rec, alts):
    # Sanitize all dynamic string inputs up front
    suburb   = _pdf_safe(suburb)
    category = _pdf_safe(category)
    rec      = _pdf_safe(rec)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header bar
    pdf.set_fill_color(29, 78, 216)
    pdf.rect(0, 0, 210, 38, 'F')
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(15, 7)
    pdf.cell(120, 10, "SuburbIQ", ln=False)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(15, 20)
    pdf.cell(180, 8, "Franchise Site Intelligence Report", ln=True)
    pdf.set_xy(15, 29)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(180, 7, f"Generated {datetime.now().strftime('%d %b %Y, %H:%M')}", ln=True)

    pdf.set_text_color(15, 23, 42)
    pdf.set_xy(15, 46)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _pdf_safe(f"{suburb}  -  {category}"), ln=True)
    pdf.ln(2)

    # Score cards (3 per row)
    metrics = [
        ("Opportunity Score", f"{opp_score}/100"),
        ("Saturation Score", f"{score}/100"),
        ("Competitors", f"{count:,}"),
        ("Density /km²", f"{density_per_km:.1f}"),
        ("Anchor Businesses", f"{anchor_total:,}"),
        ("Corporate Chains", f"{chain_count} ({indie_count} indie)"),
    ]
    col_w = 58
    x_start = 15
    for i, (label, value) in enumerate(metrics):
        col = i % 3
        row = i // 3
        x = x_start + col * (col_w + 4)
        y = 66 + row * 26
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        pdf.rect(x, y, col_w, 22, 'FD')
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(100, 116, 139)
        pdf.set_xy(x + 3, y + 3)
        pdf.cell(col_w - 6, 5, _pdf_safe(label.upper()), ln=True)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(15, 23, 42)
        pdf.set_xy(x + 3, y + 9)
        pdf.cell(col_w - 6, 8, _pdf_safe(value), ln=False)

    pdf.ln(2)
    pdf.set_xy(15, 122)

    # Recommendation
    pdf.set_fill_color(235, 245, 255)
    pdf.set_draw_color(191, 219, 254)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(15, 23, 42)
    h = len(rec) / 80 * 8 + 14
    pdf.rect(15, pdf.get_y(), 180, max(h, 16), 'FD')
    pdf.set_xy(18, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "Recommendation:", ln=True)
    pdf.set_xy(18, pdf.get_y())
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(174, 5, _pdf_safe(rec))
    pdf.ln(4)

    # Category gaps
    if len(gaps) > 0:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, "Category Gaps (Underserved Opportunities)", ln=True)
        for _, g in gaps.iterrows():
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(0, 6, _pdf_safe(f"  - {g['category']}: {int(g['raw_count'])} here vs Sydney avg {g['avg_count']:.0f}"), ln=True)
        pdf.ln(3)

    # Dominant player
    if dominant is not None:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, "Dominant Player", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(0, 6, _pdf_safe(f"  {dominant['name']} ({int(dominant['cnt'])} locations in {suburb})"), ln=True)
        pdf.ln(3)

    # Alternatives
    if len(alts) > 0:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 8, "Lower Competition Alternatives", ln=True)
        for _, r in alts.iterrows():
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(0, 6, _pdf_safe(f"  - {r['suburb']} (saturation score: {r['saturation_score']:.0f})"), ln=True)
        pdf.ln(3)

    # Footer
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 8, _pdf_safe("SuburbIQ - Powered by 311,266 Foursquare OS Places | Sydney, Australia"), align="C")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()

# ── HEADER ────────────────────────────────────────────────
st.markdown(f"""
<div class="siq-header">
    <div class="siq-logo">
        <img src="data:image/png;base64,{_LOGO_B64}"
             style="width:220px;height:auto;object-fit:contain;display:block;
                    background:transparent;border:none;box-shadow:none" />
    </div>
    <div class="siq-badge">311,266 Sydney POIs · Foursquare OS Places</div>
</div>
""", unsafe_allow_html=True)

suburbs = get_suburbs()
cats = get_categories()

tab1, tab2, tab3 = st.tabs(["  📍  Single suburb  ", "  ⚖️  Compare suburbs  ", "  ❓  Help & FAQ  "])

# ══════════════════════════════════════════════════════════
# TAB 1
# ══════════════════════════════════════════════════════════
with tab1:
    with st.container():
        c1, c2, c3 = st.columns([3, 3, 1.5])
        with c1:
            suburb = st.selectbox("Suburb", suburbs,
                index=suburbs.index("Alexandria") if "Alexandria" in suburbs else 0, key="s1")
        with c2:
            suburb_cats = get_categories_for_suburb(suburb)
            default_cat = "Café" if "Café" in suburb_cats else (suburb_cats[0] if suburb_cats else None)
            category = st.selectbox("Business category", suburb_cats,
                index=suburb_cats.index(default_cat) if default_cat in suburb_cats else 0, key="c1")
        with c3:
            st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
            analyse = st.button("Analyse ▶", use_container_width=True, key="btn1")

    if analyse:
        st.session_state.update({"analysed": True, "suburb": suburb, "category": category})

    if not st.session_state.get("analysed"):
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📍</div>
            <div class="empty-title">Select a suburb and category to begin</div>
            <div class="empty-sub">SuburbIQ analyses 311,000+ Sydney POIs to score your location</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        s = st.session_state["suburb"]
        c = st.session_state["category"]

        with st.spinner(f"Analysing {s} for {c}..."):
            stats, pois, anchors, top_cats = query(s, c)
            gaps = get_gaps(s)
            dominant = get_dominant(s, c)
            alts = get_alternatives(s, c)
            classified_pois, chain_count, indie_count = classify_competitors(s, c)

        if len(stats) == 0:
            st.warning(f"No data for **{c}** in **{s}**. Try a different combination.")
            st.stop()

        row = stats.iloc[0]
        score = float(row["saturation_score"])
        count = int(row["raw_count"])
        area  = round(float(row["area_sqkm"]), 2)
        anchor_total = int(anchors["raw_count"].sum()) if len(anchors) > 0 else 0
        density_per_km = round(count / max(area, 0.1), 1)
        opp_score = max(0, min(100, round((1 - score/100) * 60 + min(anchor_total/15, 1) * 25 + min(len(gaps)/5, 1) * 15)))
        sc, sbg, comp_label, comp_detail, fc, foot_label, foot_detail, rec = \
            verdict_data(score, count, s, c, anchor_total)
        corp_pct = round(chain_count / max(count, 1) * 100)

        # ── Hero title ────────────────────────────────────
        st.markdown(f"""
        <div style='font-size:1.1rem;font-weight:800;color:#0f172a;
                    margin:0.5rem 0 1rem;letter-spacing:-0.01em'>
            {s} <span style='color:#94a3b8;font-weight:400'>—</span> {c}
        </div>
        """, unsafe_allow_html=True)

        # ── 5 Hero metrics ────────────────────────────────
        opp_color, _ = score_color(100 - opp_score)
        st.markdown(f"""
        <div class="scoreboard-wrap">
          <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:0.75rem">
            <div style="background:white;border:2px solid rgba(29,78,216,0.5);border-radius:14px;
                        padding:1rem 1.2rem;box-shadow:0 2px 12px rgba(29,78,216,0.12)">
              <div style="color:#64748b;font-size:0.72rem;font-weight:600;text-transform:uppercase;
                          letter-spacing:0.08em;margin-bottom:4px">⚡ Opportunity</div>
              <div style="color:#0f172a;font-size:1.75rem;font-weight:800;line-height:1">{opp_score}/100</div>
            </div>
            <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;
                        padding:1rem 1.2rem;box-shadow:0 2px 8px rgba(0,0,0,0.06)">
              <div style="color:#64748b;font-size:0.72rem;font-weight:600;text-transform:uppercase;
                          letter-spacing:0.08em;margin-bottom:4px">🎯 Saturation</div>
              <div style="color:#0f172a;font-size:1.75rem;font-weight:800;line-height:1">{score}/100</div>
            </div>
            <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;
                        padding:1rem 1.2rem;box-shadow:0 2px 8px rgba(0,0,0,0.06)">
              <div style="color:#64748b;font-size:0.72rem;font-weight:600;text-transform:uppercase;
                          letter-spacing:0.08em;margin-bottom:4px">🏢 Competitors</div>
              <div style="color:#0f172a;font-size:1.75rem;font-weight:800;line-height:1">{count:,}</div>
            </div>
            <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;
                        padding:1rem 1.2rem;box-shadow:0 2px 8px rgba(0,0,0,0.06)">
              <div style="color:#64748b;font-size:0.72rem;font-weight:600;text-transform:uppercase;
                          letter-spacing:0.08em;margin-bottom:4px">📐 Density /km²</div>
              <div style="color:#0f172a;font-size:1.75rem;font-weight:800;line-height:1">{density_per_km:.1f}</div>
            </div>
            <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;
                        padding:1rem 1.2rem;box-shadow:0 2px 8px rgba(0,0,0,0.06)">
              <div style="color:#64748b;font-size:0.72rem;font-weight:600;text-transform:uppercase;
                          letter-spacing:0.08em;margin-bottom:4px">⚓ Anchors</div>
              <div style="color:#0f172a;font-size:1.75rem;font-weight:800;line-height:1">{anchor_total:,}</div>
            </div>
          </div>
          <div style="font-size:0.7rem;color:#94a3b8;margin-top:0.5rem;font-style:italic">
            Opportunity = low saturation (60%) + anchor strength (25%) + category gaps (15%)
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Saturation bar ────────────────────────────────
        st.markdown(f"""
        <div class='score-bar-wrap' style='margin:0.2rem 0 0.6rem'>
            <div class='score-bar-fill' style='width:{score}%;background:{sc}'></div>
        </div>
        """, unsafe_allow_html=True)

        # ── Chain vs. Independent callout ─────────────────
        if count > 0:
            chain_color = "#ef4444" if corp_pct >= 50 else "#f59e0b" if corp_pct >= 25 else "#10b981"
            st.markdown(f"""
            <div style='background:white;border:1px solid #e2e8f0;border-radius:12px;
                        padding:0.75rem 1.2rem;margin-bottom:0.8rem;
                        display:flex;align-items:center;gap:16px;
                        box-shadow:0 1px 4px rgba(0,0,0,0.05)'>
                <div style='font-size:0.75rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:0.08em;color:#94a3b8;flex-shrink:0'>Corporate dominance</div>
                <div style='flex:1;height:6px;background:#f1f5f9;border-radius:3px;overflow:hidden'>
                    <div style='height:6px;background:{chain_color};border-radius:3px;width:{corp_pct}%'></div>
                </div>
                <div style='font-size:0.85rem;font-weight:700;color:{chain_color};flex-shrink:0'>
                    {chain_count} chains ({corp_pct}%)
                </div>
                <div style='font-size:0.82rem;color:#64748b;flex-shrink:0'>
                    vs {indie_count} independents
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── AI Chat Co-Pilot (full-width, immediately below metrics) ──
        top_gap = gaps.iloc[0]["category"] if len(gaps) > 0 else "None identified"
        dominant_name = dominant['name'] if dominant is not None else "No clear dominant player"

        system_ctx = f"""You are a senior commercial real estate analyst embedded in SuburbIQ, \
a franchise site intelligence platform. You are advising on opening a {c} in {s}, Sydney, Australia.

Current dashboard data:
- Saturation score: {score}/100 (higher = more crowded)
- Opportunity score: {opp_score}/100 (higher = better)
- Competitor count: {count} {c.lower()} locations
- Anchor businesses nearby: {anchor_total}
- Density: {density_per_km:.1f} per km²
- Corporate chains: {chain_count} ({corp_pct}%), Independents: {indie_count}
- Top underserved category gap: {top_gap}
- Dominant player: {dominant_name}

Be direct, data-driven, and concise. Reference specific numbers when relevant. No generic advice."""

        msgs_key = f"chat_msgs_{s}_{c}"
        if msgs_key not in st.session_state:
            st.session_state[msgs_key] = []

        st.markdown("""
        <div style='font-size:0.7rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.1em;color:#94a3b8;margin-bottom:0.4rem'>
            ✨ AI Analyst — Ask anything about this market
        </div>
        """, unsafe_allow_html=True)

        chat_window = st.container(height=380, border=True)
        with chat_window:
            if not st.session_state[msgs_key]:
                st.markdown("""
                <div style='text-align:center;padding:3rem 1rem;color:#94a3b8'>
                    <div style='font-size:2.2rem;margin-bottom:0.5rem'>🤖</div>
                    <div style='font-size:0.9rem;font-weight:600;color:#475569'>
                        Ask me about this market
                    </div>
                    <div style='font-size:0.8rem;margin-top:0.4rem'>
                        Try: "Should I open here?" · "What's the biggest risk?" · "Who is the competition?"
                    </div>
                </div>
                """, unsafe_allow_html=True)
            for msg in st.session_state[msgs_key]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if user_input := st.chat_input(
            "Ask the AI Analyst about this suburb...", key=f"ci_{s}_{c}"
        ):
            st.session_state[msgs_key].append({"role": "user", "content": user_input})
            with chat_window:
                with st.chat_message("user"):
                    st.markdown(user_input)
                with st.chat_message("assistant"):
                    response_text = st.write_stream(
                        _chat_stream(
                            st.session_state[msgs_key][:-1],
                            user_input,
                            system_ctx
                        )
                    )
            st.session_state[msgs_key].append(
                {"role": "assistant", "content": response_text}
            )
            st.rerun()

        # ── 4 Verdict cards ───────────────────────────────
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        verdict_cols = st.columns(4)
        verdict_items = [
            (sc, comp_label, comp_detail),
            (fc, foot_label, foot_detail),
            ("#4f46e5", "Density", f"{density_per_km} {c.lower()} per km² · Sydney avg ~8.0"),
            ("#8b5cf6", "Dominant player",
             f"{dominant['name']} ({int(dominant['cnt'])} locations)" if dominant is not None else "<span style='color:#10b981;font-weight:600'>Market fragmented</span> — high opportunity for brand entry"),
        ]
        for col, (color, label, detail) in zip(verdict_cols, verdict_items):
            with col:
                st.markdown(f"""
                <div style='background:white;border:1px solid #e2e8f0;border-radius:14px;
                            padding:1rem 1.1rem;min-height:95px;
                            box-shadow:0 2px 8px rgba(0,0,0,0.05)'>
                    <div style='display:flex;align-items:center;gap:8px;margin-bottom:6px'>
                        <div style='width:8px;height:8px;border-radius:50%;background:{color};flex-shrink:0'></div>
                        <span style='font-weight:700;color:#0f172a;font-size:0.85rem'>{label}</span>
                    </div>
                    <div style='color:#64748b;font-size:0.8rem;line-height:1.4'>{detail}</div>
                </div>
                """, unsafe_allow_html=True)

        # ── Recommendation banner ─────────────────────────
        st.markdown(f"""
        <div style='background:rgba(29,78,216,0.88);border-radius:12px;padding:0.9rem 1.2rem;
                    color:white;font-weight:600;font-size:0.9rem;margin:0.8rem 0'>
            💡 {rec}
        </div>
        """, unsafe_allow_html=True)

        # ── Alternatives ──────────────────────────────────
        if len(alts) > 0:
            alt_sc_colors = [score_color(float(r['saturation_score']))[0] for _, r in alts.iterrows()]
            alt_cards_html = "".join([
                f"""<div class='alt-card'>
                    <span style='font-weight:600;color:#0f172a;font-size:0.88rem'>{r['suburb']}</span>
                    <span style='background:{sc};color:white;border-radius:20px;
                                 padding:3px 10px;font-size:0.75rem;font-weight:700'>
                        {r['saturation_score']:.0f}/100
                    </span>
                </div>"""
                for (_, r), sc in zip(alts.iterrows(), alt_sc_colors)
            ])
            st.markdown(f"""
            <div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:14px;
                        padding:0.9rem 1.1rem;margin-bottom:0.8rem'>
                <div style='font-size:0.7rem;font-weight:700;text-transform:uppercase;
                            letter-spacing:0.1em;color:#3b82f6;margin-bottom:0.55rem'>
                    🔍 Lower competition suburbs for {c}
                </div>
                {alt_cards_html}
            </div>
            """, unsafe_allow_html=True)

        # ── Map + Right panel ─────────────────────────────
        map_col, right_col = st.columns([5, 2])

        with map_col:
            st.markdown("<h4 style='margin:0;padding:0;font-size:0.7rem;font-weight:700;"
                        "text-transform:uppercase;letter-spacing:0.1em;color:#94a3b8'>"
                        "COMPETITOR MAP</h4>",
                        unsafe_allow_html=True)
            map_view = st.radio(
                "map_view", ["📍 Competitors", "🔥 Density heatmap", "🏢 Chain vs. Independent"],
                horizontal=True, key="map_view", label_visibility="collapsed"
            )
            if map_view == "📍 Competitors":
                st_folium(make_map(pois), width=None, height=700, key="map1", returned_objects=[])
            elif map_view == "🔥 Density heatmap":
                st_folium(make_heatmap_map(pois), width=None, height=700, key="map2", returned_objects=[])
                st.caption("Heatmap shows competitor density — red = high concentration, green = sparse")
            else:
                st_folium(make_map(pois, classified=classified_pois),
                          width=None, height=700, key="map3", returned_objects=[])
                st.markdown(
                    "<span style='display:inline-block;width:10px;height:10px;border-radius:50%;"
                    "background:#dc2626;margin-right:5px'></span>"
                    "<span style='font-size:0.82rem;color:#64748b;margin-right:16px'>Chain (3+ suburbs)</span>"
                    "<span style='display:inline-block;width:10px;height:10px;border-radius:50%;"
                    "background:#10b981;margin-right:5px'></span>"
                    "<span style='font-size:0.82rem;color:#64748b'>Independent</span>",
                    unsafe_allow_html=True)

        with right_col:
            st.markdown("<div style='height:125px'></div>"
                        "<h4 style='margin:0 0 6px 20px;padding:0;font-size:0.7rem;font-weight:700;"
                        "text-transform:uppercase;letter-spacing:0.1em;color:#94a3b8'>"
                        "CATEGORY GAPS</h4>",
                        unsafe_allow_html=True)
            if len(gaps) > 0:
                for _, g in gaps.iterrows():
                    bar_width = min(int((g['gap'] / gaps['gap'].max()) * 100), 100)
                    st.markdown(f"""
                    <div style='background:white;border:1px solid #e2e8f0;border-radius:10px;
                                padding:0.6rem 0.9rem;margin:0 0 6px 20px;
                                box-shadow:0 1px 3px rgba(0,0,0,0.04)'>
                        <div style='display:flex;justify-content:space-between;align-items:center'>
                            <span style='font-weight:600;color:#0f172a;font-size:0.85rem'>{g['category']}</span>
                            <span style='background:#f0fdf4;color:#166534;border-radius:6px;
                                        padding:2px 8px;font-size:0.75rem;font-weight:600'>
                                {int(g['raw_count'])} here · avg {g['avg_count']:.0f}
                            </span>
                        </div>
                        <div style='height:4px;background:#f1f5f9;border-radius:2px;margin-top:6px'>
                            <div style='height:4px;background:#10b981;border-radius:2px;width:{bar_width}%'></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
                            padding:0.8rem 1rem;text-align:center'>
                    <div style='font-size:1.2rem;margin-bottom:4px'>✅</div>
                    <div style='font-weight:600;color:#166534;font-size:0.82rem'>Niche market</div>
                    <div style='color:#4ade80;font-size:0.75rem;margin-top:2px'>Insufficient data for gap analysis</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            # Anchor businesses
            st.markdown("<h4 style='margin:0 0 6px 20px;padding:0;font-size:0.7rem;font-weight:700;"
                        "text-transform:uppercase;letter-spacing:0.1em;color:#94a3b8'>"
                        "ANCHOR BUSINESSES</h4>",
                        unsafe_allow_html=True)
            if len(anchors) > 0:
                rows_html = "".join([
                    f"<div style='display:flex;justify-content:space-between;align-items:center;"
                    f"padding:0.45rem 0;border-bottom:1px solid #f8fafc'>"
                    f"<span style='color:#1e293b;font-weight:500;font-size:0.87rem'>{a['category']}</span>"
                    f"<span style='background:#eff6ff;color:#4f46e5;border-radius:6px;"
                    f"padding:2px 10px;font-size:0.78rem;font-weight:700'>{int(a['raw_count'])}</span>"
                    f"</div>"
                    for _, a in anchors.iterrows()
                ])
                st.markdown(
                    f"<div style='background:white;border:1px solid #e2e8f0;border-radius:12px;"
                    f"padding:0.3rem 0.8rem;margin-left:20px'>{rows_html}</div>",
                    unsafe_allow_html=True
                )

        # ── Top categories bar chart ───────────────────────
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.7rem;font-weight:700;text-transform:uppercase;"
                    "letter-spacing:0.1em;color:#94a3b8;margin-bottom:6px'>Top categories in suburb</p>",
                    unsafe_allow_html=True)
        if len(top_cats) > 0:
            fig = go.Figure(go.Bar(
                x=top_cats["raw_count"], y=top_cats["category"],
                orientation="h",
                marker_color="#3B82F6",
                marker_line_width=0,
                text=top_cats["raw_count"], textposition="outside",
                textfont=dict(color="#1e293b", size=11)
            ))
            fig.update_layout(
                margin=dict(l=0, r=40, t=0, b=0),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                height=220,
                font=dict(family="Inter", color="#1e293b", size=11),
                xaxis=dict(showgrid=True, gridcolor="rgba(241,245,249,0.8)", zeroline=False,
                           tickfont=dict(color="#64748b", size=10)),
                yaxis=dict(showgrid=False, tickfont=dict(color="#1e293b", size=11))
            )
            st.plotly_chart(fig, use_container_width=True, config=CHART_CFG)

        # ── PDF Export ────────────────────────────────────
        st.markdown("<hr style='border-color:#e2e8f0;margin:1.2rem 0'>", unsafe_allow_html=True)
        _, exp_col, _ = st.columns([2, 2, 2])
        with exp_col:
            pdf_bytes = generate_pdf(
                s, c, score, count, anchor_total, density_per_km, opp_score,
                chain_count, indie_count, gaps, dominant, rec, alts
            )
            st.download_button(
                label="📄 Export PDF Report",
                data=pdf_bytes,
                file_name=f"SuburbIQ_{s.replace(' ','_')}_{c.replace(' ','_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="pdf_dl"
            )

        st.markdown("""
        <div class="siq-footer">
            Data Source: Foursquare Open Source Places (Refreshed April 2026)
            &nbsp;·&nbsp; Geospatial Processing: USYD Suburb Boundaries 2021
            &nbsp;·&nbsp; 311,266 Sydney POIs
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB 2
# ══════════════════════════════════════════════════════════
with tab2:
    ci1, ci2, ci3 = st.columns([3, 3, 2])
    with ci1:
        suburb_a = st.selectbox("Suburb A", suburbs,
            index=suburbs.index("Alexandria") if "Alexandria" in suburbs else 0, key="sa")
    with ci2:
        suburb_b = st.selectbox("Suburb B", suburbs,
            index=suburbs.index("Parramatta") if "Parramatta" in suburbs else 1, key="sb")
    with ci3:
        cat_cmp = st.selectbox("Category", cats,
            index=cats.index("Café") if "Café" in cats else 0, key="cc")

    if st.button("Compare suburbs ▶", use_container_width=True, key="btn2"):
        st.session_state.update({"compared": True, "cmp_a": suburb_a, "cmp_b": suburb_b, "cmp_cat": cat_cmp})

    if not st.session_state.get("compared") or "cmp_a" not in st.session_state:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">⚖️</div>
            <div class="empty-title">Compare two suburbs head to head</div>
            <div class="empty-sub">Find the better opportunity before committing to a lease</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        sa = st.session_state.get("cmp_a", suburb_a)
        sb = st.session_state.get("cmp_b", suburb_b)
        cc = st.session_state.get("cmp_cat", cat_cmp)

        with st.spinner("Comparing..."):
            stats_a, pois_a, anchors_a, _ = query(sa, cc)
            stats_b, pois_b, anchors_b, _ = query(sb, cc)

        if len(stats_a) == 0 or len(stats_b) == 0:
            st.warning("No data for one or both suburbs. Try different selections.")
            st.stop()

        ra, rb = stats_a.iloc[0], stats_b.iloc[0]
        score_a, score_b = float(ra["saturation_score"]), float(rb["saturation_score"])
        count_a, count_b = int(ra["raw_count"]), int(rb["raw_count"])
        area_a, area_b = round(float(ra["area_sqkm"]), 2), round(float(rb["area_sqkm"]), 2)
        anch_a = int(anchors_a["raw_count"].sum()) if len(anchors_a) > 0 else 0
        anch_b = int(anchors_b["raw_count"].sum()) if len(anchors_b) > 0 else 0
        sca, _ = score_color(score_a)
        scb, _ = score_color(score_b)
        a_wins, b_wins = score_a < score_b, score_b < score_a

        col_a, col_vs, col_b = st.columns([10, 1, 10])

        def render_side(sub, score, count, area, anch, wins, loses, sc):
            badge = "winner-box" if wins else ("loser-box" if loses else "tie-box")
            badge_text = "✅ Better opportunity" if wins else ("🔴 Higher competition" if loses else "🟡 Equal")
            st.markdown(f"<div style='font-size:1.1rem;font-weight:800;color:#0f172a;margin-bottom:0.8rem'>{sub}</div>",
                        unsafe_allow_html=True)
            m1, m2 = st.columns(2)
            m1.metric("Saturation", f"{score}/100")
            m2.metric("Competitors", f"{count:,}")
            m3, m4 = st.columns(2)
            m3.metric("Area", f"{area} km²")
            m4.metric("Anchors", f"{anch:,}")
            st.markdown(f"""
            <div class='score-bar-wrap'>
                <div class='score-bar-fill' style='width:{score}%;background:{sc}'></div>
            </div>
            <div class='{badge}' style='margin-top:0.7rem'>{badge_text}</div>
            """, unsafe_allow_html=True)

        with col_a:
            render_side(sa, score_a, count_a, area_a, anch_a, a_wins, b_wins, sca)
        with col_vs:
            st.markdown("<div style='text-align:center;padding-top:4rem;font-size:1.2rem;"
                        "font-weight:700;color:#cbd5e1'>vs</div>", unsafe_allow_html=True)
        with col_b:
            render_side(sb, score_b, count_b, area_b, anch_b, b_wins, a_wins, scb)

        if a_wins:
            w, reason = sa, f"lower saturation ({score_a} vs {score_b}) with {count_a:,} vs {count_b:,} competitors"
        elif b_wins:
            w, reason = sb, f"lower saturation ({score_b} vs {score_a}) with {count_b:,} vs {count_a:,} competitors"
        else:
            w, reason = None, "identical saturation — differentiate based on anchors and foot traffic"

        st.markdown(f"""
        <div class='rec-banner' style='margin:1rem 0'>
            💡 {'Recommendation: Open in <b>' + w + '</b> — ' + reason if w else 'Both suburbs are equally competitive — ' + reason}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='siq-label' style='margin-top:1rem'>Side-by-side competitor maps</div>",
                    unsafe_allow_html=True)
        map_a_col, map_b_col = st.columns(2)
        with map_a_col:
            st.caption(f"{sa} — {count_a:,} competitors")
            st_folium(make_map(pois_a), width=None, height=320, key="cmap_a", returned_objects=[])
        with map_b_col:
            st.caption(f"{sb} — {count_b:,} competitors")
            st_folium(make_map(pois_b), width=None, height=320, key="cmap_b", returned_objects=[])

        st.markdown("<div class='siq-label' style='margin-top:1rem'>Score comparison</div>",
                    unsafe_allow_html=True)
        ch1, ch2 = st.columns(2)

        with ch1:
            fig1 = go.Figure()
            fig1.add_bar(x=[sa], y=[score_a], marker_color=sca, text=[f"{score_a}"],
                         textposition="outside", width=0.4, textfont=dict(color="#1e293b"))
            fig1.add_bar(x=[sb], y=[score_b], marker_color=scb, text=[f"{score_b}"],
                         textposition="outside", width=0.4, textfont=dict(color="#1e293b"))
            fig1.update_layout(
                title=dict(text="Saturation score", font=dict(size=12, color="#64748b")),
                showlegend=False, height=240, barmode="group",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=30, b=0),
                yaxis=dict(range=[0, 115], showgrid=True, gridcolor="rgba(241,245,249,0.8)",
                           tickfont=dict(color="#64748b", size=11)),
                xaxis=dict(tickfont=dict(color="#1e293b", size=11)),
                font=dict(family="Inter", color="#1e293b", size=12)
            )
            st.plotly_chart(fig1, use_container_width=True, config=CHART_CFG)

        with ch2:
            fig2 = go.Figure()
            fig2.add_bar(x=[sa], y=[count_a], marker_color=sca, text=[f"{count_a:,}"],
                         textposition="outside", width=0.4, textfont=dict(color="#1e293b"))
            fig2.add_bar(x=[sb], y=[count_b], marker_color=scb, text=[f"{count_b:,}"],
                         textposition="outside", width=0.4, textfont=dict(color="#1e293b"))
            fig2.update_layout(
                title=dict(text="Competitor count", font=dict(size=12, color="#64748b")),
                showlegend=False, height=240, barmode="group",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=30, b=0),
                yaxis=dict(showgrid=True, gridcolor="rgba(241,245,249,0.8)",
                           tickfont=dict(color="#64748b", size=11)),
                xaxis=dict(tickfont=dict(color="#1e293b", size=11)),
                font=dict(family="Inter", color="#1e293b", size=12)
            )
            st.plotly_chart(fig2, use_container_width=True, config=CHART_CFG)

        st.markdown("""
        <div class="siq-footer">
            Data Source: Foursquare Open Source Places (Refreshed April 2026)
            &nbsp;·&nbsp; Geospatial Processing: USYD Suburb Boundaries 2021
            &nbsp;·&nbsp; 311,266 Sydney POIs
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB 3 — HELP & FAQ
# ══════════════════════════════════════════════════════════
with tab3:
    def faq_card(icon, title, body):
        st.markdown(f"""
        <div style='background:white;border:1px solid #e2e8f0;border-radius:16px;
                    padding:1.3rem 1.5rem;margin-bottom:0.9rem;
                    box-shadow:0 1px 3px rgba(0,0,0,0.07),0 4px 12px rgba(0,0,0,0.04)'>
            <div style='display:flex;align-items:center;gap:10px;margin-bottom:0.55rem'>
                <span style='font-size:1.4rem'>{icon}</span>
                <span style='font-weight:700;color:#0f172a;font-size:0.97rem'>{title}</span>
            </div>
            <div style='color:#475569;font-size:0.87rem;line-height:1.65'>{body}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size:1.25rem;font-weight:800;color:#0f172a;margin-bottom:0.25rem'>
        How to use SuburbIQ
    </div>
    <div style='color:#64748b;font-size:0.88rem;margin-bottom:1.4rem'>
        Everything you need to interpret the data and make a confident site decision.
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("<p style='font-size:0.7rem;font-weight:700;text-transform:uppercase;"
                    "letter-spacing:0.1em;color:#94a3b8;margin-bottom:0.7rem'>Understanding the scores</p>",
                    unsafe_allow_html=True)

        faq_card("🎯", "Saturation Score (0 – 100)",
            "Measures how crowded a suburb is for your chosen business category, relative to Sydney's average. "
            "<br><br>"
            "<b style='color:#10b981'>0 – 39 → Green (Low)</b> — few competitors, strong entry signal.<br>"
            "<b style='color:#f59e0b'>40 – 74 → Amber (Moderate)</b> — viable but concept quality matters.<br>"
            "<b style='color:#ef4444'>75 – 100 → Red (High)</b> — crowded market, differentiation required.")

        faq_card("⚡", "Opportunity Score (0 – 100)",
            "A composite score combining three signals:<br><br>"
            "• <b>60%</b> — inverse of Saturation (lower saturation = higher opportunity)<br>"
            "• <b>25%</b> — Anchor business strength (gyms, supermarkets, offices nearby drive foot traffic)<br>"
            "• <b>15%</b> — Category gaps (how many underserved categories exist in the suburb)<br><br>"
            "A score above <b>65</b> is generally a strong greenfield signal.")

        faq_card("📐", "Density per km²",
            "The number of businesses in your chosen category divided by the suburb's land area. "
            "Use this to compare suburbs of different sizes fairly — a suburb with 10 cafés but only 0.5 km² "
            "is far more saturated than one with 10 cafés across 5 km².")

        faq_card("⚓", "Anchor Businesses",
            "Counts of high foot-traffic generators in the suburb: Gyms, Supermarkets, Train Stations, "
            "Shopping Malls, Offices, Universities, Hospitals, and Schools. "
            "A high anchor count means consistent demand — people are already visiting this area regularly.")

    with col_b:
        st.markdown("<p style='font-size:0.7rem;font-weight:700;text-transform:uppercase;"
                    "letter-spacing:0.1em;color:#94a3b8;margin-bottom:0.7rem'>Features & how to use them</p>",
                    unsafe_allow_html=True)

        faq_card("🗺️", "How to use the map views",
            "<b>📍 Competitors</b> — plots every existing business in your category as a dot. Clusters = high competition zones.<br><br>"
            "<b>🔥 Density heatmap</b> — red areas have the highest concentration; green areas are sparse and potentially underserved.<br><br>"
            "<b>🏢 Chain vs. Independent</b> — red dots are corporate chains (present in 3+ suburbs), green are independents. "
            "A suburb dominated by chains is harder to enter; indie-heavy areas often have pricing flexibility.")

        faq_card("🔍", "Category Gaps",
            "Shows business types that Sydney suburbs average more of than your selected suburb currently has. "
            "A gap means demand likely exists but supply hasn't caught up — this is where complementary or adjacent "
            "franchise concepts can win. The green bar shows how large the gap is relative to Sydney's average.")

        faq_card("⚖️", "Compare Suburbs tab",
            "Run a head-to-head comparison of two suburbs for the same category. "
            "The app scores both on Saturation and Competitor count and gives a clear recommendation on which "
            "suburb offers the better opportunity. Use this before committing to a lease negotiation.")

        faq_card("✨", "AI Analyst chatbox",
            "Powered by Llama 3.3 via Groq. The AI is automatically loaded with your suburb's live data — "
            "saturation, competitors, anchors, dominant players — before you type anything. "
            "Ask it direct questions like:<br><br>"
            "<i>\"Should I open here?\"</i><br>"
            "<i>\"What's my biggest risk?\"</i><br>"
            "<i>\"Who are my main competitors and how do I differentiate?\"</i>")

        faq_card("📄", "PDF Export",
            "Generates a one-page intelligence report with all scores, category gaps, dominant player, "
            "alternative suburbs, and the AI recommendation. Download and share with co-founders, "
            "investors, or landlords to back up your site selection decision with data.")

    st.markdown("""
    <div style='background:rgba(29,78,216,0.06);border:1px solid rgba(29,78,216,0.15);
                border-radius:14px;padding:1.1rem 1.4rem;margin-top:0.5rem'>
        <div style='font-weight:700;color:#1d4ed8;font-size:0.88rem;margin-bottom:0.35rem'>
            💡 Recommended workflow
        </div>
        <div style='color:#334155;font-size:0.85rem;line-height:1.7'>
            1. <b>Pick your suburb + category</b> and click Analyse ▶<br>
            2. <b>Read the Opportunity score</b> — anything above 65 is worth exploring<br>
            3. <b>Ask the AI</b> one question: <i>"Give me a Go/No-Go verdict in 3 sentences"</i><br>
            4. <b>Check the map</b> — identify where competitors cluster and where gaps exist<br>
            5. <b>Review Category Gaps</b> — consider whether an adjacent concept fits the gap<br>
            6. <b>Compare suburbs</b> if you have two shortlisted locations<br>
            7. <b>Export the PDF</b> and take it to your next investor or landlord meeting
        </div>
    </div>
    <div class="siq-footer">
        Data Source: Foursquare Open Source Places (Refreshed April 2026)
        &nbsp;·&nbsp; Geospatial Processing: USYD Suburb Boundaries 2021
        &nbsp;·&nbsp; 311,266 Sydney POIs
    </div>
    """, unsafe_allow_html=True)
