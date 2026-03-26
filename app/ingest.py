import os
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "documents"
CHUNK_SIZE = 150      # palabras por chunk
CHUNK_OVERLAP = 20    # palabras de solapamiento

_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        # Se descarga la primera vez (~90MB), luego queda en cache local
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def get_chroma_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk_words = words[start:start + chunk_size]
        chunks.append(" ".join(chunk_words))
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def ingest_pdf(pdf_path: str, doc_id: str) -> int:
    """
    Carga un PDF, lo divide en chunks, genera embeddings y los guarda en ChromaDB.
    Retorna la cantidad de chunks procesados.
    """
    text = extract_text_from_pdf(pdf_path)
    chunks = split_into_chunks(text)

    model = get_embedding_model()
    embeddings = model.encode(chunks).tolist()

    collection = get_chroma_collection()

    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    return len(chunks)
