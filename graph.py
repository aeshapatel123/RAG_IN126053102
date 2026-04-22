# graph.py
"""
RAG Customer Support Graph — E-Commerce Edition
================================================
Flow:
  Query → LLM Classifier → out_of_scope  → reject
                         → ambiguous     → clarify
                         → critical      → force escalate
                         → in_scope      → retrieve
                                            → relevance_check → no chunks → escalate
                                            → generate
                                               → confidence_check → low → escalate
                                                                  → high → answer
"""

import os
import json
import re
from typing import TypedDict, List, Optional
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from retriever import get_retriever

load_dotenv()

# ═══════════════════════════════════════════════════════════════
# 1.  STATE
# ═══════════════════════════════════════════════════════════════
class GraphState(TypedDict):
    query:            str
    intent:           str          # out_of_scope | ambiguous | critical | in_scope
    intent_reason:    str          # why the classifier chose this (for debugging)
    retrieved_chunks: List[str]
    chunks_relevant:  bool
    answer:           str
    confidence:       str          # high | low
    route:            str          # answer | escalate | clarify | out_of_scope
    needs_human:      bool
    human_response:   Optional[str]

# ═══════════════════════════════════════════════════════════════
# 2.  LLM  (one shared instance, low temperature for consistency)
# ═══════════════════════════════════════════════════════════════
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,                  # zero temp → deterministic classification
    api_key=os.getenv("GROQ_API_KEY"),
)

retriever = get_retriever()

# ═══════════════════════════════════════════════════════════════
# 3.  NODE 1 — LLM-BASED INTENT CLASSIFIER
#     Uses the LLM to understand meaning, not just keywords.
#     Returns a JSON object so we can parse it reliably.
# ═══════════════════════════════════════════════════════════════
CLASSIFIER_SYSTEM = """You are an intent classifier for an e-commerce customer support system.

Classify the user's message into EXACTLY ONE of these four categories:

1. "out_of_scope"
   - Questions unrelated to e-commerce or customer support
   - Examples: weather, cooking, math, jokes, politics, general knowledge,
     "who is Einstein", "what is Python", "write a poem"

2. "ambiguous"
   - Message is too vague to act on — missing key details
   - Usually very short (1-4 words) with no clear question
   - Examples: "payment", "my order", "problem", "help", "issue", "not working"
   - NOT ambiguous: "I have a payment problem" — that has enough context

3. "critical"
   - Requires immediate human intervention — sensitive, urgent, or high-risk
   - Examples:
     * Billing disputes: charged twice, wrong amount, unauthorized charge
     * Refund requests
     * Fraud or scam reports
     * Account hacked or compromised
     * Legal threats or complaints
     * Data privacy concerns
     * Extremely negative experience demanding manager/supervisor
     * "I want to speak to a human / agent / manager"
     * Any message with strong urgency or emotional distress about money

4. "in_scope"
   - Normal customer support questions about orders, shipping, returns, products,
     accounts, discounts, delivery, tracking, cancellations, product info, etc.
   - Even if the question seems hard, if it's e-commerce related → in_scope

Respond with ONLY valid JSON. No explanation, no markdown, no extra text.
Format: {"intent": "<category>", "reason": "<one sentence why>"}"""

def classify_intent(query: str) -> tuple[str, str]:
    """Call LLM classifier. Returns (intent, reason). Falls back to in_scope on error."""
    try:
        response = llm.invoke([
            SystemMessage(content=CLASSIFIER_SYSTEM),
            HumanMessage(content=f"User message: {query}"),
        ])
        raw = response.content.strip()

        # Strip markdown code fences if LLM adds them despite instructions
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)
        intent = parsed.get("intent", "in_scope").strip().lower()
        reason = parsed.get("reason", "")

        # Validate — if LLM returns something unexpected, default to in_scope
        valid = {"out_of_scope", "ambiguous", "critical", "in_scope"}
        if intent not in valid:
            intent = "in_scope"

        return intent, reason

    except Exception as e:
        # Never crash the whole graph over a classifier failure
        return "in_scope", f"Classifier error: {e}"


def intent_node(state: GraphState) -> GraphState:
    intent, reason = classify_intent(state["query"])
    state["intent"]        = intent
    state["intent_reason"] = reason
    return state

# ═══════════════════════════════════════════════════════════════
# 4.  NODE 2 — OUT-OF-SCOPE
# ═══════════════════════════════════════════════════════════════
def out_of_scope_node(state: GraphState) -> GraphState:
    state["answer"] = (
        "I'm here to help with e-commerce support — things like orders, "
        "shipping, returns, payments, and your account. "
        "Your question seems to be outside that area.\n\n"
        "If you have a shopping or order-related question, I'm happy to help!"
    )
    state["route"]       = "out_of_scope"
    state["needs_human"] = False
    return state

# ═══════════════════════════════════════════════════════════════
# 5.  NODE 3 — AMBIGUOUS → ask for clarification
# ═══════════════════════════════════════════════════════════════
CLARIFY_SYSTEM = """You are a friendly e-commerce support assistant.
The user sent a very vague message. Ask them ONE clear, specific clarifying question
to understand what they need help with.
Keep it warm, brief, and conversational. Do not list multiple questions."""

def clarify_node(state: GraphState) -> GraphState:
    try:
        response = llm.invoke([
            SystemMessage(content=CLARIFY_SYSTEM),
            HumanMessage(content=f"Vague message from user: \"{state['query']}\""),
        ])
        clarification = response.content.strip()
    except Exception:
        clarification = (
            f"I'd love to help with that! Could you give me a bit more detail about "
            f"your \"{state['query']}\" issue — for example, is this related to an order, "
            f"a payment, or something else?"
        )

    state["answer"]      = clarification
    state["route"]       = "clarify"
    state["needs_human"] = False
    return state

# ═══════════════════════════════════════════════════════════════
# 6.  NODE 4 — CRITICAL → immediate human escalation
# ═══════════════════════════════════════════════════════════════
def critical_escalation_node(state: GraphState) -> GraphState:
    state["answer"] = (
        "🚨 **Your issue has been flagged as high priority.**\n\n"
        "I've escalated this directly to a senior support agent. "
        "You will be contacted within **1 hour** on the email linked to your account.\n\n"
        f"**Issue logged:** {state['query']}\n\n"
        "_Please do not submit this request again — it's already in our queue._"
    )
    state["route"]       = "escalate"
    state["needs_human"] = True
    return state

# ═══════════════════════════════════════════════════════════════
# 7.  NODE 5 — RETRIEVE chunks from ChromaDB
# ═══════════════════════════════════════════════════════════════
def retrieve_node(state: GraphState) -> GraphState:
    docs = retriever.invoke(state["query"])
    state["retrieved_chunks"] = [doc.page_content for doc in docs]
    return state

# ═══════════════════════════════════════════════════════════════
# 8.  NODE 6 — RELEVANCE CHECK
#     Before wasting an LLM call, check if retrieved chunks
#     are actually related to the query at all.
#     Uses a fast LLM call to judge relevance.
# ═══════════════════════════════════════════════════════════════
RELEVANCE_SYSTEM = """You are a relevance judge.
Given a user question and a set of retrieved text chunks, decide if the chunks
contain information that could help answer the question.

Respond with ONLY one word: "relevant" or "irrelevant". Nothing else."""

def relevance_check_node(state: GraphState) -> GraphState:
    chunks = state["retrieved_chunks"]

    if not chunks:
        state["chunks_relevant"] = False
        return state

    # Only check if we have something to evaluate
    sample = "\n---\n".join(chunks[:2])   # check top 2 chunks only (faster)
    try:
        response = llm.invoke([
            SystemMessage(content=RELEVANCE_SYSTEM),
            HumanMessage(content=f"Question: {state['query']}\n\nChunks:\n{sample}"),
        ])
        verdict = response.content.strip().lower()
        state["chunks_relevant"] = "relevant" in verdict
    except Exception:
        # On error, assume relevant to avoid unnecessary escalation
        state["chunks_relevant"] = True

    return state

# ═══════════════════════════════════════════════════════════════
# 9.  NODE 7 — GENERATE answer from context
# ═══════════════════════════════════════════════════════════════
GENERATE_SYSTEM = """You are a professional e-commerce customer support assistant.

Rules:
- Answer using ONLY the provided context. Do not make up information.
- Be friendly, concise, and actionable.
- If the context partially answers the question, give what you can and clearly
  state what you don't have information about.
- If the context does not answer the question at all, respond with exactly one
  line: "INSUFFICIENT_CONTEXT"
- Never guess order details, prices, or policies not mentioned in context."""

def generate_node(state: GraphState) -> GraphState:
    context = "\n\n---\n\n".join(state["retrieved_chunks"])

    try:
        response = llm.invoke([
            SystemMessage(content=GENERATE_SYSTEM),
            HumanMessage(content=f"Context:\n{context}\n\nCustomer question: {state['query']}"),
        ])
        answer = response.content.strip()
    except Exception as e:
        answer = "INSUFFICIENT_CONTEXT"

    # Confidence scoring — multiple signals
    low_signals = [
        "INSUFFICIENT_CONTEXT",
        "i don't have",
        "i do not have",
        "not in the context",
        "i cannot find",
        "no information",
        "i'm unable",
        "i am unable",
        "cannot answer",
        "don't know",
        "not sure",
    ]
    is_low = any(sig.lower() in answer.lower() for sig in low_signals)

    state["answer"]      = answer
    state["confidence"]  = "low" if is_low else "high"
    state["needs_human"] = is_low
    return state

# ═══════════════════════════════════════════════════════════════
# 10. NODE 8 — HITL escalation (soft — from low confidence)
# ═══════════════════════════════════════════════════════════════
def hitl_node(state: GraphState) -> GraphState:
    state["route"]  = "escalate"
    state["answer"] = (
        "⚠️ **I wasn't able to find a reliable answer in my knowledge base.**\n\n"
        "I've passed your question to a human support agent who will follow up shortly.\n\n"
        f"**Your question:** {state['query']}\n\n"
        "_Typical response time: 2–4 hours during business hours._"
    )
    return state

# ═══════════════════════════════════════════════════════════════
# 11. NODE 9 — OUTPUT (confident answer reaches user)
# ═══════════════════════════════════════════════════════════════
def output_node(state: GraphState) -> GraphState:
    state["route"] = "answer"
    return state

# ═══════════════════════════════════════════════════════════════
# 12. ROUTERS
# ═══════════════════════════════════════════════════════════════
def route_after_intent(state: GraphState) -> str:
    return {
        "out_of_scope": "out_of_scope",
        "ambiguous":    "clarify",
        "critical":     "critical_escalation",
        "in_scope":     "retrieve",
    }.get(state["intent"], "retrieve")


def route_after_relevance(state: GraphState) -> str:
    """If chunks aren't relevant, skip generation and escalate."""
    return "generate" if state["chunks_relevant"] else "hitl"


def route_after_generate(state: GraphState) -> str:
    return "hitl" if state["needs_human"] else "output"

# ═══════════════════════════════════════════════════════════════
# 13. BUILD THE GRAPH
# ═══════════════════════════════════════════════════════════════
def build_graph():
    wf = StateGraph(GraphState)

    # ── Nodes ──────────────────────────────────────────────────
    wf.add_node("intent",              intent_node)
    wf.add_node("out_of_scope",        out_of_scope_node)
    wf.add_node("clarify",             clarify_node)
    wf.add_node("critical_escalation", critical_escalation_node)
    wf.add_node("retrieve",            retrieve_node)
    wf.add_node("relevance_check",     relevance_check_node)
    wf.add_node("generate",            generate_node)
    wf.add_node("hitl",                hitl_node)
    wf.add_node("output",              output_node)

    # ── Entry ───────────────────────────────────────────────────
    wf.set_entry_point("intent")

    # ── After intent classifier ─────────────────────────────────
    wf.add_conditional_edges("intent", route_after_intent, {
        "out_of_scope":        "out_of_scope",
        "clarify":             "clarify",
        "critical_escalation": "critical_escalation",
        "retrieve":            "retrieve",
    })

    # ── RAG pipeline ────────────────────────────────────────────
    wf.add_edge("retrieve", "relevance_check")

    wf.add_conditional_edges("relevance_check", route_after_relevance, {
        "generate": "generate",
        "hitl":     "hitl",
    })

    wf.add_conditional_edges("generate", route_after_generate, {
        "hitl":   "hitl",
        "output": "output",
    })

    # ── Terminal edges ──────────────────────────────────────────
    for node in ["out_of_scope", "clarify", "critical_escalation", "hitl", "output"]:
        wf.add_edge(node, END)

    return wf.compile()


rag_graph = build_graph()

# ═══════════════════════════════════════════════════════════════
# 14. PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════
def run_rag(query: str) -> dict:
    return rag_graph.invoke(GraphState(
        query=query,
        intent="",
        intent_reason="",
        retrieved_chunks=[],
        chunks_relevant=False,
        answer="",
        confidence="",
        route="",
        needs_human=False,
        human_response=None,
    ))