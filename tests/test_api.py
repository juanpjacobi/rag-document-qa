import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_archivo_no_pdf():
    """Subir un archivo que no es PDF debe devolver 400."""
    data = {"file": ("documento.txt", b"contenido", "text/plain")}
    response = client.post("/upload", files=data)
    assert response.status_code == 400


def test_upload_pdf_ok():
    """Upload de PDF válido debe devolver doc_id y chunks_indexed."""
    with patch("app.main.ingest_pdf", return_value=15) as mock_ingest:
        pdf_bytes = b"%PDF-1.4 contenido de prueba"
        data = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
        response = client.post("/upload", files=data)

    assert response.status_code == 200
    body = response.json()
    assert "doc_id" in body
    assert body["filename"] == "test.pdf"
    assert body["chunks_indexed"] == 15
    mock_ingest.assert_called_once()


def test_ask_pregunta_vacia():
    """Pregunta vacía debe devolver 400."""
    response = client.post("/ask", json={"question": "  ", "doc_id": "abc123"})
    assert response.status_code == 400


def test_ask_sin_chunks():
    """Si el retriever no encuentra chunks debe devolver 404."""
    with patch("app.main.retrieve", return_value=[]):
        response = client.post("/ask", json={"question": "¿Algo?", "doc_id": "abc123"})
    assert response.status_code == 404


def test_ask_ok():
    """Pregunta válida con chunks disponibles debe devolver respuesta."""
    chunks_falsos = ["El método 50/30/20 distribuye los ingresos en tres categorías."]
    respuesta_falsa = "El método 50/30/20 divide los ingresos en necesidades, gustos y ahorro."

    with patch("app.main.retrieve", return_value=chunks_falsos), \
         patch("app.main.generate_answer", return_value=respuesta_falsa):
        response = client.post("/ask", json={"question": "¿Qué es el 50/30/20?", "doc_id": "abc123"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == respuesta_falsa
    assert body["doc_id"] == "abc123"
    assert body["chunks_used"] == 1


def test_documents_devuelve_lista():
    """GET /documents debe devolver total y lista de documentos."""
    mock_collection = MagicMock()
    mock_collection.get.return_value = {
        "metadatas": [
            {"doc_id": "abc123", "chunk_index": 0},
            {"doc_id": "abc123", "chunk_index": 1},
            {"doc_id": "xyz789", "chunk_index": 0},
        ]
    }
    with patch("app.main.get_chroma_collection", return_value=mock_collection):
        response = client.get("/documents")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    doc_ids = [d["doc_id"] for d in body["documents"]]
    assert "abc123" in doc_ids
    assert "xyz789" in doc_ids
