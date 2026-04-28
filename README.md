# ✦ NexusAI — RAG-Based Customer Support Assistant

> A production-grade Retrieval-Augmented Generation system for e-commerce customer support, built with LangGraph, ChromaDB, Groq, and Streamlit.

---

## 📌 Project Overview

This is not a simple chatbot. It is a fully designed AI support system that:

- Reads and indexes a **PDF knowledge base** using vector embeddings
- **Classifies every query** using an LLM before touching the retrieval pipeline
- Routes queries through a **9-node LangGraph workflow** with conditional branching
- Generates **context-grounded answers** from retrieved FAQ chunks
- **Escalates critical or unanswerable queries** to human agents automatically
- Serves everything through a **Streamlit web UI** with live session stats

---

## 🧠 System Architecture

```
Query
  │
  ▼
[Intent Classifier Node]  ← LLM call at temperature=0
  │
  ├── out_of_scope  ──→  Polite rejection
  ├── ambiguous     ──→  Smart clarifying question
  ├── critical      ──→  Immediate human escalation 🚨
  └── in_scope
        │
        ▼
  [Retrieve Node]  ← ChromaDB top-4 similarity search
        │
        ▼
  [Relevance Check Node]  ← LLM validates chunk usefulness
        │
        ├── irrelevant ──→  Human escalation ⚡
        └── relevant
              │
              ▼
        [Generate Node]  ← LLM answers from context
              │
              ├── low confidence ──→  Human escalation ⚡
              └── high confidence ──→  Final Answer ✦
```

---

## 🗂️ Project Structure

```
rag_support_assistant/
│
├── app.py                  # Streamlit web UI
├── graph.py                # LangGraph workflow (all nodes + routing)
├── retriever.py            # ChromaDB retriever loader
├── ingest.py               # PDF ingestion pipeline (run once)
│
├── knowledge_base/
│   └── your_faq.pdf        # ← Put your PDF here
│
├── chroma_db/              # Auto-created after running ingest.py
│   └── (vector data)
│
├── .env                    # API keys (never commit this)
├── requirements.txt        # Python dependencies
└── README.md
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| LLM | Groq API — Llama 3.3 70B Versatile |
| Embeddings | SentenceTransformers — all-MiniLM-L6-v2 (local) |
| Vector Store | ChromaDB (persistent, file-based) |
| Workflow | LangGraph (StateGraph) |
| Framework | LangChain |
| UI | Streamlit |
| Env Management | python-dotenv |

---

## 🚀 Setup & Installation

### Step 1 — Clone or download the project

```bash
cd Desktop
mkdir rag_support_assistant
cd rag_support_assistant
```

### Step 2 — Create and activate virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

> ⚠️ **Windows permission error?** Run this first:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **Python 3.13 note:** If `sentence-transformers` or `chromadb` fails:
> ```bash
> pip install sentence-transformers --pre
> pip install chromadb --only-binary=:all:
> ```

### Step 4 — Add your Groq API key

Create a `.env` file in the project root:

```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
```

Get your free key at: [https://console.groq.com](https://console.groq.com) → API Keys → Create Key

### Step 5 — Add your PDF

Place your FAQ PDF inside the `knowledge_base/` folder, then update line 10 of `ingest.py`:

```python
PDF_PATH = "knowledge_base/your_actual_filename.pdf"
```

### Step 6 — Run ingestion (once only)

```bash
python ingest.py
```

Expected output:
```
📄 Loading PDF...
   Loaded 12 pages.
✂️  Chunking documents...
   Created 87 chunks.
🔢 Creating embeddings & storing in ChromaDB...
✅ Done! ChromaDB saved to 'chroma_db/'
```

> ℹ️ First run downloads the embedding model (~90MB). Requires internet. Takes ~1 minute.
> After this, embeddings are cached locally. Never needs internet again.

### Step 7 — Launch the app

```bash
streamlit run app.py
```

Browser opens automatically at `http://localhost:8501`

---

## 🔄 Routing Logic

Every query is classified into one of four intents before the RAG pipeline runs:

| Intent | Example | Action |
|---|---|---|
| `in_scope` | "How do I track my order?" | Full RAG pipeline → answer |
| `ambiguous` | "payment" | LLM generates a clarifying question |
| `out_of_scope` | "What is the weather today?" | Polite rejection — no RAG called |
| `critical` | "I was charged twice" | Immediate human escalation — no RAG called |

---

## 🎨 UI Features

- **Dark glassmorphism design** with animated background orbs
- **Sidebar** with live session stats (answered / escalated / clarified)
- **Recent conversation history** in the sidebar
- **Suggestion chips** on welcome screen (clickable, fire real queries)
- **Colour-coded status pills** per message:
  - ✦ Green — Answered from Knowledge Base
  - ⚡ Amber — Escalated to Support Agent
  - 💬 Blue — Clarification Needed
  - 🚫 Grey — Outside Support Scope
  - 🚨 Red — Critical — Agent Notified
- **Thinking animation** while query processes
- **Clear conversation** button in sidebar

---

## ✅ Quick Sanity Test

Once the app is running, test these 4 queries to verify all routes work:

| Query | Expected |
|---|---|
| `Where is my order?` | ✦ Green — answered |
| `payment` | 💬 Blue — asks for clarification |
| `I was charged twice` | 🚨 Red — critical escalation |
| `What is the weather today?` | 🚫 Grey — out of scope |

---

## ⚠️ Common Issues & Fixes

| Problem | Fix |
|---|---|
| `chroma_db not found` | Run `python ingest.py` first |
| `GROQ_API_KEY not found` | Check `.env` file is in the project root folder |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside the venv |
| `chromadb install fails` | Run `pip install chromadb --only-binary=:all:` |
| `Model decommissioned` error | Check `graph.py` — model must be `llama-3.3-70b-versatile` |
| `venv\Scripts\activate` blocked | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Groq rate limit (429) | Free tier = 30 req/min. Wait ~60 seconds and retry |
| Answer always "I don't know" | Increase `chunk_size` to `800` in `ingest.py`, re-run ingestion |

---

## 📦 requirements.txt

```
langchain
langchain-community
langchain-groq
langchain-chroma
langgraph
chromadb
pypdf
streamlit
python-dotenv
sentence-transformers
```

---

## 📄 Deliverables

| Document | Contents |
|---|---|
| `HLD_RAG_System.docx` | System overview, architecture diagram, component descriptions, data flow, technology choices, scalability |
| `LLD_RAG_System.docx` | Module design, data structures, LangGraph workflow, routing logic, HITL design, API design, error handling |
| `TechDoc_RAG_System.docx` | Introduction to RAG, design decisions, trade-offs, testing strategy, future enhancements |

---

## 🔮 Future Enhancements

- [ ] Multi-document support (index multiple PDFs)
- [ ] Conversation memory across turns
- [ ] Real HITL integration (Zendesk / Freshdesk API)
- [ ] Streaming token-by-token responses
- [ ] Automated evaluation with RAGAS
- [ ] Feedback loop — thumbs up/down per answer
- [ ] Analytics dashboard (query volume, route distribution)
- [ ] Docker containerisation + cloud deployment

---

## 👤 Author

Built as part of an AI/ML internship project.  
Designed and implemented end-to-end: ingestion pipeline, graph workflow, routing logic, UI, and documentation.

---

> *"You are not just building a chatbot. You are designing a scalable AI system with decision-making capability."*
