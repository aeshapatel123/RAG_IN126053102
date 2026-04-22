# retriever.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

CHROMA_DIR = "chroma_db"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

def get_retriever():
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},  # Required for BGE
    )
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )
    # MMR: fetch 6 candidates, return 4 diverse+relevant chunks
    # fetch_k kept low intentionally for small FAQ databases
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 4,
            "fetch_k": 6,
            "lambda_mult": 0.6,  # Slightly favour relevance over diversity
        },
    )
    return retriever