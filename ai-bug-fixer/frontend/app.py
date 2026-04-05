"""
AI Bug Fixer - Streamlit Frontend
"""

import streamlit as st
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="AI Bug Fixer",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⬡</text></svg>",
    layout="wide",
)

st.markdown("""
<style>
/* ── Inputs & Textareas ── */
.stTextInput > div > div > input,
.stTextArea > div > textarea,
.stNumberInput > div > div > input {
    border: 1.5px solid #c7d2fe !important;
    border-radius: 8px !important;
    outline: none !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > textarea:focus,
.stNumberInput > div > div > input:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,0.12) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div,
[data-baseweb="select"] > div {
    border: 1.5px solid #c7d2fe !important;
    border-radius: 8px !important;
}

/* ── Multiselect ── */
[data-testid="stMultiSelect"] > div > div {
    border: 1.5px solid #c7d2fe !important;
    border-radius: 8px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    border: 1.5px solid #c7d2fe !important;
    border-radius: 10px !important;
    padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    border: 1.5px solid #c7d2fe !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ── Code blocks ── */
.stCode, pre {
    border: 1.5px solid #c7d2fe !important;
    border-radius: 8px !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] > div {
    border: 2px dashed #a5b4fc !important;
    border-radius: 10px !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    border: 1.5px solid #c7d2fe !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border: 1.5px solid #c7d2fe !important;
    border-radius: 8px !important;
}

/* ── Buttons ── */
.stButton > button {
    border: 1.5px solid #c7d2fe !important;
    border-radius: 8px !important;
}
.stButton > button[kind="primary"] {
    border-color: #4f46e5 !important;
}

/* ── Form ── */
[data-testid="stForm"] {
    border: 1.5px solid #c7d2fe !important;
    border-radius: 10px !important;
    padding: 16px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    border-right: 1.5px solid #c7d2fe !important;
}

/* ── Divider ── */
hr {
    border-color: #c7d2fe !important;
}
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
    "low":      "background:#dcfce7;color:#166534;border:1px solid #86efac;",
    "medium":   "background:#fef9c3;color:#854d0e;border:1px solid #fde047;",
    "high":     "background:#fee2e2;color:#991b1b;border:1px solid #fca5a5;",
    "critical": "background:#fecdd3;color:#881337;border:1px solid #fb7185;",
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
        f'color:#4b5563;background:#f3f4f6;border:1px solid #d1d5db;'
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
        <div style="background:#dcfce7;border:1px solid #86efac;border-radius:10px;
                    padding:20px 24px;display:flex;align-items:center;gap:16px;margin-bottom:24px;">
            <div style="width:36px;height:36px;background:#16a34a;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
            </div>
            <div>
                <p style="color:#166534;font-weight:600;font-size:0.95rem;margin:0 0 3px 0;">No Issues Detected</p>
                <p style="color:#4b7a56;font-size:0.82rem;margin:0;">AI analysis found no bugs in the submitted code.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        total = len(bugs)
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px;">
            <div style="background:#fecdd3;border:1px solid #fb7185;border-radius:10px;
                        padding:16px;text-align:center;">
                <p style="font-size:2rem;font-weight:800;color:#881337;margin:0 0 4px 0;">{counts['critical']}</p>
                <p style="font-size:0.7rem;color:#9f1239;text-transform:uppercase;letter-spacing:1px;margin:0;font-weight:600;">Critical</p>
            </div>
            <div style="background:#fee2e2;border:1px solid #fca5a5;border-radius:10px;
                        padding:16px;text-align:center;">
                <p style="font-size:2rem;font-weight:800;color:#991b1b;margin:0 0 4px 0;">{counts['high']}</p>
                <p style="font-size:0.7rem;color:#b91c1c;text-transform:uppercase;letter-spacing:1px;margin:0;font-weight:600;">High</p>
            </div>
            <div style="background:#fef9c3;border:1px solid #fde047;border-radius:10px;
                        padding:16px;text-align:center;">
                <p style="font-size:2rem;font-weight:800;color:#854d0e;margin:0 0 4px 0;">{counts['medium']}</p>
                <p style="font-size:0.7rem;color:#92400e;text-transform:uppercase;letter-spacing:1px;margin:0;font-weight:600;">Medium</p>
            </div>
            <div style="background:#dcfce7;border:1px solid #86efac;border-radius:10px;
                        padding:16px;text-align:center;">
                <p style="font-size:2rem;font-weight:800;color:#166534;margin:0 0 4px 0;">{counts['low']}</p>
                <p style="font-size:0.7rem;color:#15803d;text-transform:uppercase;letter-spacing:1px;margin:0;font-weight:600;">Low</p>
            </div>
        </div>
        <p style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:0 0 14px 0;border-bottom:1px solid #e5e7eb;
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
                "background:#f3f4f6;color:#374151;border:1px solid #d1d5db;")

            with st.expander(f"#{i}  —  {type_label}  /  {sev_label}", expanded=(sev in ["high", "critical"])):
                st.markdown(f"""
                <div style="background:#ffffff;
                            border:1px solid #e5e7eb;
                            border-left:3px solid {border_col};
                            border-radius:8px;padding:18px 20px;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap;">
                        {severity_badge}
                        {type_badge}
                        {fname_tag}
                        {line_tag}
                    </div>
                    <p style="font-size:0.875rem;color:#1f2937;line-height:1.7;margin:0 0 12px 0;">
                        {bug.get('description', 'No description available.')}
                    </p>
                    <p style="font-size:0.82rem;color:#4b5563;line-height:1.6;margin:0;
                              border-top:1px solid #f3f4f6;padding-top:10px;">
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
        <p style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:24px 0 12px 0;border-bottom:1px solid #e5e7eb;
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
                        f'<li style="font-size:0.875rem;color:#374151;line-height:1.75;padding:3px 0;">'
                        f'{l.lstrip("0123456789.) ")}</li>'
                        for l in lines
                    )
                    rendered_blocks.append(f'<ol style="padding-left:1.3rem;margin:0;">{items}</ol>')
                elif all(l[0] in "-*•" for l in lines if l):
                    items = "".join(
                        f'<li style="font-size:0.875rem;color:#374151;line-height:1.75;padding:3px 0;">'
                        f'{l.lstrip("-*• ")}</li>'
                        for l in lines
                    )
                    rendered_blocks.append(f'<ul style="padding-left:1.3rem;margin:0;">{items}</ul>')
                else:
                    rendered_blocks.append(
                        f'<p style="font-size:0.875rem;color:#374151;line-height:1.8;margin:0;">'
                        f'{" ".join(lines)}</p>'
                    )

            if rendered_blocks:
                st.markdown(
                    '<div style="display:flex;flex-direction:column;gap:12px;'
                    'background:#ffffff;border:1px solid #e5e7eb;'
                    'border-radius:12px;padding:20px 24px;">'
                    + "".join(rendered_blocks)
                    + "</div>",
                    unsafe_allow_html=True
                )


    # ── Code diff ────────────────────────────────────────────
    fixed = result.get("fixed_code", "")
    if fixed and isinstance(fixed, str) and original_code:
        st.markdown("""
        <p style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:24px 0 12px 0;border-bottom:1px solid #e5e7eb;
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
        <p style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:24px 0 12px 0;border-bottom:1px solid #e5e7eb;
                  padding-bottom:10px;">Fixed Files</p>
        """, unsafe_allow_html=True)
        sel = st.selectbox("Select file", list(fixed_files.keys()))
        if sel:
            st.code(fixed_files[sel], language="python", line_numbers=True)

    # ── Suggestions ──────────────────────────────────────────
    suggestions = result.get("suggestions", [])
    if suggestions:
        st.markdown("""
        <p style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:1px;
                  font-weight:600;margin:24px 0 12px 0;border-bottom:1px solid #e5e7eb;
                  padding-bottom:10px;">Recommendations</p>
        """, unsafe_allow_html=True)
        for s in suggestions:
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:10px;padding:10px 14px;
                        background:#eef0f8;border:1px solid #c7d2fe;
                        border-radius:7px;margin-bottom:7px;">
                <span style="color:#4f46e5;font-weight:700;flex-shrink:0;margin-top:1px;font-size:0.85rem;">—</span>
                <span style="font-size:0.85rem;color:#1e1b4b;line-height:1.55;">{s}</span>
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
    <p style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:1px;
              font-weight:600;margin:24px 0 12px 0;border-bottom:1px solid #e5e7eb;
              padding-bottom:10px;">Ask Questions About <span style="color:#4f46e5;font-family:'JetBrains Mono',monospace;">{file_label}</span></p>
    """, unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state[history_key]:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="display:flex;justify-content:flex-end;margin-bottom:12px;">
                <div style="background:#e0e7ff;border:1px solid #c7d2fe;
                            border-radius:12px 12px 4px 12px;padding:12px 16px;max-width:80%;">
                    <p style="font-size:0.85rem;color:#1e1b4b;margin:0;line-height:1.5;">{msg["content"]}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex;justify-content:flex-start;margin-bottom:12px;">
                <div style="background:#f9fafb;border:1px solid #e5e7eb;
                            border-radius:12px 12px 12px 4px;padding:12px 16px;max-width:80%;">
                    <p style="font-size:0.85rem;color:#374151;margin:0;line-height:1.6;">{msg["content"]}</p>
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
    <div style="padding:52px 0 36px 0;border-bottom:1px solid #e5e7eb;margin-bottom:36px;">
        <div style="display:inline-flex;align-items:center;gap:8px;background:#e0e7ff;
                    border:1px solid #c7d2fe;border-radius:4px;padding:3px 12px;
                    margin-bottom:18px;">
            <div style="width:6px;height:6px;border-radius:50%;background:#4f46e5;"></div>
            <span style="font-size:0.72rem;font-weight:600;color:#4338ca;letter-spacing:1px;text-transform:uppercase;">
                AI-Powered
            </span>
        </div>
        <h1 style="font-size:clamp(2rem,4vw,3rem);font-weight:800;letter-spacing:-0.5px;
                   color:#1a1d2e;line-height:1.2;margin:0 0 14px 0;">
            AI Bug Fixer
        </h1>
        <p style="font-size:1rem;color:#4b5563;line-height:1.65;max-width:560px;margin:0 0 28px 0;">
            Detect bugs, vulnerabilities and performance issues. Get structured AI-generated
            fixes with clear, actionable explanations.
        </p>
        <div style="display:flex;gap:16px;flex-wrap:wrap;">
            <div style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#4b5563;">
                <div style="width:7px;height:7px;border-radius:50%;background:#16a34a;"></div>
                Semantic code indexing
            </div>
            <div style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#4b5563;">
                <div style="width:7px;height:7px;border-radius:50%;background:#16a34a;"></div>
                Cross-file analysis
            </div>
            <div style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#4b5563;">
                <div style="width:7px;height:7px;border-radius:50%;background:#16a34a;"></div>
                GitHub repository support
            </div>
            <div style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#4b5563;">
                <div style="width:7px;height:7px;border-radius:50%;background:#16a34a;"></div>
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
        <p style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:1px;
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
                             color:#4b5563;text-transform:uppercase;
                             background:#f3f4f6;border:1px solid #d1d5db;
                             border-radius:4px;padding:3px 9px;">Detected: {lang}</span>
                """, unsafe_allow_html=True)
                st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            # Q&A Chat Interface (at top)
            display_chat_ui(orig, result, chat_key="code", filename=st.session_state.get("code_filename") or filename or None)
            display_results(result, original_code=orig, code_lang=lang)

    # ── Tab 2: File Upload ────────────────────────────────────
    with tab2:
        st.markdown("""
        <p style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:1px;
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
                        background:#f9fafb;border:1px solid #e5e7eb;
                        border-radius:8px;margin-bottom:14px;">
                <div style="width:32px;height:32px;background:#e0e7ff;border-radius:6px;
                            display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
                         stroke="#4f46e5" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                </div>
                <div>
                    <p style="font-size:0.85rem;color:#1f2937;margin:0 0 2px 0;font-weight:500;">
                        {uploaded_file.name}
                    </p>
                    <p style="font-size:0.75rem;color:#6b7280;margin:0;">{size_kb:.1f} KB</p>
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
        <p style="font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:1px;
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
                            background:#f9fafb;border:1px solid #e5e7eb;
                            border-radius:8px;margin-bottom:20px;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
                         stroke="#4b5563" stroke-width="2">
                        <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35
                                 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1
                                 S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07
                                 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37
                                 3.37 0 0 0 9 18.13V22"/>
                    </svg>
                    <span style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;
                                 color:#374151;">{repo_display}</span>
                </div>
                """, unsafe_allow_html=True)
            # Q&A Chat Interface (at top)
            repo_code = f"Repository: {repo_display}\n\nAnalysis results are displayed below."
            display_chat_ui(repo_code, result, chat_key="repo", filename=repo_display)
            display_results(result)


if __name__ == "__main__":
    main()
