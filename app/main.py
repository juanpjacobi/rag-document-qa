import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.ingest import ingest_pdf, get_chroma_collection
from app.retriever import retrieve
from app.generator import generate_answer

app = FastAPI(title="RAG Q&A System")

UPLOAD_DIR = "pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class QuestionRequest(BaseModel):
    question: str
    doc_id: str | None = None


class QuestionResponse(BaseModel):
    answer: str
    doc_id: str | None
    chunks_used: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/documents")
def list_documents():
    collection = get_chroma_collection()
    results = collection.get(include=["metadatas"])
    metadatas = results.get("metadatas") or []

    docs: dict[str, int] = {}
    for m in metadatas:
        doc_id = m["doc_id"]
        docs[doc_id] = docs.get(doc_id, 0) + 1

    return {
        "total": len(docs),
        "documents": [{"doc_id": did, "chunks": count} for did, count in docs.items()],
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF.")

    doc_id = str(uuid.uuid4())[:8]
    pdf_path = os.path.join(UPLOAD_DIR, f"{doc_id}.pdf")

    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    chunks_count = ingest_pdf(pdf_path, doc_id)

    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "chunks_indexed": chunks_count,
    }


@app.post("/ask", response_model=QuestionResponse)
def ask(body: QuestionRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")

    chunks = retrieve(body.question, doc_id=body.doc_id)

    if not chunks:
        raise HTTPException(status_code=404, detail="No hay documentos indexados para consultar.")

    answer = generate_answer(body.question, chunks)

    return QuestionResponse(
        answer=answer,
        doc_id=body.doc_id,
        chunks_used=len(chunks),
    )
