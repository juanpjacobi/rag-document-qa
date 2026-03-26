# RAG Q&A System

A document question-answering API built with RAG (Retrieval-Augmented Generation). Upload a PDF, ask questions in natural language, and get answers grounded in the document content.

**Live demo:** https://rag-document-qa-production-c235.up.railway.app/docs

---

## How it works

```
PDF upload
    │
    ▼
Text extraction (pypdf)
    │
    ▼
Word-based chunking (150 words, 20 overlap)
    │
    ▼
Semantic embeddings (sentence-transformers, runs locally)
    │
    ▼
ChromaDB vector storage
    │
User question ──► semantic search ──► top 4 relevant chunks
                                              │
                                       Gemini 2.5 Flash
                                              │
                                        Grounded answer
```

---

## Tech stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| PDF parsing | pypdf |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) — runs locally |
| Vector DB | ChromaDB |
| LLM | Google Gemini 2.5 Flash |
| Deploy | Render |
| CI | GitHub Actions |

100% free to run (no paid APIs required beyond Gemini free tier).

---

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/upload` | Upload and index a PDF |
| `POST` | `/ask` | Ask a question about an indexed document |
| `GET` | `/documents` | List all indexed documents |

### POST /upload
```bash
curl -X POST https://your-url/upload \
  -F "file=@document.pdf"
```
```json
{
  "doc_id": "8506ebe8",
  "filename": "document.pdf",
  "chunks_indexed": 30
}
```

### POST /ask
```bash
curl -X POST https://your-url/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?", "doc_id": "8506ebe8"}'
```
```json
{
  "answer": "The document covers...",
  "doc_id": "8506ebe8",
  "chunks_used": 4
}
```

---

## Run locally

```bash
# 1. Clone and create virtual environment
git clone https://github.com/YOUR_USER/rag-qa-system.git
cd rag-qa-system
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Gemini API key
cp .env.example .env
# Edit .env and add your key from https://aistudio.google.com/apikey

# 4. Run
uvicorn app.main:app --reload

# 5. Open interactive docs
# http://localhost:8000/docs
```

## Run with Docker

```bash
docker build -t rag-qa-system .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key rag-qa-system
```

---

## Run tests

```bash
pytest tests/ -v
```

13 tests covering chunking logic and all API endpoints. External dependencies (Gemini, ChromaDB) are mocked.

---

## Notes

- ChromaDB stores data locally. On Render free tier, indexed documents are cleared on each restart — re-upload your PDF after a cold start.
- The embeddings model (`all-MiniLM-L6-v2`, ~90MB) is pre-downloaded during Docker build so the first request is fast.

---

## Related projects

- [diabetes-ml-api](https://github.com/juanpjacobi/diabetes-ml-api) — ML prediction API (FastAPI + scikit-learn, deployed on Render)
