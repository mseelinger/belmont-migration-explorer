"""Tar Heel Tally's publication styling, shared across the explorer."""
import base64
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go

NAVY='#062B55'
BLUE='#3F7CAC'
ORANGE='#D07A3A'
CREAM='#F7EFE4'
SLATE='#5C7088'
GRID='#E8E3DB'
FONT='-apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif'

# One template keeps chart labels, gridlines, hover cards and spacing consistent.
TEMPLATE=go.layout.Template(layout=dict(
    font=dict(family=FONT,size=13,color=NAVY),paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF',
    colorway=[BLUE,ORANGE,'#8FB3CF','#E4B184',NAVY],
    hoverlabel=dict(bgcolor=NAVY,font=dict(color='#FFFFFF',size=13),bordercolor=NAVY),
    xaxis=dict(gridcolor=GRID,zerolinecolor=GRID,tickfont=dict(color=SLATE),title_font=dict(color=SLATE)),
    yaxis=dict(gridcolor=GRID,zerolinecolor=GRID,tickfont=dict(color=SLATE),title_font=dict(color=SLATE)),
    legend=dict(font=dict(color=SLATE),title_text=''),
    margin=dict(l=15,r=20,t=30,b=30)))


def apply_brand(compact=False):
    st.html('''<style>
    :root { --tally-navy:#062B55; --tally-blue:#3F7CAC; --tally-cream:#F7EFE4; }
    .stApp, [data-testid="stAppViewContainer"] { background:#F7EFE4; color:#062B55; }
    [data-testid="stHeader"] { background:rgba(247,239,228,.95); }
    [data-testid="stMainBlockContainer"] { max-width:1440px; padding:4.5rem 3.5rem 4rem; }
    [data-testid="stSidebar"] { background:#EEE6DA; border-right:1px solid #D8D3CA; }
    [data-testid="stSidebar"] h2 { font-size:1.15rem; color:#062B55; }
    [data-testid="stMarkdownContainer"] h1 { color:#062B55; font-family:Georgia,'Times New Roman',serif !important; letter-spacing:-.035em; }
    h2,h3 { color:#062B55; letter-spacing:-.025em; }
    [data-testid="stMarkdownContainer"] p { line-height:1.65; }
    [data-testid="stCaptionContainer"] { color:#5C7088; }
    .tally-masthead { display:flex; justify-content:space-between; align-items:center; gap:1rem; padding:0 0 1.25rem; border-bottom:2px solid #062B55; margin-bottom:.4rem; }
    .tally-wordmark { width:280px; max-width:55vw; height:auto; }
    .tally-publication { color:#5C7088; font-size:.7rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; text-align:right; line-height:1.8; }
    .tally-kicker { color:#3F7CAC; font-size:.72rem; font-weight:750; text-transform:uppercase; letter-spacing:.14em; margin-top:1rem; }
    .tally-footer { margin-top:2rem; padding-top:1.2rem; border-top:1px solid #D8D3CA; display:flex; justify-content:space-between; gap:1rem; color:#5C7088; font-size:.8rem; }
    [data-testid="stTabs"] [role="tablist"] { gap:.35rem; border-bottom:0; padding:.35rem 0 1rem; }
    [data-testid="stTabs"] [role="tab"] { border-radius:6px; padding:.65rem .85rem; height:auto; color:#5C7088; font-weight:600; }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] { background:#062B55; color:#FFFFFF; }
    [data-testid="stTabs"] [role="tab"]:hover { background:#D9ECFA; color:#062B55; }
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display:none; }
    [data-testid="stMetric"] { background:#FFFFFF; border:1px solid #E1DCD3; border-top:3px solid #8DBFEA; border-radius:8px; padding:1rem 1.2rem; min-height:112px; box-shadow:0 2px 6px rgba(6,43,85,.025); }
    .st-key-origin_cards [data-testid="stMetric"] { height:160px; }
    [data-testid="stMetricLabel"] { color:#5C7088; font-size:.8rem; }
    [data-testid="stMetricValue"] { color:#062B55; font-size:2rem; font-weight:650; letter-spacing:-.04em; font-variant-numeric:tabular-nums; }
    [data-testid="stPlotlyChart"] { background:#FFFFFF; border:1px solid #E1DCD3; border-radius:8px; padding:0; overflow:hidden; }
    [data-testid="stDataFrame"] { border:1px solid #E1DCD3; border-radius:8px; overflow:hidden; }
    [data-testid="stDownloadButton"] button { border:1px solid #B8CADB; border-radius:6px; color:#062B55; background:transparent; font-size:.85rem; }
    [data-testid="stDownloadButton"] button:hover { border-color:#062B55; background:#D9ECFA; }
    [data-testid="stAlert"] { border-radius:6px; font-size:.9rem; border:1px solid #E6D8C2; }
    [data-testid="stExpander"] { border-color:#D8D3CA; border-radius:6px; }
    @media(max-width:800px) {
      [data-testid="stMainBlockContainer"] { padding:4rem 1rem 3rem; }
      .tally-wordmark { width:210px; }
      .tally-publication { font-size:.6rem; }
      [data-testid="stTabs"] [role="tab"] { padding:.5rem .6rem; font-size:.8rem; }
      [data-testid="stMetric"] { padding:.8rem; }
      [data-testid="stMetricValue"] { font-size:1.6rem; }
    }
    </style>''')
    mobile_rules = [
        ('[data-testid="stMainBlockContainer"]', 'padding:4rem .9rem 2rem; max-width:420px;'),
        ('.tally-masthead', 'gap:.5rem; padding-bottom:.8rem;'),
        ('.tally-wordmark', 'width:160px; max-width:46%;'),
        ('.tally-publication', 'font-size:.56rem; letter-spacing:.08em;'),
        ('.tally-kicker', 'font-size:.62rem; letter-spacing:.09em;'),
        ('[data-testid="stMarkdownContainer"] h1', 'font-size:2rem; line-height:1.12;'),
        ('[data-testid="stMarkdownContainer"] h3', 'font-size:1.2rem; line-height:1.3;'),
        ('[data-testid="stCaptionContainer"]', 'font-size:.8rem; color:#52677E;'),
        ('[data-testid="stTabs"] [role="tablist"]', 'flex-wrap:wrap; overflow:visible; gap:.3rem; padding-bottom:.6rem;'),
        ('[data-testid="stTabs"] [role="tab"]', 'min-height:44px; padding:.6rem .7rem; flex-shrink:0;'),
        ('[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"])', 'flex-direction:row !important; flex-wrap:wrap; gap:.65rem;'),
        ('[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"]', 'flex:1 1 calc(50% - .65rem) !important; min-width:0 !important; width:calc(50% - .65rem) !important;'),
        ('[data-testid="stMetric"]', 'padding:.8rem; min-height:120px; height:120px;'),
        ('[data-testid="stMetricValue"]', 'font-size:1.6rem;'),
        ('.st-key-origin_cards [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"]', 'flex:1 1 100% !important; width:100% !important;'),
        ('.st-key-origin_cards [data-testid="stMetric"]', 'height:130px;'),
        ('[data-testid="stDownloadButton"] button', 'min-height:44px; width:100%;'),
        ('[data-baseweb="select"]', 'min-height:44px;'),
        ('.tally-footer', 'flex-direction:column; gap:.3rem;'),
        ('.st-key-retention_triangle', 'overflow-x:auto; overscroll-behavior-x:contain; padding-bottom:.5rem;'),
        ('.st-key-retention_triangle [data-testid="stFullScreenFrame"]', 'min-width:720px;'),
        ('.st-key-retention_triangle [data-testid="stPlotlyChart"]', 'min-width:720px;'),
        ('.modebar-btn', 'padding:8px !important;'),
    ]
    responsive = ''.join(selector+' {'+rules+'}' for selector,rules in mobile_rules)
    forced = ''.join('.stApp:has(.tally-compact-marker) '+selector+' {'+rules+'}' for selector,rules in mobile_rules)
    st.html('<style>@media(max-width:640px) {'+responsive+'}'+forced+'</style>')
    if compact:
        st.html('<span class="tally-compact-marker" aria-hidden="true"></span>')
    logo=base64.b64encode((Path(__file__).parent/'brand-wordmark.png').read_bytes()).decode()
    st.html(f'<div class="tally-masthead"><img class="tally-wordmark" src="data:image/png;base64,{logo}" alt="Tar Heel Tally"><div class="tally-publication">Less spin. More substance.<br>North Carolina, by the numbers.</div></div>')
    st.html('<div class="tally-kicker">Data explorer / Belmont, North Carolina</div>')


def footer():
    st.html('<div class="tally-footer"><span>Tar Heel Tally · Belmont Migration Explorer</span><span>January 1 snapshots, 2016–2026</span></div>')
