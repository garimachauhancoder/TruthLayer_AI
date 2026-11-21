"""TruthLayer AI: Enterprise-Grade AI-Powered Fact-Check Agent web application."""

import os
from urllib.parse import urlparse
from dotenv import load_dotenv
import pandas as pd
import pymupdf
import streamlit as st

from pdf_processor import extract_text_from_pdf, PDFProcessingError
from claim_extractor import extract_claims
from fact_checker import verify_claims_batch

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
        display: flex;
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
    for k in ["results", "claims", "doc_name", "pdf_bytes"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

st.sidebar.caption("🛡️ TruthLayer AI &bull; Strict Grounding &bull; Zero Hallucinations")


# --- Main Application Header ---
st.markdown('<div class="page-title">Document Verification Hub</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Upload any research paper, earnings release, news report, or whitepaper to extract checkable factual claims and audit them against live web ground truth.</div>', unsafe_allow_html=True)

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
    uploaded_file = st.file_uploader(
        "Drop files here. Get extracted claims, live search verification, and audit reports with exact citations.",
        type=["pdf"],
        help="Upload any text-based PDF file."
    )

with col_demo:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button("⚡ Try Sample Document", help="Click to load a pre-built 2-page tech & financial intelligence document"):
        st.session_state["pdf_bytes"] = generate_sample_pdf()
        st.session_state["doc_name"] = "Sample_AI_Market_Briefing_2024.pdf"
        st.toast("Sample PDF loaded! Click 'Analyze Document' below.", icon="📄")

# Set active document source
active_pdf_data = None
active_doc_name = None

if uploaded_file is not None:
    active_pdf_data = uploaded_file
    active_doc_name = uploaded_file.name
    st.session_state["doc_name"] = uploaded_file.name
elif "pdf_bytes" in st.session_state and st.session_state["pdf_bytes"]:
    active_pdf_data = st.session_state["pdf_bytes"]
    active_doc_name = st.session_state.get("doc_name", "sample_document.pdf")


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


# --- Action & Execution Banner ---
if active_pdf_data is not None:
    st.markdown("<br>", unsafe_allow_html=True)
    doc_size_display = ""
    if hasattr(active_pdf_data, "size"):
        doc_size_display = f"&bull; {round(active_pdf_data.size / 1024, 1)} KB"
    elif isinstance(active_pdf_data, (bytes, bytearray)):
        doc_size_display = f"&bull; {round(len(active_pdf_data) / 1024, 1)} KB (Interactive Demo)"

    st.markdown(f"""
    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:1.1rem 1.5rem; display:flex; align-items:center; justify-content:space-between; margin-bottom:1.2rem; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
        <div style="display:flex; align-items:center; gap:0.9rem;">
            <span style="font-size:2rem;">📄</span>
            <div>
                <div style="font-weight:700; color:#0f172a !important; font-size:1.02rem;">{active_doc_name}</div>
                <div style="font-size:0.83rem; color:#475569 !important;">Ready for automated multi-step verification {doc_size_display}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    can_run = bool(gemini_api_key and tavily_api_key)
    run_audit_btn = st.button("🚀 Analyze & Audit Document", type="primary", disabled=not can_run)

    if not can_run:
        st.info("⚠️ Please ensure a Gemini API key and Tavily search key are provided to start the audit.")

    if run_audit_btn:
        try:
            with st.status("Auditing document with TruthLayer AI...", expanded=True) as status_box:
                # Step 1: Text extraction
                st.write("📄 **Step 1/3:** Extracting text page-by-page via PyMuPDF...")
                pages = extract_text_from_pdf(active_pdf_data)
                st.write(f"✓ Successfully extracted text across **{len(pages)}** document page(s).")

                # Step 2: Claim extraction
                st.write("🧠 **Step 2/3:** Extracting checkable factual assertions with Gemini 2.5 Flash...")
                claims = extract_claims(
                    pages=pages,
                    gemini_api_key=gemini_api_key,
                    max_claims=max_claims_setting
                )

                if not claims:
                    status_box.update(label="No checkable claims detected", state="error")
                    st.error("No factual claims (statistics, dates, financial, or technical assertions) were found in this document.")
                    st.stop()

                st.write(f"✓ Extracted **{len(claims)}** distinct verifiable claims with page citations.")

                # Step 3: Web search & verification
                st.write("🌐 **Step 3/3:** Querying live web via Tavily and evaluating evidence with Gemini...")
                results = verify_claims_batch(
                    claims=claims,
                    gemini_api_key=gemini_api_key,
                    tavily_api_key=tavily_api_key
                )

                status_box.update(label="Audit Completed Successfully!", state="complete")

            st.session_state["results"] = results
            st.session_state["claims"] = claims

        except PDFProcessingError as pdf_err:
            st.error(f"❌ PDF Processing Error: {pdf_err}")
        except Exception as exc:
            st.error(f"❌ Verification Pipeline Error: {exc}")


# --- Results & Audit Intelligence Dashboard ---
if "results" in st.session_state and st.session_state["results"]:
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

                st.markdown(f"**Document Statement:**\n> *\"{r['claim']}\"*")

                # Ground truth correction box with explicit contrast
                if r.get("correct_fact") and r["correct_fact"] != "N/A":
                    st.markdown(f"""
                    <div style="background:#fefce8 !important; border-left:4px solid #eab308; padding:0.8rem 1.1rem; border-radius:6px; margin:0.85rem 0;">
                        <strong style="color:#854d0e !important; font-size:0.95rem;">💡 Ground Truth & Correction:</strong><br>
                        <span style="color:#713f12 !important; font-size:0.92rem; font-weight:500;">{r['correct_fact']}</span>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"**Verification Rationale:**\n{r.get('explanation', 'No detailed rationale available.')}")

                sources = r.get("sources", [])
                st.markdown("**🔗 Verified Evidence Sources:**")
                if sources:
                    source_html = " ".join([
                        f'<a href="{url}" target="_blank" class="source-tag">🌐 {get_domain_from_url(url)}</a>'
                        for url in sources
                    ])
                    st.markdown(source_html, unsafe_allow_html=True)
                else:
                    st.caption("No authoritative sources found for this assertion.")

    # TAB 2: Statistical Breakdown
    with tab_analytics:
        st.markdown("#### Claim Distribution Analysis")
        chart_df = pd.DataFrame({
            "Status": ["Verified", "Inaccurate", "False", "Insufficient Evidence"],
            "Count": [n_verified, n_inaccurate, n_false, n_insufficient]
        }).set_index("Status")

        st.bar_chart(chart_df, color="#0284c7")

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
            for s in r.get("sources", []):
                if s not in all_sources:
                    all_sources.append(s)

        if all_sources:
            for s_idx, src in enumerate(all_sources, start=1):
                st.markdown(f"**{s_idx}.** [{src}]({src}) &nbsp; `({get_domain_from_url(src)})`")
        else:
            st.info("No external source URLs were retrieved for this document.")

    # TAB 4: Export & Report
    with tab_export:
        st.markdown("#### Export Audit Report")
        st.write("Download the complete fact-checking report for records, presentations, or compliance audits.")

        df_export = pd.DataFrame([
            {
                "Claim Number": i,
                "Original Claim": r["claim"],
                "Page": r.get("page", 1),
                "Category": r.get("category", ""),
                "Audit Status": r["status"],
                "Correct Information": r.get("correct_fact", "N/A"),
                "Explanation": r.get("explanation", ""),
                "Sources": " | ".join(r.get("sources", []))
            }
            for i, r in enumerate(results, start=1)
        ])

        csv_bytes = df_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Full CSV Audit Report",
            data=csv_bytes,
            file_name=f"truthlayer_audit_{doc_name}.csv",
            mime="text/csv"
        )
