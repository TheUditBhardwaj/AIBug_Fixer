"""
AI Bug Fixer - Streamlit Frontend
"""

import streamlit as st
import requests
import time
import os

API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="AI Bug Fixer",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⬡</text></svg>",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #06070d !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #c9d1d9;
}

[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 70% 50% at 15% 10%, rgba(79,70,229,0.09) 0%, transparent 60%),
        radial-gradient(ellipse 50% 40% at 85% 85%, rgba(124,58,237,0.07) 0%, transparent 55%);
    pointer-events: none;
    z-index: 0;
}
[data-testid="stMain"] { position: relative; z-index: 1; }

#MainMenu { visibility: visible !important; }
footer { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(10,11,18,0.97) !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] * { color: #8b949e !important; font-size: 0.85rem !important; }
[data-testid="stSidebar"] h3 { color: #c9d1d9 !important; font-size: 0.9rem !important; font-weight: 600 !important; }

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: #4f46e5 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.6rem 1.4rem !important;
    letter-spacing: 0.2px !important;
    transition: background 0.2s, box-shadow 0.2s, transform 0.15s !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.4), 0 0 0 0 rgba(79,70,229,0) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #4338ca !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.5), 0 0 16px rgba(79,70,229,0.25) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"]:active { transform: translateY(0) !important; }

/* ── Secondary button ── */
.stButton > button[kind="secondary"],
.stButton > button:not([kind]) {
    background: rgba(255,255,255,0.04) !important;
    color: #8b949e !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    transition: all 0.15s !important;
}
.stButton > button[kind="secondary"]:hover,
.stButton > button:not([kind]):hover {
    background: rgba(255,255,255,0.08) !important;
    color: #c9d1d9 !important;
    border-color: rgba(255,255,255,0.16) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > textarea {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 8px !important;
    color: #c9d1d9 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextArea > div > textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    line-height: 1.6 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > textarea:focus {
    border-color: rgba(79,70,229,0.6) !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,0.12) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > textarea::placeholder { color: #3d444d !important; }

/* ── Labels ── */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stFileUploader label,
.stMultiSelect label {
    color: #6e7681 !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.6px !important;
    text-transform: uppercase !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div > div {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 8px !important;
    color: #c9d1d9 !important;
}

/* ── Multiselect ── */
[data-testid="stMultiSelect"] > div > div {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 8px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    color: #6e7681 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    transition: all 0.15s !important;
    padding: 0.45rem 1.1rem !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(79,70,229,0.18) !important;
    color: #a5b4fc !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #c9d1d9 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
}
.streamlit-expanderContent {
    background: rgba(255,255,255,0.015) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-top: none !important;
    border-bottom-left-radius: 8px !important;
    border-bottom-right-radius: 8px !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border: none !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
}

/* ── Progress ── */
.stProgress > div > div {
    background: #4f46e5 !important;
    border-radius: 999px !important;
}
.stProgress > div {
    background: rgba(255,255,255,0.06) !important;
    border-radius: 999px !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] > div {
    background: rgba(255,255,255,0.02) !important;
    border: 1px dashed rgba(255,255,255,0.14) !important;
    border-radius: 10px !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"] > div:hover {
    border-color: rgba(79,70,229,0.45) !important;
}

/* ── Code blocks ── */
.stCode, pre {
    border-radius: 8px !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
}

/* ── Metrics ── */
[data-testid="stMetricValue"] { color: #c9d1d9 !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #6e7681 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.07) !important; margin: 1.5rem 0 !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] > div { border-top-color: #4f46e5 !important; }

/* ── Caption ── */
.stCaption, caption { color: #6e7681 !important; font-size: 0.78rem !important; }
</style>
""", unsafe_allow_html=True)


# ───────────────────────────────────────────────────────────────
# HELPERS
# ───────────────────────────────────────────────────────────────

def call_api(endpoint: str, data: dict, method: str = "POST") -> dict:
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "POST":
            response = requests.post(url, json=data, timeout=300)
        else:
            response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to backend at {API_BASE_URL}. Ensure the server is running.")
        return {}
    except requests.exceptions.Timeout:
        st.error("Request timed out. Large repositories may require more time. Please retry.")
        return {}
    except requests.exceptions.HTTPError as e:
        detail = str(e)
        try:
            detail = response.json().get("detail", str(e))
        except Exception:
            detail = response.text or str(e)
        st.error(f"Server Error: {detail}")
        return {}


def upload_file(file) -> dict:
    url = f"{API_BASE_URL}/analyze-file"
    try:
        files = {"file": (file.name, file.getvalue(), "text/plain")}
        response = requests.post(url, files=files, timeout=300)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend API.")
        return {}
    except requests.exceptions.HTTPError as e:
        detail = str(e)
        try:
            detail = response.json().get("detail", str(e))
        except Exception:
            detail = response.text or str(e)
        st.error(f"Server Error: {detail}")
        return {}


def analyze_github_repo(repo_url: str, branch: str = "main") -> dict:
    return call_api("/analyze-repo", {"repo_url": repo_url, "branch": branch})


def ask_question(question: str, code: str, analysis_result: dict = None, filename: str = None) -> str:
    """Ask a question about analyzed code."""
    data = {
        "question": question,
        "code": code,
        "filename": filename,
        "analysis_result": analysis_result,
    }
    result = call_api("/ask-question", data)
    return result.get("answer", "") if result else ""


SEV_BORDER = {
    "low":      "#238636",
    "medium":   "#9e6a03",
    "high":     "#da3633",
    "critical": "#b91c1c",
}
SEV_CHIP = {
    "low":      "background:#0d2d1f;color:#3fb950;border:1px solid #238636;",
    "medium":   "background:#2d1f0d;color:#d29922;border:1px solid #9e6a03;",
    "high":     "background:#2d0d0d;color:#f85149;border:1px solid #da3633;",
    "critical": "background:#3b0000;color:#ff7b72;border:1px solid #b91c1c;",
}
SEV_LABEL = {
    "low": "LOW", "medium": "MEDIUM", "high": "HIGH", "critical": "CRITICAL"
}
TYPE_LABEL = {
    "syntax": "Syntax", "logic": "Logic", "performance": "Performance",
    "security": "Security", "quality": "Quality",
}


def _badge(text: str, style: str) -> str:
    return (
        f'<span style="display:inline-flex;align-items:center;border-radius:4px;'
        f'padding:2px 8px;font-size:0.72rem;font-weight:600;letter-spacing:0.4px;{style}">'
        f'{text}</span>'
    )


def _mono_tag(text: str) -> str:
    return (
        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.75rem;'
        f'color:#8b949e;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);'
        f'border-radius:4px;padding:2px 7px;">{text}</span>'
    )


def display_results(result: dict, original_code: str = "", code_lang: str = "python"):
    bugs = result.get("bugs", [])
    counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for b in bugs:
        sev = b.get("severity", "medium").lower()
        if sev in counts:
            counts[sev] += 1

    # ── Summary cards ─────────────────────────────────────────
    if not bugs:
        st.markdown("""
        <div style="background:#0d2d1f;border:1px solid #238636;border-radius:10px;
                    padding:20px 24px;display:flex;align-items:center;gap:16px;margin-bottom:24px;">
            <div style="width:36px;height:36px;background:#238636;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
            </div>
            <div>
                <p style="color:#3fb950;font-weight:600;font-size:0.95rem;margin:0 0 3px 0;">No Issues Detected</p>
                <p style="color:#6e7681;font-size:0.82rem;margin:0;">AI analysis found no bugs in the submitted code.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        total = len(bugs)
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px;">
            <div style="background:#3b0000;border:1px solid #b91c1c;border-radius:10px;
                        padding:16px;text-align:center;">
                <p style="font-size:2rem;font-weight:800;color:#ff7b72;margin:0 0 4px 0;">{counts['critical']}</p>
                <p style="font-size:0.7rem;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin:0;font-weight:600;">Critical</p>
            </div>
            <div style="background:#2d0d0d;border:1px solid #da3633;border-radius:10px;
                        padding:16px;text-align:center;">
                <p style="font-size:2rem;font-weight:800;color:#f85149;margin:0 0 4px 0;">{counts['high']}</p>
                <p style="font-size:0.7rem;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin:0;font-weight:600;">High</p>
            </div>
            <div style="background:#2d1f0d;border:1px solid #9e6a03;border-radius:10px;
                        padding:16px;text-align:center;">
                <p style="font-size:2rem;font-weight:800;color:#d29922;margin:0 0 4px 0;">{counts['medium']}</p>
                <p style="font-size:0.7rem;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin:0;font-weight:600;">Medium</p>
            </div>
            <div style="background:#0d2d1f;border:1px solid #238636;border-radius:10px;
                        padding:16px;text-align:center;">
                <p style="font-size:2rem;font-weight:800;color:#3fb950;margin:0 0 4px 0;">{counts['low']}</p>
                <p style="font-size:0.7rem;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin:0;font-weight:600;">Low</p>
            </div>
        </div>
        <p style="font-size:0.75rem;color:#6e7681;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:0 0 14px 0;border-bottom:1px solid rgba(255,255,255,0.07);
                  padding-bottom:10px;">{total} issue{'s' if total != 1 else ''} found</p>
        """, unsafe_allow_html=True)

        for i, bug in enumerate(bugs, 1):
            sev  = bug.get("severity", "medium").lower()
            btype = bug.get("type", "unknown").lower()
            border_col = SEV_BORDER.get(sev, "#4f46e5")
            chip_sty   = SEV_CHIP.get(sev, "")
            sev_label  = SEV_LABEL.get(sev, sev.upper())
            type_label = TYPE_LABEL.get(btype, btype.capitalize())
            fname = bug.get("filename", "")
            fname_tag = _mono_tag(fname) if fname else ""

            line_tag = ""
            if bug.get("line_start"):
                l = f"L{bug['line_start']}"
                if bug.get("line_end") and bug["line_end"] != bug["line_start"]:
                    l += f"–{bug['line_end']}"
                line_tag = _mono_tag(l)

            severity_badge = _badge(sev_label, chip_sty)
            type_badge     = _badge(type_label,
                "background:rgba(255,255,255,0.06);color:#8b949e;border:1px solid rgba(255,255,255,0.10);")

            with st.expander(f"#{i}  —  {type_label}  /  {sev_label}", expanded=(sev in ["high", "critical"])):
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.025);
                            border:1px solid rgba(255,255,255,0.07);
                            border-left:3px solid {border_col};
                            border-radius:8px;padding:18px 20px;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap;">
                        {severity_badge}
                        {type_badge}
                        {fname_tag}
                        {line_tag}
                    </div>
                    <p style="font-size:0.875rem;color:#c9d1d9;line-height:1.7;margin:0 0 12px 0;">
                        {bug.get('description', 'No description available.')}
                    </p>
                    <p style="font-size:0.82rem;color:#6e7681;line-height:1.6;margin:0;
                              border-top:1px solid rgba(255,255,255,0.06);padding-top:10px;">
                        {bug.get('simple_explanation', '')}
                    </p>
                </div>
                """, unsafe_allow_html=True)

    # ── Explanation ──────────────────────────────────────────
    raw_explanation = result.get("explanation", "")
    if raw_explanation:
        # Sanitize: if explanation looks like a raw JSON dump, show a warning instead
        stripped = raw_explanation.strip()
        is_json_dump = (
            (stripped.startswith("{") and "fixed_code" in stripped[:200])
            or (stripped.startswith("[") and len(stripped) > 2000)
            or stripped.count("\\n") > 30  # Escaped newlines = raw JSON string
        )

        st.markdown("""
        <p style="font-size:0.75rem;color:#6e7681;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:24px 0 12px 0;border-bottom:1px solid rgba(255,255,255,0.07);
                  padding-bottom:10px;">Analysis Summary</p>
        """, unsafe_allow_html=True)

        if is_json_dump:
            st.warning("⚠️ The AI returned an unstructured response. Try analyzing again for a cleaner result.")
        else:
            # Render paragraphs/lists cleanly
            paragraphs = raw_explanation.split("\n\n")
            rendered_blocks = []
            for para in paragraphs:
                lines = [l.strip() for l in para.split("\n") if l.strip()]
                if not lines:
                    continue
                if all(l[0].isdigit() for l in lines if l):
                    items = "".join(
                        f'<li style="font-size:0.875rem;color:#8b949e;line-height:1.75;padding:3px 0;">'
                        f'{l.lstrip("0123456789.) ")}</li>'
                        for l in lines
                    )
                    rendered_blocks.append(f'<ol style="padding-left:1.3rem;margin:0;">{items}</ol>')
                elif all(l[0] in "-*•" for l in lines if l):
                    items = "".join(
                        f'<li style="font-size:0.875rem;color:#8b949e;line-height:1.75;padding:3px 0;">'
                        f'{l.lstrip("-*• ")}</li>'
                        for l in lines
                    )
                    rendered_blocks.append(f'<ul style="padding-left:1.3rem;margin:0;">{items}</ul>')
                else:
                    rendered_blocks.append(
                        f'<p style="font-size:0.875rem;color:#8b949e;line-height:1.8;margin:0;">'
                        f'{" ".join(lines)}</p>'
                    )

            if rendered_blocks:
                st.markdown(
                    '<div style="display:flex;flex-direction:column;gap:12px;'
                    'background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);'
                    'border-radius:12px;padding:20px 24px;">'
                    + "".join(rendered_blocks)
                    + "</div>",
                    unsafe_allow_html=True
                )


    # ── Code diff ────────────────────────────────────────────
    fixed = result.get("fixed_code", "")
    if fixed and isinstance(fixed, str) and original_code:
        st.markdown("""
        <p style="font-size:0.75rem;color:#6e7681;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:24px 0 12px 0;border-bottom:1px solid rgba(255,255,255,0.07);
                  padding-bottom:10px;">Code Comparison</p>
        """, unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Original")
            st.code(original_code, language=code_lang, line_numbers=True)
        with c2:
            st.caption("Fixed")
            st.code(fixed, language=code_lang, line_numbers=True)

    # ── Fixed files (repo) ────────────────────────────────────
    fixed_files = result.get("fixed_code", {})
    if isinstance(fixed_files, dict) and fixed_files:
        st.markdown("""
        <p style="font-size:0.75rem;color:#6e7681;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:24px 0 12px 0;border-bottom:1px solid rgba(255,255,255,0.07);
                  padding-bottom:10px;">Fixed Files</p>
        """, unsafe_allow_html=True)
        sel = st.selectbox("Select file", list(fixed_files.keys()))
        if sel:
            st.code(fixed_files[sel], language="python", line_numbers=True)

    # ── Suggestions ──────────────────────────────────────────
    suggestions = result.get("suggestions", [])
    if suggestions:
        st.markdown("""
        <p style="font-size:0.75rem;color:#6e7681;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:24px 0 12px 0;border-bottom:1px solid rgba(255,255,255,0.07);
                  padding-bottom:10px;">Recommendations</p>
        """, unsafe_allow_html=True)
        for s in suggestions:
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:10px;padding:10px 14px;
                        background:rgba(79,70,229,0.06);border:1px solid rgba(79,70,229,0.15);
                        border-radius:7px;margin-bottom:7px;">
                <span style="color:#4f46e5;font-weight:700;flex-shrink:0;margin-top:1px;font-size:0.85rem;">—</span>
                <span style="font-size:0.85rem;color:#8b949e;line-height:1.55;">{s}</span>
            </div>
            """, unsafe_allow_html=True)


def display_chat_ui(code: str, analysis_result: dict, chat_key: str = "default", filename: str = None):
    """Display the Q&A chat interface."""
    # Initialize chat history in session state
    history_key = f"chat_history_{chat_key}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    file_label = filename or "your code"
    st.markdown(f"""
    <p style="font-size:0.75rem;color:#6e7681;text-transform:uppercase;letter-spacing:1px;
              font-weight:600;margin:24px 0 12px 0;border-bottom:1px solid rgba(255,255,255,0.07);
              padding-bottom:10px;">Ask Questions About <span style="color:#a5b4fc;font-family:'JetBrains Mono',monospace;">{file_label}</span></p>
    """, unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state[history_key]:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="display:flex;justify-content:flex-end;margin-bottom:12px;">
                <div style="background:rgba(79,70,229,0.15);border:1px solid rgba(79,70,229,0.3);
                            border-radius:12px 12px 4px 12px;padding:12px 16px;max-width:80%;">
                    <p style="font-size:0.85rem;color:#c9d1d9;margin:0;line-height:1.5;">{msg["content"]}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex;justify-content:flex-start;margin-bottom:12px;">
                <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                            border-radius:12px 12px 12px 4px;padding:12px 16px;max-width:80%;">
                    <p style="font-size:0.85rem;color:#8b949e;margin:0;line-height:1.6;">{msg["content"]}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Input form
    with st.form(key=f"chat_form_{chat_key}", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_question = st.text_input(
                "Question",
                placeholder=f"Ask a question about {file_label}...",
                label_visibility="collapsed"
            )
        with col2:
            submit = st.form_submit_button("Ask", use_container_width=True)

    if submit and user_question.strip():
        # Add user message to history
        st.session_state[history_key].append({"role": "user", "content": user_question})
        
        # Get AI response — pass filename so RAG knows which file we're discussing
        with st.spinner("Thinking..."):
            answer = ask_question(user_question, code, analysis_result, filename=filename)

        
        if answer:
            st.session_state[history_key].append({"role": "assistant", "content": answer})
        else:
            st.session_state[history_key].append({
                "role": "assistant",
                "content": "Sorry, I couldn't generate an answer. Please try again."
            })
        
        st.rerun()

    # Clear chat button
    if st.session_state[history_key]:
        if st.button("Clear Chat", key=f"clear_chat_{chat_key}"):
            st.session_state[history_key] = []
            st.rerun()


# ───────────────────────────────────────────────────────────────
# SIDEBAR
# ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Configuration")
    api_url_input = st.text_input("Backend URL", API_BASE_URL)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Test", use_container_width=True):
            try:
                r = requests.get(f"{api_url_input}/health", timeout=5)
                if r.ok:
                    st.success("Connected")
                else:
                    st.error("API error")
            except Exception:
                st.error("Unreachable")
    with c2:
        if st.button("Clear", use_container_width=True):
            for k in ["analysis_result", "file_result", "repo_result",
                      "uploaded_filename", "uploaded_content", "repo_url",
                      "code_input_snapshot", "code_lang",
                      "chat_history_code", "chat_history_file", "chat_history_repo"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.divider()
    st.markdown("""
**Usage**

**Code Input** — paste code directly  
**File Upload** — upload a source file  
**GitHub Repo** — enter a repository URL  

---
**Detection capabilities**

- Syntax errors  
- Logic bugs  
- Performance issues  
- Security vulnerabilities  
- Code quality issues
""")


# ───────────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────────
def main():
    # ── Header ────────────────────────────────────────────────
    st.markdown("""
    <div style="padding:52px 0 36px 0;border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:36px;">
        <div style="display:inline-flex;align-items:center;gap:8px;background:rgba(79,70,229,0.12);
                    border:1px solid rgba(79,70,229,0.25);border-radius:4px;padding:3px 12px;
                    margin-bottom:18px;">
            <div style="width:6px;height:6px;border-radius:50%;background:#4f46e5;"></div>
            <span style="font-size:0.72rem;font-weight:600;color:#a5b4fc;letter-spacing:1px;text-transform:uppercase;">
                AI-Powered
            </span>
        </div>
        <h1 style="font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-0.5px;
                   color:#e6edf3;line-height:1.2;margin:0 0 14px 0;">
            AI Bug Fixer
        </h1>
        <p style="font-size:1rem;color:#6e7681;line-height:1.65;max-width:560px;margin:0 0 28px 0;">
            Detect bugs, vulnerabilities and performance issues. Get structured AI-generated
            fixes with clear, actionable explanations.
        </p>
        <div style="display:flex;gap:16px;flex-wrap:wrap;">
            <div style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#6e7681;">
                <div style="width:7px;height:7px;border-radius:50%;background:#238636;"></div>
                Semantic code indexing
            </div>
            <div style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#6e7681;">
                <div style="width:7px;height:7px;border-radius:50%;background:#238636;"></div>
                Cross-file analysis
            </div>
            <div style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#6e7681;">
                <div style="width:7px;height:7px;border-radius:50%;background:#238636;"></div>
                GitHub repository support
            </div>
            <div style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#6e7681;">
                <div style="width:7px;height:7px;border-radius:50%;background:#238636;"></div>
                Parallel file processing
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["  Code Input  ", "  File Upload  ", "  GitHub Repository  "])

    # ── Tab 1: Code Input ─────────────────────────────────────
    with tab1:
        st.markdown("""
        <p style="font-size:0.75rem;color:#6e7681;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:20px 0 16px 0;">Paste Code</p>
        """, unsafe_allow_html=True)

        col_lang, col_fn = st.columns([2, 3])
        with col_lang:
            language = st.selectbox("Language", [
                "Auto-detect", "Python", "JavaScript", "TypeScript",
                "Java", "C++", "Go", "Rust", "Ruby", "PHP",
            ], index=0)
        with col_fn:
            filename = st.text_input("Filename (optional)", placeholder="example.py")

        code_input = st.text_area(
            "Source Code",
            height=340,
            placeholder="Paste your source code here...",
        )

        if st.button("Analyze Code", type="primary", use_container_width=True, key="btn_code"):
            if not code_input.strip():
                st.warning("Please enter some code to analyze.")
            else:
                with st.spinner("Analyzing..."):
                    result = call_api("/analyze-code", {
                        "code": code_input,
                        "filename": filename if filename else None,
                        "use_rag": True,
                    })
                if result:
                    st.session_state["analysis_result"] = result
                    st.session_state["code_input_snapshot"] = code_input
                    st.session_state["code_lang"] = result.get("language", language.lower())
                    st.session_state["code_filename"] = filename if filename else None

        if "analysis_result" in st.session_state:
            result = st.session_state["analysis_result"]
            lang = st.session_state.get("code_lang", "python")
            orig = st.session_state.get("code_input_snapshot", code_input)
            st.divider()
            if lang and lang != "auto-detect":
                st.markdown(f"""
                <span style="font-size:0.72rem;font-weight:600;letter-spacing:0.5px;
                             color:#8b949e;text-transform:uppercase;
                             background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);
                             border-radius:4px;padding:3px 9px;">Detected: {lang}</span>
                """, unsafe_allow_html=True)
                st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            # Q&A Chat Interface (at top)
            display_chat_ui(orig, result, chat_key="code", filename=st.session_state.get("code_filename") or filename or None)
            display_results(result, original_code=orig, code_lang=lang)

    # ── Tab 2: File Upload ────────────────────────────────────
    with tab2:
        st.markdown("""
        <p style="font-size:0.75rem;color:#6e7681;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:20px 0 16px 0;">Upload Source File</p>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Drag and drop or click to browse",
            type=["py","js","ts","jsx","tsx","java","cpp","c","go","rs","rb","php","swift","kt"],
            help="Supported: Python, JS/TS, Java, C/C++, Go, Rust, Ruby, PHP, Swift, Kotlin",
        )

        if uploaded_file is not None:
            size_kb = len(uploaded_file.getvalue()) / 1024
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:10px 14px;
                        background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.09);
                        border-radius:8px;margin-bottom:14px;">
                <div style="width:32px;height:32px;background:rgba(79,70,229,0.15);border-radius:6px;
                            display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
                         stroke="#a5b4fc" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                </div>
                <div>
                    <p style="font-size:0.85rem;color:#c9d1d9;margin:0 0 2px 0;font-weight:500;">
                        {uploaded_file.name}
                    </p>
                    <p style="font-size:0.75rem;color:#6e7681;margin:0;">{size_kb:.1f} KB</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Analyze File", type="primary", use_container_width=True, key="btn_file"):
                with st.spinner("Analyzing..."):
                    result = upload_file(uploaded_file)
                if result:
                    st.session_state["file_result"] = result
                    st.session_state["uploaded_filename"] = uploaded_file.name
                    st.session_state["uploaded_content"] = uploaded_file.getvalue().decode("utf-8", errors="ignore")

        if "file_result" in st.session_state:
            result = st.session_state["file_result"]
            orig = st.session_state.get("uploaded_content", "")
            lang = result.get("language", "python")
            st.divider()
            # Q&A Chat Interface (at top)
            uploaded_fname = st.session_state.get("uploaded_filename")
            display_chat_ui(orig, result, chat_key="file", filename=uploaded_fname)
            display_results(result, original_code=orig, code_lang=lang)

    # ── Tab 3: GitHub Repo ────────────────────────────────────
    with tab3:
        st.markdown("""
        <p style="font-size:0.75rem;color:#6e7681;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:20px 0 16px 0;">Repository Analysis</p>
        """, unsafe_allow_html=True)

        col_url, col_branch = st.columns([4, 1])
        with col_url:
            repo_url = st.text_input("Repository URL", placeholder="https://github.com/owner/repository")
        with col_branch:
            branch = st.text_input("Branch", value="main")

        extensions = st.multiselect(
            "File Extensions",
            ["py","js","ts","jsx","tsx","java","cpp","c","go","rs","rb","php"],
            default=["py","js","ts"],
        )

        if st.button("Analyze Repository", type="primary", use_container_width=True, key="btn_repo"):
            if not repo_url.strip():
                st.warning("Please enter a repository URL.")
            elif "github.com" not in repo_url:
                st.warning("Please enter a valid GitHub URL.")
            else:
                prog_ph = st.empty()
                with prog_ph.container():
                    bar = st.progress(0, text="Cloning repository...")
                    time.sleep(0.4)
                    bar.progress(30, text="Indexing files...")
                    time.sleep(0.3)
                    bar.progress(60, text="Running analysis...")

                with st.spinner("Analyzing repository. This may take a minute for large codebases..."):
                    result = analyze_github_repo(repo_url, branch)

                prog_ph.empty()
                if result:
                    st.session_state["repo_result"] = result
                    st.session_state["repo_url"] = repo_url

        if "repo_result" in st.session_state:
            result = st.session_state["repo_result"]
            repo_display = st.session_state.get("repo_url", "")
            st.divider()
            if repo_display:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:10px 14px;
                            background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.09);
                            border-radius:8px;margin-bottom:20px;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
                         stroke="#6e7681" stroke-width="2">
                        <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35
                                 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1
                                 S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07
                                 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37
                                 3.37 0 0 0 9 18.13V22"/>
                    </svg>
                    <span style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;
                                 color:#8b949e;">{repo_display}</span>
                </div>
                """, unsafe_allow_html=True)
            # Q&A Chat Interface (at top)
            repo_code = f"Repository: {repo_display}\n\nAnalysis results are displayed below."
            display_chat_ui(repo_code, result, chat_key="repo", filename=repo_display)
            display_results(result)


if __name__ == "__main__":
    main()
