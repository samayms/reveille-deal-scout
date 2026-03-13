import html as _html
import re
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from database import fetch_leads, update_status
from main import run_pipeline

STATUS_OPTIONS = ["New", "Reviewing", "Pass"]
SIDEBAR_QUERY_KEY = "sidebar"
VALID_SIDEBAR_STATES = {"expanded", "collapsed"}

_initial_sidebar_state = st.query_params.get(SIDEBAR_QUERY_KEY, "expanded")
if _initial_sidebar_state not in VALID_SIDEBAR_STATES:
    _initial_sidebar_state = "expanded"


st.set_page_config(
    page_title="Reveille · Deal Scout",
    layout="wide",
    initial_sidebar_state=_initial_sidebar_state,
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Syne:wght@500;600;700;800&family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600;1,700&family=IBM+Plex+Mono:wght@400;500;600&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

:root {
    --bg:           #07090d;
    --bg-card:      #0d1219;
    --bg-raised:    #121a27;
    --border:       #1e2840;
    --border-faint: #131c2c;
    --text:         #d4d9e8;
    --text-dim:     #8896aa;   /* was #5c677d — now readable */
    --text-muted:   #526070;   /* was #2d3548 — now readable */
    --amber:        #c98b0e;
    --amber-soft:   rgba(201,139,14,0.09);
    --amber-border: rgba(201,139,14,0.25);
    --teal:         #17b584;
    --teal-soft:    rgba(23,181,132,0.10);
    --teal-border:  rgba(23,181,132,0.25);
    --serif:        'Cormorant Garamond', Georgia, serif;
    --mono:         'IBM Plex Mono', monospace;
    --sans:         'DM Sans', sans-serif;
    --font-display: 'Bebas Neue', Impact, sans-serif;
}

/* ── Base ─────────────────────────────────────────────────────────────────── */
html, body {
    overflow: hidden !important;
    height: 100% !important;
}
.stApp {
    background: var(--bg) !important;
    font-family: var(--sans);
    color: var(--text);
    height: 100vh !important;
    overflow: hidden !important;
}
[data-testid="stAppViewContainer"] {
    height: 100vh !important;
    overflow-y: auto !important;
}

#MainMenu, footer, .stDeployButton { display: none !important; }

/* Header: fixed so it doesn't push content down; transparent so it's invisible */
[data-testid="stHeader"] {
    position: fixed !important;
    top: 0 !important; left: 0 !important; right: 0 !important;
    height: auto !important;
    background: transparent !important;
    border-bottom: none !important;
    box-shadow: none !important;
    z-index: 999 !important;
    pointer-events: none !important;
}
[data-testid="stDecoration"] { display: none !important; }

/* Hide toolbar action buttons and deploy */
[data-testid="stToolbarActions"],
[data-testid="stToolbarActionButton"],
[data-testid="stAppDeployButton"],
[data-testid="stMainMenuButton"] {
    display: none !important;
}

/* Sidebar expand button (correct testid in Streamlit 1.55) */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"] {
    pointer-events: all !important;
}
[data-testid="stExpandSidebarButton"] button,
[data-testid="stSidebarCollapseButton"] button {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 2px !important;
}
[data-testid="stExpandSidebarButton"] button:hover,
[data-testid="stSidebarCollapseButton"] button:hover {
    border-color: var(--amber-border) !important;
    color: var(--amber) !important;
    background: var(--amber-soft) !important;
}

/* Remove header gap — logo spacer and main block container are the sources */
[data-testid="stLogoSpacer"] { display: none !important; }

html body [data-testid="stMain"],
html body [data-testid="stMainBlockContainer"],
html body [data-testid="stAppViewContainer"],
html body section.main {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
html body .main .block-container {
    padding: 0 2.5rem 2rem !important;
    margin-top: 0 !important;
    max-width: 100% !important;
}
html body [data-testid="stMainBlockContainer"] {
    padding-top: 0.1rem !important;
}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #09090f !important;
    border-right: 1px solid var(--border) !important;
    overflow: hidden !important;
}
/* Hide content when sidebar is collapsed so text doesn't bleed through */
[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarUserContent"],
[data-testid="stSidebar"][aria-expanded="false"] > div {
    display: none !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 1.25rem 1.25rem !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 1.25rem !important;
}
[data-testid="stSidebar"] .element-container,
[data-testid="stSidebar"] .stMarkdown {
    margin-bottom: 0 !important;
    margin-top: 0 !important;
}

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    border-bottom: 1px solid var(--border) !important;
    background: transparent !important;
    padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-family: var(--mono) !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 14px 22px !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    margin: 0 !important;
    white-space: nowrap !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text) !important;
    background: rgba(255,255,255,0.015) !important;
}
.stTabs [aria-selected="true"] {
    color: var(--amber) !important;
    border-bottom: 2px solid var(--amber) !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.5rem !important;
}

/* ── Card click overlay ────────────────────────────────────────────────────── */
.rl-research-card { position: relative; }
.rl-card-overlay {
    position: absolute;
    inset: 0;
    z-index: 1;
    text-decoration: none !important;
    cursor: pointer;
}
/* Source links and other interactive elements sit above the overlay */
.rl-research-card a:not(.rl-card-overlay) {
    position: relative;
    z-index: 2;
}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-dim) !important;
    font-family: var(--mono) !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 10px 16px !important;
    border-radius: 1px !important;
    transition: all 0.1s !important;
}
.stButton > button:hover {
    border-color: var(--amber-border) !important;
    color: var(--amber) !important;
    background: var(--amber-soft) !important;
}

/* ── Metrics ──────────────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 1px !important;
    padding: 14px !important;
}
[data-testid="stMetricLabel"] p {
    font-family: var(--mono) !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--text-dim) !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--mono) !important;
    font-size: 22px !important;
    font-weight: 600 !important;
    color: var(--text) !important;
}

/* ── Headings ─────────────────────────────────────────────────────────────── */
h2, h3 {
    font-family: var(--serif) !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    letter-spacing: -0.01em !important;
}

/* ── Divider ──────────────────────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1rem 0 !important;
}

/* ── Info / Alert ─────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-left: 2px solid var(--text-muted) !important;
    border-radius: 0 1px 1px 0 !important;
    font-family: var(--sans) !important;
    font-size: 13px !important;
    line-height: 1.75 !important;
    color: var(--text-dim) !important;
}

/* ── Caption ──────────────────────────────────────────────────────────────── */
.stCaption p {
    font-family: var(--mono) !important;
    font-size: 12px !important;
    color: var(--text-dim) !important;
    letter-spacing: 0.05em !important;
}

/* ── Widget labels ────────────────────────────────────────────────────────── */
label[data-testid="stWidgetLabel"] p {
    font-family: var(--mono) !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--text-dim) !important;
}

/* ── Select inputs ────────────────────────────────────────────────────────── */
[data-baseweb="select"] > div:first-child {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
    border-radius: 1px !important;
    font-family: var(--mono) !important;
    font-size: 12px !important;
    color: var(--text) !important;
    min-height: 36px !important;
}
[data-baseweb="select"] svg { color: var(--text-muted) !important; }

/* ── Multiselect tags ─────────────────────────────────────────────────────── */
[data-baseweb="tag"] {
    background: var(--bg-raised) !important;
    border: 1px solid var(--border) !important;
    border-radius: 1px !important;
    color: var(--text-dim) !important;
}
[data-baseweb="tag"] span {
    color: var(--text-dim) !important;
    font-family: var(--mono) !important;
    font-size: 10px !important;
}
[data-baseweb="tag"] [role="presentation"] svg {
    color: var(--text-muted) !important;
}

/* ── Slider ───────────────────────────────────────────────────────────────── */
[data-testid="stSlider"] [role="slider"] {
    background: var(--amber) !important;
    border-color: var(--amber) !important;
}

/* ── Expander ─────────────────────────────────────────────────────────────── */
details[data-testid="stExpander"] summary {
    font-family: var(--serif) !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 1px !important;
    padding: 12px 16px !important;
}
details[data-testid="stExpander"] {
    border: none !important;
    background: transparent !important;
}

/* ── Status box ───────────────────────────────────────────────────────────── */
[data-testid="stStatusWidget"] {
    background: var(--bg-raised) !important;
    border: 1px solid var(--border) !important;
    border-radius: 2px !important;
    font-family: var(--mono) !important;
    font-size: 11px !important;
    color: var(--text-dim) !important;
}
[data-testid="stStatusWidget"] p {
    font-family: var(--mono) !important;
    font-size: 11px !important;
    color: var(--text-dim) !important;
}

/* ── Dataframe ────────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 1px !important;
    overflow: hidden !important;
}

/* ─────────────────────────────────────────────────────────────────────────────
   CUSTOM COMPONENTS
   ───────────────────────────────────────────────────────────────────────────── */

/* Sidebar brand */
.rl-brand {
    padding-bottom: 1.1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0;
}
.rl-brand-name {
    font-family: 'Syne', sans-serif;
    font-size: 68px;
    font-weight: 800;
    color: var(--amber);
    letter-spacing: -0.03em;
    line-height: 1.0;
    margin: 0 0 2px 0;
}
.rl-brand-sub {
    font-family: 'Syne', sans-serif;
    font-size: 24px;
    font-weight: 800;
    color: var(--amber);
    letter-spacing: -0.02em;
    margin: 0 0 10px 0;
}
.rl-brand-tagline {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 0;
}

/* Sidebar footer */
.rl-sidebar-footer {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--text-muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    line-height: 2;
    padding-top: 14px;
    border-top: 1px solid var(--border);
}

/* Section headers */
.rl-section-head {
    display: flex;
    align-items: baseline;
    gap: 16px;
    padding-bottom: 14px;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
}
.rl-section-title {
    font-family: var(--serif);
    font-size: 26px;
    font-weight: 700;
    font-style: italic;
    color: var(--text);
    letter-spacing: -0.01em;
    margin: 0;
}
.rl-section-sub {
    font-family: var(--mono);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-dim);
}

/* ── Source badges ────────────────────────────────────────────────────────── */
.rl-source-badge {
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 2px 6px;
    border: 1px solid var(--border);
    color: var(--text-muted);
}
.rl-source-badge-openalex { border-color: #2d4f7a; color: #5b8fd5; }
.rl-source-badge-nsf      { border-color: #1f5c35; color: #3da66e; }
.rl-source-badge-sbir     { border-color: #5c3a1f; color: #c97040; }

/* ── Score chips ──────────────────────────────────────────────────────────── */
.rl-chip {
    font-family: var(--font-display);
    font-size: 15px;
    line-height: 1.55;
    min-width: 28px;
    text-align: center;
    padding: 0 5px;
    border: 1px solid var(--teal-border);
    background: var(--teal-soft);
    color: var(--teal);
}
.rl-chip-mid {
    border-color: var(--amber-border);
    background: var(--amber-soft);
    color: var(--amber);
}
.rl-chip-low {
    border-color: var(--border);
    background: transparent;
    color: var(--text-muted);
}

/* ── Research cards (redesigned) ─────────────────────────────────────────── */
.rl-research-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-top: 2px solid var(--amber-border);
    padding: 16px 20px 14px;
    margin-bottom: 0;
    transition: background 0.12s;
    min-width: 0;
    cursor: pointer;
    position: relative;
    z-index: 1;
}
.rl-research-card.rl-rc-hi {
    border-top-color: var(--amber);
    background: linear-gradient(120deg, rgba(201,139,14,0.055) 0%, var(--bg-card) 55%);
}
.rl-research-card:hover { background: var(--bg-raised); }
.rl-research-card.rl-rc-hi:hover {
    background: linear-gradient(120deg, rgba(201,139,14,0.09) 0%, var(--bg-raised) 55%);
}
.rl-research-toprow {
    display: flex;
    align-items: center;
    gap: 6px 8px;
    margin-bottom: 10px;
    flex-wrap: nowrap;
    overflow: hidden;
}
.rl-rc-date {
    font-family: var(--mono);
    font-size: 12px;
    color: var(--text-dim);
    letter-spacing: 0.02em;
}
/* Status pill */
.rl-rc-status-pill {
    font-family: var(--mono);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 2px 8px;
    border-radius: 1px;
    white-space: nowrap;
    flex-shrink: 0;
}
.rl-rc-pill-new {
    background: rgba(100,160,210,0.07);
    border: 1px solid rgba(100,160,210,0.28);
    color: #7eb5d6;
}
.rl-rc-pill-reviewing {
    background: var(--amber-soft);
    border: 1px solid var(--amber-border);
    color: var(--amber);
}
.rl-rc-pill-pass {
    background: rgba(140,155,175,0.07);
    border: 1px solid rgba(140,155,175,0.3);
    color: #8d9db2;
}
.rl-research-authors {
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 2px;
}
.rl-research-institutions {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-muted);
    margin-bottom: 10px;
}
/* Title in warm amber — also used as an <a> for card navigation */
.rl-research-title {
    font-family: var(--serif);
    font-size: 19px;
    font-weight: 600;
    color: var(--amber) !important;
    line-height: 1.4;
    margin-bottom: 10px;
    letter-spacing: -0.01em;
    overflow-wrap: break-word;
    word-break: break-word;
    text-decoration: none !important;
    display: block;
    position: relative;
    z-index: 2;
}
.rl-research-title:link,
.rl-research-title:visited,
.rl-research-title:active,
.rl-research-title:hover {
    color: var(--amber) !important;
}
/* Abstract inset block */
.rl-rc-abstract {
    background: rgba(7,9,13,0.6);
    border: 1px solid var(--border-faint);
    border-left: 2px solid var(--border);
    padding: 9px 14px;
    margin-bottom: 10px;
}
.rl-rc-abstract-lbl {
    font-family: var(--mono);
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--text-muted);
    margin-bottom: 4px;
}
.rl-rc-abstract-txt {
    font-family: var(--sans);
    font-size: 12.5px;
    color: #6d7a92;
    line-height: 1.72;
}
/* Investment signal — amber left border */
.rl-rc-signal {
    border-left: 2px solid var(--amber);
    background: rgba(201,139,14,0.035);
    padding: 8px 12px;
    margin-bottom: 12px;
}
.rl-rc-signal-lbl {
    font-family: var(--mono);
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--amber);
    margin-bottom: 4px;
}
.rl-rc-signal-txt {
    font-family: var(--sans);
    font-size: 13px;
    color: var(--text-dim);
    line-height: 1.65;
}
/* Card footer: keywords left, meta right */
.rl-rc-footer2 {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding-top: 10px;
    border-top: 1px solid var(--border-faint);
    flex-wrap: wrap;
}
.rl-rc-footer-kw {
    flex: 1;
    min-width: 0;
}
.rl-rc-footer-kw.rl-rc-footer-kw-right {
    text-align: right;
    padding-top: 8px;
}
.rl-rc-footer-meta {
    text-align: right;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-muted);
    line-height: 1.5;
    flex-shrink: 0;
}
.rl-rc-footer-meta b { color: var(--text-dim); font-weight: 500; }

/* ── OpenAlex top-right block (venue + source link) ─────────────────────── */
.rl-rc-topright {
    margin-left: auto;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 5px;
    min-width: 0;
    max-width: 65%;
}
.rl-rc-topright-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: nowrap;
    min-width: 0;
    overflow: hidden;
}
.rl-rc-venue {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-dim);
    min-width: 0;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-style: italic;
}
/* ── Source link — unified across all card types ──────────────────────── */
.rl-src-link {
    font-family: var(--mono);
    font-size: 12px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-dim);
    text-decoration: none;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
    vertical-align: middle;
    transition: color 0.1s, border-color 0.1s;
    position: relative;
    top: -2px;
}
.rl-src-link::after {
    content: "↗";
    font-size: 20px;
    vertical-align: -1px;
    letter-spacing: 0;
}
.rl-src-link:hover { color: var(--amber); border-bottom-color: var(--amber); }

/* ── NSF/SBIR full-width meta strip footer ──────────────────────────────── */
.rl-rc-footer-nsf {
    padding-top: 10px;
    border-top: 1px solid var(--border-faint);
}
/* Meta strip: chips left, source link right, all in one horizontal band */
.rl-rc-meta-strip {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 5px 0;
    margin-bottom: 5px;
}
.rl-rc-meta-strip .rl-meta-grid {
    justify-content: flex-start;
    max-width: none;
    flex: 1;
    gap: 4px 10px;
}
.rl-rc-meta-strip.rl-rc-meta-strip-right {
    justify-content: flex-end;
    margin-bottom: 0;
}
.rl-rc-meta-strip.rl-rc-meta-strip-right .rl-meta-grid {
    justify-content: flex-end;
}

/* ── Meta grid items ────────────────────────────────────────────────────── */
.rl-meta-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 14px;
    justify-content: flex-start;
}
.rl-meta-item {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-muted);
    white-space: nowrap;
    padding: 2px 7px;
    background: rgba(255,255,255,0.025);
    border: 1px solid var(--border-faint);
}
.rl-meta-item b {
    color: var(--text-dim);
    font-weight: 500;
    margin-right: 4px;
}
.rl-kw-chip {
    display: inline-block;
    font-family: var(--mono);
    font-size: 9px;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    padding: 2px 5px;
    border: 1px solid var(--border);
    color: var(--text-muted);
    margin-right: 4px;
    margin-bottom: 4px;
}

/* ── Page header (DEAL SCOUT) ─────────────────────────────────────────────── */
.rl-page-header {
    display: flex;
    align-items: baseline;
    gap: 1.2rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.8rem;
    margin-bottom: 1.25rem;
}
.rl-page-wordmark {
    font-family: var(--font-display) !important;
    font-size: 1.6rem;
    letter-spacing: 0.22em;
    color: var(--amber);
}
.rl-page-tagline {
    font-family: var(--mono) !important;
    font-size: 10px;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    text-transform: uppercase;
}

@media (max-width: 1100px) {
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }
}

/* ── Lead Detail Page ─────────────────────────────────────────────────────── */
.rl-detail-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1.6rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
}
.rl-detail-date {
    font-family: var(--mono);
    font-size: 13px;
    color: var(--text-dim);
    margin-left: auto;
}
.rl-detail-title {
    font-family: var(--serif);
    font-size: 36px;
    font-weight: 700;
    font-style: italic;
    color: var(--text);
    line-height: 1.25;
    letter-spacing: -0.02em;
    margin: 0 0 1.1rem;
    overflow-wrap: break-word;
}
.rl-detail-byline {
    font-family: var(--mono);
    margin-bottom: 1.6rem;
    padding-bottom: 1.2rem;
    border-bottom: 1px solid var(--border-faint);
}
.rl-detail-authors {
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 5px;
    line-height: 1.5;
}
.rl-detail-inst {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.6;
}
.rl-detail-signal {
    border-left: 3px solid var(--amber);
    background: rgba(201,139,14,0.05);
    padding: 18px 22px;
    margin-bottom: 2rem;
}
.rl-detail-signal-lbl {
    font-family: var(--mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: var(--amber);
    margin-bottom: 10px;
}
.rl-detail-signal-txt {
    font-family: var(--sans);
    font-size: 15px;
    color: var(--text-dim);
    line-height: 1.85;
}
.rl-detail-sec-lbl {
    font-family: var(--mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: var(--text-muted);
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 16px;
    margin-top: 2rem;
}
.rl-detail-abstract {
    font-family: var(--sans);
    font-size: 14px;
    color: var(--text-dim);
    line-height: 1.9;
    margin-bottom: 0.5rem;
}
.rl-detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0 3.5rem;
}
.rl-detail-field {
    margin-bottom: 22px;
}
.rl-detail-field-lbl {
    font-family: var(--mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--text-muted);
    margin-bottom: 5px;
}
.rl-detail-field-val {
    font-family: var(--sans);
    font-size: 14px;
    color: var(--text);
    line-height: 1.55;
    overflow-wrap: break-word;
}
.rl-detail-field-val a {
    color: var(--amber);
    text-decoration: none;
    border-bottom: 1px solid var(--amber-border);
    padding-bottom: 1px;
    transition: border-color 0.1s;
}
.rl-detail-field-val a:hover { border-bottom-color: var(--amber); }
.rl-detail-award-val {
    font-family: var(--font-display);
    font-size: 34px;
    color: var(--teal);
    letter-spacing: 0.03em;
    line-height: 1.2;
}
.rl-detail-kw {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.rl-detail-kw-chip {
    font-family: var(--mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 4px 9px;
    border: 1px solid var(--border);
    color: var(--text-muted);
}
</style>
""", unsafe_allow_html=True)


# ── Persist sidebar collapse / expand state ─────────────────────────────────
components.html("""
<script>
(function () {
  const parentWindow = window.parent;
  const doc = parentWindow.document;
  const STORAGE_KEY = "reveille.sidebar.state";
  const QUERY_KEY = "sidebar";
  const VALID = new Set(["expanded", "collapsed"]);

  function getSidebar() {
    return doc.querySelector('[data-testid="stSidebar"], section[data-testid="stSidebar"]');
  }

  function readUrlState() {
    try {
      const url = new URL(parentWindow.location.href);
      const value = url.searchParams.get(QUERY_KEY);
      return VALID.has(value) ? value : null;
    } catch (e) {
      return null;
    }
  }

  function readStoredState() {
    try {
      const value = parentWindow.localStorage.getItem(STORAGE_KEY);
      return VALID.has(value) ? value : null;
    } catch (e) {
      return null;
    }
  }

  function getCurrentState() {
    const sidebar = getSidebar();
    if (!sidebar) return null;
    return sidebar.getAttribute("aria-expanded") === "false" ? "collapsed" : "expanded";
  }

  function writeState(state) {
    if (!VALID.has(state)) return;
    try {
      parentWindow.localStorage.setItem(STORAGE_KEY, state);
    } catch (e) {}

    try {
      const url = new URL(parentWindow.location.href);
      if (url.searchParams.get(QUERY_KEY) !== state) {
        url.searchParams.set(QUERY_KEY, state);
        parentWindow.history.replaceState({}, "", url.toString());
      }
    } catch (e) {}

    if (doc.body) {
      doc.body.dataset.rlSidebarState = state;
    }
  }

  function desiredState() {
    return readUrlState() || readStoredState() || "expanded";
  }

  function applyDesiredState() {
    const sidebar = getSidebar();
    if (!sidebar) return;

    const current = getCurrentState();
    const desired = desiredState();

    if (current === desired) {
      writeState(current);
      return;
    }

    const selector = desired === "collapsed"
      ? '[data-testid="stSidebarCollapseButton"] button'
      : '[data-testid="stExpandSidebarButton"] button';
    const button = doc.querySelector(selector);
    if (!button) return;

    button.click();
    setTimeout(() => {
      const next = getCurrentState();
      if (next) writeState(next);
    }, 0);
  }

  function bindSidebarPersistence() {
    if (doc.body?.dataset.rlSidebarPersistenceBound === "1") return;
    if (doc.body) doc.body.dataset.rlSidebarPersistenceBound = "1";

    const observer = new MutationObserver(() => {
      const current = getCurrentState();
      if (current) writeState(current);
    });
    observer.observe(doc.body, {
      attributes: true,
      attributeFilter: ["aria-expanded"],
      childList: true,
      subtree: true,
    });
  }

  applyDesiredState();
  bindSidebarPersistence();

  let attempts = 0;
  const interval = setInterval(() => {
    applyDesiredState();
    if (++attempts >= 13) clearInterval(interval);
  }, 150);

  const hydrationObserver = new MutationObserver(() => applyDesiredState());
  hydrationObserver.observe(doc.body, { childList: true, subtree: true });

  setTimeout(() => {
    hydrationObserver.disconnect();
    clearInterval(interval);
  }, 2000);
})();

</script>
""", height=0)

# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner="Fetching leads…")
def load_all():
    return fetch_leads()


def section_header(title, sub=""):
    sub_html = f'<span class="rl-section-sub">{sub}</span>' if sub else ""
    return f"""
    <div class="rl-section-head">
        <h2 class="rl-section-title">{title}</h2>
        {sub_html}
    </div>
    """


def coerce_str(val) -> str:
    if not val:
        return ""
    if isinstance(val, list):
        return ", ".join(str(v) for v in val if v)
    return str(val)


def coerce_list(val) -> list:
    if not val:
        return []
    if isinstance(val, list):
        return val
    return [v.strip() for v in str(val).split(",") if v.strip()]


def score_chip_cls(score) -> str:
    s = score or 0
    if s >= 7:
        return "rl-chip"
    if s >= 5:
        return "rl-chip rl-chip-mid"
    return "rl-chip rl-chip-low"


def source_badge(source: str) -> str:
    s = (source or "").lower()
    if "openalex" in s:
        return '<span class="rl-source-badge rl-source-badge-openalex">OpenAlex</span>'
    if "nsf" in s:
        return '<span class="rl-source-badge rl-source-badge-nsf">NSF</span>'
    if "sbir" in s:
        return '<span class="rl-source-badge rl-source-badge-sbir">SBIR.gov</span>'
    return f'<span class="rl-source-badge">{source or "Unknown"}</span>'


def safe_status(val) -> str:
    return val if val in STATUS_OPTIONS else "New"


def sync_status_widget_state(widget_key: str, current_status: str) -> None:
    db_state_key = f"__db_status__{widget_key}"
    widget_value = st.session_state.get(widget_key)
    previous_db_status = st.session_state.get(db_state_key)

    pending_user_change = (
        widget_key in st.session_state
        and widget_value in STATUS_OPTIONS
        and previous_db_status in STATUS_OPTIONS
        and widget_value != previous_db_status
    )

    if not pending_user_change and widget_value != current_status:
        st.session_state[widget_key] = current_status

    st.session_state[db_state_key] = current_status


def _e(s) -> str:
    return _html.escape(str(s)) if s else ""


def clean_text_field(val) -> str:
    if not val:
        return ""
    s = val if isinstance(val, str) else str(val)
    s = _html.unescape(s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _status_pill_cls(status: str) -> str:
    lower = (status or "").lower()
    if lower == "reviewing":
        return "rl-rc-pill-reviewing"
    if lower == "pass":
        return "rl-rc-pill-pass"
    return "rl-rc-pill-new"


def _fmt_amt(val) -> str:
    try:
        return f"${int(float(str(val))):,}"
    except (ValueError, TypeError):
        return str(val or "")


def _fmt_phone(val) -> str:
    raw = coerce_str(val)
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return raw


def _tel_href(val) -> str:
    raw = coerce_str(val)
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return raw


def _card_meta(row, source: str) -> str:
    """Return compact meta HTML for NSF/SBIR cards."""
    items = []
    s = (source or "").lower()
    if "nsf" in s:
        if row.get("grant_type"):
            items.append(f"<b>Type:</b>{_e(row.get('grant_type', ''))}")
        if row.get("award_amount"):
            items.append(f"<b>Award:</b>{_fmt_amt(row.get('award_amount'))}")
        if row.get("pi_email"):
            items.append(f"<b>PI:</b>{_e(row.get('pi_email', ''))}")
        loc = ", ".join(filter(None, [str(row.get("company_city") or ""), str(row.get("company_state") or "")]))
        if loc:
            items.append(f"<b>Location:</b>{_e(loc)}")
        if row.get("grant_expiry"):
            items.append(f"<b>Exp:</b>{_e(str(row.get('grant_expiry', ''))[:10])}")
    elif "sbir" in s:
        for field, label in [("agency", "Agency"), ("branch", "Branch"), ("grant_type", "Type"), ("topic_code", "Topic")]:
            v = row.get(field, "")
            if v:
                items.append(f"<b>{label}</b>{_e(str(v))}")
        if row.get("award_amount"):
            items.append(f"<b>Award</b>{_fmt_amt(row.get('award_amount'))}")
        if row.get("poc_email"):
            items.append(f"<b>POC</b>{_e(row.get('poc_email', ''))}")
    else:
        return ""
    if not items:
        return ""
    inner = "".join(f'<span class="rl-meta-item">{it}</span>' for it in items)
    return f'<div class="rl-meta-grid">{inner}</div>'


def render_card(
    row,
    key_suffix: str,
    current_tab: str = "brief",
    abstract_limit: int = 600,
):
    """Render a research-style card with integrated status footer."""
    paper_id     = str(row.get("paper_id") or "")
    score        = int(row.get("relevance_score") or 0)
    source       = coerce_str(row.get("source") or "")
    title        = clean_text_field(row.get("title") or "Untitled")
    authors_str  = clean_text_field(row.get("authors") or "")
    inst_str     = clean_text_field(row.get("institutions") or "")
    abstract_raw = clean_text_field(row.get("abstract") or "")
    abstract_txt = abstract_raw[:abstract_limit]
    insight      = clean_text_field(row.get("why_this_matters") or "")
    url          = coerce_str(row.get("source_url") or "")
    pub_date     = coerce_str(row.get("publication_date") or "")
    date_str     = str(pub_date)[:10] if pub_date else ""
    cur_stat     = safe_status(row.get("status"))
    keywords     = coerce_list(row.get("keywords") or "")

    is_openalex = "openalex" in source.lower()
    is_nsf      = "nsf" in source.lower()
    venue_str   = clean_text_field(row.get("publication_venue") or "") if is_openalex else ""

    card_hi_cls = "rl-rc-hi" if score >= 7 else ""
    chip_html   = f'<span class="{score_chip_cls(score)}">{score}</span>'
    badge_html  = source_badge(source)
    date_span   = f'<span class="rl-rc-date">{_e(date_str)}</span>' if date_str else ""
    byline_block = ""
    if authors_str or inst_str:
        byline_block = (
            '<div style="margin-bottom:8px">'
            + (f'<div class="rl-research-authors">{_e(authors_str)}</div>' if authors_str else "")
            + (f'<div class="rl-research-institutions">{_e(inst_str)}</div>' if inst_str else "")
            + "</div>"
        )

    abstract_block = ""
    if abstract_txt:
        ellipsis = "&hellip;" if len(abstract_raw) > abstract_limit else ""
        abstract_block = (
            f'<div class="rl-rc-abstract">'
            f'<div class="rl-rc-abstract-lbl">Abstract</div>'
            f'<div class="rl-rc-abstract-txt">{_e(abstract_txt)}{ellipsis}</div>'
            f'</div>'
        )

    signal_block = ""
    if insight:
        signal_block = (
            f'<div class="rl-rc-signal">'
            f'<div class="rl-rc-signal-lbl">Investment Signal</div>'
            f'<div class="rl-rc-signal-txt">{_e(insight)}</div>'
            f'</div>'
        )

    # ── Top row: OpenAlex and NSF get source link in the header top-right
    if is_openalex or is_nsf:
        src_link = (
            f'<a class="rl-src-link" href="{_e(url)}">Source</a>'
            if url else ""
        )
        topright_html = (
            f'<div class="rl-rc-topright">'
            f'<div class="rl-rc-topright-row">{date_span}{src_link}</div>'
            f'</div>'
        )
        toprow_html = f'<div class="rl-research-toprow">{chip_html}{badge_html}{topright_html}</div>'
    else:
        # Non-OpenAlex: date floats right via wrapper
        right_html  = f'<span style="margin-left:auto;display:flex;align-items:center;gap:8px">{date_span}</span>'
        toprow_html = f'<div class="rl-research-toprow">{chip_html}{badge_html}{right_html}</div>'

    # ── Footer meta + keywords
    kw_html   = "".join(f'<span class="rl-kw-chip">{_e(kw)}</span>' for kw in keywords[:8])
    meta_html = _card_meta(row, source)
    if not is_openalex:
        # NSF / SBIR: full-width meta strip across bottom; NSF source link lives in header
        strip_link = (
            f'<a class="rl-src-link" href="{_e(url)}" style="margin-left:auto;flex-shrink:0">Source</a>'
            if (url and not is_nsf) else ""
        )
        meta_strip_cls = "rl-rc-meta-strip rl-rc-meta-strip-right" if is_nsf else "rl-rc-meta-strip"
        meta_strip = (
            f'<div class="{meta_strip_cls}">{meta_html}{strip_link}</div>'
            if (meta_html or strip_link) else ""
        )
        kw_cls = "rl-rc-footer-kw rl-rc-footer-kw-right" if is_nsf else "rl-rc-footer-kw"
        kw_part = f'<div class="{kw_cls}">{kw_html}</div>' if kw_html else ""
        footer_main = meta_strip
        footer_html = (
            f'<div class="rl-rc-footer-nsf">{footer_main}{kw_part}</div>'
            if (footer_main or kw_part) else ""
        )
    else:
        # OpenAlex: keywords left, venue bottom-right
        venue_html = f'<span class="rl-rc-venue">{_e(venue_str)}</span>' if venue_str else ""
        footer_html = (
            f'<div class="rl-rc-footer2">'
            f'<div class="rl-rc-footer-kw">{kw_html}</div>'
            f'<div class="rl-rc-footer-meta">{venue_html}</div>'
            f'</div>'
            if (kw_html or venue_html) else ""
        )

    _detail_href = f"?tab={_e(current_tab)}&detail_id={_e(paper_id)}" if paper_id else ""
    overlay   = (
        f'<a class="rl-card-overlay" href="{_detail_href}" target="_self"></a>'
        if _detail_href else ""
    )
    title_el  = (
        f'<a class="rl-research-title" href="{_detail_href}" target="_self">{_e(title)}</a>'
        if _detail_href else
        f'<div class="rl-research-title">{_e(title)}</div>'
    )
    card_html = "".join([
        f'<div class="rl-research-card {card_hi_cls}" id="rl-card-{_e(paper_id)}">',
        overlay,
        toprow_html,
        byline_block,
        title_el,
        abstract_block,
        signal_block,
        footer_html,
        '</div>',
    ])

    st.markdown(card_html, unsafe_allow_html=True)
    widget_key = f"status_{key_suffix}"
    sync_status_widget_state(widget_key, cur_stat)
    new_status = st.selectbox(
        "Status",
        STATUS_OPTIONS,
        key=widget_key,
        label_visibility="collapsed",
    )

    if new_status != cur_stat:
        update_status(paper_id, new_status)
        st.cache_data.clear()
        st.rerun()

    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)


# ── Detail page helpers ────────────────────────────────────────────────────────
def _detail_field(label: str, value: str, link_href: str = "") -> str:
    if not value:
        return ""
    val_html = (
        f'<a href="{_e(link_href)}">{_e(value)}</a>' if link_href else _e(value)
    )
    return (
        f'<div class="rl-detail-field">'
        f'<div class="rl-detail-field-lbl">{_e(label)}</div>'
        f'<div class="rl-detail-field-val">{val_html}</div>'
        f'</div>'
    )


def render_detail_page(df_all):
    """Full-page detail view for a single lead, driven by ?detail_id=<paper_id>."""
    paper_id = st.query_params.get("detail_id", "")
    return_tab = st.query_params.get("tab", "brief")
    rows = df_all[df_all["paper_id"].astype(str) == str(paper_id)]

    if st.button("← Back to Leads"):
        st.query_params.pop("detail_id", None)
        st.query_params["tab"] = return_tab
        st.rerun()

    if rows.empty:
        st.error("Lead not found.")
        return

    row      = rows.iloc[0].to_dict()
    source   = coerce_str(row.get("source") or "")
    is_oa    = "openalex" in source.lower()
    is_nsf   = "nsf"      in source.lower()
    # is_sbir covers anything else (SBIR.gov)

    title    = clean_text_field(row.get("title")            or "Untitled")
    score    = int(row.get("relevance_score")               or 0)
    authors  = clean_text_field(row.get("authors")          or "")
    inst     = clean_text_field(row.get("institutions")     or "")
    abstract = clean_text_field(row.get("abstract")         or "")
    insight  = clean_text_field(row.get("why_this_matters") or "")
    url      = coerce_str(row.get("source_url")             or "")
    pub_date = coerce_str(row.get("publication_date")       or "")
    date_str = str(pub_date)[:10] if pub_date else ""
    cur_stat = safe_status(row.get("status"))
    keywords = coerce_list(row.get("keywords")              or "")
    pid_s    = str(row.get("paper_id") or "")

    # ── Header: score chip · source badge · status pill · source link · date ──
    src_anchor = (
        f'&ensp;<a class="rl-src-link" href="{_e(url)}">Source</a>'
        if url else ""
    )
    date_html = f'<span class="rl-detail-date">{_e(date_str)}</span>' if date_str else ""
    st.markdown(
        f'<div class="rl-detail-header">'
        f'<span class="{score_chip_cls(score)}">{score}</span>'
        f'{source_badge(source)}'
        f'<span class="rl-rc-status-pill {_status_pill_cls(cur_stat)}">{_e(cur_stat)}</span>'
        f'{src_anchor}{date_html}'
        f'</div>'
        f'<h1 class="rl-detail-title">{_e(title)}</h1>',
        unsafe_allow_html=True,
    )

    # ── Byline ────────────────────────────────────────────────────────────────
    if authors or inst:
        st.markdown(
            f'<div class="rl-detail-byline">'
            + (f'<div class="rl-detail-authors">{_e(authors)}</div>' if authors else "")
            + (f'<div class="rl-detail-inst">{_e(inst)}</div>'      if inst     else "")
            + '</div>',
            unsafe_allow_html=True,
        )

    # ── Investment signal ─────────────────────────────────────────────────────
    if insight:
        st.markdown(
            f'<div class="rl-detail-signal">'
            f'<div class="rl-detail-signal-lbl">Investment Signal</div>'
            f'<div class="rl-detail-signal-txt">{_e(insight)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Abstract ──────────────────────────────────────────────────────────────
    if abstract:
        st.markdown(
            f'<div class="rl-detail-sec-lbl">Abstract</div>'
            f'<div class="rl-detail-abstract">{_e(abstract)}</div>',
            unsafe_allow_html=True,
        )

    # ── Status control ────────────────────────────────────────────────────────
    st.markdown('<div class="rl-detail-sec-lbl" style="margin-top:1.5rem">Status</div>', unsafe_allow_html=True)
    detail_widget_key = f"detail_status_{pid_s}"
    sync_status_widget_state(detail_widget_key, cur_stat)
    new_status = st.selectbox(
        "Status", STATUS_OPTIONS,
        key=detail_widget_key,
        label_visibility="collapsed",
    )
    if new_status != cur_stat:
        update_status(pid_s, new_status)
        st.cache_data.clear()
        st.rerun()

    # ── Metadata grid ─────────────────────────────────────────────────────────
    left_fields, right_fields = [], []

    if is_oa:
        if row.get("publication_venue"):
            left_fields.append(_detail_field("Publication Venue",  clean_text_field(row["publication_venue"])))
        if date_str:
            left_fields.append(_detail_field("Publication Date",   date_str))
        if row.get("citation_count"):
            left_fields.append(_detail_field("Citation Count",     str(row["citation_count"])))
        if row.get("funding_source"):
            left_fields.append(_detail_field("Funding Source",     clean_text_field(row["funding_source"])))
        if row.get("search_term"):
            left_fields.append(_detail_field("Search Term",        clean_text_field(row["search_term"])))
        if row.get("record_type"):
            left_fields.append(_detail_field("Record Type",        clean_text_field(row["record_type"])))
        if url:
            right_fields.append(_detail_field("Source URL",        url, link_href=url))

    elif is_nsf:
        if row.get("grant_type"):
            left_fields.append(_detail_field("Grant Type",         clean_text_field(row["grant_type"])))
        if row.get("fund_program_name"):
            left_fields.append(_detail_field("Program Name",       clean_text_field(row["fund_program_name"])))
        if row.get("award_amount"):
            amt = _fmt_amt(row["award_amount"])
            left_fields.append(
                f'<div class="rl-detail-field">'
                f'<div class="rl-detail-field-lbl">Award Amount</div>'
                f'<div class="rl-detail-award-val">{_e(amt)}</div>'
                f'</div>'
            )
        if row.get("grant_expiry"):
            left_fields.append(_detail_field("Grant Expiry",       str(row["grant_expiry"])[:10]))
        if row.get("search_term"):
            left_fields.append(_detail_field("Search Term",        clean_text_field(row["search_term"])))
        if row.get("record_type"):
            left_fields.append(_detail_field("Record Type",        clean_text_field(row["record_type"])))

        pi_email = coerce_str(row.get("pi_email") or "")
        if pi_email:
            right_fields.append(_detail_field("PI Email",          pi_email,  link_href=f"mailto:{pi_email}"))
        loc = ", ".join(p for p in [
            str(row.get("company_city")  or ""),
            str(row.get("company_state") or ""),
        ] if p and p.lower() not in ("", "none"))
        if loc:
            right_fields.append(_detail_field("Location",          loc))
        if row.get("company_phone"):
            ph = coerce_str(row["company_phone"])
            right_fields.append(_detail_field("Company Phone",     _fmt_phone(ph), link_href=f"tel:{_tel_href(ph)}"))
        if row.get("company_url"):
            co = coerce_str(row["company_url"])
            right_fields.append(_detail_field("Company Website",   co,        link_href=co))
        if row.get("uei"):
            right_fields.append(_detail_field("UEI",               coerce_str(row["uei"])))
        if url:
            right_fields.append(_detail_field("Award Page",        url,       link_href=url))

    else:  # SBIR.gov
        if row.get("agency"):
            left_fields.append(_detail_field("Agency",             clean_text_field(row["agency"])))
        if row.get("branch"):
            left_fields.append(_detail_field("Branch",             clean_text_field(row["branch"])))
        if row.get("grant_type"):
            left_fields.append(_detail_field("Grant Type",         clean_text_field(row["grant_type"])))
        if row.get("topic_code"):
            left_fields.append(_detail_field("Topic Code",         clean_text_field(row["topic_code"])))
        if row.get("award_amount"):
            amt = _fmt_amt(row["award_amount"])
            left_fields.append(
                f'<div class="rl-detail-field">'
                f'<div class="rl-detail-field-lbl">Award Amount</div>'
                f'<div class="rl-detail-award-val">{_e(amt)}</div>'
                f'</div>'
            )
        if row.get("fund_program_name"):
            left_fields.append(_detail_field("Program Name",       clean_text_field(row["fund_program_name"])))
        if row.get("ri_name"):
            left_fields.append(_detail_field("Research Institution", clean_text_field(row["ri_name"])))
        if row.get("search_term"):
            left_fields.append(_detail_field("Search Term",        clean_text_field(row["search_term"])))

        poc_name = coerce_str(row.get("poc_name") or "")
        if poc_name:
            right_fields.append(_detail_field("Point of Contact",  poc_name))
        poc_email = coerce_str(row.get("poc_email") or "")
        if poc_email:
            right_fields.append(_detail_field("POC Email",         poc_email, link_href=f"mailto:{poc_email}"))
        poc_phone = coerce_str(row.get("poc_phone") or "")
        if poc_phone:
            right_fields.append(_detail_field("POC Phone",         poc_phone, link_href=f"tel:{poc_phone}"))
        if row.get("company_phone"):
            ph = coerce_str(row["company_phone"])
            right_fields.append(_detail_field("Company Phone",     _fmt_phone(ph), link_href=f"tel:{_tel_href(ph)}"))
        if row.get("company_url"):
            co = coerce_str(row["company_url"])
            right_fields.append(_detail_field("Company Website",   co,        link_href=co))
        if row.get("number_employees"):
            right_fields.append(_detail_field("Employees",         str(row["number_employees"])))
        if row.get("uei"):
            right_fields.append(_detail_field("UEI",               coerce_str(row["uei"])))
        if url:
            right_fields.append(_detail_field("Award Page",        url,       link_href=url))

    if left_fields or right_fields:
        st.markdown(
            f'<div class="rl-detail-sec-lbl">Details</div>'
            f'<div class="rl-detail-grid">'
            f'<div>{"".join(left_fields)}</div>'
            f'<div>{"".join(right_fields)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Keywords ──────────────────────────────────────────────────────────────
    if keywords:
        kw_html = "".join(f'<span class="rl-detail-kw-chip">{_e(kw)}</span>' for kw in keywords)
        st.markdown(
            f'<div class="rl-detail-sec-lbl">Keywords</div>'
            f'<div class="rl-detail-kw">{kw_html}</div>',
            unsafe_allow_html=True,
        )
def sync_tab_query_param() -> None:
    components.html(
        """
        <script>
        (() => {
          const tabMap = {
            "Signal Brief": "brief",
            "All Leads": "all",
            "Research Signals": "research",
            "Funded Companies": "nsf",
            "Federal Grants": "sbir",
          };

          const parentWindow = window.parent;
          const parentDoc = parentWindow.document;

          const updateQuery = (tabKey) => {
            const url = new URL(parentWindow.location.href);
            url.searchParams.set("tab", tabKey);
            parentWindow.history.replaceState({}, "", url.toString());
          };

          const syncTabs = () => {
            const buttons = Array.from(parentDoc.querySelectorAll('.stTabs [data-baseweb="tab"]'));
            if (!buttons.length) return;

            const desired = new URL(parentWindow.location.href).searchParams.get("tab");
            if (desired) {
              const target = buttons.find((btn) => tabMap[btn.textContent.trim()] === desired);
              if (target && target.getAttribute("aria-selected") !== "true") {
                target.click();
              }
            }

            buttons.forEach((btn) => {
              if (btn.dataset.rlTabBound === "1") return;
              btn.dataset.rlTabBound = "1";
              btn.addEventListener("click", () => {
                const tabKey = tabMap[btn.textContent.trim()];
                if (tabKey) updateQuery(tabKey);
              });
            });
          };

          let attempts = 0;
          const interval = setInterval(() => {
            syncTabs();
            if (++attempts >= 30) {
              clearInterval(interval);
            }
          }, 150);

          const observer = new MutationObserver(() => {
            syncTabs();
          });
          observer.observe(parentDoc.body, { childList: true, subtree: true });

          setTimeout(() => observer.disconnect(), 10000);

          syncTabs();
        })();
        </script>
        """,
        height=0,
    )

with st.sidebar:
    st.markdown("""
    <div class="rl-brand">
        <p class="rl-brand-name">Reveille</p>
        <p class="rl-brand-sub">Deal Scouting</p>
        <p class="rl-brand-tagline">Power · Protection · Productivity</p>
    </div>
    """, unsafe_allow_html=True)

    data = load_all()
    df_all = pd.DataFrame(data) if data else pd.DataFrame()

    total = len(df_all)
    high_signal = int((df_all["relevance_score"] >= 7).sum()) if total else 0

    col1, col2 = st.columns(2)
    col1.metric("Leads", total)
    col2.metric("High Signal", high_signal)

    if st.button("Refresh Pipeline", use_container_width=True):
        with st.status("Running pipeline…", expanded=True) as status:
            st.write("Checking for new leads…")
            run_pipeline()
            status.update(label="Pipeline complete", state="complete", expanded=False)
        st.cache_data.clear()
        st.toast("New leads loaded.")
        st.rerun()

    st.markdown("""
    <div class="rl-sidebar-footer">
        <div>Cache TTL · 5 min</div>
        <div>Score threshold · 7+</div>
        <div>Reveille v0.1</div>
    </div>
    """, unsafe_allow_html=True)


# ── Routing ────────────────────────────────────────────────────────────────────
_detail = st.query_params.get("detail_id", None)

if _detail:
    render_detail_page(df_all)
    st.stop()

# ── Page Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rl-page-header">
    <span class="rl-page-wordmark">DEAL SCOUT</span>
    <span class="rl-page-tagline">Signal Intelligence | Reveille VC</span>
</div>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_brief, tab_all, tab_research, tab_nsf, tab_sbir = st.tabs(
    ["Signal Brief", "All Leads", "Research Signals", "Funded Companies", "Federal Grants"]
)
sync_tab_query_param()


# ─────────────────────────────────────────────────────────────────────────────
# TAB — Signal Brief
# ─────────────────────────────────────────────────────────────────────────────
with tab_brief:
    st.markdown(section_header("Signal Brief", "Score ≥ 7"), unsafe_allow_html=True)

    if df_all.empty:
        st.info("No data yet. Run the ingestion pipeline first.")
    else:
        brief = df_all[df_all["relevance_score"] >= 7].sort_values("relevance_score", ascending=False).copy()
        if brief.empty:
            st.info("No leads with score ≥ 7 found.")
        else:
            brief_sources = sorted(brief["source"].dropna().unique().tolist())
            f1, f2 = st.columns([2, 2])
            with f1:
                brief_sel_sources = st.multiselect(
                    "Source", brief_sources, default=brief_sources, key="brief_source_filter"
                )
            with f2:
                brief_sel_statuses = st.multiselect(
                    "Status", STATUS_OPTIONS, default=STATUS_OPTIONS, key="brief_status_filter"
                )

            brief["_status_norm"] = brief["status"].fillna("New").apply(safe_status)
            brief_filtered = brief[
                brief["source"].isin(brief_sel_sources)
                & brief["_status_norm"].isin(brief_sel_statuses)
            ]
            st.caption(f"{len(brief_filtered)} record(s)")

            cols = st.columns(2)
            for i, (_, row) in enumerate(brief_filtered.iterrows()):
                with cols[i % 2]:
                    render_card(
                        row,
                        key_suffix=f"brief_{row.get('paper_id', i)}_{i}",
                        current_tab="brief",
                    )


# ─────────────────────────────────────────────────────────────────────────────
# TAB — All Leads
# ─────────────────────────────────────────────────────────────────────────────
with tab_all:
    st.markdown(section_header("All Leads"), unsafe_allow_html=True)

    if df_all.empty:
        st.info("No data yet.")
    else:
        sources = sorted(df_all["source"].dropna().unique().tolist())

        f1, f2, f3 = st.columns([2, 2, 2])
        with f1:
            sel_sources = st.multiselect("Source", sources, default=sources)
        with f2:
            min_score = st.slider("Min score", 1, 10, 1)
        with f3:
            sel_statuses = st.multiselect("Status", STATUS_OPTIONS, default=STATUS_OPTIONS)

        status_col = df_all["status"].fillna("New") if "status" in df_all.columns else pd.Series(["New"] * len(df_all), index=df_all.index)
        mask = (
            df_all["source"].isin(sel_sources)
            & (df_all["relevance_score"] >= min_score)
            & status_col.isin(sel_statuses)
        )
        filtered = df_all[mask].sort_values("relevance_score", ascending=False)
        st.caption(f"{len(filtered)} record(s)")

        for i, (_, row) in enumerate(filtered.iterrows()):
            render_card(
                row,
                key_suffix=f"all_{row.get('paper_id', i)}_{i}",
                current_tab="all",
                abstract_limit=400,
            )


# ─────────────────────────────────────────────────────────────────────────────
# TAB — Research Signals (OpenAlex)
# ─────────────────────────────────────────────────────────────────────────────
with tab_research:
    st.markdown(section_header("Research Signals", "OpenAlex"), unsafe_allow_html=True)

    if df_all.empty:
        st.info("No data yet.")
    else:
        oa = df_all[df_all["source"] == "OpenAlex"].copy()
        if oa.empty:
            st.info("No OpenAlex records found.")
        else:
            # ── Filter bar ───────────────────────────────────────────────────
            f1, f2, f3 = st.columns([2, 2, 2])
            with f1:
                oa_min_score = st.slider("Min Score", 1, 10, 1, key="oa_score_filter")
            with f2:
                oa_status_filter = st.multiselect(
                    "Status", STATUS_OPTIONS, default=STATUS_OPTIONS, key="oa_status_filter"
                )
            with f3:
                pass  # spacer

            # ── Apply filters ─────────────────────────────────────────────
            oa["_status_norm"] = oa["status"].fillna("New").apply(safe_status)
            oa_filtered = oa[
                (oa["relevance_score"] >= oa_min_score)
                & (oa["_status_norm"].isin(oa_status_filter))
            ].sort_values("relevance_score", ascending=False)

            st.caption(f"{len(oa_filtered)} record(s)")

            for i, (_, row) in enumerate(oa_filtered.iterrows()):
                render_card(
                    row,
                    key_suffix=f"oa_{row.get('paper_id', i)}",
                    current_tab="research",
                )


# ─────────────────────────────────────────────────────────────────────────────
# TAB — Funded Companies (NSF)
# ─────────────────────────────────────────────────────────────────────────────
with tab_nsf:
    st.markdown(section_header("Funded Companies", "NSF SBIR / STTR"), unsafe_allow_html=True)

    if df_all.empty:
        st.info("No data yet.")
    else:
        nsf = df_all[df_all["source"] == "NSF"].copy()
        if nsf.empty:
            st.info("No NSF records found.")
        else:
            nsf["award_amount"] = pd.to_numeric(nsf["award_amount"], errors="coerce")
            avg_award = nsf["award_amount"].mean()
            pi_count  = int(nsf["pi_email"].notna().sum())

            m1, m2, m3 = st.columns(3)
            m1.metric("NSF Leads",     len(nsf))
            m2.metric("Avg Award",     f"${avg_award:,.0f}" if pd.notna(avg_award) else "—")
            m3.metric("With PI Email", pi_count)

            f1, f2 = st.columns([2, 2])
            with f1:
                nsf_min_score = st.slider("Min Score", 1, 10, 1, key="nsf_score_filter")
            with f2:
                nsf_status_filter = st.multiselect("Status", STATUS_OPTIONS, default=STATUS_OPTIONS, key="nsf_status_filter")

            nsf["_status_norm"] = nsf["status"].fillna("New").apply(safe_status)
            nsf_filtered = nsf[
                (nsf["relevance_score"] >= nsf_min_score)
                & (nsf["_status_norm"].isin(nsf_status_filter))
            ].sort_values("relevance_score", ascending=False)

            st.caption(f"{len(nsf_filtered)} record(s)")
            for i, (_, row) in enumerate(nsf_filtered.iterrows()):
                render_card(
                    row,
                    key_suffix=f"nsf_{row.get('paper_id', i)}",
                    current_tab="nsf",
                    abstract_limit=500,
                )


# ─────────────────────────────────────────────────────────────────────────────
# TAB — Federal Grants (SBIR.gov)
# ─────────────────────────────────────────────────────────────────────────────
with tab_sbir:
    st.markdown(section_header("Federal Grants", "SBIR.gov"), unsafe_allow_html=True)

    sbir_df = pd.DataFrame()
    if not df_all.empty:
        sbir_df = df_all[df_all["source"] == "SBIR.gov"].copy()

    if sbir_df.empty:
        st.info(
            "No SBIR.gov records yet.\n\n"
            "**Why:** The SBIR.gov API is currently disabled (`ENABLE_SBIR_GOV = False` in `config.py`).\n\n"
            "**To enable:** Set `ENABLE_SBIR_GOV = True` and re-run the ingestion pipeline. "
            "Once live, this tab will show DoD/federal SBIR & STTR award data including agency, "
            "award amounts, company details, topic codes, and AI-generated relevance notes."
        )
    else:
        f1, f2 = st.columns([2, 2])
        with f1:
            sbir_min_score = st.slider("Min Score", 1, 10, 1, key="sbir_score_filter")
        with f2:
            sbir_status_filter = st.multiselect("Status", STATUS_OPTIONS, default=STATUS_OPTIONS, key="sbir_status_filter")

        sbir_df["_status_norm"] = sbir_df["status"].fillna("New").apply(safe_status)
        sbir_filtered = sbir_df[
            (sbir_df["relevance_score"] >= sbir_min_score)
            & (sbir_df["_status_norm"].isin(sbir_status_filter))
        ].sort_values("relevance_score", ascending=False)

        st.caption(f"{len(sbir_filtered)} record(s)")
        for i, (_, row) in enumerate(sbir_filtered.iterrows()):
            render_card(
                row,
                key_suffix=f"sbir_{row.get('paper_id', i)}",
                current_tab="sbir",
                abstract_limit=500,
            )
