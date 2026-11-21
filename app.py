"""TruthLayer AI: Enterprise-Grade AI-Powered Fact-Check Agent web application."""

import os
import hashlib
import textwrap
from urllib.parse import urlparse
from dotenv import load_dotenv
import pandas as pd
import altair as alt
import pymupdf
import streamlit as st

from pdf_processor import extract_text_from_pdf
from claim_extractor import extract_claims
from fact_checker import verify_claims_batch
from pdf_highlighter import annotate_problematic_claims, render_pdf_page
from web_search import search_web_query
from report_generator import generate_factcheck_pdf, report_filename

# Page configuration
st.set_page_config(
    page_title="TruthLayer AI | Autonomous Fact-Check Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-Contrast Cross-Theme CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    /* Global Base */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0f172a !important;
    }

    h1, h2, h3, h4, .brand-font {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #0f172a !important;
    }

    p, span, label, div {
        color: #1e293b;
    }

    .stApp {
        background-color: #f8fafc !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Top Navigation Bar Exact RunDocs Style */
    .top-navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff !important;
        padding: 0.65rem 1.5rem;
        border-radius: 14px;
        border: 1px solid #f1f5f9;
        margin-bottom: 1.8rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .top-left-brand {
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .top-brand-title {
        font-weight: 800;
        font-size: 1.12rem;
        color: #0f172a !important;
        letter-spacing: -0.02em;
    }
    .top-search-pill {
        display: none;
        align-items: center;
        gap: 0.65rem;
        background: #f8fafc !important;
        border: 1.5px solid #bae6fd !important;
        box-shadow: 0 0 0 4px rgba(224, 242, 254, 0.65) !important;
        padding: 0.42rem 1.15rem;
        border-radius: 9999px;
        width: 380px;
    }
    .top-search-icon {
        color: #94a3b8 !important;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
    }
    .top-search-text {
        color: #94a3b8 !important;
        font-size: 0.88rem;
        font-weight: 400;
    }
    .top-search-kbd {
        margin-left: auto;
        font-size: 0.72rem;
        background: #e2e8f0 !important;
        border: 1px solid #cbd5e1;
        padding: 0.15rem 0.45rem;
        border-radius: 6px;
        color: #64748b !important;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .top-right-group {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .top-bell-btn {
        color: #64748b !important;
        font-size: 1.15rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        padding: 0.2rem;
        transition: color 0.15s ease;
    }
    .top-bell-btn:hover {
        color: #0f172a !important;
    }
    .top-gratuit-pill {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        background: #eafaf1 !important;
        color: #16a34a !important;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.3rem 0.75rem;
        border-radius: 9999px;
        border: 1px solid #bbf7d0 !important;
        letter-spacing: 0.01em;
    }
    .top-avatar-au {
        width: 34px;
        height: 34px;
        background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.84rem;
        letter-spacing: 0.02em;
        box-shadow: 0 2px 6px rgba(99, 102, 241, 0.3);
    }

    /* Page Header Titles */
    .page-title {
        font-size: 1.65rem;
        font-weight: 800;
        color: #0f172a !important;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .page-subtitle {
        color: #475569 !important;
        font-size: 0.95rem;
        margin-top: 0.25rem;
        margin-bottom: 1.8rem;
    }

    /* Dropzone Customization with High Contrast */
    [data-testid="stFileUploader"] {
        padding: 0;
    }
    [data-testid="stFileUploaderDropzone"] {
        border: 2px solid #38bdf8 !important;
        border-radius: 20px !important;
        background-color: #ffffff !important;
        padding: 2.8rem 1.5rem !important;
        text-align: center !important;
        box-shadow: 0 8px 30px -4px rgba(56, 189, 248, 0.12) !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #0284c7 !important;
        background-color: #f8fbff !important;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: #0f172a !important;
    }
    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] small {
        color: #475569 !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        color: #0284c7 !important;
        background-color: #f0f9ff !important;
        border: 1px solid #bae6fd !important;
        font-weight: 600 !important;
    }

    /* Feature Cards */
    .section-eyebrow {
        text-align: center;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #64748b !important;
        margin: 2.4rem 0 1.2rem 0;
    }
    .feature-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.25rem 1.35rem;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        height: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .feature-icon {
        width: 40px;
        height: 40px;
        min-width: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.15rem;
    }
    .icon-violet { background: #f5f3ff !important; color: #7c3aed !important; }
    .icon-amber { background: #fffbeb !important; color: #d97706 !important; }
    .icon-emerald { background: #ecfdf5 !important; color: #059669 !important; }

    .feature-title {
        font-weight: 700;
        font-size: 0.95rem;
        color: #0f172a !important;
        margin-bottom: 0.25rem;
    }
    .feature-desc {
        font-size: 0.83rem;
        color: #475569 !important;
        line-height: 1.4;
    }

    /* Supported Formats Footer */
    .supported-footer {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        margin-top: 2.2rem;
        color: #64748b !important;
        font-size: 0.82rem;
    }
    .format-tag {
        background: #0ea5e9 !important;
        color: #ffffff !important;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 0.2rem 0.65rem;
        border-radius: 9999px;
    }

    /* Truth Score Hero Card (DARK BACKGROUND -> PURE WHITE TEXT) */
    .score-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        border-radius: 16px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .score-card, .score-card * {
        color: #ffffff !important;
    }
    .score-card .score-eyebrow {
        color: #94a3b8 !important;
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .score-card .score-title {
        font-size: 1.65rem;
        font-weight: 800;
        color: #ffffff !important;
        margin: 0.2rem 0;
    }
    .score-card .score-desc {
        font-size: 0.9rem;
        color: #cbd5e1 !important;
        max-width: 550px;
    }
    .score-card .score-metric {
        font-size: 2.8rem;
        font-weight: 800;
        line-height: 1;
    }
    .score-card .score-label {
        font-size: 0.78rem;
        color: #94a3b8 !important;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* KPI Summary Cards (WHITE BACKGROUND -> DARK TEXT) */
    .kpi-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.15rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .kpi-card * {
        color: #0f172a !important;
    }

    /* Status Badges */
    .badge-pill {
        display: inline-block;
        font-size: 0.74rem;
        font-weight: 700;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        letter-spacing: 0.02em;
    }
    .badge-verified { background: #dcfce7 !important; color: #14532d !important; border: 1px solid #86efac; }
    .badge-inaccurate { background: #fef9c3 !important; color: #713f12 !important; border: 1px solid #fde047; }
    .badge-false { background: #fee2e2 !important; color: #7f1d1d !important; border: 1px solid #fca5a5; }
    .badge-insufficient { background: #f1f5f9 !important; color: #334155 !important; border: 1px solid #cbd5e1; }

    /* Source Links */
    .source-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: #f8fafc !important;
        border: 1px solid #cbd5e1;
        color: #1d4ed8 !important;
        padding: 0.35rem 0.75rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        text-decoration: none;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
    }
    .source-tag:hover {
        background: #eff6ff !important;
        border-color: #93c5fd;
    }

    /* Expanders High Contrast */
    [data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        margin-bottom: 0.6rem !important;
    }
    [data-testid="stExpander"] summary {
        color: #0f172a !important;
    }
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    [data-testid="stExpander"] [data-testid="stVerticalBlock"] p,
    [data-testid="stExpander"] [data-testid="stVerticalBlock"] span,
    [data-testid="stExpander"] [data-testid="stVerticalBlock"] div {
        color: #1e293b !important;
    }
    [data-testid="stExpander"] blockquote,
    [data-testid="stExpander"] blockquote p {
        color: #334155 !important;
        background: #f8fafc !important;
        border-left: 3px solid #cbd5e1 !important;
        padding: 0.4rem 0.8rem !important;
    }

    /* Tabs Styling */
    button[data-baseweb="tab"] {
        color: #475569 !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0284c7 !important;
        font-weight: 700 !important;
    }

    /* Radio / Segment Filter */
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] p,
    [data-testid="stRadio"] span {
        color: #0f172a !important;
        font-weight: 600 !important;
    }

    /* Sidebar High Contrast */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #0f172a !important;
    }
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] small {
        color: #64748b !important;
    }
    section[data-testid="stSidebar"] input {
        color: #0f172a !important;
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
    }

    /* Primary Action Buttons */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border-radius: 9px !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 0.6rem 1.6rem !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.25) !important;
    }
    div.stButton > button:first-child * {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

STATUS_CONFIG = {
    "Verified": {"icon": "✅", "badge": "badge-verified", "label": "Verified"},
    "Inaccurate": {"icon": "⚠️", "badge": "badge-inaccurate", "label": "Inaccurate"},
    "False": {"icon": "❌", "badge": "badge-false", "label": "False"},
    "Insufficient Evidence": {"icon": "ℹ️", "badge": "badge-insufficient", "label": "Insufficient Evidence"}
}


def get_api_keys() -> tuple[str, str]:
    """Retrieves API keys dynamically from environment variables or Streamlit secrets."""
    load_dotenv(override=True)
    gemini_key = ""
    tavily_key = ""

    try:
        gemini_key = st.secrets.get("GEMINI_API_KEY", "") or st.secrets.get("GOOGLE_API_KEY", "")
        tavily_key = st.secrets.get("TAVILY_API_KEY", "")
    except Exception:
        pass

    if not gemini_key:
        gemini_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not tavily_key:
        tavily_key = os.getenv("TAVILY_API_KEY", "")

    return (gemini_key or "").strip().strip("'\""), (tavily_key or "").strip().strip("'\"")


def generate_sample_pdf() -> bytes:
    """Creates a sample 2-page business & tech PDF document for immediate testing."""
    doc = pymupdf.open()
    p1 = doc.new_page()
    p1.insert_text((50, 72), """Global AI & Cloud Market Intelligence Briefing 2024
Page 1: Executive Highlights & Performance

1. Google was founded on September 4, 1998 by Larry Page and Sergey Brin in Menlo Park, California.
2. In 2023, the global artificial intelligence software market reached a valuation of $136 billion.
3. Apple Inc. reported record annual revenue of $850 billion for the fiscal year ended September 2023.
4. The first commercial iPhone was unveiled by Steve Jobs on January 9, 2007 and released in June 2007.
5. In 2024, Python ranked as the world's most widely adopted programming language on the TIOBE index.""")

    p2 = doc.new_page()
    p2.insert_text((50, 72), """Global AI & Cloud Market Intelligence Briefing 2024
Page 2: Technological Infrastructure & Projections

6. By December 2020, commercial fusion power plants were providing 25% of the United States power grid.
7. GPT-4 was announced and launched by OpenAI in March 2023.
8. The global population exceeded 8 billion human beings in November 2022 according to the United Nations.
9. NASA successfully landed astronauts on the surface of Mars in July 2021.
10. Global smartphone users reached approximately 4.9 billion individuals worldwide by 2024.""")
    return doc.tobytes()


def get_domain_from_url(url: str) -> str:
    """Helper to extract a clean host domain from a URL."""
    try:
        domain = urlparse(url).netloc
        return domain.replace("www.", "") if domain else url
    except Exception:
        return url


def _open_highlighted_review(audit_id: str) -> None:
    """Reveal the selected PDF preview after its download button is clicked."""
    st.session_state["open_highlighted_review_for"] = audit_id


# --- Background Key & Engine Resolution ---
env_gemini_key, env_tavily_key = get_api_keys()
gemini_api_key = env_gemini_key
tavily_api_key = env_tavily_key

# Render Top Bar matching exact reference design
navbar_html = '''<div class="top-navbar">
<div class="top-left-brand">
<span style="font-size:1.35rem;">🛡️</span>
<span class="top-brand-title brand-font">TruthLayer AI</span>
</div>
<div class="top-search-pill">
<span class="top-search-icon">🔍</span>
<span class="top-search-text">Search or run a command...</span>
<span class="top-search-kbd">⌘K</span>
</div>
<div class="top-right-group">
<span class="top-bell-btn" title="Notifications">🔔</span>
<span class="top-gratuit-pill">✨ Gratuit</span>
<div class="top-avatar-au">AU</div>
</div>
</div>'''

st.markdown(navbar_html, unsafe_allow_html=True)

with st.form("live_web_search_form", clear_on_submit=False):
    search_col, button_col = st.columns([6, 1], vertical_alignment="bottom")
    with search_col:
        web_query = st.text_input(
            "Search the live web",
            placeholder="Search the web for a topic, fact, or source...",
            label_visibility="collapsed",
        )
    with button_col:
        web_search_submitted = st.form_submit_button(
            "Search web",
            icon=":material/search:",
            type="primary",
            width="stretch",
        )

if web_search_submitted:
    if not tavily_api_key:
        st.session_state["web_search_result"] = {
            "query": web_query,
            "error": "Tavily API key is not configured. Add TAVILY_API_KEY to .env and restart the app.",
        }
    elif not web_query.strip():
        st.session_state["web_search_result"] = {"query": "", "error": "Enter a query to search the web."}
    else:
        with st.spinner("Searching the live web..."):
            try:
                search_output = search_web_query(web_query, tavily_api_key=tavily_api_key)
                st.session_state["web_search_result"] = search_output.to_dict()
            except Exception as exc:
                st.session_state["web_search_result"] = {"query": web_query, "error": str(exc)}

web_search_output = st.session_state.get("web_search_result")
if web_search_output:
    if web_search_output.get("error"):
        st.error(f"Web search failed: {web_search_output['error']}")
    else:
        st.markdown(f"#### Live results for: {web_search_output.get('query', '')}")
        if web_search_output.get("warnings"):
            st.warning("Some search sources did not respond: " + "; ".join(web_search_output["warnings"]))
        for source in web_search_output.get("source_details", []):
            title = " ".join((source.get("title") or source.get("url")).split())
            short_title = textwrap.shorten(title, width=100, placeholder="…")
            st.link_button(short_title, source["url"], icon=":material/open_in_new:", width="content")
            pub_date = source.get("published_date") or "Publication date not provided by search source"
            topics = " + ".join(source.get("search_topics", []))
            st.caption(f"{pub_date} · {topics} search")
            if source.get("excerpt"):
                excerpt = " ".join(source["excerpt"].split())
                st.text(textwrap.shorten(excerpt, width=220, placeholder="…"))
                if len(excerpt) > 220:
                    with st.expander("Read more"):
                        st.text(excerpt)


# --- Sidebar Navigation & Controls ---
st.sidebar.markdown("""
<div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:1rem;">
<span style="font-size:1.5rem;">🛡️</span>
<div>
<div style="font-weight:800; font-size:1.15rem; color:#0f172a !important;" class="brand-font">TruthLayer</div>
<div style="font-size:0.75rem; color:#64748b !important;">v2.5 Production</div>
</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.caption("NAVIGATION")
st.sidebar.markdown("📁 **Workspaces** &nbsp; <span style='background:#f1f5f9; padding:2px 8px; border-radius:12px; font-size:0.75rem; color:#334155;'>Default</span>", unsafe_allow_html=True)
st.sidebar.markdown("📄 **Active Document** &nbsp; <span style='background:#e0f2fe; padding:2px 8px; border-radius:12px; font-size:0.75rem; color:#0369a1;'>Live</span>", unsafe_allow_html=True)
st.sidebar.markdown("📊 **Audit Intelligence** &nbsp; <span style='background:#f1f5f9; padding:2px 8px; border-radius:12px; font-size:0.75rem; color:#334155;'>Active</span>", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.caption("AUDIT SETTINGS")

max_claims_setting = st.sidebar.slider(
    "Max claims to analyze",
    min_value=3,
    max_value=15,
    value=8,
    help="Target number of claims to extract and verify."
)

if st.sidebar.button("🔄 Reset / Clear Session"):
    for k in ["results", "claims", "doc_name", "sample_doc_name", "pdf_bytes", "active_doc_digest", "highlighted_pdf_bytes", "highlight_summary", "highlight_error", "report_pdf_bytes", "report_pdf_error", "document_audits", "document_audit_errors", "selected_audit_id", "open_highlighted_review_for"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

st.sidebar.caption("🛡️ TruthLayer AI &bull; Strict Grounding &bull; Zero Hallucinations")


# --- Main Application Header ---
st.markdown('<div class="page-title">Document Verification Hub</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Upload any research paper, earnings release, news report, or whitepaper to extract checkable factual claims and audit them against live web ground truth.</div>', unsafe_allow_html=True)

# --- WHAT HAPPENS TO YOUR DOCUMENTS (Feature Cards) ---
st.markdown('<div class="section-eyebrow">WHAT HAPPENS TO YOUR DOCUMENTS</div>', unsafe_allow_html=True)

f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon icon-violet">🧠</div>
        <div>
            <div class="feature-title">AI Claim Extraction</div>
            <div class="feature-desc">PyMuPDF extracts text page-by-page. Gemini identifies hard statistics, dates, financial data, and technical metrics.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with f_col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon icon-amber">⚡</div>
        <div>
            <div class="feature-title">Live Web Verification</div>
            <div class="feature-desc">Tavily executes real-time targeted queries across authoritative sources, government databases, and verified publications.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with f_col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon icon-emerald">🛡️</div>
        <div>
            <div class="feature-title">Zero Hallucinations</div>
            <div class="feature-desc">Rigorous evidence evaluation. Only genuine, verified source URLs are cited with full page-number traceability.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="supported-footer">
    <span>Supported formats:</span>
    <span class="format-tag">PDF</span>
    <span class="format-tag">EARNINGS REPORTS</span>
    <span class="format-tag">RESEARCH PAPERS</span>
    <span class="format-tag">GOV BRIEFS</span>
    <span style="color:#0ea5e9; font-weight:700;">+</span>
</div>
""", unsafe_allow_html=True)



# Missing Key Alert Banner
has_ai = bool(gemini_api_key)
if not has_ai or not tavily_api_key:
    missing_items = []
    if not has_ai:
        missing_items.append("**Gemini API Key**")
    if not tavily_api_key:
        missing_items.append("**Tavily API Key** ([Get free key](https://tavily.com/))")

    st.warning(f"🔑 **Configuration Notice:** Please add your {' and '.join(missing_items)} in `.env` to enable live fact-checking.")


# --- Document Input Section (Upload or Demo Sample) ---
col_upload, col_demo = st.columns([3, 1])

with col_upload:
    uploaded_files = st.file_uploader(
        "Drop files here. Get extracted claims, live search verification, and audit reports with exact citations.",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more text-based PDF files."
    )

with col_demo:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button("⚡ Try Sample Document", help="Click to load a pre-built 2-page tech & financial intelligence document"):
        st.session_state["pdf_bytes"] = generate_sample_pdf()
        st.session_state["sample_doc_name"] = "Sample_AI_Market_Briefing_2024.pdf"
        st.toast("Sample PDF loaded! Click 'Analyze Document' below.", icon="📄")

# Keep every selected PDF together with its original bytes for its own audit and report.
active_documents = []
if uploaded_files:
    for uploaded_pdf in uploaded_files:
        active_documents.append((uploaded_pdf.name, uploaded_pdf.getvalue()))
elif st.session_state.get("pdf_bytes"):
    active_documents.append((st.session_state.get("sample_doc_name", "sample_document.pdf"), bytes(st.session_state["pdf_bytes"])))

# --- Multi-document audit action ---
if active_documents:
    st.markdown("### PDFs selected for audit")
    for file_name, file_bytes in active_documents:
        st.caption(f"{file_name} · {len(file_bytes) / 1024:.1f} KB")

    can_run_batch = bool(gemini_api_key and tavily_api_key)
    run_batch_audit = st.button(
        f"Analyze and audit {len(active_documents)} PDF(s)",
        type="primary",
        disabled=not can_run_batch,
    )
    if not can_run_batch:
        st.info("Configure both Gemini and Tavily API keys to run an audit.")

    if run_batch_audit:
        audits = dict(st.session_state.get("document_audits", {}))
        audit_errors = {}
        for file_name, file_bytes in active_documents:
            audit_id = hashlib.sha256(file_name.encode("utf-8") + b"\0" + file_bytes).hexdigest()
            try:
                with st.status(f"Auditing {file_name}...", expanded=False) as status_box:
                    pages = extract_text_from_pdf(file_bytes)
                    claims = extract_claims(
                        pages=pages,
                        gemini_api_key=gemini_api_key,
                        max_claims=max_claims_setting,
                    )
                    if not claims:
                        audit_errors[file_name] = "No checkable claims were extracted."
                        status_box.update(label=f"No claims found in {file_name}", state="error")
                        continue
                    results = verify_claims_batch(
                        claims=claims,
                        gemini_api_key=gemini_api_key,
                        tavily_api_key=tavily_api_key,
                    )
                    status_box.update(label=f"Audit complete: {file_name}", state="complete")
                highlighted_pdf = None
                highlight_summary = {"details": [], "unmatched": [], "pages": []}
                highlight_error = ""
                try:
                    highlighted_pdf, highlight_summary = annotate_problematic_claims(file_bytes, results)
                except Exception as exc:
                    highlight_error = str(exc)
                report_pdf = None
                report_error = ""
                try:
                    report_pdf = generate_factcheck_pdf(results, file_name)
                except Exception as exc:
                    report_error = str(exc)
                audits[audit_id] = {
                    "document_name": file_name,
                    "pdf_bytes": file_bytes,
                    "claims": claims,
                    "results": results,
                    "highlighted_pdf_bytes": highlighted_pdf,
                    "highlight_summary": highlight_summary,
                    "report_pdf_bytes": report_pdf,
                    "highlight_error": highlight_error,
                    "report_pdf_error": report_error,
                }
            except Exception as exc:
                audit_errors[file_name] = str(exc)

        st.session_state["document_audits"] = audits
        st.session_state["document_audit_errors"] = audit_errors
        if audits:
            st.success("PDF processing finished. Select an audited document below to view its results.")

# Choose one audited PDF at a time so claim pages, annotations, and exports remain document-specific.
document_audits = st.session_state.get("document_audits", {})
for failed_name, error in st.session_state.get("document_audit_errors", {}).items():
    st.error(f"{failed_name}: {error}")

if document_audits:
    audit_ids = list(document_audits)
    selected_audit_id = st.selectbox(
        "View results for",
        audit_ids,
        format_func=lambda audit_id: f"{document_audits[audit_id]['document_name']} ({len(document_audits[audit_id]['results'])} claims)",
        key="selected_audit_id",
    )
    selected_audit = document_audits[selected_audit_id]
    st.session_state["results"] = selected_audit["results"]
    st.session_state["claims"] = selected_audit["claims"]
    st.session_state["doc_name"] = selected_audit["document_name"]
    if selected_audit.get("highlighted_pdf_bytes") is not None:
        st.session_state["highlighted_pdf_bytes"] = selected_audit["highlighted_pdf_bytes"]
    else:
        st.session_state.pop("highlighted_pdf_bytes", None)
    st.session_state["highlight_summary"] = selected_audit["highlight_summary"]
    st.session_state["report_pdf_bytes"] = selected_audit["report_pdf_bytes"]
    st.session_state["highlight_error"] = selected_audit.get("highlight_error", "")
    st.session_state["report_pdf_error"] = selected_audit.get("report_pdf_error", "")
elif not st.session_state.get("results"):
    st.session_state.pop("results", None)

# --- Results & Audit Intelligence Dashboard ---
if document_audits and st.session_state.get("results"):
    results = st.session_state["results"]
    claims = st.session_state.get("claims", [])
    doc_name = st.session_state.get("doc_name", "Document")

    st.markdown("<hr style='border:none; border-top:1px solid #e2e8f0; margin:2.5rem 0 2rem 0;'/>", unsafe_allow_html=True)

    # 1. Truth Score & Executive KPI Summary
    status_counts = pd.Series([r["status"] for r in results]).value_counts()
    n_verified = int(status_counts.get("Verified", 0))
    n_inaccurate = int(status_counts.get("Inaccurate", 0))
    n_false = int(status_counts.get("False", 0))
    n_insufficient = int(status_counts.get("Insufficient Evidence", 0))
    n_total = len(results)

    # Calculate Factuality Reliability Index
    evaluable = n_total - n_insufficient
    if evaluable > 0:
        truth_score = int(round((n_verified / evaluable) * 100))
    else:
        truth_score = 50

    if truth_score >= 80:
        score_grade = "High Reliability"
        score_desc = "Majority of claims corroborated by authoritative live web data."
        score_color = "#38bdf8"
    elif truth_score >= 50:
        score_grade = "Moderate Credibility"
        score_desc = "Document contains several inaccurate or outdated assertions."
        score_color = "#facc15"
    else:
        score_grade = "High Misinformation Risk"
        score_desc = "Critical claims contradicted or disproven by credible evidence."
        score_color = "#f87171"

    st.markdown(f"""
    <div class="score-card">
        <div>
            <div class="score-eyebrow">EXECUTIVE INTEGRITY AUDIT</div>
            <div class="score-title brand-font">{score_grade}</div>
            <div class="score-desc">{score_desc} Evaluated across {n_total} key factual assertions in <em>{doc_name}</em>.</div>
        </div>
        <div style="text-align:right;">
            <div class="score-metric" style="color:{score_color} !important;">{truth_score}%</div>
            <div class="score-label">Factuality Score</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4 KPI Overview Cards
    k_col1, k_col2, k_col3, k_col4 = st.columns(4)
    with k_col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:0.75rem; font-weight:800; color:#15803d !important; letter-spacing:0.05em;">VERIFIED</div>
            <div style="font-size:1.8rem; font-weight:800; color:#16a34a !important; margin:0.2rem 0;">{n_verified}</div>
            <div style="font-size:0.75rem; color:#475569 !important;">Matches ground truth</div>
        </div>
        """, unsafe_allow_html=True)

    with k_col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:0.75rem; font-weight:800; color:#854d0e !important; letter-spacing:0.05em;">INACCURATE</div>
            <div style="font-size:1.8rem; font-weight:800; color:#d97706 !important; margin:0.2rem 0;">{n_inaccurate}</div>
            <div style="font-size:0.75rem; color:#475569 !important;">Outdated / wrong figures</div>
        </div>
        """, unsafe_allow_html=True)

    with k_col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:0.75rem; font-weight:800; color:#991b1b !important; letter-spacing:0.05em;">FALSE</div>
            <div style="font-size:1.8rem; font-weight:800; color:#dc2626 !important; margin:0.2rem 0;">{n_false}</div>
            <div style="font-size:0.75rem; color:#475569 !important;">Directly contradicted</div>
        </div>
        """, unsafe_allow_html=True)

    with k_col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:0.75rem; font-weight:800; color:#334155 !important; letter-spacing:0.05em;">INSUFFICIENT</div>
            <div style="font-size:1.8rem; font-weight:800; color:#64748b !important; margin:0.2rem 0;">{n_insufficient}</div>
            <div style="font-size:0.75rem; color:#475569 !important;">Inconclusive proof</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Tabbed Audit Views ---
    tab_claims, tab_analytics, tab_sources, tab_export = st.tabs([
        f"🔎 Detailed Claims Audit ({n_total})",
        "📊 Statistical Breakdown",
        "🌐 Source Citations Directory",
        "📥 Export & Report"
    ])

    # TAB 1: Detailed Claims Audit with Status Filter
    with tab_claims:
        f_options = ["All", "Verified", "Inaccurate", "False", "Insufficient Evidence"]
        selected_filter = st.radio(
            "Filter by status:",
            f_options,
            horizontal=True,
            format_func=lambda x: f"{x} ({n_verified if x=='Verified' else n_inaccurate if x=='Inaccurate' else n_false if x=='False' else n_insufficient if x=='Insufficient Evidence' else n_total})"
        )

        filtered_results = [r for r in results if selected_filter == "All" or r["status"] == selected_filter]

        if not filtered_results:
            st.info(f"No claims found with status: **{selected_filter}**")

        for idx, r in enumerate(filtered_results, start=1):
            status_info = STATUS_CONFIG.get(r["status"], STATUS_CONFIG["Insufficient Evidence"])
            icon = status_info["icon"]
            badge_class = status_info["badge"]
            status_label = status_info["label"]

            header_str = f"{icon} Claim #{idx} (Page {r.get('page', 1)}) — [{status_label}]"

            with st.expander(header_str, expanded=(r["status"] in ["False", "Inaccurate"])):
                st.markdown(f"""
                <div style="margin-bottom:0.75rem;">
                    <span class="badge-pill {badge_class}">{status_label}</span>
                    <span style="font-size:0.8rem; font-weight:700; color:#475569 !important; margin-left:0.6rem;">PAGE {r.get('page', 1)}</span>
                    <span style="font-size:0.8rem; font-weight:700; color:#64748b !important; margin-left:0.6rem;">&bull;&nbsp; CATEGORY: {r.get('category', 'factual').upper()}</span>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"**Original sentence (verbatim):**\n> {r.get('original_sentence', r['claim'])}")
                st.markdown(f"**Claim checked:** {r['claim']}")

                # Ground truth correction box with explicit contrast
                if r.get("correct_fact") and r["correct_fact"] != "N/A":
                    st.markdown(f"""
                    <div style="background:#fefce8 !important; border-left:4px solid #eab308; padding:0.8rem 1.1rem; border-radius:6px; margin:0.85rem 0;">
                        <strong style="color:#854d0e !important; font-size:0.95rem;">💡 Ground Truth & Correction:</strong><br>
                        <span style="color:#713f12 !important; font-size:0.92rem; font-weight:500;">{r['correct_fact']}</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"**Verification Rationale:**\n{r.get('explanation', 'No detailed rationale available.')}")
                if r.get("search_warnings"):
                    st.warning("Search was partial: " + "; ".join(r["search_warnings"]))

                sources = r.get("sources", [])
                st.markdown("**🔗 Verified Evidence Sources:**")
                if sources:
                    details_by_url = {
                        item.get("url"): item for item in r.get("source_details", [])
                    }
                    for url in sources:
                        detail = details_by_url.get(url, {})
                        title = detail.get("title") or get_domain_from_url(url)
                        pub_date = detail.get("published_date") or "Publication date unavailable"
                        angles = detail.get("evidence_angles", [])
                        topics = detail.get("search_topics", [])
                        angle_label = f" · {' + '.join(a.title() for a in angles)} search" if angles else ""
                        topic_label = f" · {' + '.join(t.title() for t in topics)} index" if topics else ""
                        st.markdown(f"- [{title}]({url}) · {pub_date}{angle_label}{topic_label}")
                else:
                    st.caption("No authoritative sources found for this assertion.")

    # TAB 2: Statistical Breakdown
    with tab_analytics:
        st.markdown("#### Claim Distribution Analysis")
        chart_df = pd.DataFrame({
            "Status": ["Verified", "Inaccurate", "False", "Insufficient Evidence"],
            "Count": [n_verified, n_inaccurate, n_false, n_insufficient]
        })
        status_order = ["False", "Inaccurate", "Insufficient Evidence", "Verified"]
        distribution_chart = (
            alt.Chart(chart_df)
            .mark_bar(color="#0284c7")
            .encode(
                x=alt.X(
                    "Status:N",
                    sort=status_order,
                    axis=alt.Axis(labelAngle=0, labelOverlap=False, labelLimit=220),
                    title=None,
                ),
                y=alt.Y("Count:Q", title="Claims", scale=alt.Scale(domainMin=0)),
                tooltip=["Status:N", "Count:Q"],
            )
            .properties(height=320)
        )
        st.altair_chart(
            distribution_chart,
            alt="Claim counts by verification status",
            width="stretch",
        )

        st.markdown("#### Audit Diagnosis")
        if n_false > 0:
            st.error(f"⚠️ **Contradictions Identified:** Found {n_false} claims directly contradicted by current records.")
        if n_inaccurate > 0:
            st.warning(f"⚠️ **Inaccuracies Detected:** Found {n_inaccurate} claims containing outdated or skewed figures.")
        if n_verified > 0:
            st.success(f"✓ **Corroborated Facts:** {n_verified} factual assertions matched live web ground truth.")

    # TAB 3: Source Citations Directory
    with tab_sources:
        st.markdown("#### Verified Live Web Sources")
        st.caption("All URLs retrieved and cross-referenced by Tavily Search and verified by Gemini.")

        all_sources = []
        for r in results:
            details_by_url = {
                item.get("url"): item for item in r.get("source_details", [])
            }
            for s in r.get("sources", []):
                if s not in [item["url"] for item in all_sources]:
                    all_sources.append(details_by_url.get(s, {"url": s}))

        if all_sources:
            for s_idx, source in enumerate(all_sources, start=1):
                src = source["url"]
                title = source.get("title") or get_domain_from_url(src)
                pub_date = source.get("published_date") or "Publication date unavailable"
                angles = source.get("evidence_angles", [])
                topics = source.get("search_topics", [])
                angle_label = f" · {' + '.join(a.title() for a in angles)} search" if angles else ""
                topic_label = f" · {' + '.join(t.title() for t in topics)} index" if topics else ""
                st.markdown(f"**{s_idx}.** [{title}]({src}) · {pub_date}{angle_label}{topic_label}")
        else:
            st.info("No external source URLs were retrieved for this document.")

    # TAB 4: Export & Report
    with tab_export:
        st.markdown("#### Export Audit Report")
        st.write("Download the complete fact-checking report for records, presentations, or compliance audits.")

        df_export = pd.DataFrame([
            {
                "Claim Number": i,
                "Original Sentence": r.get("original_sentence", r["claim"]),
                "Original Claim": r["claim"],
                "Page": r.get("page", 1),
                "Category": r.get("category", ""),
                "Audit Status": r["status"],
                "Correct Information": r.get("correct_fact", "N/A"),
                "Explanation": r.get("explanation", ""),
                "Search Warnings": " | ".join(r.get("search_warnings", [])),
                "Sources": " | ".join(r.get("sources", [])),
                "Source Details": " | ".join(
                    f"{s.get('title') or s.get('url')} — {s.get('published_date') or 'Publication date unavailable'} — {' + '.join(s.get('evidence_angles', [])) or 'unclassified'} — {' + '.join(s.get('search_topics', [])) or 'general'}"
                    for s in r.get("source_details", [])
                ),
                "Evidence Excerpts": " | ".join(
                    f"{s.get('title') or s.get('url')}: {s.get('excerpt', '')}"
                    for s in r.get("source_details", []) if s.get("excerpt")
                )
            }
            for i, r in enumerate(results, start=1)
        ])

        csv_bytes = df_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Full CSV Audit Report",
            data=csv_bytes,
            file_name=report_filename(doc_name, "csv"),
            mime="text/csv"
        )
        report_pdf_bytes = st.session_state.get("report_pdf_bytes")
        report_pdf_error = st.session_state.get("report_pdf_error")
        if report_pdf_bytes is None and not report_pdf_error:
            try:
                report_pdf_bytes = generate_factcheck_pdf(results, doc_name)
                st.session_state["report_pdf_bytes"] = report_pdf_bytes
            except Exception as report_exc:
                report_pdf_error = str(report_exc)

        if report_pdf_bytes is not None:
            st.download_button(
                label="Download PDF report",
                data=report_pdf_bytes,
                file_name=report_filename(doc_name, "pdf"),
                mime="application/pdf",
                icon=":material/picture_as_pdf:",
            )
        else:
            st.error(f"Could not generate the PDF report: {report_pdf_error}")

    with tab_export:
        if st.session_state.get("highlight_error"):
            st.error(f"Could not prepare PDF annotations: {st.session_state['highlight_error']}")
        elif "highlighted_pdf_bytes" not in st.session_state:
            st.info("Run the document audit to create highlighted PDF annotations.")
        else:
            highlighted_pdf = st.session_state["highlighted_pdf_bytes"]
            highlight_summary = st.session_state.get("highlight_summary", {})
            marked_pages = highlight_summary.get("pages", [])
            st.download_button(
                "Download highlighted PDF",
                data=highlighted_pdf,
                file_name=f"{os.path.splitext(doc_name)[0]}_highlighted.pdf",
                mime="application/pdf",
                icon=":material/download:",
                key=f"download_highlighted_pdf_{selected_audit_id}",
                on_click=_open_highlighted_review,
                args=(selected_audit_id,),
            )

            review_open = st.session_state.get("open_highlighted_review_for") == selected_audit_id
            if review_open:
                st.markdown("### Highlighted PDF review")
                st.caption("Red marks False claims. Amber marks Inaccurate claims. The downloaded PDF includes claim numbers and page references.")
                if marked_pages:
                    details = highlight_summary.get("details", [])
                    page_counts = {
                        page_num: sum(1 for item in details if item["page"] == page_num)
                        for page_num in marked_pages
                    }
                    selected_page = st.selectbox(
                        "Page with highlighted claims",
                        marked_pages,
                        format_func=lambda page_num: f"Page {page_num} · {page_counts[page_num]} highlighted claim(s)",
                        key="highlighted_pdf_page",
                    )
                    for item in details:
                        if item["page"] == selected_page:
                            st.markdown(f"**Claim #{item['claim_number']} · {item['status']}:** {item['claim']}")
                            st.caption(f"Source sentence: {item['original_sentence']}")
                    st.image(
                        render_pdf_page(highlighted_pdf, selected_page),
                        alt=f"Page {selected_page} of the PDF with problematic claims highlighted",
                        caption=f"PDF page {selected_page} · Red: False · Amber: Inaccurate",
                        width="stretch",
                    )
                else:
                    if highlight_summary.get("unmatched"):
                        st.info("No problematic sentences could be matched for highlighting. Review the unmatched claims below and use their page references to locate them manually.")
                    else:
                        st.success("No False or Inaccurate claims were found, so there are no passages to highlight.")

                unmatched = highlight_summary.get("unmatched", [])
                if unmatched:
                    st.warning(f"{len(unmatched)} problematic claim(s) could not be highlighted because the extracted sentence did not match the PDF text on its reported page.")
                    with st.expander("Claims needing manual review"):
                        for item in unmatched:
                            st.write(f"Claim #{item['claim_number']} · Page {item['page']}: {item['reason']}")
