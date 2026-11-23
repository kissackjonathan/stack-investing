import html
import json
import logging
import math
import os
import random
import re
import sys
import unicodedata
import time
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))  # so decorations.py is found however the app is launched
from decorations import DECOR, UNIT_DECOR  # noqa: E402
import garden  # noqa: E402
import storage  # noqa: E402
import market_data as md  # noqa: E402
import portfolio as pfm  # noqa: E402
from universe import BENCHMARK, BENCHMARK_NAME, CLASSES, COMMODITY_NOTE  # noqa: E402

# STACK — gamified investing-literacy learning MVP
# Run locally (from this folder): streamlit run app.py
# Each player picks a name on arrival; progress is saved to users/<name>.json next to this file.

st.set_page_config(
    page_title="STACK | Learn investing",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

USERS_DIR = Path(os.environ.get("STACK_USERS_DIR", Path(__file__).with_name("users")))

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{
  --bg:#050706; --surface:#111914; --surface-2:#0b100d; --line:#25352a; --line-2:#2f4536;
  --text:#f4f7f4; --soft:#d3dbd5; --muted:#9daaa0;
  --green:#7df59b; --green-2:#a0ff9d; --green-ink:#061109; --green-soft:#14291b; --green-line:#285638;
  --red:#ff7b7b; --red-soft:#2a1416;
}
html, body, [class*="css"], .stApp, button, input { font-family: Inter, sans-serif; }
.stApp { background: radial-gradient(circle at 80% 0%, #102519 0, #080b09 35%, #050706 100%); color:var(--text); }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1100px; padding-top: 2rem; padding-bottom: 4rem; }
h1,h2,h3,h4 { color:var(--text) !important; letter-spacing:-.03em; }
p, label, span, li { color: var(--soft); }
hr { border-color: var(--line); }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] { background:#070a08; border-right:1px solid var(--line); }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap:.35rem; }
.logo { display:flex; align-items:center; gap:10px; padding:4px 6px 18px; }
.logo-mark { width:38px; height:38px; border-radius:12px; display:grid; place-items:center; font-size:20px;
  background:linear-gradient(135deg,#72f39a,#a0ff9d); box-shadow:0 0 24px rgba(125,245,155,.25); }
.logo-text { font-weight:800; font-size:22px; letter-spacing:.08em; color:var(--text); }
.logo-sub { font-size:12px; color:var(--muted); display:block; letter-spacing:0; font-weight:500; }
.side-note { margin-top:18px; padding:14px; border:1px solid var(--line); border-radius:14px; background:var(--surface-2); }
.side-note b { color:var(--text); }
.side-note .bar { margin-top:8px; }
[class*="st-key-nav_"] button { background:transparent !important; border:1px solid transparent !important;
  justify-content:flex-start !important; border-radius:12px !important; min-height:2.7rem; padding:0 .9rem; }
[class*="st-key-nav_"] button p { color:#b8c4bb !important; font-weight:600; }
[class*="st-key-nav_off"] button:hover { background:#0f1712 !important; }
[class*="st-key-nav_on"] button { background:var(--green-soft) !important; border-color:var(--green-line) !important; }
[class*="st-key-nav_on"] button p { color:var(--green) !important; font-weight:800; }

/* ---------- Buttons ---------- */
[data-testid="stBaseButton-primary"] { background:linear-gradient(90deg,#72f39a,#a0ff9d) !important; border:0 !important;
  border-radius:999px !important; min-height:2.8rem; padding:0 1.3rem; }
[data-testid="stBaseButton-primary"] p { color:var(--green-ink) !important; font-weight:800; }
[data-testid="stBaseButton-primary"]:hover { background:#b3ffb4 !important; }
[data-testid="stMain"] [data-testid="stBaseButton-secondary"] { background:#101612; border:1px solid var(--line-2);
  border-radius:999px; min-height:2.8rem; }
[data-testid="stMain"] [data-testid="stBaseButton-secondary"] p { color:var(--text); font-weight:700; }
[data-testid="stMain"] [data-testid="stBaseButton-secondary"]:hover { border-color:var(--green); }

/* Answer buttons (A/B/C/D) */
[class*="st-key-ans_"] button { background:var(--surface) !important; border:1px solid var(--line-2) !important;
  justify-content:flex-start !important; border-radius:14px !important; min-height:3.2rem; padding:.65rem 1rem !important; opacity:1 !important; }
[class*="st-key-ans_"] button div, [class*="st-key-ans_"] button p { text-align:left; justify-content:flex-start; }
[class*="st-key-ans_"] button p { color:var(--text) !important; font-weight:500 !important; }
[class*="st-key-ans_idle"] button:hover { border-color:var(--green) !important; background:#14211a !important; }
[class*="st-key-ans_ok"] button { background:#0f2a18 !important; border-color:var(--green) !important; }
[class*="st-key-ans_ok"] button p { color:#c9ffd6 !important; font-weight:700 !important; }
[class*="st-key-ans_bad"] button { background:var(--red-soft) !important; border-color:var(--red) !important; }
[class*="st-key-ans_bad"] button p { color:#ffd2d2 !important; }
[class*="st-key-ans_off"] button { opacity:.45 !important; }
[class*="st-key-ans_"] button:disabled { cursor:default; }

/* ---------- Cards ---------- */
[class*="st-key-card"] { background:linear-gradient(145deg,#111a14,#0b100d); border:1px solid var(--line);
  border-radius:20px; padding:22px 24px; }
[class*="st-key-card_locked"] { opacity:.5; }
[class*="st-key-card_done"] { border-color:var(--green-line); }
.st-key-card_hero { background:radial-gradient(circle at 100% 0%, rgba(125,245,155,.16), transparent 55%), linear-gradient(145deg,#12201a,#0b100d);
  border-color:#2c5a3a; padding:30px 32px; }
.stack-card { background:linear-gradient(145deg,#111a14,#0b100d); border:1px solid var(--line); border-radius:20px; padding:22px 24px; margin:8px 0 16px; }
.pill { display:inline-block; background:var(--green-soft); border:1px solid var(--green-line); color:#8bf5a6;
  border-radius:999px; padding:5px 12px; font-size:12px; font-weight:700; letter-spacing:.06em; margin-right:6px; }
.muted { color:var(--muted); }
.hero-title { font-size:34px; font-weight:800; letter-spacing:-.03em; color:var(--text); margin:14px 0 6px; line-height:1.15; }
.big-title { font-size:28px; font-weight:800; letter-spacing:-.03em; color:var(--text); margin:14px 0 10px; line-height:1.2; }
.big-body { font-size:19px; line-height:1.65; color:var(--soft); margin:0; }

/* ---------- Page header + chips ---------- */
.page-title { font-size:32px; font-weight:800; letter-spacing:-.03em; color:var(--text); margin:0; line-height:1.15; }
.page-sub { color:var(--muted); margin:4px 0 0; font-size:15px; }
/* One flex row holds every chip + the currency picker; all share --chip-h, the same box style and an 8px gap. */
:root { --chip-h:44px; }
.st-key-hdr_chips { gap:8px !important; row-gap:8px !important; flex-wrap:wrap; }
.st-key-hdr_chips > [data-testid="stElementContainer"] { margin:0 !important; }
/* Streamlit gives markdown a -16px bottom margin: without this the chip boxes overflow a 28px container and sit 8px low. */
.st-key-hdr_chips [data-testid="stMarkdownContainer"] { margin:0 !important; }
.chip { box-sizing:border-box; height:var(--chip-h); display:flex; align-items:center; gap:5px; padding:0 12px;
  background:var(--surface); border:1px solid var(--line); border-radius:14px; white-space:nowrap; line-height:1; }
.chip b { color:var(--text); font-weight:800; font-size:15px; }
.chip small { color:var(--muted); font-size:12px; }
.chip-rank { flex-direction:column; align-items:stretch; justify-content:center; gap:6px; min-width:170px; }
.chip-row { display:flex; align-items:baseline; gap:5px; }
.chip-rank .bar { margin:0; height:5px; }
.st-key-pf_ccy [data-testid="stWidgetLabel"] { display:none; }
.st-key-pf_ccy [data-baseweb="select"] > div { box-sizing:border-box; height:var(--chip-h); min-height:var(--chip-h);
  display:flex; align-items:center; padding:0 6px 0 12px; background:var(--surface); border:1px solid var(--line);
  border-radius:14px; cursor:pointer; }
.st-key-pf_ccy [data-baseweb="select"] > div:focus-within { border-color:var(--green-line); }
.st-key-pf_ccy [data-baseweb="select"] > div > div:first-child { padding:0; display:flex; align-items:center; }
.st-key-pf_ccy [data-baseweb="select"] div { color:var(--text); font-weight:800; font-size:15px; line-height:1; }
.st-key-pf_ccy [data-baseweb="select"] svg { color:var(--muted); }
.bar { height:6px; background:#1c2a20; border-radius:999px; overflow:hidden; margin-top:6px; }
.bar i { display:block; height:100%; background:linear-gradient(90deg,#72f39a,#a0ff9d); border-radius:999px; }

/* ---------- Stats ---------- */
.stat { background:linear-gradient(145deg,#111a14,#0b100d); border:1px solid var(--line); border-radius:20px; padding:20px;
  display:flex; align-items:center; gap:16px; height:100%; }
.stat-label { color:var(--muted); font-size:13px; font-weight:600; text-transform:uppercase; letter-spacing:.06em; }
.stat-value { color:var(--text); font-size:28px; font-weight:800; letter-spacing:-.02em; line-height:1.2; }
.stat-sub { color:var(--muted); font-size:13px; }
.stat-icon { width:64px; height:64px; border-radius:50%; display:grid; place-items:center; font-size:28px; background:var(--green-soft);
  border:1px solid var(--green-line); flex:none; }
.ring { width:72px; height:72px; border-radius:50%; flex:none; display:grid; place-items:center;
  background:conic-gradient(var(--green) calc(var(--p) * 1%), #1c2a20 0); }
.ring span { width:56px; height:56px; border-radius:50%; background:#0d140f; display:grid; place-items:center;
  font-weight:800; color:var(--text); font-size:15px; }

/* ---------- Journey ---------- */
.badge { width:48px; height:48px; border-radius:50%; display:grid; place-items:center; font-weight:800; font-size:18px; }
.badge.done { background:linear-gradient(135deg,#72f39a,#a0ff9d); color:var(--green-ink); }
.badge.open { border:2px solid var(--green); color:var(--green); background:var(--green-soft); }
.badge.locked { border:1px solid var(--line-2); background:#0d130f; font-size:18px; }
.lvl-name { font-weight:800; color:var(--text); font-size:17px; }
.lvl-meta { color:var(--muted); font-size:14px; }
.best { color:var(--muted); font-size:13px; text-align:center; }
.best b { color:var(--green); font-size:17px; display:block; }

/* ---------- Journey map ---------- */
.map { position:relative; width:100%; margin:0 auto; overflow:hidden; border-radius:28px; }
.zone { position:absolute; left:0; right:0; border-radius:28px; pointer-events:none;
  background:linear-gradient(180deg, color-mix(in srgb, var(--accent) 11%, transparent) 0%,
    color-mix(in srgb, var(--accent) 5%, transparent) 55%, transparent 100%); }
.blob { position:absolute; border-radius:50%; pointer-events:none; }
.deco { position:absolute; width:var(--s); height:var(--s); pointer-events:none; opacity:var(--o);
  rotate:var(--r); animation:floaty var(--d) ease-in-out infinite; animation-delay:var(--dl); }
.deco svg { width:100%; height:100%; display:block; }
@keyframes floaty { 0%,100% { translate:0 0; } 50% { translate:0 -10px; } }
.map-svg { position:absolute; top:0; overflow:visible; }
.lab-note { color:var(--muted); font-size:12.5px; line-height:1.45; margin:-6px 0 14px; }
.unit-banner { position:absolute; left:0; right:0; box-sizing:border-box; border-radius:20px; padding:14px 20px;
  background:linear-gradient(90deg, color-mix(in srgb, var(--accent) 30%, #0b100d), color-mix(in srgb, var(--accent) 10%, #0b100d));
  border:1px solid color-mix(in srgb, var(--accent) 50%, transparent); overflow:hidden; }
.unit-banner.locked { filter:saturate(.35); opacity:.7; }
.unit-banner .bar { margin-top:8px; background:rgba(0,0,0,.35); }
.unit-banner .bar i { background:var(--accent); }
.unit-kicker { color:var(--accent); font-size:12px; font-weight:800; letter-spacing:.1em; }
.unit-title { color:var(--text); font-size:21px; font-weight:800; letter-spacing:-.02em; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.unit-desc { color:#c3cdc6; font-size:13px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.seg { fill:none; stroke:#2f4536; stroke-width:6; stroke-linecap:round; stroke-dasharray:1 14; }
.seg.done { stroke:var(--green); stroke-width:7; stroke-dasharray:1 12; filter:drop-shadow(0 0 4px rgba(125,245,155,.45)); }
.node-wrap { position:absolute; width:120px; margin-left:-60px; display:flex; flex-direction:column; align-items:center; text-align:center; }
.node { width:80px; height:80px; border-radius:50%; display:grid; place-items:center; font-size:30px; font-weight:800;
  text-decoration:none !important; position:relative; transition:transform .15s ease; }
.node:hover { transform:translateY(-2px) scale(1.04); }
.node:active { transform:translateY(2px); }
.node.done { background:var(--accent); color:var(--green-ink) !important; box-shadow:0 6px 0 color-mix(in srgb, var(--accent) 55%, #000); }
.node.open { background:var(--accent); color:var(--green-ink) !important; box-shadow:0 6px 0 color-mix(in srgb, var(--accent) 55%, #000); }
.node.open::after { content:""; position:absolute; inset:-8px; border-radius:50%; border:3px solid var(--accent);
  animation:pulse 1.6s ease-out infinite; pointer-events:none; }
@keyframes pulse { 0% { transform:scale(.92); opacity:.9; } 100% { transform:scale(1.35); opacity:0; } }
.node.locked { background:#18211b; color:#5d6a61 !important; box-shadow:0 6px 0 #0e1410; font-size:26px; }
.node.locked:hover { transform:none; }
.node-wrap.locked .node-name, .node-wrap.locked .node-xp { color:#6b786f; }
.bubble { position:absolute; top:-44px; background:var(--surface); border:2px solid var(--accent); color:var(--accent); z-index:2;
  font-weight:800; font-size:13px; letter-spacing:.08em; padding:5px 12px; border-radius:10px; animation:bob 1.6s ease-in-out infinite; }
.bubble::after { content:""; position:absolute; left:50%; bottom:-7px; width:10px; height:10px; margin-left:-5px;
  background:var(--surface); border-right:2px solid var(--accent); border-bottom:2px solid var(--accent); transform:rotate(45deg); }
@keyframes bob { 0%,100% { transform:translateY(0); } 50% { transform:translateY(-4px); } }
.stars { margin-top:12px; padding-top:3px !important; padding-bottom:3px !important; color:#ffd45c; font-size:17px; letter-spacing:2px; line-height:1; }
.stars span { color:#2a3a2f; }
.node-name { margin-top:10px; color:var(--text); font-size:13px; font-weight:700; line-height:1.2; }
.node-name, .node-xp, .stars { background:#070b08; padding:1px 8px; border-radius:8px; position:relative; }
.stars + .node-name { margin-top:6px; }
.node-xp { color:var(--muted); font-size:12px; margin-top:0; }
.mascot-slot { position:absolute; width:60px; height:60px; margin-left:-30px; display:grid; place-items:center; }
.mascot { width:56px; height:56px; border-radius:50%; display:grid; place-items:center; font-size:28px;
  background:var(--green-soft); border:2px dashed var(--green-line); }
@media (prefers-reduced-motion: reduce) { .node.open::after, .bubble, .deco { animation:none; } }
@media (max-width: 640px) {
  .deco.alt { display:none; }
  .deco { scale:.6; opacity:calc(var(--o) * .8); }
  .blob { scale:.6; }
}

/* ---------- Lesson steps ---------- */
.steps { display:flex; gap:6px; margin:6px 0 4px; }
.steps i { flex:1; height:7px; border-radius:999px; background:#1c2a20; }
.steps i.q { background:#1a2430; }
.steps i.done { background:var(--green); }
.steps i.cur { background:linear-gradient(90deg,#72f39a,#a0ff9d); box-shadow:0 0 10px rgba(125,245,155,.5); }
.steps-label { color:var(--muted); font-size:13px; margin-bottom:12px; }
.explain { background:#0d1510; border:1px solid var(--line); border-left:3px solid var(--green); border-radius:12px; padding:14px 16px; margin:10px 0; }
.explain.bad { border-left-color:var(--red); }

/* ---------- Done ---------- */
.done-wrap { text-align:center; padding:10px 0; }
.done-emoji { font-size:56px; }
.done-score { font-size:54px; font-weight:800; color:var(--green); letter-spacing:-.03em; line-height:1; margin:10px 0 4px; }
.xp-gain { display:inline-block; margin-top:12px; padding:8px 16px; border-radius:999px; background:var(--green-soft);
  border:1px solid var(--green-line); color:var(--green); font-weight:800; }

/* ---------- Rewards ---------- */
.badges { display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:14px; }
.reward { background:linear-gradient(145deg,#111a14,#0b100d); border:1px solid var(--green-line); border-radius:20px; padding:20px; }
.reward .ico { font-size:38px; }
.reward .t { color:var(--text); font-weight:800; font-size:17px; margin-top:8px; }
.reward .d { color:var(--muted); font-size:14px; margin-top:2px; }
.reward .s { margin-top:12px; font-size:12px; font-weight:700; letter-spacing:.06em; color:var(--green); }
.reward.locked { border-color:var(--line); filter:grayscale(1); opacity:.45; }
.reward.locked .s { color:var(--muted); }

/* Metrics */
div[data-testid="stMetric"] { background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:14px 16px; }
div[data-testid="stMetric"] label p { color:var(--muted) !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color:var(--green) !important; }

/* ---------- Portfolio ---------- */
[class*="st-key-seg_"] [role="radiogroup"] { gap:6px; flex-wrap:wrap; }
[class*="st-key-seg_"] label[data-baseweb="radio"] { margin:0; padding:6px 14px; border-radius:999px; background:#101612;
  border:1px solid var(--line-2); cursor:pointer; }
[class*="st-key-seg_"] label[data-baseweb="radio"] > div:first-child { display:none; }
[class*="st-key-seg_"] label[data-baseweb="radio"] p { font-weight:700; color:var(--soft); font-size:14px; }
[class*="st-key-seg_"] label[data-baseweb="radio"]:has(input:checked) { background:var(--green-soft); border-color:var(--green); }
[class*="st-key-seg_"] label[data-baseweb="radio"]:has(input:checked) p { color:var(--green); }
.pf-banner { background:linear-gradient(90deg,#2a2210,#15130b); border:1px solid #5a4a1e; color:#ffd98a; border-radius:14px;
  padding:9px 16px; font-size:14px; font-weight:700; letter-spacing:.02em; margin:0 0 14px; }
.asset-head { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; flex-wrap:wrap; margin:6px 0 8px; }
.asset-price { text-align:right; display:flex; flex-direction:column; }
.asset-price b { color:var(--text); font-size:30px; font-weight:800; letter-spacing:-.02em; }
.asset-price span { color:var(--muted); font-size:14px; font-weight:600; }
.recap { width:100%; border-collapse:collapse; margin:10px 0 12px; font-size:14px; }
.recap td { padding:6px 0; border-bottom:1px solid var(--line); color:var(--soft); }
.recap td:last-child { text-align:right; color:var(--text); font-weight:600; font-variant-numeric:tabular-nums; }
.recap tr.tot td { color:var(--text); font-weight:800; border-bottom:2px solid var(--line-2); }
.st-key-searchbar [data-baseweb="input"] { background:#0b100d; border:1px solid var(--line-2); border-radius:14px; min-height:3rem; }
.st-key-searchbar [data-baseweb="input"]:focus-within { border-color:var(--green); box-shadow:0 0 0 3px rgba(125,245,155,.15); }
.st-key-searchbar input { background:transparent no-repeat 14px center/18px
  url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%239daaa0' stroke-width='2.4' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-4-4'/%3E%3C/svg%3E");
  padding-left:44px !important; font-size:16px; color:var(--text); }
[class*="st-key-srrow_"], [class*="st-key-wlrow_"] { background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:10px 14px; }
[class*="st-key-srrow_"]:hover { border-color:var(--line-2); }
[class*="st-key-srrow_"] button, [class*="st-key-wlrow_"] button { min-height:2.3rem !important; padding:0 .6rem !important; }
.sr-name { color:var(--text); font-weight:700; font-size:15px; line-height:1.3; }
.sr-sub { color:var(--muted); font-size:12.5px; margin-top:2px; }
.sr-price { display:flex; flex-direction:column; align-items:flex-end; }
.sr-price b { color:var(--text); font-size:15px; font-variant-numeric:tabular-nums; white-space:nowrap; }
.sr-price span { font-size:13px; font-weight:700; }
.tag { display:inline-block; font-size:11px; font-weight:800; letter-spacing:.04em; padding:2px 8px; border-radius:999px; vertical-align:middle; }
.tag-held { background:var(--green-soft); color:var(--green); border:1px solid var(--green-line); }
.st-key-card_watch { padding:16px 18px; margin-bottom:6px; }
@media (max-width: 640px) {
  .sr-price { align-items:flex-start; }
  /* keep the action buttons of a result / watchlist row on one line on phones */
  :is([class*="st-key-srrow_"], [class*="st-key-wlrow_"]) [data-testid="stColumn"] [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; gap:6px !important; }
  :is([class*="st-key-srrow_"], [class*="st-key-wlrow_"]) [data-testid="stColumn"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width:0 !important; width:auto !important; flex:1 1 0 !important; }
  :is([class*="st-key-srrow_"], [class*="st-key-wlrow_"]) button p { font-size:13px; white-space:nowrap; }
}
[class*="st-key-mneg_"] div[data-testid="stMetric"] [data-testid="stMetricValue"] { color:var(--red) !important; }
.minis { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:10px; margin:4px 0 12px; }
.mini { background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:12px 14px; min-width:0; }
.mini b { display:block; font-size:20px; font-weight:800; margin:4px 0 2px; overflow-wrap:anywhere; }
.mini span { color:var(--muted); font-size:13px; }
.mover { display:flex; justify-content:space-between; gap:12px; padding:8px 0; border-bottom:1px solid var(--line); }
.mover:last-child { border-bottom:0; }
.mover span { color:var(--text); font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
/* ---------- Profile card (sidebar) ---------- */
.user-card { display:flex; align-items:center; gap:10px; margin-top:10px; padding:10px 12px; border:1px solid var(--line);
  border-radius:14px; background:var(--surface-2); }
.avatar { width:38px; height:38px; border-radius:50%; flex:none; display:grid; place-items:center; font-weight:800; font-size:17px;
  color:var(--green-ink); background:linear-gradient(135deg,#72f39a,#a0ff9d); }
.user-meta { min-width:0; display:flex; flex-direction:column; }
.user-meta b { color:var(--text); font-weight:800; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.user-meta small { color:var(--muted); font-size:12px; }

/* ---------- Rank ladder ---------- */
.ladder { display:grid; grid-template-columns:repeat(auto-fill, minmax(230px, 1fr)); gap:10px; }
.rung { display:flex; gap:12px; align-items:center; padding:12px 14px; border-radius:16px; border:1px solid var(--line); background:var(--surface); }
.rung-ico { width:44px; height:44px; border-radius:50%; flex:none; display:grid; place-items:center; font-size:22px;
  background:#0d130f; border:1px solid var(--line-2); }
.rung-body { min-width:0; flex:1; display:flex; flex-direction:column; }
.rung-body b { color:var(--text); font-weight:800; }
.rung-body span { color:var(--muted); font-size:12.5px; }
.rung-body small { color:var(--muted); font-size:12px; margin-top:4px; }
.rung.got { border-color:var(--green-line); }
.rung.got .rung-ico { background:var(--green-soft); border-color:var(--green-line); }
.rung.got small { color:var(--green); font-weight:700; }
.rung.now { border:2px solid var(--green); background:linear-gradient(145deg,#14291b,#0b100d); box-shadow:0 0 22px rgba(125,245,155,.15); }
.rung.now .rung-ico { background:linear-gradient(135deg,#72f39a,#a0ff9d); border:0; }
.rung.now small { color:var(--soft); }
.rung.next { opacity:.55; }
.rung.next .rung-ico { filter:grayscale(1); }

@media (max-width: 640px) {
  .asset-price { text-align:left; }
  .st-key-hdr_chips { justify-content:flex-start !important; }
  .hero-title { font-size:26px; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
CONTENT_FILE = Path(__file__).with_name("content.json")


@st.cache_data
def load_content(mtime):
    """Read content.json (re-read automatically whenever the file changes)."""
    data = json.loads(CONTENT_FILE.read_text(encoding="utf-8"))
    units, lessons = [], []
    for u_idx, unit in enumerate(data["units"]):
        first = len(lessons)
        for lv in unit["levels"]:
            quiz = []
            for q in lv["quiz"]:
                if not 0 <= q["answer"] < len(q["options"]):
                    raise ValueError(f"Bad answer index in '{q['question']}'")
                quiz.append((q["question"], q["options"], q["answer"], q["explanation"]))
            lessons.append({
                "unit": u_idx, "level": len(lessons) + 1, "name": lv["name"], "subtitle": lv["subtitle"],
                "minutes": lv["minutes"], "xp": lv["xp"],
                "cards": [(c["title"], c["body"]) for c in lv["cards"]], "quiz": quiz,
            })
        units.append({"number": u_idx + 1, "title": unit["title"], "description": unit["description"],
                      "color": unit["color"], "levels": list(range(first, len(lessons)))})
    return units, lessons


UNITS, LESSONS = load_content(CONTENT_FILE.stat().st_mtime)

RETURN_NOTE = ("For reference: the MSCI World index returned about 8.5% per year on average in USD over the last 20 years "
               "(2006–2025, net dividends reinvested), with big swings along the way (e.g. −41% in 2008, +30% in 2009). "
               "Measured in euros or francs the result differs, because exchange rates move too. Past performance does not predict future returns.")
DISCLAIMER = "STACK is an educational prototype. It does not provide personal financial advice, recommend investments, or connect to a broker. All examples are for learning only."

# Used as the daily challenge until the first level is completed.
FALLBACK_DAILY = ("What is diversification?", ["Putting everything into one company", "Spreading investments across different assets", "Buying and selling every day", "A guaranteed return"], 1,
                  "Diversification spreads exposure across different assets.")

DAILY_XP = 20
ANSWER_XP = 10
LETTERS = "ABCD"
# (name, icon, XP needed, short description). The full path gives ~3'960 XP (lessons + first-time correct
# answers) and portfolio badges ~100 more, so "Stacker" means finishing nearly everything and "Legend"
# also needs daily challenges on top. The gaps grow, so ranks keep coming all along the path.
RANKS = [
    ("Seedling", "🌱", 0, "Just planted"),
    ("Sprout", "🌿", 100, "First lessons done"),
    ("Sapling", "🪴", 250, "Basics are taking root"),
    ("Grower", "🌳", 500, "Foundations in place"),
    ("Saver", "💰", 850, "Knows the asset classes"),
    ("Investor", "📈", 1300, "Funds and costs make sense"),
    ("Strategist", "🧠", 1850, "Risk and biases under control"),
    ("Analyst", "🔍", 2500, "Reads the macro picture"),
    ("Portfolio pro", "💼", 3200, "Spots the red flags"),
    ("Stacker", "🏔️", 4000, "Finished the whole path"),
    ("Legend", "👑", 5000, "Daily challenges, every day"),
]
NAV = [("home", "🏠", "Home"), ("journey", "🗺️", "Journey"), ("lab", "🧪", "Money lab"), ("portfolio", "📈", "Portfolio"), ("rewards", "🏆", "Rewards"), ("profile", "👤", "Profile")]

# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
DEFAULT_PROGRESS = {
    "name": "",               # display name, as typed the first time
    "created": "",            # ISO date the profile was created
    "xp": 0,
    "completed": [],          # lesson indexes as strings
    "best_scores": {},        # lesson index -> best quiz score
    "correct_answers": [],    # "lesson:question" already rewarded with XP
    "daily": {"date": None, "done": False},
    "daily_total": 0,
    "streak": {"count": 0, "last_day": None},
    "lab_visited": False,
    "portfolio": {},          # virtual-money simulator (see portfolio.py); {} until opened
    "display_currency": "EUR",  # currency used to show Portfolio amounts (values are stored in CHF)
}


NAME_MAX = 24
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def clean_name(raw):
    """Display name: trimmed, inner spaces collapsed, at most NAME_MAX characters."""
    return " ".join(str(raw or "").split())[:NAME_MAX]


def name_slug(name):
    """Profile id used for the file name and the URL: 'Jonathan K.' -> 'jonathan-k', 'Zoé' -> 'zoe'.
    Case, accents and punctuation are ignored, so the same person always finds the same profile."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40].strip("-")


def name_error(name):
    """Why a typed name cannot be used (None if it is fine)."""
    if not name:
        return "Type a name to continue."
    slug = name_slug(name)
    if len(slug.replace("-", "")) < 2:
        return "Use at least 2 letters or digits (accents are fine)."
    return None


def supabase_conf():
    """(url, key) from the [supabase] secrets, or (None, None) when there are no secrets."""
    try:
        conf = st.secrets.get("supabase") or {}
        return conf.get("url"), conf.get("key")
    except Exception:                         # no secrets.toml at all
        return None, None


@st.cache_resource
def get_store(url, key, folder):
    """Supabase when url + key are set (online), else one JSON file per player in `folder`.
    Cached per (url, key): adding or changing the secrets takes effect without a reboot."""
    return storage.get_store({"supabase": {"url": url, "key": key}} if url and key else None, folder)


STORE = get_store(*supabase_conf(), str(USERS_DIR))


def profile_exists(slug):
    return bool(slug) and SLUG_RE.fullmatch(slug) is not None and STORE.exists(slug)


def file_mtime(slug):
    """Changes on every save of this profile (file mtime locally, updated_at online)."""
    return STORE.version(slug)


def load_progress(slug):
    data = deepcopy(DEFAULT_PROGRESS)
    saved = STORE.load(slug)
    if isinstance(saved, dict):
        for key, default in DEFAULT_PROGRESS.items():
            if key in saved and isinstance(saved[key], type(default)):
                data[key] = saved[key]
    return data


def save_progress():
    """Save the logged-in player's progress (file or Supabase, see storage.py)."""
    S = st.session_state
    if not S.get("user"):
        return
    try:
        S.progress_mtime = STORE.save(S.user, S.progress)
    except Exception as exc:                  # network hiccup online: keep playing, warn the player
        logging.getLogger("stack").warning("Could not save %s: %s", S.user, exc)
        toast("Could not save your progress right now. It will be saved with your next action.", "⚠️")


def open_profile(slug, typed_name=None):
    """Log this session into profile `slug`, creating it if needed. Returns True if it already existed."""
    S = st.session_state
    existed = profile_exists(slug)
    S.user = slug
    S.progress = load_progress(slug)
    missing = not S.progress["name"] or not S.progress["created"]
    S.progress["name"] = S.progress["name"] or typed_name or slug
    S.progress["created"] = S.progress["created"] or date.today().isoformat()
    if not existed or missing:
        save_progress()
    S.progress_mtime = file_mtime(slug)
    st.query_params["u"] = slug           # keeps the session alive across reloads and journey links
    return existed


def login_submit():
    """'Let's go' on the welcome screen."""
    S = st.session_state
    name = clean_name(S.get("login_name"))
    err = name_error(name)
    if err:
        S.login_error = err
        return
    S.login_error = None
    if open_profile(name_slug(name), name):
        toast(f"Welcome back, {S.progress['name']}! Your progress is loaded.", "👋")
    else:
        toast(f"Profile created for {name}. Let's start!", "🌱")


def logout():
    """'Switch profile': forget everything about this session (the saved file stays on disk)."""
    S = st.session_state
    for k in list(S.keys()):
        del S[k]
    st.query_params.clear()


def sync_from_disk():
    """If the same name is open in another tab or device and saved since our last render, pick up its changes."""
    S = st.session_state
    m = file_mtime(S.user)
    if m is not None and m != S.get("progress_mtime"):
        S.progress = load_progress(S.user)
        S.progress_mtime = m


UI_DEFAULTS = {
    "view": "home", "lesson_index": 0, "phase": "cards", "card_index": 0,
    "quiz_index": 0, "quiz_answer": None, "quiz_score": 0, "answer_xp": False, "quiz_orders": [],
    "lesson_xp_awarded": False, "new_best": False,
    "daily_wrong": [], "confirm_reset": False, "toasts": [], "celebrate": False,
    "pf_asset": None, "pf_quick": False, "pf_table_n": 0, "pf_confirm_reset": False, "pf_updated": None,
    "login_error": None,
}


def init_state():
    for k, v in UI_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = deepcopy(v)


init_state()
S = st.session_state
# P (the logged-in player's progress) is bound in the "Render" section, once a profile is open.

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def esc(text):
    return html.escape(str(text))


def today_iso():
    return date.today().isoformat()


def toast(msg, icon="⚡"):
    S.setdefault("toasts", []).append((msg, icon))


def touch_streak():
    s = P["streak"]
    today = date.today()
    if s["last_day"] == today.isoformat():
        return
    s["count"] = s["count"] + 1 if s["last_day"] == (today - timedelta(days=1)).isoformat() else 1
    s["last_day"] = today.isoformat()


def current_streak():
    s = P["streak"]
    alive = {today_iso(), (date.today() - timedelta(days=1)).isoformat()}
    return s["count"] if s["last_day"] in alive else 0


def add_xp(amount, reason):
    before = rank_info(P["xp"])
    P["xp"] += amount
    touch_streak()
    toast(f"+{amount} XP · {reason}")
    after = rank_info(P["xp"])
    if after["index"] > before["index"]:
        toast(f"Rank up! You are now {after['icon']} {after['name']}", "🎉")
        S.celebrate = True
    save_progress()


def completed_count():
    return len(P["completed"])


def progress_pct():
    return int(completed_count() / len(LESSONS) * 100)


def is_done(i):
    return str(i) in P["completed"]


def best_score(i):
    return P["best_scores"].get(str(i))


def is_passed(i):
    """Done with at least one correct answer: this is what unlocks the next level."""
    return is_done(i) and (best_score(i) or 0) >= 1


def is_unlocked(i):
    return i == 0 or is_passed(i - 1)


def current_level():
    """The level the learner should play next (None when the whole path is passed)."""
    return next((i for i in range(len(LESSONS)) if not is_passed(i)), None)


def stars(i):
    """0-3 stars from the best quiz score: >= 50% = 1, >= 80% = 2, 100% = 3."""
    pct = (best_score(i) or 0) / len(LESSONS[i]["quiz"])
    return 3 if pct >= 1 else 2 if pct >= 0.8 else 1 if pct >= 0.5 else 0


def rank_info(xp):
    """Current rank for an XP total: name, icon, index, lo/hi XP bounds, % to the next rank, next rank name."""
    idx = max(i for i, (_, _, lo, _) in enumerate(RANKS) if xp >= lo)
    name, icon, lo, _ = RANKS[idx]
    hi = RANKS[idx + 1][2] if idx + 1 < len(RANKS) else None
    pct = 100 if hi is None else int((xp - lo) / (hi - lo) * 100)
    return {"name": name, "icon": icon, "index": idx, "lo": lo, "pct": pct, "hi": hi,
            "next": RANKS[idx + 1][0] if hi is not None else None}


def daily_done():
    return P["daily"].get("date") == today_iso() and P["daily"].get("done")


def daily_question():
    """Today's question, drawn at random from completed levels and stored so it stays fixed all day.
    Returns (question tuple, shuffled option order)."""
    d = P["daily"]
    pool = [(i, qi) for i in sorted(int(k) for k in P["completed"] if int(k) < len(LESSONS))
            for qi in range(len(LESSONS[i]["quiz"]))]
    ref = d.get("q")
    valid = (d.get("date") == today_iso() and isinstance(ref, list) and len(ref) == 2
             and ref[0] < len(LESSONS) and ref[1] < len(LESSONS[ref[0]]["quiz"]))
    if not valid and not (d.get("date") == today_iso() and d.get("done")):
        ref = list(random.Random(date.today().toordinal()).choice(pool)) if pool else None
        P["daily"] = {"date": today_iso(), "done": False, "q": ref}
        save_progress()
    question = LESSONS[ref[0]]["quiz"][ref[1]] if ref else FALLBACK_DAILY
    order = random.Random(f"{today_iso()}-{ref}").sample(range(len(question[1])), len(question[1]))
    return question, order


def has_perfect_score():
    return any(P["best_scores"].get(str(i), 0) == len(l["quiz"]) for i, l in enumerate(LESSONS))


def eur(x):
    """Money lab amounts (illustrative, always in euros)."""
    return "EUR " + f"{x:,.0f}".replace(",", "'")


# ---------------------------------------------------------------------------
# Callbacks (run before the page re-renders, so every click is handled exactly once)
# ---------------------------------------------------------------------------
def go_to(view):
    S.view = view
    S.confirm_reset = False


def start_lesson(i):
    S.update(view="lesson", lesson_index=i, phase="cards", card_index=0,
             quiz_index=0, quiz_answer=None, quiz_score=0)


def prev_card():
    S.card_index = max(0, S.card_index - 1)


def next_card():
    S.card_index = min(len(LESSONS[S.lesson_index]["cards"]) - 1, S.card_index + 1)


def start_quiz():
    quiz = LESSONS[S.lesson_index]["quiz"]
    orders = [random.sample(range(len(q[1])), len(q[1])) for q in quiz]   # new order every attempt
    S.update(phase="quiz", quiz_index=0, quiz_answer=None, quiz_score=0, quiz_orders=orders)


def answer_quiz(choice):
    if S.quiz_answer is not None:   # question already answered: locked
        return
    idx, qi = S.lesson_index, S.quiz_index
    S.quiz_answer = choice
    S.answer_xp = False
    if choice == LESSONS[idx]["quiz"][qi][2]:
        S.quiz_score += 1
        key = f"{idx}:{qi}"
        if key not in P["correct_answers"]:
            P["correct_answers"].append(key)
            add_xp(ANSWER_XP, "Correct answer")
            S.answer_xp = True
        else:
            toast("Correct! XP for this question was already earned.", "✅")


def next_question():
    S.quiz_index += 1
    S.quiz_answer = None
    if S.quiz_index >= len(LESSONS[S.lesson_index]["quiz"]):
        finish_lesson()


def finish_lesson():
    idx = S.lesson_index
    key = str(idx)
    lesson = LESSONS[idx]
    previous = P["best_scores"].get(key)
    P["best_scores"][key] = max(previous or 0, S.quiz_score)
    S.new_best = previous is not None and S.quiz_score > previous
    S.lesson_xp_awarded = key not in P["completed"]
    if S.lesson_xp_awarded:
        P["completed"].append(key)
        add_xp(lesson["xp"], f"{lesson['name']} complete")
    if S.quiz_score == len(lesson["quiz"]):
        toast("Perfect score!", "🎯")
    S.phase = "done"
    S.celebrate = True
    save_progress()


def answer_daily(choice):
    if daily_done():
        return
    if choice == daily_question()[0][2]:
        P["daily"]["done"] = True
        P["daily_total"] += 1
        S.daily_wrong = []
        add_xp(DAILY_XP, "Daily challenge")
    elif choice not in S.daily_wrong:
        S.daily_wrong.append(choice)


def reset_progress():
    """Erase this player's progress but keep the profile itself (name, creation date)."""
    keep = {k: S.progress[k] for k in ("name", "created")}
    S.progress = {**deepcopy(DEFAULT_PROGRESS), **keep}
    save_progress()
    for k, v in UI_DEFAULTS.items():
        S[k] = deepcopy(v)
    S.view = "profile"
    toast("Progress reset", "🔄")


# ---------------------------------------------------------------------------
# UI building blocks
# ---------------------------------------------------------------------------
def answer_buttons(prefix, options, correct, on_pick, selected=None, wrong=(), order=None):
    """A/B/C/D buttons shown in `order`. Callbacks receive the ORIGINAL option index.
    Once `selected` is set the question is locked and coloured."""
    locked = selected is not None
    for pos, i in enumerate(order or range(len(options))):
        opt = options[i]
        if locked:
            state = "ok" if i == correct else ("bad" if i == selected else "off")
        else:
            state = "bad" if i in wrong else "idle"
        with st.container(key=f"ans_{state}_{prefix}_{i}"):
            st.button(f"**{LETTERS[pos]}** · {opt}", key=f"btn_{prefix}_{i}", on_click=on_pick, args=(i,),
                      disabled=locked or i in wrong, width="stretch")


def chips():
    """The rank / XP / streak chips of the page header, one HTML snippet each."""
    r = rank_info(P["xp"])
    sub = "Top rank reached" if r["hi"] is None else f"{P['xp']} / {r['hi']} XP to {r['next']}"
    streak = current_streak()
    return [
        f'<div class="chip chip-rank"><div class="chip-row"><b>{r["icon"]} {esc(r["name"])}</b><small>· {esc(sub)}</small></div>'
        f'<div class="bar"><i style="width:{r["pct"]}%"></i></div></div>',
        f'<div class="chip"><b>⚡ {P["xp"]}</b><small>XP</small></div>',
        f'<div class="chip"><b>🔥 {streak}</b><small>day{"s" if streak != 1 else ""}</small></div>',
    ]


def page_header(title, subtitle, currency_picker=False):
    """Title on the left; chips (and the currency picker) on the right, in ONE horizontal flex row so they share
    the same line, the same 8px spacing and — through --chip-h in the CSS — exactly the same height."""
    left, right = st.columns([1, 1.45] if currency_picker else [1.25, 1], vertical_alignment="center")
    left.markdown(f'<h1 class="page-title">{esc(title)}</h1><p class="page-sub">{esc(subtitle)}</p>', unsafe_allow_html=True)
    with right, st.container(key="hdr_chips", horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
        for chip in chips():
            st.markdown(chip, unsafe_allow_html=True, width="content")
        if currency_picker:
            currency_select("pf_ccy", label_visibility="collapsed", width=112)
    st.write("")


def sidebar():
    with st.sidebar:
        st.markdown(
            '<div class="logo"><div class="logo-mark">🌱</div>'
            '<div><span class="logo-text">STACK</span><span class="logo-sub">Learn investing, step by step</span></div></div>',
            unsafe_allow_html=True,
        )
        active = "journey" if S.view == "lesson" else S.view
        for view, icon, label in NAV:
            with st.container(key=f"nav_{'on' if view == active else 'off'}_{view}"):
                st.button(f"{icon}  {label}", key=f"navbtn_{view}", on_click=go_to, args=(view,), width="stretch")
        st.markdown(
            f'<div class="side-note"><b>{completed_count()}/{len(LESSONS)}</b> <span class="muted">lessons completed</span>'
            f'<div class="bar"><i style="width:{progress_pct()}%"></i></div></div>',
            unsafe_allow_html=True,
        )
        r = rank_info(P["xp"])
        name = P["name"] or S.user
        st.markdown(
            f'<div class="user-card"><div class="avatar">{esc(name[:1].upper())}</div>'
            f'<div class="user-meta"><b>{esc(name)}</b><small>{r["icon"]} {esc(r["name"])} · {P["xp"]} XP</small></div></div>',
            unsafe_allow_html=True,
        )
        with st.container(key="nav_off_switch"):
            st.button("↩  Switch profile", key="logout_btn", on_click=logout, width="stretch",
                      help="Your progress stays saved under this name. Type it again later to pick up where you left off.")


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def greeting():
    h = __import__("datetime").datetime.now().hour
    return "Good morning" if h < 12 else ("Good afternoon" if h < 18 else "Good evening")


def home_page():
    page_header(f"{greeting()}! 👋", "Understand money, one small lesson at a time.")

    nxt = current_level()
    with st.container(key="card_hero"):
        if nxt is None:
            st.markdown('<span class="pill">PATH COMPLETE</span><div class="hero-title">You completed the STACK learning path 🎓</div>'
                        '<p class="muted">Great work! Replay any lesson to beat your best score.</p>', unsafe_allow_html=True)
            st.button("Go to journey →", type="primary", on_click=go_to, args=("journey",), key="hero_journey")
        else:
            l = LESSONS[nxt]
            retry = is_done(nxt)
            st.markdown(
                f'<span class="pill">{"TRY AGAIN" if retry else "UP NEXT"} · UNIT {l["unit"] + 1} · LEVEL {l["level"]}</span>'
                f'<div class="hero-title">{esc(l["name"])}</div>'
                f'<p class="muted">{esc(l["subtitle"])} · {l["minutes"]} min · +{l["xp"]} XP</p>'
                '<p class="muted">Five-minute lessons, quick quizzes and small wins. No pressure to invest real money.</p>',
                unsafe_allow_html=True,
            )
            st.button("Retry lesson →" if retry else "Start lesson →", type="primary",
                      on_click=start_lesson, args=(nxt,), key="hero_start")

    st.write("")
    st.markdown(garden.garden_html(P["xp"]) + garden.garden_stats_html(P["xp"]), unsafe_allow_html=True)

    st.write("")
    r = rank_info(P["xp"])
    to_next = "Top rank reached" if r["hi"] is None else f"{r['hi'] - P['xp']} XP to {r['next']}"
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f'<div class="stat"><div class="ring" style="--p:{progress_pct()}"><span>{progress_pct()}%</span></div>'
        f'<div><div class="stat-label">Progress</div><div class="stat-value">{completed_count()}/{len(LESSONS)}</div>'
        '<div class="stat-sub">lessons completed</div></div></div>', unsafe_allow_html=True)
    c2.markdown(
        f'<div class="stat"><div class="stat-icon">⚡</div><div><div class="stat-label">Total XP</div>'
        f'<div class="stat-value">{P["xp"]}</div><div class="stat-sub">{to_next}</div></div></div>', unsafe_allow_html=True)
    c3.markdown(
        f'<div class="stat"><div class="stat-icon">{r["icon"]}</div><div><div class="stat-label">Rank</div>'
        f'<div class="stat-value">{r["name"]}</div><div class="bar"><i style="width:{r["pct"]}%"></i></div></div></div>',
        unsafe_allow_html=True)

    st.write("")
    (q, options, correct, explanation), order = daily_question()
    with st.container(key="card_daily"):
        st.markdown(f'<span class="pill">DAILY CHALLENGE · +{DAILY_XP} XP</span>'
                    f'<div class="big-title">⚡ {esc(q)}</div>', unsafe_allow_html=True)
        if daily_done():
            answer_buttons("daily", options, correct, answer_daily, selected=correct, order=order)
            st.success(f"Daily challenge completed · +{DAILY_XP} XP earned. Come back tomorrow for a new question!")
            st.markdown(f'<div class="explain">{esc(explanation)}</div>', unsafe_allow_html=True)
        else:
            answer_buttons("daily", options, correct, answer_daily, wrong=S.daily_wrong, order=order)
            if S.daily_wrong:
                st.error("Not quite. Try again!")


# Journey map geometry (px). Nodes zigzag inside a 320px column centred in the page.
MAP_W = 320
MAP_STEP = 225        # vertical distance between two nodes of the same unit
NODE = 80             # node diameter
BANNER_H = 112        # unit banner height
ZIGZAG = [0, 70, 0, -70]  # centre, right, centre, left, centre, ...


def map_layout():
    """Banner tops, node centres and total height for the whole multi-unit map."""
    y, banners, centres = 0, [], [None] * len(LESSONS)
    for unit in UNITS:
        banners.append(y)
        y += BANNER_H + 80                      # room for the START bubble
        for k, i in enumerate(unit["levels"]):
            centres[i] = (MAP_W / 2 + ZIGZAG[k % len(ZIGZAG)], y + NODE / 2)
            y += MAP_STEP
        y += NODE + 95 - MAP_STEP               # room for the last label before the next banner
    return banners, centres, y


def mascot():
    """Placeholder for the future mascot. Replace the returned HTML with your character."""
    return '<div class="mascot" title="Your future STACK mascot">🌱</div>'


def col(x):
    """Horizontal position inside the centred 320px column."""
    return f"calc(50% - {MAP_W / 2}px + {x}px)"


def unit_banner_html(unit, top):
    levels = unit["levels"]
    done = sum(1 for i in levels if is_done(i))
    locked = "" if is_unlocked(levels[0]) else " locked"
    pct = int(done / len(levels) * 100)
    return (f'<div class="unit-banner{locked}" style="top:{top}px;height:{BANNER_H}px;--accent:{unit["color"]}">'
            f'<div class="unit-kicker">UNIT {unit["number"]} · {done}/{len(levels)} LEVELS</div>'
            f'<div class="unit-title">{esc(unit["title"])}</div>'
            f'<div class="unit-desc">{esc(unit["description"])}</div>'
            f'<div class="bar"><i style="width:{pct}%"></i></div></div>')


def deco_html(name, side, gap, top, size, rng, alt=False):
    """One floating illustration. `gap` = distance (px) between the map centre and the illustration's
    near edge; on narrow screens it is clamped so the illustration stays inside the map."""
    svg = DECOR.get(name)
    if not svg:
        return ""
    edge = f"{'right' if side < 0 else 'left'}:min(calc(50% + {gap}px), calc(100% - {size}px))"
    style = (f"{edge};top:{top - size / 2:.0f}px;--s:{size}px;--o:{rng.uniform(.5, .8):.2f};"
             f"--r:{rng.uniform(-14, 14):.0f}deg;--d:{rng.uniform(5, 9):.1f}s;--dl:-{rng.uniform(0, 6):.1f}s")
    return f'<div class="deco{" alt" if alt else ""}" style="{style}">{svg}</div>'


def map_background_html(banners, centres, height):
    """Unit zones, soft blobs and themed illustrations, drawn behind the path and the nodes."""
    parts = []
    for u, unit in enumerate(UNITS):
        top = max(banners[u] - 24, 0)
        bottom = banners[u + 1] - 24 if u + 1 < len(UNITS) else height
        parts.append(f'<div class="zone" style="top:{top}px;height:{bottom - top}px;--accent:{unit["color"]}"></div>')
        for k, (side, rgb) in enumerate(((-1, "125,245,155"), (1, "124,196,255"))):
            size = 380 if k == 0 else 320
            y = top + (bottom - top) * (0.35 if k == 0 else 0.75)
            parts.append(f'<div class="blob" style="{"left" if side < 0 else "right"}:-{size // 3}px;top:{y - size / 2:.0f}px;'
                         f'width:{size}px;height:{size}px;background:radial-gradient(circle, rgba({rgb},.10), rgba({rgb},0) 70%)"></div>')

    current = current_level()
    for u, unit in enumerate(UNITS):
        names = UNIT_DECOR[u % len(UNIT_DECOR)] if UNIT_DECOR else []
        if not names:
            continue
        levels, n = unit["levels"], 0
        for k, i in enumerate(levels):
            rng = random.Random(i * 31 + 7)
            x, y = centres[i]
            dx = x - MAP_W / 2
            # Beside the node, on the side away from it (centre nodes: away from the next node).
            nxt = centres[levels[k + 1]][0] - MAP_W / 2 if k + 1 < len(levels) else centres[levels[k - 1]][0] - MAP_W / 2
            side = -1 if (dx or nxt) > 0 else 1
            if i != current:   # leave the mascot slot free
                gap = rng.randint(80, 250) if dx else rng.randint(100, 260)
                parts.append(deco_html(names[n % len(names)], side, gap, y - 20, rng.randint(60, 110), rng))
                n += 1
            # Between this node and the next one, opposite the bend of the path (skipped before a banner).
            if k + 1 < len(levels):
                ndx = centres[levels[k + 1]][0] - MAP_W / 2
                mside = -1 if (dx or ndx) > 0 else 1
                parts.append(deco_html(names[n % len(names)], mside, rng.randint(140, 330), y + MAP_STEP / 2 + 10,
                                       rng.randint(80, 140), rng, alt=True))
                n += 1
    return "".join(parts)


def journey_map_html():
    banners, centres, height = map_layout()
    background = map_background_html(banners, centres, height)

    # Curved dashed path between consecutive nodes (also across units): green once the next node is reached.
    paths = []
    for i in range(len(LESSONS) - 1):
        (x1, y1), (x2, y2) = centres[i], centres[i + 1]
        bend = min(MAP_STEP, y2 - y1) / 2
        d = f"M{x1},{y1} C{x1},{y1 + bend} {x2},{y2 - bend} {x2},{y2}"
        cls = "seg done" if is_unlocked(i + 1) else "seg"
        paths.append(f'<path class="{cls}" d="{d}"/>')
    svg = (f'<svg class="map-svg" width="{MAP_W}" height="{height}" viewBox="0 0 {MAP_W} {height}" '
           f'style="left:{col(0)}" aria-hidden="true">{"".join(paths)}</svg>')

    parts = [unit_banner_html(u, top) for u, top in zip(UNITS, banners)]
    current = current_level()
    for i, lesson in enumerate(LESSONS):
        x, y = centres[i]
        done, unlocked = is_done(i), is_unlocked(i)
        state = "done" if done else ("open" if unlocked else "locked")
        inner = "✓" if done else (str(lesson["level"]) if unlocked else "🔒")
        extra = ""
        if done:
            k = stars(i)
            extra = f'<div class="stars" aria-label="{k} of 3 stars">{"★" * k}<span>{"★" * (3 - k)}</span></div>'
        bubble = f'<div class="bubble">{"RETRY" if done else "START"}</div>' if i == current else ""
        action = "Replay" if done else ("Start" if unlocked else "Locked")
        parts.append(
            f'<div class="node-wrap {state}" style="left:{col(x)};top:{y - NODE / 2}px;--accent:{UNITS[lesson["unit"]]["color"]}">'
            f'{bubble}<a class="node {state}" href="?u={S.user}&start={i}" target="_self" '
            f'aria-label="{action} level {lesson["level"]}: {esc(lesson["name"])}">{inner}</a>'
            f'{extra}<div class="node-name">{esc(lesson["name"])}</div>'
            f'<div class="node-xp">+{lesson["xp"]} XP</div></div>'
        )

    # Empty slot beside the current node for the mascot (opposite side of the zigzag).
    if current is not None:
        x, y = centres[current]
        mx = x - 105 if x > MAP_W / 2 else x + 105
        parts.append(f'<div class="mascot-slot" style="left:{col(mx)};top:{y - 30}px">{mascot()}</div>')

    return f'<div class="map" style="height:{height}px">{background}{svg}{"".join(parts)}</div>'


def journey_page():
    page_header("Your learning journey",
                f"{len(UNITS)} units · {len(LESSONS)} levels. Get at least 1 correct answer to unlock the next level.")
    st.markdown(journey_map_html(), unsafe_allow_html=True)


def steps_html(lesson):
    n_cards, n_q = len(lesson["cards"]), len(lesson["quiz"])
    cur = S.card_index if S.phase == "cards" else n_cards + S.quiz_index
    segs = []
    for s in range(n_cards + n_q):
        cls = "done" if s < cur else ("cur" if s == cur else ("q" if s >= n_cards else ""))
        segs.append(f'<i class="{cls}"></i>')
    if S.phase == "cards":
        label = f"Card {S.card_index + 1} of {n_cards} · then {n_q} quiz questions"
    else:
        label = f"Question {S.quiz_index + 1} of {n_q}"
    return f'<div class="steps">{"".join(segs)}</div><div class="steps-label">{label}</div>'


def lesson_page():
    idx = S.lesson_index
    lesson = LESSONS[idx]
    unit = UNITS[lesson["unit"]]
    page_header(f"Level {lesson['level']}: {lesson['name']}", f"Unit {unit['number']} · {unit['title']} — {lesson['subtitle']}")

    if S.phase == "done":
        return lesson_done(lesson)

    st.markdown(steps_html(lesson), unsafe_allow_html=True)

    if S.phase == "cards":
        title, body = lesson["cards"][S.card_index]
        st.markdown(f'<div class="stack-card" style="padding:34px 36px"><span class="pill">STACK CLASS</span>'
                    f'<div class="big-title" style="font-size:32px">{esc(title)}</div>'
                    f'<p class="big-body">{esc(body)}</p></div>', unsafe_allow_html=True)
        c1, _, c2 = st.columns([1, 2, 1])
        c1.button("← Previous", on_click=prev_card, disabled=S.card_index == 0, key="prev_card", width="stretch")
        if S.card_index < len(lesson["cards"]) - 1:
            c2.button("Continue →", type="primary", on_click=next_card, key="next_card", width="stretch")
        else:
            c2.button("Start quiz →", type="primary", on_click=start_quiz, key="start_quiz", width="stretch")
        return

    # Quiz phase
    qi = S.quiz_index
    q, options, correct, explanation = lesson["quiz"][qi]
    with st.container(key="card_quiz"):
        st.markdown(f'<span class="pill">🧠 QUICK QUIZ · +{ANSWER_XP} XP</span><div class="big-title">{esc(q)}</div>',
                    unsafe_allow_html=True)
        order = S.quiz_orders[qi] if qi < len(S.quiz_orders) else None
        answer_buttons(f"q{idx}_{qi}", options, correct, answer_quiz, selected=S.quiz_answer, order=order)
        if S.quiz_answer is not None:
            ok = S.quiz_answer == correct
            if ok:
                st.success(f"Correct! +{ANSWER_XP} XP" if S.answer_xp else "Correct! (XP for this question already earned)")
            else:
                pos = order.index(correct) if order else correct
                st.error(f"Not quite. The right answer is {LETTERS[pos]}.")
            st.markdown(f'<div class="explain{"" if ok else " bad"}">{esc(explanation)}</div>', unsafe_allow_html=True)
            last = qi == len(lesson["quiz"]) - 1
            st.button("See results →" if last else "Next question →", type="primary", on_click=next_question, key="next_q")


def lesson_done(lesson):
    idx = S.lesson_index
    n = len(lesson["quiz"])
    perfect = S.quiz_score == n
    if S.lesson_xp_awarded:
        gain = f'<div class="xp-gain">+{lesson["xp"]} XP lesson bonus</div>'
    else:
        gain = '<div class="xp-gain">Lesson XP already earned · replay keeps your best score</div>'
    best = P["best_scores"].get(str(idx), S.quiz_score)
    note = "🎯 Perfect score! Keep building your knowledge." if perfect else "Good effort. Review the lesson cards if you want to practise again."
    if S.new_best:
        note = "🏅 New best score! " + note
    if not is_passed(idx) and idx < len(LESSONS) - 1:
        note = "🔒 Try again to unlock the next level — you need at least 1 correct answer."
    with st.container(key="card_done"):
        st.markdown(
            '<div class="done-wrap"><div class="done-emoji">🎉</div>'
            '<div class="big-title">Lesson complete!</div>'
            f'<div class="done-score">{S.quiz_score}/{n}</div><div class="muted">correct answers · best {best}/{n}</div>'
            f'{gain}<p class="muted" style="margin-top:14px">{note}</p></div>',
            unsafe_allow_html=True,
        )
        _, c1, c2, _ = st.columns([1, 1.3, 1.6, 1])
        c1.button("↻ Replay", on_click=start_lesson, args=(idx,), key="done_replay", width="stretch")
        c2.button("Back to journey →", type="primary", on_click=go_to, args=("journey",), key="done_journey", width="stretch")


def lab_page():
    if not P["lab_visited"]:
        P["lab_visited"] = True
        save_progress()
        st.toast("Badge unlocked: Lab rat", icon="🧪")
    page_header("Money lab", "Explore how compound growth could work over time.")

    left, right = st.columns([1, 1.7], gap="large")
    with left:
        with st.container(key="card_lab"):
            start = st.number_input("Starting amount (EUR)", min_value=0, value=1_000, step=100)
            st.caption(f"= {eur(start)}")
            monthly = st.number_input("Monthly saving (EUR)", min_value=0, value=100, step=50)
            st.caption(f"= {eur(monthly)} per month")
            rate = st.number_input("Assumed annual return (%)", min_value=-20.0, value=7.0, step=0.1, format="%.1f")
            st.markdown(f'<div class="lab-note">{esc(RETURN_NOTE)}</div>', unsafe_allow_html=True)
            years = st.number_input("Duration (years)", min_value=1, value=20, step=1)

    # Compounded monthly, contributions at the end of each month (closed form per year, so long durations stay fast).
    r = rate / 100 / 12
    g = (1 + r) ** 12
    yearly_add = monthly * ((g - 1) / r if r else 12)
    balance, paid = float(start), float(start)
    xs, values, paid_in = [0], [balance], [paid]
    if years > 500:
        st.warning("Please choose a duration of 500 years or less to see the simulation.")
        return
    for year in range(1, int(years) + 1):
        balance = balance * g + yearly_add
        paid += monthly * 12
        xs.append(year)
        values.append(balance)
        paid_in.append(paid)
    if not math.isfinite(balance) or balance > 1e15:
        st.warning("These numbers are too large to show. Try a shorter duration or a lower return.")
        return
    growth = balance - paid
    share = growth / balance * 100 if balance > 0 else 0

    with right:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=xs, y=paid_in, name="Total paid in", mode="lines",
                                 line=dict(color="#5b8fcc", width=2), fill="tozeroy", fillcolor="rgba(91,143,204,.18)",
                                 hovertemplate="%{y:,.0f} EUR<extra>Total paid in</extra>"))
        fig.add_trace(go.Scatter(x=xs, y=values, name="Invested + growth", mode="lines",
                                 line=dict(color="#2fa862", width=2), fill="tonexty", fillcolor="rgba(47,168,98,.22)",
                                 hovertemplate="%{y:,.0f} EUR<extra>Invested + growth</extra>"))
        for y, label in ((values[-1], "Invested + growth"), (paid_in[-1], "Total paid in")):
            fig.add_annotation(x=xs[-1], y=y, text=label, showarrow=False, xanchor="right", yanchor="bottom",
                               font=dict(color="#d3dbd5", size=12))
        fig.update_layout(
            height=380, margin=dict(l=10, r=10, t=40, b=10), hovermode="x unified", separators=".'",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#9daaa0"),
            legend=dict(orientation="h", y=1.12, x=0, font=dict(color="#d3dbd5")),
            hoverlabel=dict(bgcolor="#111914", bordercolor="#2f4536", font=dict(color="#f4f7f4")),
        )
        fig.update_xaxes(title="Years", gridcolor="#1a261e", zeroline=False, linecolor="#25352a")
        fig.update_yaxes(title=None, gridcolor="#1a261e", zeroline=False, separatethousands=True, ticksuffix=" EUR")
        st.plotly_chart(fig, config={"displayModeBar": False}, width="stretch")

        m1, m2 = st.columns(2)
        m1.metric("Final value (illustrative)", eur(balance), f"{eur(paid)} paid in", delta_color="off")
        m2.metric("Due to growth", eur(growth), f"{share:.0f}% of final value", delta_color="off")
    st.info("This simulation is illustrative only. It assumes a constant return every year, which never happens in reality: "
            "actual returns vary, can be negative, and fees, taxes and inflation are not included. It is not a forecast or advice.")


def badges():
    return [
        ("🌱", "First steps", "Complete your first lesson", completed_count() >= 1),
        ("📚", "Curious learner", "Complete three lessons", completed_count() >= 3),
        ("🎓", "STACK scholar", f"Complete all {len(LESSONS)} levels", completed_count() == len(LESSONS)),
        ("🎯", "Sharp mind", "Get a perfect score on a quiz", has_perfect_score()),
        ("⚡", "XP explorer", "Earn 200 XP", P["xp"] >= 200),
        ("☀️", "Daily thinker", "Complete a daily challenge", P["daily_total"] >= 1),
        ("🧪", "Lab rat", "Open the Money lab", P["lab_visited"]),
    ] + [(ico, t, d, key in P["portfolio"].get("earned", [])) for key, ico, t, d in PF_BADGES]


def rewards_page():
    items = badges()
    unlocked = sum(1 for b in items if b[3])
    page_header("Rewards", f"{unlocked} of {len(items)} badges unlocked. Keep learning to collect them all.")
    cards = "".join(
        f'<div class="reward{"" if ok else " locked"}"><div class="ico">{ico}</div><div class="t">{esc(t)}</div>'
        f'<div class="d">{esc(d)}</div><div class="s">{"✓ UNLOCKED" if ok else "🔒 LOCKED"}</div></div>'
        for ico, t, d, ok in items
    )
    st.markdown(f'<div class="badges">{cards}</div>', unsafe_allow_html=True)


def rank_ladder_html():
    """Every rank as a step: reached ones in green, the current one highlighted with its progress bar."""
    xp = P["xp"]
    r = rank_info(xp)
    steps = []
    for i, (name, icon, lo, desc) in enumerate(RANKS):
        if i < r["index"]:
            state, foot = "got", "<small>✓ Reached</small>"
        elif i == r["index"]:
            left = "Top rank reached" if r["hi"] is None else f"{xp_fmt(r['hi'] - xp)} XP to {r['next']}"
            state, foot = "now", f'<div class="bar"><i style="width:{r["pct"]}%"></i></div><small>{esc(left)}</small>'
        else:
            state, foot = "next", f"<small>{xp_fmt(lo - xp)} XP to go</small>"
        steps.append(f'<div class="rung {state}"><div class="rung-ico">{icon}</div><div class="rung-body">'
                     f'<b>{esc(name)}</b><span>{xp_fmt(lo)} XP · {esc(desc)}</span>{foot}</div></div>')
    return f'<div class="ladder">{"".join(steps)}</div>'


def xp_fmt(n):
    return f"{n:,}".replace(",", "'")


def profile_page():
    page_header(f"{P['name']}'s profile" if P["name"] else "Your STACK profile",
                f"Playing since {P['created'] or today_iso()} · progress saved under this name.")
    r = rank_info(P["xp"])
    perfect = sum(1 for i, l in enumerate(LESSONS) if P["best_scores"].get(str(i), 0) == len(l["quiz"]))
    c1, c2, c3 = st.columns(3)
    c1.metric("Total XP", P["xp"])
    c2.metric("Rank", f"{r['icon']} {r['name']}")
    c3.metric("Learning streak", f"{current_streak()} day{'s' if current_streak() != 1 else ''}")
    c4, c5, c6 = st.columns(3)
    c4.metric("Lessons completed", f"{completed_count()}/{len(LESSONS)}")
    c5.metric("Perfect quizzes", perfect)
    c6.metric("Daily challenges", P["daily_total"])

    st.write("")
    st.markdown("#### Rank ladder")
    st.markdown(rank_ladder_html(), unsafe_allow_html=True)

    st.write("")
    with st.container(key="card_settings"):
        st.markdown("**Settings**", unsafe_allow_html=True)
        c, _ = st.columns([1, 1.6])
        with c:
            currency_select("prof_ccy")
        st.caption("Used for every amount on the Portfolio page.")
    st.write("")
    with st.container(key="card_reset"):
        st.markdown("**Reset progress**  \n<span class='muted'>Erase XP, lessons, scores, streak, badges and the virtual portfolio.</span>", unsafe_allow_html=True)
        if not S.confirm_reset:
            if st.button("Reset demo progress", key="reset_ask"):
                S.confirm_reset = True
                st.rerun()
        else:
            st.warning("Are you sure? This permanently erases all your progress.")
            a, b, _ = st.columns([1, 1, 2])
            a.button("Yes, reset everything", type="primary", on_click=reset_progress, key="reset_yes", width="stretch")
            b.button("Cancel", on_click=go_to, args=("profile",), key="reset_no", width="stretch")


# ---------------------------------------------------------------------------
# Portfolio simulator (virtual money, real prices). Maths in portfolio.py, data in market_data.py.
# ---------------------------------------------------------------------------
PF_BADGES = [
    ("first_trade", "🤝", "First trade", "Buy your first asset in the Portfolio simulator"),
    ("diversified", "🧺", "Diversified", "Hold stocks, ETFs, commodities and crypto at the same time"),
    ("global", "🌍", "Global investor", "Hold assets in at least 3 different currencies"),
    ("long_term", "⏳", "Long-term thinker", "Keep a position open for 30 days"),
    ("beat_market", "🏁", "Beat the market", "Beat MSCI World over 1 month (time-weighted return)"),
]
PF_BADGE_XP = {"first_trade": 50, "diversified": 50}
CLASS_KEYS = {"Stocks": "stock", "ETFs": "etf", "Commodities": "commodity", "Crypto": "crypto"}
DONUT = ["#2fa862", "#5b8fcc", "#b8862a", "#8f6fd6", "#d4664f", "#2aa898"]   # validated on the dark surface
OTHER_GREY = "#5d6a61"
UP, DOWN = "#7df59b", "#ff7b7b"
DATA_NOTE = ("Data: Yahoo Finance. Prices can be delayed by about 15 minutes depending on the exchange. "
             "Amounts are converted with Yahoo FX rates.")


def seg(label, options, default=None, key=None, label_visibility="collapsed"):
    """Segmented pills (a horizontal radio styled by CSS: testable with AppTest, unlike segmented_control)."""
    if S.get(key) not in options:
        S[key] = default if default in options else options[0]
    with st.container(key=f"seg_{key}"):
        return st.radio(label, options, key=key, horizontal=True, label_visibility=label_visibility)


def pf():
    return P["portfolio"]


DISPLAY_CURRENCIES = {"EUR": "EUR €", "CHF": "CHF", "USD": "USD $", "GBP": "GBP £", "JPY": "JPY ¥", "CNY": "CNY ¥",
                      "HKD": "HKD HK$", "CAD": "CAD C$", "AUD": "AUD A$", "SEK": "SEK kr", "NOK": "NOK kr",
                      "SGD": "SGD S$", "INR": "INR ₹"}


def disp():
    """Display currency code (falls back to CHF if its FX rate cannot be loaded)."""
    code = P.get("display_currency", "EUR")
    return code if code in DISPLAY_CURRENCIES and to_disp_rate(code) else "CHF"


def to_disp_rate(code=None):
    """Multiply a CHF amount by this to get the display currency (Yahoo rate, 5-min cache)."""
    code = code or P.get("display_currency", "EUR")
    if code == "CHF":
        return 1.0
    rate = md.fx_now((code,)).get(code, (None, None))[0]      # CHF per 1 unit of `code`
    return 1 / rate if rate else None


def to_disp(x_chf):
    return x_chf * to_disp_rate(disp())


def from_disp(x):
    return x / to_disp_rate(disp())


def set_display_currency(key):
    P["display_currency"] = S[key]
    save_progress()
    if to_disp_rate(S[key]):
        toast(f"Amounts now shown in {S[key]}", "💱")
    else:
        toast(f"No exchange rate for {S[key]} right now: showing CHF", "⚠️")


def currency_select(key, label="Display currency", label_visibility="visible", width="stretch"):
    S[key] = P.get("display_currency", "EUR")
    st.selectbox(label, list(DISPLAY_CURRENCIES), format_func=DISPLAY_CURRENCIES.get, key=key, width=width,
                 on_change=set_display_currency, args=(key,), label_visibility=label_visibility,
                 help="Portfolio amounts are stored in CHF and shown in this currency at today's Yahoo exchange rate.")


def money_chf(x, dec=2):
    """Always CHF, never converted."""
    return f"CHF {x:,.{dec}f}".replace(",", "'")


def money(x, cur="CHF", dec=2):
    """Format an amount. CHF amounts are converted into the display currency."""
    if cur == "CHF" and disp() != "CHF":
        x, cur = to_disp(x), disp()
    return f"{cur} {x:,.{dec}f}".replace(",", "'")


def signed(x, cur="CHF", dec=2):
    """'+CHF 12.30' / '-CHF 12.30' (st.metric reads the leading sign to colour the delta). Sign is kept through conversion."""
    return f"{'+' if x >= 0 else '-'}{money(abs(x), cur, dec)}"   # rates are > 0, so the sign survives conversion


def price_fmt(x, cur):
    return money(x, cur, 2 if abs(x) >= 1 else 6)


def qty_fmt(x):
    return f"{x:,.6f}".rstrip("0").rstrip(".").replace(",", "'")


def signed_metric(col, label, number, value, delta, delta_color="normal"):
    """st.metric whose value turns red when the number is negative."""
    with col.container(key=f"m{'neg' if number < 0 else 'pos'}_{label.replace(' ', '_').replace('/', '')}"):
        st.metric(label, value, delta, delta_color=delta_color)


def mini_stats(items):
    """Compact stat row (label, value, sub, color) that never truncates, unlike st.metric in narrow columns."""
    cells = "".join(f'<div class="mini"><div class="stat-label">{esc(l)}</div><b style="color:{c}">{esc(v)}</b>'
                    f'<span>{esc(sub)}</span></div>' for l, v, sub, c in items)
    st.markdown(f'<div class="minis">{cells}</div>', unsafe_allow_html=True)


def pf_live_quotes(tickers):
    """Live quotes, shared across the whole page for 5 minutes so every screen shows the same price."""
    book = S.setdefault("pf_quotes", {})            # ticker -> (quote, epoch seconds)
    now = time.time()
    missing = tuple(sorted({t for t in tickers if t not in book or now - book[t][1] > 300}))
    if missing:
        fresh = md.quotes(missing)
        for t in missing:
            if t in fresh:
                book[t] = (fresh[t], now)
        S.pf_updated = fresh.get("_fetched_at")
    S.pf_updated = S.pf_updated or datetime.now().strftime("%H:%M")
    return {t: book[t][0] for t in tickers if t in book}


def pf_refresh():
    md.refresh_prices()
    S.pf_quotes = {}
    toast("Prices refreshed", "↻")


def pf_start(amount):
    P["portfolio"] = pfm.new_portfolio()
    if amount > 0:
        pfm.record_flow(pf(), "deposit", amount)
    save_progress()
    toast(f"Virtual portfolio opened with {money(amount, dec=0)}", "💼")


def pf_cash_flow(kind, amount):
    if amount <= 0:
        toast("Enter an amount greater than zero", "⚠️")
        return
    if kind == "withdrawal" and amount > pfm.cash(pf()) + 1e-6:
        toast(f"You only have {money(pfm.cash(pf()))} in cash", "⚠️")
        return
    pfm.record_flow(pf(), kind, amount)
    save_progress()
    S.pf_flow_amount = 0.0
    toast(f"{'Deposited' if kind == 'deposit' else 'Withdrew'} {money(amount)}", "💰")


def pf_open_asset(asset, quick=False):
    """Open the asset sheet (quick=True: straight to the Buy form, without the chart)."""
    S.pf_asset = asset
    S.pf_quick = quick
    S.pf_table_n += 1          # fresh table keys, so the selection does not reopen the asset on return
    if quick:
        S.pf_side = "Buy"


def pf_open_from_search(asset, quick):
    pf_open_asset(asset, quick)
    S.pf_query = ""            # close the result list


def pf_set_quick(value):
    S.pf_quick = value


def watchlist():
    return pf().setdefault("watchlist", [])


def pf_toggle_watch(asset):
    wl = watchlist()
    if any(w["ticker"] == asset["ticker"] for w in wl):
        wl[:] = [w for w in wl if w["ticker"] != asset["ticker"]]
        toast(f"Removed {asset['name']} from your watchlist", "☆")
    else:
        wl.append({k: asset[k] for k in ("ticker", "name", "cls", "currency")})
        toast(f"Added {asset['name']} to your watchlist", "⭐")
    save_progress()


def pf_back():
    S.pf_asset, S.pf_quick = None, False
    S.pf_table_n += 1


def pf_update_badges(hist=None, bench=None):
    earned = pf().setdefault("earned", [])
    names = {k: t for k, _, t, _ in PF_BADGES}
    new = sorted(pfm.badge_status(pf(), hist, bench) - set(earned))
    for key in new:
        earned.append(key)
        if key in PF_BADGE_XP:
            add_xp(PF_BADGE_XP[key], f"Badge: {names[key]}")
        else:
            toast(f"Badge unlocked: {names[key]}", "🏅")
    if new:
        save_progress()


def pf_execute(side, asset, qty, price, rate):
    pv = pfm.preview_order(pf(), side, asset["ticker"], price, rate, qty=qty, fmt=money)
    if pv["error"]:
        toast(pv["error"], "⚠️")
        return
    pfm.record_trade(pf(), side, asset, pv, price, rate)
    save_progress()
    verb = "Bought" if side == "buy" else "Sold"
    toast(f"{verb} {qty_fmt(pv['qty'])} {asset['name']} for {money(pv['gross_chf'])}", "✅")
    for k in (f"pf_amt_{asset['ticker']}", f"pf_qty_{asset['ticker']}"):
        S[k] = 0.0
    pf_update_badges()


def pf_sell_all(ticker):
    S.pf_mode = "Quantity"
    S[f"pf_qty_{ticker}"] = pfm.held_qty(pf(), ticker)


def pf_set_fee():
    pf()["settings"]["fee_pct"] = float(S.pf_fee)
    save_progress()
    toast(f"Fee per order set to {S.pf_fee:.2f}%", "⚙️")


def pf_reset():
    P["portfolio"] = {}
    S.pf_asset, S.pf_confirm_reset = None, False
    save_progress()
    toast("Portfolio reset", "🔄")


def pf_history(p, live_q, live_fx):
    """Daily value history (CHF) and the MSCI World comparison, rebuilt from transactions + Yahoo history."""
    start = pfm.first_day(p)
    if start is None:
        return pd.DataFrame(), None
    since = (start - timedelta(days=10)).date().isoformat()
    tickers = tuple(sorted({t["ticker"] for t in p["trades"]}))
    curs = tuple(sorted({t["currency"] for t in p["trades"]} | {"USD"}))
    closes = md.history(tickers + (BENCHMARK,), since)
    fx_hist = md.fx_history(curs, since)
    hist = pfm.value_history(p, closes.reindex(columns=list(tickers)), fx_hist, live_q, live_fx)
    bench_chf = None
    if BENCHMARK in closes and "USD" in fx_hist:
        usd = fx_hist["USD"].reindex(closes.index.union(fx_hist.index)).ffill()
        bench_chf = (closes[BENCHMARK].reindex(usd.index).ffill() * usd).dropna()
        if BENCHMARK in live_q and "USD" in live_fx:
            bench_chf.loc[pd.Timestamp(date.today())] = live_q[BENCHMARK]["price"] * live_fx["USD"][0]
    return hist, pfm.benchmark_history(hist, bench_chf)


def dark_layout(fig, height=360, **kw):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, sans-serif", color="#9daaa0"),
                      separators=".'", hoverlabel=dict(bgcolor="#111914", bordercolor="#2f4536", font=dict(color="#f4f7f4")),
                      legend=dict(orientation="h", y=1.12, x=0, font=dict(color="#d3dbd5")), **kw)
    fig.update_xaxes(gridcolor="#1a261e", zeroline=False, linecolor="#25352a")
    fig.update_yaxes(gridcolor="#1a261e", zeroline=False)
    return fig


def donut(title, data):
    items = [(k, to_disp(v)) for k, v in data.items()]
    if len(items) > len(DONUT):
        items = items[:len(DONUT) - 1] + [("Other", sum(v for _, v in items[len(DONUT) - 1:]))]
    labels, values = [k for k, _ in items], [v for _, v in items]
    colors = [OTHER_GREY if k == "Other" else DONUT[i % len(DONUT)] for i, k in enumerate(labels)]
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=.62, sort=False, direction="clockwise",
                           marker=dict(colors=colors, line=dict(color="#0b100d", width=2)),
                           textinfo="percent", textfont=dict(color="#f4f7f4"),
                           hovertemplate="%{label}<br>%{value:,.0f} " + disp() + " · %{percent}<extra></extra>"))
    dark_layout(fig, height=300, showlegend=True, title=dict(text=title, font=dict(color="#f4f7f4", size=15), x=0))
    fig.update_layout(legend=dict(orientation="v", y=.5, x=1.02, yanchor="middle"), margin=dict(l=0, r=0, t=40, b=0))
    return fig


def pf_onboarding():
    with st.container(key="card_pf_start"):
        st.markdown('<div class="big-title" style="margin-top:0">Open your virtual portfolio</div>'
                    f'<p class="muted">Pick any starting amount of <b>virtual</b> {disp()}. You can deposit or withdraw more at any time. '
                    'Prices follow the real markets, but no real money is ever involved.</p>', unsafe_allow_html=True)
        amount = st.number_input(f"Starting amount ({disp()})", min_value=0, value=10_000, step=1_000, key="pf_start_amt")
        label = money(from_disp(amount), dec=0)
        st.caption(f"= {label}")
        st.button(f"Start with {label}", type="primary", on_click=pf_start, args=(from_disp(amount),), key="pf_start_btn")


def pf_cash_popover():
    with st.popover("💰 Deposit / withdraw", width="stretch"):
        kind = st.radio("Operation", ["Deposit", "Withdraw"], horizontal=True, key="pf_flow_kind")
        amount = st.number_input(f"Amount ({disp()})", min_value=0.0, step=100.0, key="pf_flow_amount")
        st.caption(f"Available cash: {money(pfm.cash(pf()))}")
        st.button("Confirm", type="primary", key="pf_flow_go", width="stretch", on_click=pf_cash_flow,
                  args=("deposit" if kind == "Deposit" else "withdrawal", from_disp(amount)))


def positions_table(rows):
    if not rows:
        st.info("No positions yet. Open **Markets** to buy your first asset.")
        return
    D, k = disp(), to_disp_rate(disp())
    pru, val, pnl = f"PRU ({D})", f"Value ({D})", f"P&L ({D})"
    df = pd.DataFrame([{
        "Asset": short(r["name"]), "Class": CLASSES[r["cls"]], "Quantity": r["qty"],
        pru: r["pru_chf"] * k, "Price": price_fmt(r["price"], r["currency"]) if r["price"] is not None else "—",
        val: r["value_chf"] * k,
        "Weight %": r["weight_pct"], pnl: r["pnl_chf"] * k, "P&L %": r["pnl_pct"], "Day %": r["day_pct"],
    } for r in sorted(rows, key=lambda r: -r["value_chf"])])
    sep = lambda f: (lambda v: "" if pd.isna(v) else f.format(v).replace(",", "'"))  # noqa: E731
    styler = (df.style
              .format({"Quantity": qty_fmt, pru: sep("{:,.2f}"), val: sep("{:,.2f}"),
                       "Weight %": "{:.1f}%", pnl: sep("{:+,.2f}"), "P&L %": "{:+.2f}%", "Day %": "{:+.2f}%"})
              .map(lambda v: f"color: {UP if v >= 0 else DOWN}; font-weight: 600", subset=[pnl, "P&L %", "Day %"]))
    ordered = sorted(rows, key=lambda r: -r["value_chf"])
    event = st.dataframe(styler, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row",
                         key=f"pf_pos_table_{S.pf_table_n}")
    picked = event.selection.rows[0] if event.selection.rows else asset_picker(ordered, "pos")
    if picked is not None:
        r = ordered[picked]
        pf_open_asset({k: r[k] for k in ("ticker", "name", "cls", "currency")})
        st.rerun()


def short(name, n=30):
    return name if len(name) <= n else name[:n - 1].rstrip() + "…"


def asset_picker(rows, tag):
    """Dropdown alternative to ticking a table row (handy on phones). Returns the picked row index or None."""
    labels = [f"{r['name']} ({r['ticker']})" for r in rows]
    choice = st.selectbox("Or open an asset", labels, index=None, placeholder="Choose an asset…",
                          key=f"pf_pick_{tag}_{S.pf_table_n}")
    return labels.index(choice) if choice else None


def mover_list(title, items):
    body = "".join(
        f'<div class="mover"><span>{esc(r["name"])}</span><b style="color:{UP if r["pnl_pct"] >= 0 else DOWN}">'
        f'{r["pnl_pct"]:+.2f}%</b></div>' for r in items) or '<div class="muted">—</div>'
    st.markdown(f'<div class="stack-card"><div class="stat-label">{title}</div>{body}</div>', unsafe_allow_html=True)


def pf_overview():
    p = pf()
    pos, realized = pfm.positions(p)
    with st.spinner("Loading prices from Yahoo Finance…"):
        q = pf_live_quotes(list(pos) + [t["ticker"] for t in p["trades"]] + [BENCHMARK])
        fx = md.fx_now(tuple(sorted({t["currency"] for t in p["trades"]} | {"USD"})))
        rows = pfm.value_positions(pos, q, fx)
        hist, bench = pf_history(p, q, fx)
    cash_chf = pfm.cash(p)
    total = cash_chf + sum(r["value_chf"] for r in rows)
    invested = pfm.net_invested(p)
    pnl = total - invested
    day_chf, day_pct = pfm.day_change(hist)
    all_twr = pfm.twr(hist)
    pf_update_badges(hist, bench)
    if any(r["price"] is None for r in rows):
        st.warning("Some prices could not be loaded right now; those positions are shown at cost.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total value", money(total), signed(day_chf) + " today")
    c2.metric("Cash", money(cash_chf), f"{cash_chf / total * 100 if total else 0:.1f}% of portfolio", delta_color="off")
    c3.metric("Total invested", money(invested), "deposits − withdrawals", delta_color="off")
    c4, c5, c6 = st.columns(3)
    signed_metric(c4, "Gain / loss", pnl, signed(pnl), f"{pnl / invested * 100 if invested else 0:+.2f}% of money invested")
    signed_metric(c5, "Time-weighted return", all_twr, f"{all_twr * 100:+.2f}%", "ignores deposits & withdrawals", "off")
    signed_metric(c6, "Today", day_chf, signed(day_chf), f"{day_pct:+.2f}%")

    # Value over time
    with st.container(key="card_pf_chart"):
        a, b = st.columns([1.4, 1], vertical_alignment="center")
        with a:
            period = seg("Period", ["1W", "1M", "6M", "1Y", "All"], default="All", key="pf_range",
                                          label_visibility="collapsed") or "All"
        compare = b.toggle(f"Compare with {BENCHMARK_NAME}", key="pf_bench")
        since = None if period == "All" else md.start_of_range(period)
        h = hist if since is None else hist[hist.index >= pd.Timestamp(since)]
        D, k = disp(), to_disp_rate(disp())
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=h.index, y=h["invested"] * k, name="Total invested", mode="lines", line=dict(color="#9daaa0", width=2, dash="dot", shape="hv"),
                                 hovertemplate="%{y:,.2f} " + D + "<extra>Total invested</extra>"))
        fig.add_trace(go.Scatter(x=h.index, y=h["value"] * k, name="Portfolio value", mode="lines+markers" if len(h) < 3 else "lines",
                                 line=dict(color="#2fa862", width=2), fill="tozeroy", fillcolor="rgba(47,168,98,.16)",
                                 hovertemplate="%{y:,.2f} " + D + "<extra>Portfolio</extra>"))
        if compare and bench is not None:
            bh = bench.reindex(h.index)
            fig.add_trace(go.Scatter(x=bh.index, y=bh["value"] * k, name="Same deposits in MSCI World", mode="lines",
                                     line=dict(color="#5b8fcc", width=2), hovertemplate="%{y:,.2f} " + D + "<extra>MSCI World</extra>"))
        dark_layout(fig, height=380, hovermode="x unified")
        fig.update_yaxes(ticksuffix=f" {D}", separatethousands=True)
        fig.update_xaxes(tickformat="%d %b", hoverformat="%d %b %Y", **({"dtick": 86_400_000} if len(h) <= 14 else {}))
        st.plotly_chart(fig, config={"displayModeBar": False}, width="stretch")
        line = f"Time-weighted return over this period: **{pfm.twr(hist, since) * 100:+.2f}%**"
        if compare and bench is not None:
            line += f" · MSCI World: **{pfm.bench_return(bench, since) * 100:+.2f}%**"
        st.markdown(line)
        if compare:
            st.caption("Comparison: the same deposits and withdrawals, on the same days, invested in the iShares MSCI World ETF (URTH).")
        if len(hist) < 3:
            st.caption("The chart fills in day by day: history is rebuilt from your transactions and daily closing prices.")

    st.markdown("#### Positions")
    positions_table(rows)

    if rows or cash_chf > 0:
        st.markdown("#### Allocation")
        for r in rows:
            r["cls_label"] = CLASSES[r["cls"]]
        stock_info = md.asset_info(tuple(sorted(r["ticker"] for r in rows if r["cls"] == "stock"))) if any(r["cls"] == "stock" for r in rows) else {}
        stock_rows = [{**r, "country": stock_info.get(r["ticker"], {}).get("country"),
                       "sector": stock_info.get(r["ticker"], {}).get("sector")} for r in rows if r["cls"] == "stock"]
        d1, d2 = st.columns(2)
        d1.plotly_chart(donut("By asset class", pfm.allocation(rows, cash_chf, "cls_label", "Cash")), config={"displayModeBar": False}, width="stretch")
        d2.plotly_chart(donut("By currency of the assets", pfm.allocation(rows, cash_chf, "currency", disp())), config={"displayModeBar": False}, width="stretch")
        if stock_rows:
            d3, d4 = st.columns(2)
            d3.plotly_chart(donut("Stocks by country", pfm.allocation(stock_rows, 0, "country")), config={"displayModeBar": False}, width="stretch")
            d4.plotly_chart(donut("Stocks by sector", pfm.allocation(stock_rows, 0, "sector")), config={"displayModeBar": False}, width="stretch")

    if rows:
        top, flop = pfm.top_flop(rows)
        t1, t2 = st.columns(2)
        with t1:
            mover_list("🏆 Top 3 positions", top)
        with t2:
            mover_list("📉 Flop 3 positions", flop)


def pf_markets():
    label = seg("Asset class", list(CLASS_KEYS), default="Stocks", key="pf_cls", label_visibility="collapsed") or "Stocks"
    cls = CLASS_KEYS[label]
    search = st.text_input("Search by name or ticker", key="pf_search", placeholder="e.g. Nestlé, AAPL, gold, BTC")
    with st.spinner("Loading the list from Yahoo Finance (the first load of the day can take ~20 seconds)…"):
        uni = md.universe(cls)
        tickers = [r["ticker"] for r in uni["rows"]]
        q = pf_live_quotes(tickers)
        spark = md.sparklines(tuple(tickers))
    rows = [r for r in uni["rows"] if r["ticker"] in q]
    if search:
        s = search.strip().lower()
        rows = [r for r in rows if s in r["name"].lower() or s in r["ticker"].lower()]
    notes = {
        "stock": f"The {len(uni['rows'])} largest companies by current market cap (in USD) from a candidate list, ranked with Yahoo data and refreshed daily.",
        "etf": "The 30 largest ETFs by total assets from a candidate list, refreshed daily. Yahoo publishes no total-assets figure for some European listings: they are listed last, marked “AUM n/a”.",
        "commodity": COMMODITY_NOTE,
        "crypto": "Crypto-assets trade 24/7 and are very volatile.",
    }
    st.caption(notes[cls])
    if not rows:
        st.info("No asset matches your search." if search else "Market data is not available right now. Try **Refresh prices** in a minute.")
        return
    data = pd.DataFrame([{
        "Name": r["name"], "Ticker": r["ticker"], "Tag": r["tag"],
        "Price": price_fmt(q[r["ticker"]]["price"], "").strip(),
        "Day %": q[r["ticker"]]["change_pct"], "Currency": r["currency"],
        "Size (bn USD)": r["size_usd"] / 1e9 if r["size_usd"] else None, "1 year": spark.get(r["ticker"], []),
    } for r in rows])
    if cls in ("commodity", "crypto"):
        data = data.drop(columns=["Size (bn USD)", "Tag"])
    size_label = "Market cap (bn USD)" if cls == "stock" else "Total assets (bn USD)"
    styler = data.style.map(lambda v: f"color: {UP if v >= 0 else DOWN}", subset=["Day %"]).format({"Day %": "{:+.2f}%"})
    event = st.dataframe(
        styler, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row",
        key=f"pf_mkt_table_{cls}_{S.pf_table_n}", height=min(38 + 35 * len(data), 640),
        column_config={
            "Price": st.column_config.TextColumn("Price"),
            "Size (bn USD)": st.column_config.NumberColumn(size_label, format="%.0f"),
            "1 year": st.column_config.LineChartColumn("1 year", width="small"),
        })
    st.caption("Tick the box at the start of a row to open the asset sheet and buy or sell.")
    picked = event.selection.rows[0] if event.selection.rows else asset_picker(rows, cls)
    if picked is not None:
        r = rows[picked]
        pf_open_asset({"ticker": r["ticker"], "name": r["name"], "cls": cls, "currency": r["currency"]})
        st.rerun()


def pf_asset_page():
    a = S.pf_asset
    st.button("← Back", key="pf_back", on_click=pf_back)
    with st.spinner("Loading prices…"):
        q = pf_live_quotes([a["ticker"]]).get(a["ticker"])
        fx = md.fx_now((a["currency"],))
        rate = fx.get(a["currency"], (None, None))[0]
        is_open = md.market_open(a["ticker"], a["cls"])
    if not q or not rate:
        st.error("No price data is available for this asset right now. Try **Refresh prices** in a minute.")
        return
    price = q["price"]
    held_pos = pfm.positions(pf())[0].get(a["ticker"])
    chg_color = UP if q["change_pct"] >= 0 else DOWN
    st.markdown(
        f'<div class="asset-head"><div><div class="stat-label">{CLASSES[a["cls"]]} · {esc(a["ticker"])} · {a["currency"]}</div>'
        f'<div class="big-title" style="margin:4px 0">{esc(a["name"])}</div></div>'
        f'<div class="asset-price"><b>{price_fmt(price, a["currency"])}</b>'
        + (f'<span>≈ {price_fmt(price * rate, "CHF")}</span>' if a["currency"] != disp() else "") +
        f'<span style="color:{chg_color}">{q["change_pct"]:+.2f}% today</span></div></div>',
        unsafe_allow_html=True)
    watched = a["ticker"] in {w["ticker"] for w in watchlist()}
    st.button("★ In watchlist" if watched else "☆ Add to watchlist", key="pf_watch_toggle", on_click=pf_toggle_watch, args=(a,))
    if not is_open:
        st.markdown('<span class="pill">Market closed — last close price</span>', unsafe_allow_html=True)
    if a["currency"] != disp():
        st.caption(f"1 {a['currency']} = {rate * to_disp_rate(disp()):.4f} {disp()} (Yahoo FX).")
    if a["cls"] == "commodity":
        st.info(COMMODITY_NOTE)

    if S.pf_quick:
        _, form, _ = st.columns([.5, 2, .5])
        form.button("📈 View full chart & details", key="pf_view_full", on_click=pf_set_quick, args=(False,))
    else:
        chart, form = st.columns([1.6, 1], gap="large")
        with chart:
            period = seg("Period", ["1M", "6M", "1Y", "5Y"], default="1Y", key="pf_asset_range",
                                          label_visibility="collapsed") or "1Y"
            start5 = md.start_of_range("5Y").isoformat()
            h = md.history((a["ticker"],), start5)
            s = h[a["ticker"]].dropna() if a["ticker"] in h else pd.Series(dtype=float)
            s.loc[pd.Timestamp(date.today())] = price
            s = s[s.index >= pd.Timestamp(md.start_of_range(period))]
            fig = go.Figure(go.Scatter(x=s.index, y=s.values, mode="lines", name=a["name"], line=dict(color="#2fa862", width=2),
                                       hovertemplate=f"%{{y:,.2f}} {a['currency']}<extra></extra>"))
            trades = [t for t in pf()["trades"] if t["ticker"] == a["ticker"]]
            for side, color, symbol in (("buy", UP, "triangle-up"), ("sell", DOWN, "triangle-down")):
                pts = [t for t in trades if t["side"] == side]
                if pts:
                    fig.add_trace(go.Scatter(x=[pd.Timestamp(t["ts"]) for t in pts], y=[t["price"] for t in pts], mode="markers",
                                             name="Your buys" if side == "buy" else "Your sells",
                                             marker=dict(color=color, size=13, symbol=symbol, line=dict(color="#0b100d", width=2)),
                                             hovertemplate=f"{side.title()} %{{y:,.2f}} {a['currency']}<extra></extra>"))
            dark_layout(fig, height=360, hovermode="x unified", showlegend=bool(trades))
            st.plotly_chart(fig, config={"displayModeBar": False}, width="stretch")
            if held_pos:
                v = held_pos["qty"] * price * rate
                pnl = v - held_pos["cost_chf"]
                mini_stats([("You hold", qty_fmt(held_pos["qty"]), "units", "var(--text)"),
                            ("Value", money(v), f"PRU {money(held_pos['cost_chf'] / held_pos['qty'])}", "var(--text)"),
                            ("Gain / loss", signed(pnl), f"{pnl / held_pos['cost_chf'] * 100:+.2f}%", UP if pnl >= 0 else DOWN)])

    with form, st.container(key="card_trade"):
        side_label = seg("Order", ["Buy", "Sell"], default="Buy", key="pf_side") or "Buy"
        side = side_label.lower()
        if S.get("pf_mode") not in ("Amount", "Quantity"):
            S.pf_mode = "Amount"
        mode = st.radio("Order by", ["Amount", "Quantity"], horizontal=True, key="pf_mode",
                        format_func=lambda o: f"Amount ({disp()})" if o == "Amount" else o)
        qty_key, amt_key = f"pf_qty_{a['ticker']}", f"pf_amt_{a['ticker']}"
        if mode == "Amount":
            amount = st.number_input(f"Order value in {disp()} (before fees)", min_value=0.0, step=100.0, key=amt_key)
            pv = pfm.preview_order(pf(), side, a["ticker"], price, rate, amount_chf=from_disp(amount), fmt=money)
        else:
            qty = st.number_input("Quantity (fractions allowed)", min_value=0.0, step=1.0, format="%.6f", key=qty_key)
            pv = pfm.preview_order(pf(), side, a["ticker"], price, rate, qty=qty, fmt=money)
        if side == "sell" and held_pos:
            st.button(f"Sell all ({qty_fmt(held_pos['qty'])})", key="pf_sell_all", on_click=pf_sell_all, args=(a["ticker"],))
        cash_after = pfm.cash(pf()) + (-pv.get("total_chf", 0) if side == "buy" else pv.get("total_chf", 0))
        fee_pct = pf()["settings"].get("fee_pct", 0)
        st.markdown(
            '<table class="recap">'
            f'<tr><td>Quantity</td><td>{qty_fmt(pv["qty"])}</td></tr>'
            f'<tr><td>Price</td><td>{price_fmt(price, a["currency"])}' + (f' · {price_fmt(pv["unit_chf"], "CHF")}' if a["currency"] != disp() else "") + '</td></tr>'
            f'<tr><td>Order value</td><td>{money(pv["gross_chf"])}</td></tr>'
            f'<tr><td>Fee ({fee_pct:g}%)</td><td>{money(pv["fee_chf"])}</td></tr>'
            f'<tr class="tot"><td>{"Total debited" if side == "buy" else "Total credited"}</td><td>{money(pv.get("total_chf", 0))}</td></tr>'
            f'<tr><td>Cash after order</td><td>{money(cash_after)}</td></tr></table>',
            unsafe_allow_html=True)
        if pv["error"] and pv["qty"] > 0:
            st.warning(pv["error"])
        st.button(f"Confirm {side}", type="primary", key="pf_confirm", width="stretch", disabled=bool(pv["error"]),
                  on_click=pf_execute, args=(side, a, pv["qty"], price, rate))
        st.caption(("Market closed: the order uses the last close price. " if not is_open else "") +
                   "Orders are filled instantly at the price shown, in virtual money.")


def pf_transactions():
    p = pf()
    rows = [{"Date": f["ts"].replace("T", " ")[:16], "Type": "Deposit" if f["kind"] == "deposit" else "Withdrawal",
             "Asset": "", "Quantity": None, "Price": "", "Cash (CHF)": f["amount"] if f["kind"] == "deposit" else -f["amount"],
             "Fee (CHF)": 0.0} for f in p["cash_flows"]]
    rows += [{"Date": t["ts"].replace("T", " ")[:16], "Type": t["side"].title(), "Asset": f"{t['name']} ({t['ticker']})",
              "Quantity": t["qty"], "Price": price_fmt(t["price"], t["currency"]),
              "Cash (CHF)": -(t["gross_chf"] + t["fee_chf"]) if t["side"] == "buy" else t["gross_chf"] - t["fee_chf"],
              "Fee (CHF)": t["fee_chf"]} for t in p["trades"]]
    if not rows:
        st.info("No transactions yet.")
        return
    D, k = disp(), to_disp_rate(disp())
    df = pd.DataFrame(rows).sort_values("Date", ascending=False)
    df["Cash (CHF)"] *= k
    df["Fee (CHF)"] *= k
    df = df.rename(columns={"Cash (CHF)": f"Cash ({D})", "Fee (CHF)": f"Fee ({D})"})
    st.dataframe(df, hide_index=True, width="stretch", column_config={
        "Quantity": st.column_config.NumberColumn(format="%.6g"),
        f"Cash ({D})": st.column_config.NumberColumn(format="%+.2f"),
        f"Fee ({D})": st.column_config.NumberColumn(format="%.2f")})
    st.caption(f"{len(p['trades'])} orders · {len(p['cash_flows'])} deposits/withdrawals · total fees {money(pfm.total_fees(p))}. "
               "“Cash” is the effect on your cash balance, fees included.")


def pf_settings():
    with st.container(key="card_pf_settings"):
        if "pf_fee" not in S:
            S.pf_fee = float(pf()["settings"].get("fee_pct", 0.1))
        st.number_input("Fee per order (%)", min_value=0.0, step=0.05, format="%.2f", key="pf_fee", on_change=pf_set_fee,
                        help="Charged on every buy and sell, as a % of the order value. 0 is allowed.")
        st.caption("Real brokers charge fees, spreads and sometimes FX costs. This simulator uses one simple percentage.")
    st.write("")
    with st.container(key="card_pf_reset"):
        st.markdown("**Reset portfolio**  \n<span class='muted'>Erase all virtual cash, positions and transactions. "
                    "Badges and XP you earned are kept.</span>", unsafe_allow_html=True)
        if not S.pf_confirm_reset:
            if st.button("Reset portfolio", key="pf_reset_ask"):
                S.pf_confirm_reset = True
                st.rerun()
        else:
            st.warning("Are you sure? This erases the whole virtual portfolio.")
            x, y, _ = st.columns([1, 1, 2])
            x.button("Yes, reset", type="primary", on_click=pf_reset, key="pf_reset_yes", width="stretch")
            if y.button("Cancel", key="pf_reset_no", width="stretch"):
                S.pf_confirm_reset = False
                st.rerun()


NO_RESULTS = "No results — try the company name or the Yahoo ticker (e.g. RACE.MI)"


def quote_html(price, change, cur):
    color = UP if change >= 0 else DOWN
    return (f'<div class="sr-price"><b>{price_fmt(price, cur)}</b>'
            f'<span style="color:{color}">{change:+.2f}%</span></div>')


def pf_search_bar():
    with st.container(key="searchbar"):
        query = st.text_input("Search", key="pf_query", placeholder="Search stocks, ETFs, commodities, crypto…",
                              label_visibility="collapsed")
    if query.strip():
        pf_search_results(query.strip())
    pf_watchlist()


def pf_search_results(query):
    if len(query) < 2:
        st.caption("Type at least 2 characters.")
        return
    with st.spinner("Searching Yahoo Finance…"):
        res = md.search(query)
        q = pf_live_quotes([r["ticker"] for r in res["results"]])
    results = [r for r in res["results"] if r["ticker"] in q]
    if not results:
        st.info(res["error"] or NO_RESULTS)
        return
    held = set(pfm.positions(pf())[0])
    watched = {w["ticker"] for w in watchlist()}
    st.caption(f"{len(results)} result{'s' if len(results) > 1 else ''} for “{query}”. Prices from Yahoo Finance, possibly delayed.")
    for i, r in enumerate(results):
        asset = {k: r[k] for k in ("ticker", "name", "cls", "currency")}
        badge = '<span class="tag tag-held">In portfolio</span>' if r["ticker"] in held else ""
        sub = " · ".join(x for x in (r["ticker"], r["exchange"], r["type"], r["currency"]) if x)
        with st.container(key=f"srrow_{i}"):
            info, price, acts = st.columns([2.3, 1, 2.1], vertical_alignment="center")
            info.markdown(f'<div class="sr-name">{esc(r["name"])} {badge}</div><div class="sr-sub">{esc(sub)}</div>',
                          unsafe_allow_html=True)
            price.markdown(quote_html(q[r["ticker"]]["price"], q[r["ticker"]]["change_pct"], r["currency"]), unsafe_allow_html=True)
            b1, b2, b3 = acts.columns([1, 1, 1.25])
            b1.button("\\+ Add", key=f"sr_add_{i}", type="primary", on_click=pf_open_from_search, args=(asset, True), width="stretch")
            b2.button("View", key=f"sr_view_{i}", on_click=pf_open_from_search, args=(asset, False), width="stretch")
            b3.button("★ Watching" if r["ticker"] in watched else "☆ Watchlist", key=f"sr_watch_{i}",
                      on_click=pf_toggle_watch, args=(asset,), width="stretch")


def pf_watchlist():
    wl = watchlist()
    if not wl:
        return
    q = pf_live_quotes([w["ticker"] for w in wl])
    with st.container(key="card_watch"):
        st.markdown('<div class="stat-label">☆ Watchlist</div>', unsafe_allow_html=True)
        for w in wl:
            with st.container(key=f"wlrow_{w['ticker'].replace('.', '_').replace('=', '_')}"):
                info, price, acts = st.columns([2.3, 1, 2.1], vertical_alignment="center")
                info.markdown(f'<div class="sr-name">{esc(w["name"])}</div><div class="sr-sub">{esc(w["ticker"])} · '
                              f'{CLASSES[w["cls"]]} · {w["currency"]}</div>', unsafe_allow_html=True)
                if w["ticker"] in q:
                    price.markdown(quote_html(q[w["ticker"]]["price"], q[w["ticker"]]["change_pct"], w["currency"]), unsafe_allow_html=True)
                else:
                    price.caption("No price right now")
                b1, b2 = acts.columns([1, 1])
                b1.button("Buy", key=f"wl_buy_{w['ticker']}", type="primary", on_click=pf_open_from_search, args=(w, True),
                          width="stretch", disabled=w["ticker"] not in q)
                b2.button("✕ Remove", key=f"wl_rm_{w['ticker']}", on_click=pf_toggle_watch, args=(w,), width="stretch")


def portfolio_page():
    page_header("Portfolio", "Practise investing with virtual money and real market prices.", currency_picker=True)
    st.markdown('<div class="pf-banner">🎓 Virtual money · educational simulation · not investment advice</div>', unsafe_allow_html=True)
    if not pf():
        pf_onboarding()
        st.caption(DATA_NOTE)
        return
    bar = st.columns([1, 1, 2.2], vertical_alignment="center")
    bar[0].button("↻ Refresh prices", key="pf_refresh", on_click=pf_refresh, width="stretch")
    with bar[1]:
        pf_cash_popover()
    status = bar[2].empty()
    pf_search_bar()
    if S.pf_asset:
        pf_asset_page()
    else:
        section = seg("Section", ["Overview", "Markets", "Transactions", "Settings"], default="Overview",
                                       key="pf_tab", label_visibility="collapsed") or "Overview"
        {"Overview": pf_overview, "Markets": pf_markets, "Transactions": pf_transactions, "Settings": pf_settings}[section]()
    status.caption(f"Prices updated at {S.pf_updated or '—'} · cash {money(pfm.cash(pf()))}")
    st.caption(DATA_NOTE)


def welcome_page():
    """First screen: pick a name. Same name later = same progress."""
    st.markdown(WELCOME_CSS, unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid, st.container(key="welcome"):
        st.markdown('<div class="w-logo">🌱</div><div class="w-brand">STACK</div><div class="w-title">What’s your name?</div>',
                    unsafe_allow_html=True)
        with st.form("login_form", border=False):
            st.text_input("Your name", key="login_name", max_chars=NAME_MAX, placeholder="Your name",
                          label_visibility="collapsed")
            st.form_submit_button("Continue", type="primary", on_click=login_submit, width="stretch", key="login_go")
        if S.login_error:
            st.markdown(f'<div class="w-error">{esc(S.login_error)}</div>', unsafe_allow_html=True)


# Welcome screen only: flat black, soft dark green, nothing else on the page.
WELCOME_CSS = """
<style>
section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"],
header[data-testid="stHeader"] { display:none !important; }
.stApp { background:#0b0d0c !important; }
.block-container { padding-top:22vh !important; }
.st-key-welcome { text-align:center; }
.w-logo { width:60px; height:60px; margin:0 auto 14px; border-radius:18px; display:grid; place-items:center;
  font-size:30px; background:#16241b; border:1px solid #22382a; }
.w-brand { color:#7fa88c; font-weight:800; font-size:22px; letter-spacing:.28em; padding-left:.28em; }
.w-title { color:#e4ebe6; font-size:28px; font-weight:700; letter-spacing:-.02em; margin:14px 0 22px; }
.st-key-welcome [data-baseweb="input"] { background:#121614 !important; border:1px solid #1e2722 !important;
  border-radius:12px; min-height:3rem; }
.st-key-welcome [data-baseweb="input"]:focus-within { border-color:#3f6b4f !important; box-shadow:none !important; }
.st-key-welcome input { color:#e4ebe6; font-size:16px; text-align:center; }
.st-key-welcome input::placeholder { color:#55625a; }
.st-key-welcome [data-testid="InputInstructions"] { display:none; }
.st-key-welcome button[data-testid^="stBaseButton-primary"] { background:#1d3a28 !important; border:1px solid #1d3a28 !important;
  border-radius:12px !important; min-height:3rem; box-shadow:none !important; }
.st-key-welcome button[data-testid^="stBaseButton-primary"]:hover,
.st-key-welcome button[data-testid^="stBaseButton-primary"]:focus { background:#244832 !important; border-color:#244832 !important; }
.st-key-welcome button[data-testid^="stBaseButton-primary"] p { color:#ffffff !important; font-weight:600; }
.w-error { color:#b9867f; font-size:14px; margin-top:4px; }
</style>
"""


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
# Profile gate. The name lives in the URL (?u=name), so a reload or a journey link keeps the same player.
url_user = st.query_params.get("u")
if url_user and url_user != S.get("user"):
    if profile_exists(url_user):
        if S.get("user"):                         # another name typed in the URL: start a clean session
            for k in list(S.keys()):
                del S[k]
            init_state()
        open_profile(url_user)
    else:                                         # unknown or invalid name in the URL: ask for a name
        del st.query_params["u"]
if not S.get("user"):
    for msg, icon in S.toasts:
        st.toast(msg, icon=icon)
    S.toasts = []
    welcome_page()
    st.stop()
if st.query_params.get("u") != S.user:            # e.g. the URL was edited by hand: put the name back
    st.query_params["u"] = S.user
sync_from_disk()
P = S.progress

# Journey links (<a href="?u=name&start=N">) arrive as query params: open the lesson if it is unlocked.
if "start" in st.query_params:
    raw = st.query_params.get("start")
    del st.query_params["start"]
    level = int(raw) if str(raw).isdigit() else -1
    if 0 <= level < len(LESSONS) and is_unlocked(level):
        start_lesson(level)
    else:
        S.view = "journey"
        toast("Complete the previous level first", "🔒")
    st.rerun()

for msg, icon in S.toasts:
    st.toast(msg, icon=icon)
S.toasts = []
if S.celebrate:
    st.balloons()
    S.celebrate = False

sidebar()
PAGES = {"home": home_page, "journey": journey_page, "lesson": lesson_page,
         "lab": lab_page, "portfolio": portfolio_page, "rewards": rewards_page, "profile": profile_page}
PAGES.get(S.view, home_page)()

st.markdown("---")
st.caption(DISCLAIMER)
