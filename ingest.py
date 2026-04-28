# ingest.py
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

PDF_PATH = "knowledge_base/RAG_DATABASE.pdf"   # ← Change this to your PDF filename
CHROMA_DIR = "chroma_db"                   # Where ChromaDB stores data on disk

def ingest():
    print("📄 Loading PDF...")
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()
    print(f"   Loaded {len(documents)} pages.")

    print("✂️  Chunking documents...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,        # Each chunk = 500 characters
        chunk_overlap=100,     # 100 char overlap so context isn't cut off
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    print(f"   Created {len(chunks)} chunks.")

    print("🔢 Creating embeddings & storing in ChromaDB...")
    # SentenceTransformer runs locally — no API key needed
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
    )
    print(f"✅ Done! ChromaDB saved to '{CHROMA_DIR}/'")

if __name__ == "__main__":
    ingest()