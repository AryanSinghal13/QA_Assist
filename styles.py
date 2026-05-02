"""styles.py — Injects the premium dark-mode CSS for QA Assist."""
import streamlit as st

DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base reset ────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── App background ────────────────────────────────── */
.stApp {
    background: linear-gradient(135deg, #0f1117 0%, #1a1f2e 50%, #0d1117 100%);
    color: #e2e8f0;
}

/* ── Sidebar ───────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04) !important;
    border-right: 1px solid rgba(255,255,255,0.08) !important;
    backdrop-filter: blur(20px);
}
section[data-testid="stSidebar"] * {
    color: #cbd5e1 !important;
}
section[data-testid="stSidebar"] .stRadio label {
    padding: 8px 12px;
    border-radius: 8px;
    transition: background 0.2s;
    cursor: pointer;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(124,58,237,0.15);
}

/* ── Main content area ─────────────────────────────── */
.main .block-container {
    padding: 2rem 2.5rem 4rem;
    max-width: 1200px;
}

/* ── Headings ──────────────────────────────────────── */
h1 { font-size: 2rem !important; font-weight: 800 !important; color: #f1f5f9 !important; letter-spacing: -0.5px; }
h2 { font-size: 1.4rem !important; font-weight: 700 !important; color: #e2e8f0 !important; }
h3 { font-size: 1.1rem !important; font-weight: 600 !important; color: #cbd5e1 !important; }

/* ── Metric cards ──────────────────────────────────── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 14px;
    padding: 20px 24px !important;
    backdrop-filter: blur(10px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(124,58,237,0.2);
}
[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #7c3aed, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
[data-testid="stMetricLabel"] {
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    color: #94a3b8 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Kill ALL Streamlit red / blue focus outlines ──── */
*:focus, *:focus-visible, *:focus-within {
    outline: none !important;
    box-shadow: none !important;
}
.stButton > button:focus,
.stButton > button:focus-visible,
.stButton > button:active {
    outline: none !important;
    box-shadow: none !important;
    border: none !important;
}

/* ── Buttons ───────────────────────────────────────── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s ease !important;
    border: none !important;
    outline: none !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(124,58,237,0.4) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(124,58,237,0.6) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.07) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.12) !important;
    transform: translateY(-1px) !important;
}

/* ── Input fields ──────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 0.9rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.15) !important;
}

/* ── Labels ───────────────────────────────────────── */
.stTextInput label, .stTextArea label, .stSelectbox label,
.stMultiSelect label, .stFileUploader label {
    color: #94a3b8 !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

/* ── Tabs ──────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04);
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    color: #94a3b8 !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: white !important;
    font-weight: 700 !important;
}

/* ── Expander ──────────────────────────────────────── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #cbd5e1 !important;
    font-weight: 600 !important;
}
.streamlit-expanderContent {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}

/* ── Alert / info / success / error boxes ──────────── */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
}
div[data-testid="stInfoContainer"] {
    background: rgba(99,179,237,0.12) !important;
    border-left: 4px solid #63b3ed !important;
    border-radius: 8px !important;
    color: #bee3f8 !important;
}
div[data-testid="stSuccessContainer"] {
    background: rgba(72,187,120,0.12) !important;
    border-left: 4px solid #48bb78 !important;
    border-radius: 8px !important;
    color: #c6f6d5 !important;
}
div[data-testid="stErrorContainer"] {
    background: rgba(252,129,74,0.12) !important;
    border-left: 4px solid #fc814a !important;
    border-radius: 8px !important;
    color: #fed7aa !important;
}
div[data-testid="stWarningContainer"] {
    background: rgba(237,189,66,0.12) !important;
    border-left: 4px solid #edbv42 !important;
    border-radius: 8px !important;
    color: #fefcbf !important;
}

/* ── DataFrames / Tables ───────────────────────────── */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08) !important;
}
.stDataFrame thead th {
    background: rgba(124,58,237,0.3) !important;
    color: #e2e8f0 !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    font-size: 0.78rem !important;
    letter-spacing: 0.5px;
}
.stDataFrame tbody tr:nth-child(even) {
    background: rgba(255,255,255,0.03) !important;
}
.stDataFrame tbody tr:hover {
    background: rgba(124,58,237,0.1) !important;
}

/* ── Code blocks ───────────────────────────────────── */
.stCodeBlock {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}

/* ── Divider ───────────────────────────────────────── */
hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 1.5rem 0 !important;
}

/* ── Download button ───────────────────────────────── */
.stDownloadButton > button {
    background: rgba(6,182,212,0.15) !important;
    color: #67e8f9 !important;
    border: 1px solid rgba(6,182,212,0.3) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
    background: rgba(6,182,212,0.25) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(6,182,212,0.3) !important;
}

/* ── Multiselect pills ─────────────────────────────── */
.stMultiSelect [data-baseweb="tag"] {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: white !important;
    border-radius: 6px !important;
}

/* ── File uploader ─────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.03) !important;
    border: 2px dashed rgba(124,58,237,0.4) !important;
    border-radius: 12px !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(124,58,237,0.7) !important;
}

/* ── Spinner ───────────────────────────────────────── */
.stSpinner > div {
    border-top-color: #7c3aed !important;
}

/* ── Caption / small text ──────────────────────────── */
.stCaption, small {
    color: #64748b !important;
    font-size: 0.8rem !important;
}

/* ── Checkbox ──────────────────────────────────────── */
.stCheckbox label {
    color: #cbd5e1 !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
}

/* ── Section cards ─────────────────────────────────── */
.qa-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    backdrop-filter: blur(10px);
    transition: all 0.2s ease;
}
.qa-card:hover {
    border-color: rgba(124,58,237,0.3);
    box-shadow: 0 8px 32px rgba(124,58,237,0.1);
}

/* ── Gradient badge ────────────────────────────────── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.badge-purple { background: rgba(124,58,237,0.2); color: #a78bfa; border: 1px solid rgba(124,58,237,0.3); }
.badge-teal   { background: rgba(6,182,212,0.2);  color: #67e8f9; border: 1px solid rgba(6,182,212,0.3); }
.badge-green  { background: rgba(72,187,120,0.2); color: #6ee7b7; border: 1px solid rgba(72,187,120,0.3); }

/* ── Page header gradient text ─────────────────────── */
.gradient-text {
    background: linear-gradient(135deg, #a78bfa, #67e8f9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
}

/* ── Framework card buttons ────────────────────────── */
.fw-card {
    background: rgba(255,255,255,0.04);
    border: 1.5px solid rgba(255,255,255,0.1);
    border-radius: 14px;
    padding: 20px 12px 14px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    height: 100%;
    min-height: 130px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
}
.fw-card:hover {
    border-color: rgba(124,58,237,0.5);
    background: rgba(124,58,237,0.08);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(124,58,237,0.2);
}
.fw-card.active {
    border-color: #7c3aed !important;
    background: rgba(124,58,237,0.15) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.2), 0 8px 24px rgba(124,58,237,0.25);
}
.fw-icon { font-size: 1.8rem; line-height:1; }
.fw-name { font-size: 0.8rem; font-weight: 700; color: #e2e8f0; margin-top: 6px; }
.fw-desc { font-size: 0.68rem; color: #64748b; line-height: 1.4; }

/* ── Sidebar logo area ─────────────────────────────── */
.sidebar-logo {
    padding: 16px 0 8px;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 16px;
}
.sidebar-logo h1 {
    font-size: 1.4rem !important;
    background: linear-gradient(135deg, #a78bfa, #67e8f9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 !important;
}

/* ── User card in sidebar ──────────────────────────── */
.user-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 12px;
    margin: 8px 0;
}
</style>
"""


def inject():
    """Call this once at the top of app.py after set_page_config."""
    st.markdown(DARK_CSS, unsafe_allow_html=True)


def section_header(icon: str, title: str, subtitle: str = ""):
    """Render a styled page header."""
    st.markdown(
        f"""
        <div style="margin-bottom:24px">
            <h1 style="margin:0">{icon} <span class="gradient-text">{title}</span></h1>
            {"<p style='color:#64748b;margin:4px 0 0;font-size:0.95rem'>"+subtitle+"</p>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_row(metrics: list[dict]):
    """Render a row of metric cards. Each dict: {label, value, delta?}"""
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        col.metric(m["label"], m["value"], m.get("delta"))


def info_card(icon: str, title: str, body: str):
    """Render a styled info card using HTML."""
    st.markdown(
        f"""
        <div class="qa-card">
            <div style="font-size:1.6rem;margin-bottom:8px">{icon}</div>
            <div style="font-weight:700;color:#e2e8f0;margin-bottom:4px">{title}</div>
            <div style="color:#64748b;font-size:0.85rem">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def step_header(num: str, title: str):
    """Render a numbered step header."""
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:12px;margin:24px 0 12px">
            <div style="background:linear-gradient(135deg,#7c3aed,#4f46e5);
                        color:white;border-radius:50%;width:32px;height:32px;
                        display:flex;align-items:center;justify-content:center;
                        font-weight:800;font-size:0.9rem;flex-shrink:0">{num}</div>
            <span style="font-size:1.05rem;font-weight:700;color:#e2e8f0">{title}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
