import streamlit as st
import os
import json
import re
from groq import Groq
from datetime import datetime
import time

st.set_page_config(
    page_title="EDITH",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* Dark background */
.stApp {
    background: #0a0a0f;
    color: #e8e8f0;
}

/* Fix the main app layout */
.stApp > section {
    max-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Landing page */
.landing {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 24px;
    background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(99,102,241,0.15), transparent);
}

.logo-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 48px;
}

.logo-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}

.logo-text {
    font-size: 20px;
    font-weight: 600;
    color: #e8e8f0;
    letter-spacing: -0.3px;
}

.hero-title {
    font-size: clamp(36px, 6vw, 72px);
    font-weight: 700;
    letter-spacing: -2px;
    line-height: 1.05;
    text-align: center;
    color: #ffffff;
    margin-bottom: 20px;
}

.hero-title span {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-size: 18px;
    color: #9090b0;
    text-align: center;
    margin-bottom: 48px;
    font-weight: 400;
}

.input-wrapper {
    width: 100%;
    max-width: 680px;
    background: #13131f;
    border: 1px solid #2a2a3d;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 24px;
    box-shadow: 0 0 0 1px rgba(99,102,241,0.05), 0 20px 60px rgba(0,0,0,0.4);
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 13px;
    color: #a78bfa;
    margin-bottom: 20px;
}

/* Chat area */
.chat-container {
    display: flex;
    height: 100vh;
    background: #0a0a0f;
}

.sidebar-panel {
    width: 280px;
    background: #0f0f1a;
    border-right: 1px solid #1e1e2e;
    padding: 20px 16px;
    overflow-y: auto;
    flex-shrink: 0;
}

.main-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
    height: 100vh;
}

.chat-header {
    padding: 20px 32px;
    border-bottom: 1px solid #1e1e2e;
    display: flex;
    align-items: center;
    gap: 12px;
    background: #0a0a0f;
    flex-shrink: 0;
    z-index: 10;
}

.messages-area {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 32px;
    max-width: 800px;
    margin: 0 auto;
    width: 100%;
    box-sizing: border-box;
    scroll-behavior: smooth;
}

.message-user {
    background: #1a1a2e;
    border: 1px solid #2a2a40;
    border-radius: 12px 12px 4px 12px;
    padding: 14px 18px;
    margin-bottom: 24px;
    margin-left: auto;
    max-width: 80%;
    color: #e0e0f0;
    font-size: 14px;
    line-height: 1.6;
    animation: fadeInUp 0.6s ease-out;
}

.message-ai {
    background: #111120;
    border: 1px solid #1e1e30;
    border-radius: 4px 12px 12px 12px;
    padding: 20px 24px;
    margin-bottom: 24px;
    max-width: 100%;
    color: #d0d0e8;
    font-size: 14px;
    line-height: 1.7;
    animation: fadeInUp 0.6s ease-out;
}

.message-ai-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #1e1e30;
}

.ai-avatar {
    width: 28px;
    height: 28px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
}

/* Report card */
.report-card {
    background: #0f0f1e;
    border: 1px solid #2a2a40;
    border-radius: 16px;
    padding: 28px;
    margin: 16px 0;
}

.report-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
}

.report-title {
    font-size: 20px;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 6px;
    line-height: 1.3;
}

.report-meta {
    font-size: 12px;
    color: #6060a0;
    display: flex;
    align-items: center;
    gap: 8px;
}

.report-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(34,197,94,0.1);
    border: 1px solid rgba(34,197,94,0.25);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: #4ade80;
    font-weight: 500;
}

.key-insight {
    background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.1));
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 20px 0;
}

.key-insight-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: #8b8bcc;
    margin-bottom: 8px;
}

.key-insight-text {
    font-size: 15px;
    font-weight: 500;
    color: #c8c8f0;
    line-height: 1.5;
}

.section-title {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: #6060a0;
    margin: 20px 0 10px 0;
}

.section-content {
    font-size: 14px;
    color: #c0c0e0;
    line-height: 1.7;
}

.feature-chip {
    display: inline-block;
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.18);
    border-radius: 8px;
    padding: 5px 12px;
    font-size: 13px;
    color: #a0a0d0;
    margin: 3px;
}

.competitor-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid #1a1a28;
}

.competitor-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #6366f1;
    flex-shrink: 0;
}

.sources-count {
    font-size: 12px;
    color: #6060a0;
    margin-top: 16px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Sidebar history items */
.history-item {
    padding: 10px 12px;
    border-radius: 10px;
    margin-bottom: 6px;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.15s ease;
}

.history-item:hover {
    background: #1a1a28;
    border-color: #2a2a40;
}

.history-item-title {
    font-size: 13px;
    color: #c0c0e0;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.history-item-date {
    font-size: 11px;
    color: #505070;
    margin-top: 2px;
}

/* Input bar styling */
/* Target the columns/buttons that appear after messages */
.stApp > section [data-testid="stHorizontalBlock"] {
    max-width: 800px;
    margin: 32px auto 0 auto;
    width: 100%;
    display: flex !important;
    gap: 12px !important;
}

/* Text input - Make it responsive */
.stTextInput {
    flex: 1;
    width: 100%;
}

.stTextInput input {
    background: #13131f !important;
    border: 1.5px solid #2a2a3d !important;
    border-radius: 12px !important;
    color: #e0e0f0 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 14px 18px !important;
    font-size: 15px !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}

.stTextInput input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
    outline: none !important;
    background: #13131f !important;
}

.stTextInput input::placeholder {
    color: #6060a0 !important;
    opacity: 1 !important;
}

/* Send / quick prompt button styling */
.stButton > button {
    background: transparent !important;
    color: #e8e8f0 !important;
    border: 1px solid rgba(99, 102, 241, 0.17) !important;
    border-radius: 12px !important;
    padding: 14px 24px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s !important;
    min-height: 48px !important;
    cursor: pointer !important;
    backdrop-filter: none !important;
}

.stButton > button:hover {
    background: rgba(255, 255, 255, 0.05) !important;
    opacity: 1 !important;
}

.stButton > button:active {
    opacity: 0.85 !important;
}


/* Stagger animation placeholders */
.typing-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #6366f1;
    margin: 0 2px;
    animation: typing 1.2s infinite;
}

@keyframes typing {
    0%, 60%, 100% { opacity: 0.2; transform: translateY(0); }
    30% { opacity: 1; transform: translateY(-4px); }
}

/* Fade in animation */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Streamlit widget overrides */
.stTextArea textarea {
    background: #13131f !important;
    border: 1px solid #2a2a3d !important;
    border-radius: 12px !important;
    color: #e0e0f0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    padding: 14px 16px !important;
    resize: none !important;
}

.stTextArea textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

.stTextInput input {
    background: #13131f !important;
    border: 1px solid #2a2a3d !important;
    border-radius: 12px !important;
    color: #e0e0f0 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 12px 16px !important;
    font-size: 15px !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}

.stTextInput input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    outline: none !important;
    background: #13131f !important;
}

.stTextInput input::placeholder {
    color: #6060a0 !important;
    opacity: 1 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 28px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    transition: opacity 0.2s !important;
    min-height: 44px !important;
    width: 100% !important;
}

.stButton > button:hover {
    opacity: 0.85 !important;
}

.stButton > button:active {
    opacity: 0.75 !important;
}

.stButton > button[kind="secondary"] {
    background: #13131f !important;
    border: 1px solid #2a2a3d !important;
    color: #c0c0e0 !important;
}

[data-testid="stSidebar"] {
    background: #0f0f1a !important;
    border-right: 1px solid #1e1e2e !important;
}

[data-testid="stSidebar"] * {
    color: #c0c0e0 !important;
}

.stCheckbox label {
    color: #9090b0 !important;
    font-size: 14px !important;
}

hr {
    border-color: #1e1e2e !important;
    margin: 16px 0 !important;
}

h1, h2, h3 { color: #ffffff !important; }

.stSpinner > div {
    border-top-color: #6366f1 !important;
}

/* FLOATING INPUT BOX POSITIONING */
.stApp > section [data-testid="stHorizontalBlock"]:last-of-type {
    position: fixed !important; 
    bottom: 32px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 800px !important;
    max-width: calc(100% - 360px) !important;
    z-index: 1001 !important;
    display: flex !important;
    gap: 12px !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
}

/* Quick prompts - position above input */
.stApp > section [data-testid="stHorizontalBlock"]:nth-last-of-type(2) {
    position: fixed !important;
    bottom: 100px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    width: 800px !important;
    max-width: calc(100% - 360px) !important;
    z-index: 1000 !important;
    gap: 8px !important;
    border: none !important;
}

/* Hide spacer element */
[data-testid="stVerticalBlock"] > [data-testid="stMarkdownContainer"]:nth-last-of-type(1) {
    display: none !important;
}

/* Remove any red borders */
[data-testid="stHorizontalBlock"],
[data-testid="stVerticalBlock"],
.stApp > section {
    border: none !important;
}

</style>
""", unsafe_allow_html=True)


def get_client():
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY not set.")
        st.stop()
    return Groq(api_key=api_key)


def call_cofounder(messages: list, privacy: bool = False) -> str:
    client = get_client()
    system = """You are an expert AI cofounder, startup mentor, and market research analyst.
Your role is to help founders research and build products people actually want.

I'm so excited to help you turn your idea into something amazing! Let's dive deep and build something people will love.

When a user shares a startup idea, you:
1. Ask smart clarifying questions OR immediately generate a comprehensive market research report
2. Provide deep market research with realistic data
3. Identify key insights, competitors, gaps, and opportunities
4. Give honest, evidence-based feedback — not just validation

Format your market research reports with these sections using markdown:
- **Key Insight** (one powerful sentence)
- **Problem & Market Pain**
- **Market Opportunity** (TAM/SAM/SOM estimates)
- **Target Users** (specific personas)
- **Competitive Landscape** (real or likely competitors)
- **Differentiation & Moat**
- **Validation Strategy** (how to test before building)
- **Key Features** (must-haves for MVP)
- **Revenue Model**
- **Pricing Strategy** (formula and approach for setting prices)
- **Business Location** (where to operate: states/districts, ecommerce platforms, or specific regions based on analysis)
- **Fresh Starter Guide** (legal requirements, funding options, marketing basics, operational setup, first profit strategies, and everything a beginner needs to know)
- **Go-To-Market**
- **Risks & Red Flags**

Be specific, realistic, and cite reasoning. Act like a brilliant cofounder who has done their homework. Show enthusiasm and support throughout!"""

    if privacy:
        system += "\n\nPRIVACY MODE: The user has enabled privacy mode. Do not reference external companies or publicly known data points that could identify the user's idea. Keep analysis generic."

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system}] + messages,
            temperature=0.7,
            max_tokens=3000,
            stream=True
        )
        full_response = ""
        for chunk in resp:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        return full_response
    except Exception as e:
        return f"❌ Error: {e}"


def render_report(content: str, idea_title: str):
    now = datetime.now().strftime("%B %d, %Y")
    lines = content.split("\n")

    key_insight = ""
    for i, line in enumerate(lines):
        if "key insight" in line.lower():
            for j in range(i + 1, min(i + 4, len(lines))):
                txt = lines[j].strip().lstrip("*-:").strip()
                if txt:
                    key_insight = txt
                    break
            break

    st.markdown(f"""
    <div class="report-card">
        <div class="report-header">
            <div>
                <div class="report-title">Market Research Report</div>
                <div style="font-size:16px;color:#a0a0c8;margin-top:4px;font-weight:500">{idea_title[:60]}{"..." if len(idea_title) > 60 else ""}</div>
                <div class="report-meta">
                    <span>🔍 AI Analysis</span>
                    <span>·</span>
                    <span>{now}</span>
                </div>
            </div>
            <div class="report-badge">✓ Published</div>
        </div>
        <div class="sources-count">📊 Powered by llama-3.3-70b · Deep AI research</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(content)


def render_message(role: str, content: str, idea_title: str = ""):
    if role == "user":
        st.markdown(f'<div class="message-user">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="message-ai">
            <div class="message-ai-header">
                <div class="ai-avatar">🤖</div>
                <div style="font-size:13px;font-weight:600;color:#9090c0">EDITH</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if "market research report" in content.lower() or "key insight" in content.lower() or "**" in content:
            render_report(content, idea_title or "Your Startup Idea")
        else:
            st.markdown(content)


def init_state():
    if "page" not in st.session_state:
        st.session_state.page = "landing"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "sessions" not in st.session_state:
        st.session_state.sessions = []
    if "current_idea" not in st.session_state:
        st.session_state.current_idea = ""
    if "privacy" not in st.session_state:
        st.session_state.privacy = False


def save_session():
    if st.session_state.messages:
        first_user = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), "")
        if first_user:
            session = {
                "title": first_user[:50],
                "date": datetime.now().strftime("%b %d"),
                "messages": st.session_state.messages.copy()
            }
            if len(st.session_state.sessions) == 0 or st.session_state.sessions[0]["title"] != session["title"]:
                st.session_state.sessions.insert(0, session)


def render_landing():
    st.markdown("""
    <div class="landing">
        <div class="logo-row">
            <div class="logo-icon">🚀</div>
            <div class="logo-text">EDITH</div>
        </div>
        <div class="badge">✨ Trusted by 40,000+ founders</div>
        <div class="hero-title">Make something people<br><span>actually want</span></div>
        <div class="hero-sub">Research and build your product with AI</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        idea = st.text_area(
            "Startup idea",
            placeholder="Describe your startup idea... e.g. 'An app that helps remote teams track async work and summarize meetings'",
            height=120,
            key="landing_idea",
            label_visibility="collapsed"
        )

        priv_col, btn_col = st.columns([1, 1])
        with priv_col:
            privacy = st.checkbox("🔒 Privacy mode", value=st.session_state.privacy)
            st.session_state.privacy = privacy
        with btn_col:
            if st.button("🚀 Brainstorm with AI", key="start_btn"):
                if idea.strip():
                    st.session_state.current_idea = idea.strip()
                    st.session_state.messages = [{"role": "user", "content": idea.strip()}]
                    st.session_state.page = "chat"
                    with st.spinner("EDITH is thinking..."):
                        response = call_cofounder(
                            st.session_state.messages,
                            st.session_state.privacy
                        )
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    save_session()
                    st.rerun()
                else:
                    st.warning("Please describe your startup idea first.")

        st.markdown("""
        <div style="text-align:center;margin-top:32px;">
            <div style="display:flex;justify-content:center;gap:24px;flex-wrap:wrap;">
                <div style="text-align:center;">
                    <div style="font-size:22px;font-weight:700;color:#fff">40K+</div>
                    <div style="font-size:12px;color:#606080">Founders</div>
                </div>
                <div style="width:1px;background:#1e1e2e;"></div>
                <div style="text-align:center;">
                    <div style="font-size:22px;font-weight:700;color:#fff">5★</div>
                    <div style="font-size:12px;color:#606080">Rating</div>
                </div>
                <div style="width:1px;background:#1e1e2e;"></div>
                <div style="text-align:center;">
                    <div style="font-size:22px;font-weight:700;color:#fff">100+</div>
                    <div style="font-size:12px;color:#606080">Sources per report</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_chat():
    with st.sidebar:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid #1e1e2e">
            <span style="font-size:18px">🚀</span>
            <span style="font-weight:600;font-size:15px">EDITH</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("＋  New idea", key="new_idea_btn"):
            save_session()
            st.session_state.messages = []
            st.session_state.current_idea = ""
            st.session_state.page = "landing"
            st.rerun()

        st.markdown("<div style='font-size:11px;font-weight:600;letter-spacing:1px;color:#404060;text-transform:uppercase;margin:20px 0 10px'>Recent</div>", unsafe_allow_html=True)

        for i, session in enumerate(st.session_state.sessions[:10]):
            if st.button(f"📄 {session['title'][:35]}...", key=f"session_{i}"):
                st.session_state.messages = session["messages"].copy()
                st.session_state.current_idea = session["title"]
                st.session_state.page = "chat"
                st.rerun()

        st.markdown("---")
        privacy = st.checkbox("🔒 Privacy mode", value=st.session_state.privacy, key="chat_privacy")
        st.session_state.privacy = privacy

    st.markdown(f"""
    <div style="padding:16px 24px;border-bottom:1px solid #1e1e2e;display:flex;align-items:center;gap:10px;background:#0a0a0f;">
        <div style="width:28px;height:28px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;">🤖</div>
        <div>
            <div style="font-size:14px;font-weight:600;color:#e0e0f0">EDITH</div>
            <div style="font-size:12px;color:#4ade80">● Online</div>
        </div>
        {'<div style="margin-left:auto;background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2);border-radius:20px;padding:4px 12px;font-size:12px;color:#a78bfa;">🔒 Privacy</div>' if st.session_state.privacy else ''}
    </div>
    """, unsafe_allow_html=True)

    # Render messages with extra bottom padding for the floating input
    idea_title = st.session_state.current_idea or "Your idea"
    for msg in st.session_state.messages:
        render_message(msg["role"], msg["content"], idea_title)
    
    # Add massive bottom padding to prevent messages from hiding under floating input
    st.markdown("<div style='height: 280px;'></div>", unsafe_allow_html=True)

    # Floating input box - completely separate from the flow
    st.markdown("""
    <div style="
        position: fixed;
        bottom: 0;
        left: 280px;
        right: 0;
        width: calc(100% - 280px);
        padding: 20px 32px 32px 32px;
        background: transparent;
        border-top: none;
        z-index: 999;
        box-sizing: border-box;
        backdrop-filter: none;
    " id="floating-input-container">
    </div>
    """, unsafe_allow_html=True)

    # Callback to handle input submission
    def submit_input():
        if st.session_state.follow_up_input.strip():
            st.session_state.messages.append({"role": "user", "content": st.session_state.follow_up_input.strip()})
            with st.spinner("Thinking..."):
                response = call_cofounder(st.session_state.messages, st.session_state.privacy)
            st.session_state.messages.append({"role": "assistant", "content": response})
            save_session()
            st.session_state.follow_up_input = ""
            st.rerun()
    
    # Input controls in columns
    col1, col2 = st.columns([6, 1], gap="small")
    with col1:
        follow_up = st.text_input(
            "Follow-up message",
            placeholder="Ask a follow-up question, request deeper analysis, or pivot the idea...",
            key="follow_up_input",
            label_visibility="collapsed",
            on_change=submit_input
        )
    with col2:
        if st.button("Send →", key="send_btn", use_container_width=True):
            if follow_up.strip():
                st.session_state.messages.append({"role": "user", "content": follow_up.strip()})
                with st.spinner("Thinking..."):
                    response = call_cofounder(st.session_state.messages, st.session_state.privacy)
                st.session_state.messages.append({"role": "assistant", "content": response})
                save_session()
                st.rerun()

    # Quick prompts
    st.write("")
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4, gap="small")
    quick_prompts = [
        ("🎯 Validate idea", "Can you help me validate this idea with real market signals and evidence? What should I test first?"),
        ("🏆 Competitors", "Do a deep competitive analysis. Who are the main competitors, what are their weaknesses, and where is the gap?"),
        ("💰 Revenue model", "What's the best revenue model for this? Give me 3 options with pros, cons, and realistic numbers."),
        ("💸 Pricing Strategy", "Give me a detailed pricing strategy and formula for this product/service. How should I set prices to maximize profit?"),
    ]
    for col, (label, prompt) in zip([quick_col1, quick_col2, quick_col3, quick_col4], quick_prompts):
        with col:
            if st.button(label, key=f"quick_{label}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.spinner("Thinking..."):
                    response = call_cofounder(st.session_state.messages, st.session_state.privacy)
                st.session_state.messages.append({"role": "assistant", "content": response})
                save_session()
                st.rerun()



def main():
    init_state()
    if st.session_state.page == "landing":
        render_landing()
    else:
        render_chat()


if __name__ == "__main__":
    main()
