# app.py
import streamlit as st
from graph import run_rag
import os

st.set_page_config(page_title="NexusAI Support", page_icon="✦", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #080b14 !important;
    font-family: 'DM Sans', sans-serif;
    color: #e8eaf0;
}

[data-testid="stAppViewContainer"]::before {
    content: ''; position: fixed; top: -30%; left: -20%;
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
    animation: orbFloat 12s ease-in-out infinite alternate;
    pointer-events: none; z-index: 0;
}
[data-testid="stAppViewContainer"]::after {
    content: ''; position: fixed; bottom: -20%; right: -10%;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(6,182,212,0.12) 0%, transparent 70%);
    animation: orbFloat2 15s ease-in-out infinite alternate;
    pointer-events: none; z-index: 0;
}
@keyframes orbFloat  { 0% { transform: translate(0,0) scale(1); } 100% { transform: translate(60px,80px) scale(1.15); } }
@keyframes orbFloat2 { 0% { transform: translate(0,0) scale(1); } 100% { transform: translate(-50px,-60px) scale(1.2); } }

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

[data-testid="stMain"] > div { padding: 0 !important; }
.block-container { max-width: 780px !important; margin: 0 auto !important; padding: 2rem 1.5rem 6rem !important; position: relative; z-index: 1; }

/* Header */
.nexus-header { text-align: center; padding: 3rem 0 2.5rem; animation: fadeDown 0.7s ease both; }
.nexus-logo-icon { width: 44px; height: 44px; background: linear-gradient(135deg, #6366f1, #06b6d4); border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; font-size: 1.3rem; box-shadow: 0 0 24px rgba(99,102,241,0.4); margin-bottom: 0.75rem; }
.nexus-title { font-family: 'Syne', sans-serif; font-size: 2.6rem; font-weight: 800; letter-spacing: -0.03em; background: linear-gradient(90deg, #c7d2fe 0%, #06b6d4 60%, #c7d2fe 100%); background-size: 200%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: shimmer 4s linear infinite; }
@keyframes shimmer { 0% { background-position: 0% center; } 100% { background-position: 200% center; } }
.nexus-subtitle { font-size: 0.92rem; color: #6b7280; font-weight: 300; letter-spacing: 0.04em; margin-top: 0.3rem; }
.nexus-divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(99,102,241,0.3), rgba(6,182,212,0.3), transparent); margin: 0.5rem 0 2rem; }

/* Welcome card */
.welcome-card { text-align: center; padding: 2.2rem 2rem 1.5rem; background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.07); border-radius: 20px; backdrop-filter: blur(8px); margin-bottom: 0.75rem; animation: fadeUp 0.6s ease 0.2s both; }
.welcome-card h3 { font-family: 'Syne', sans-serif; font-size: 1.15rem; font-weight: 700; color: #c7d2fe; margin-bottom: 0.4rem; }
.welcome-card p  { font-size: 0.88rem; color: #6b7280; line-height: 1.6; max-width: 420px; margin: 0 auto; }

/* Chip buttons */
div[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; justify-content: center !important; flex-wrap: wrap !important; margin-top: 1rem !important; }
div[data-testid="stHorizontalBlock"] > div { flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }
div[data-testid="stHorizontalBlock"] button { background: rgba(99,102,241,0.1) !important; border: 1px solid rgba(99,102,241,0.25) !important; border-radius: 99px !important; color: #a5b4fc !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.78rem !important; font-weight: 400 !important; padding: 5px 16px !important; height: auto !important; line-height: 1.5 !important; transition: all 0.2s ease !important; white-space: nowrap !important; }
div[data-testid="stHorizontalBlock"] button:hover { background: rgba(99,102,241,0.22) !important; border-color: rgba(99,102,241,0.45) !important; color: #c7d2fe !important; transform: translateY(-1px) !important; box-shadow: 0 4px 14px rgba(99,102,241,0.2) !important; }

/* Chat */
.chat-feed { display: flex; flex-direction: column; gap: 1.2rem; margin-bottom: 1.5rem; }
.msg-row { display: flex; gap: 0.75rem; animation: fadeUp 0.4s ease both; }
.msg-row.user { flex-direction: row-reverse; }

@keyframes fadeUp   { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }

.avatar { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; margin-top: 2px; }
.avatar.user-av { background: linear-gradient(135deg, #4f46e5, #7c3aed); box-shadow: 0 0 14px rgba(99,102,241,0.35); }
.avatar.bot-av  { background: linear-gradient(135deg, #0891b2, #06b6d4); box-shadow: 0 0 14px rgba(6,182,212,0.3); }

.bubble { max-width: 78%; padding: 0.9rem 1.2rem; border-radius: 16px; font-size: 0.95rem; line-height: 1.65; }
.bubble.user-bubble      { background: linear-gradient(135deg, rgba(79,70,229,0.35), rgba(99,102,241,0.2)); border: 1px solid rgba(99,102,241,0.25); border-top-right-radius: 4px; color: #e0e7ff; }
.bubble.bot-bubble       { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-top-left-radius: 4px; color: #d1d5db; backdrop-filter: blur(12px); }
.bubble.escalate-bubble  { background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.25); border-top-left-radius: 4px; color: #fde68a; }
.bubble.critical-bubble  { background: rgba(239,68,68,0.08);  border: 1px solid rgba(239,68,68,0.3);   border-top-left-radius: 4px; color: #fca5a5; }
.bubble.clarify-bubble   { background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.25); border-top-left-radius: 4px; color: #bfdbfe; }
.bubble.scope-bubble     { background: rgba(107,114,128,0.1); border: 1px solid rgba(107,114,128,0.2); border-top-left-radius: 4px; color: #9ca3af; }

.status-tag { display: inline-flex; align-items: center; gap: 5px; font-size: 0.7rem; font-weight: 500; padding: 3px 10px; border-radius: 99px; margin-top: 6px; letter-spacing: 0.04em; }
.tag-success  { background: rgba(16,185,129,0.12); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.2); }
.tag-warn     { background: rgba(245,158,11,0.12);  color: #fcd34d; border: 1px solid rgba(245,158,11,0.2); }
.tag-critical { background: rgba(239,68,68,0.12);   color: #fca5a5; border: 1px solid rgba(239,68,68,0.25); }
.tag-info     { background: rgba(59,130,246,0.12);  color: #93c5fd; border: 1px solid rgba(59,130,246,0.2); }
.tag-muted    { background: rgba(107,114,128,0.12); color: #9ca3af; border: 1px solid rgba(107,114,128,0.2); }

/* Thinking dots */
.thinking { display: flex; align-items: center; gap: 5px; padding: 0.75rem 1.1rem; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; border-top-left-radius: 4px; width: fit-content; backdrop-filter: blur(12px); }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #06b6d4; animation: bounce 1.2s ease-in-out infinite; }
.dot:nth-child(2) { animation-delay: 0.2s; background: #818cf8; }
.dot:nth-child(3) { animation-delay: 0.4s; background: #a5b4fc; }
@keyframes bounce { 0%,80%,100% { transform: translateY(0); opacity:0.4; } 40% { transform: translateY(-7px); opacity:1; } }

/* Chat input */
[data-testid="stChatInput"] { position: fixed !important; bottom: 0; left: 0; right: 0; background: rgba(8,11,20,0.92) !important; backdrop-filter: blur(20px); border-top: 1px solid rgba(255,255,255,0.06); padding: 1rem 1.5rem 1.2rem; z-index: 100; }
[data-testid="stChatInput"] textarea { background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(99,102,241,0.25) !important; border-radius: 12px !important; color: #e8eaf0 !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.95rem !important; caret-color: #6366f1; }
[data-testid="stChatInput"] textarea:focus { border-color: rgba(99,102,241,0.5) !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important; }
[data-testid="stChatInputSubmitButton"] { background: linear-gradient(135deg, #6366f1, #06b6d4) !important; border-radius: 10px !important; border: none !important; }

.error-box { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.25); border-radius: 14px; padding: 1.2rem 1.5rem; color: #fca5a5; font-size: 0.9rem; display: flex; gap: 0.75rem; align-items: flex-start; }
</style>
""", unsafe_allow_html=True)

# ── ChromaDB check ────────────────────────────────────────────────────────────
if not os.path.exists("chroma_db"):
    st.markdown("""<div class="error-box"><span style="font-size:1.2rem">⚠️</span>
    <div><strong>Knowledge base not found.</strong><br>Run <code>python ingest.py</code> first, then refresh.</div></div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Session state ─────────────────────────────────────────────────────────────
if "messages"   not in st.session_state: st.session_state.messages   = []
if "chip_query" not in st.session_state: st.session_state.chip_query = None

# route → (bubble class, tag class, tag label)
ROUTE_STYLE = {
    "answer":      ("bot-bubble",      "tag-success",  "✦ Answered from Knowledge Base"),
    "escalate":    ("escalate-bubble", "tag-warn",     "⚡ Escalated to Support Agent"),
    "clarify":     ("clarify-bubble",  "tag-info",     "💬 Clarification Needed"),
    "out_of_scope":("scope-bubble",    "tag-muted",    "🚫 Outside Support Scope"),
}
# critical escalation also uses escalate route but gets red styling
CRITICAL_STYLE = ("critical-bubble", "tag-critical", "🚨 Critical — Agent Notified")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nexus-header">
    <div class="nexus-logo-icon">✦</div>
    <div class="nexus-title">NexusAI Support</div>
    <div class="nexus-subtitle">Intelligent · Contextual · Instant</div>
</div>
<div class="nexus-divider"></div>
""", unsafe_allow_html=True)

# ── Welcome card + chips ──────────────────────────────────────────────────────
CHIPS = [
    "📦 Where is my order?",
    "↩️ How do I return an item?",
    "💳 Why was I charged twice?",
    "🚚 How long does shipping take?",
]

if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        <h3>How can I help you today?</h3>
        <p>Ask me anything about your orders, returns, shipping, or account.
        Urgent issues are escalated to a human agent automatically.</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(len(CHIPS))
    for col, chip_text in zip(cols, CHIPS):
        with col:
            if st.button(chip_text, key=f"chip_{chip_text}"):
                st.session_state.chip_query = chip_text

# ── Process chip click ────────────────────────────────────────────────────────
if st.session_state.chip_query:
    prompt = st.session_state.chip_query
    st.session_state.chip_query = None
    st.session_state.messages.append({"role": "user", "content": prompt})
    result = run_rag(prompt)
    st.session_state.messages.append({
        "role": "assistant", "content": result["answer"],
        "route": result["route"], "intent": result.get("intent", ""),
    })
    st.rerun()

# ── Render chat history ───────────────────────────────────────────────────────
st.markdown('<div class="chat-feed">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    role   = msg["role"]
    text   = msg["content"]
    route  = msg.get("route", "answer")
    intent = msg.get("intent", "")

    if role == "user":
        st.markdown(f"""
        <div class="msg-row user">
            <div class="avatar user-av">👤</div>
            <div class="bubble user-bubble">{text}</div>
        </div>""", unsafe_allow_html=True)
    else:
        # Critical gets its own red style even though route="escalate"
        if intent == "critical":
            bubble_cls, tag_cls, tag_text = CRITICAL_STYLE
        else:
            bubble_cls, tag_cls, tag_text = ROUTE_STYLE.get(route, ROUTE_STYLE["answer"])

        st.markdown(f"""
        <div class="msg-row bot">
            <div class="avatar bot-av">✦</div>
            <div>
                <div class="bubble {bubble_cls}">{text}</div>
                <span class="status-tag {tag_cls}">{tag_text}</span>
            </div>
        </div>""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about your order, return, payment, or account…"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    thinking_ph = st.empty()
    thinking_ph.markdown("""
    <div class="msg-row bot" style="margin-top:0.5rem">
        <div class="avatar bot-av">✦</div>
        <div class="thinking"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
    </div>""", unsafe_allow_html=True)

    result = run_rag(prompt)
    thinking_ph.empty()

    st.session_state.messages.append({
        "role": "assistant", "content": result["answer"],
        "route": result["route"], "intent": result.get("intent", ""),
    })
    st.rerun()