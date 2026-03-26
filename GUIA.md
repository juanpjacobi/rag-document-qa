# Guía de aprendizaje — RAG Q&A System

Este archivo documenta todo lo que construimos, en orden, con explicaciones de por qué cada pieza existe.
Se actualiza a medida que avanza el proyecto.

---

## ¿Qué es RAG?

**RAG = Retrieval-Augmented Generation** (Generación aumentada por recuperación).

El problema que resuelve: los LLMs (como Gemini, GPT, Claude) fueron entrenados hasta cierta fecha y no conocen *tus* documentos. Si le preguntás a Gemini sobre el contrato de tu empresa o el manual técnico de tu cliente, no tiene esa información.

RAG resuelve esto en 3 pasos:
1. **Indexar** el documento (partirlo en pedazos y guardarlos de forma buscable)
2. **Recuperar** los pedazos relevantes para la pregunta del usuario
3. **Generar** una respuesta usando esos pedazos como contexto

El LLM no necesita "saber" el documento de antemano — se lo damos en cada consulta.

---

## Arquitectura del proyecto

```
PDF
 │
 ▼
[ingest.py]  ── extrae texto ──► chunks ──► embeddings ──► ChromaDB
                                                               │
Usuario ──► pregunta ──► [retriever.py] ──► busca en ChromaDB ─┘
                                │
                          top-4 chunks relevantes
                                │
                         [generator.py] ──► Gemini API ──► respuesta
                                │
                          [main.py / FastAPI] ──► HTTP response
```

---

## Stack y por qué cada tecnología

| Pieza | Tecnología | Por qué |
|---|---|---|
| LLM | Google Gemini 1.5 Flash | Tier gratuito, sin tarjeta de crédito |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Corre local, sin costo, buena calidad |
| Vector DB | ChromaDB | Local, sin servidor, persistente en disco |
| API | FastAPI | Ya lo dominás del proyecto diabetes |
| Parsing PDF | pypdf | Simple y sin dependencias nativas |

---

## Paso 1 — Setup del proyecto

### Estructura de archivos

```
rag-qa-system/
├── app/
│   ├── __init__.py        ← marca la carpeta como módulo Python
│   ├── main.py            ← FastAPI: define los endpoints HTTP
│   ├── ingest.py          ← Pipeline: PDF → chunks → embeddings → ChromaDB
│   ├── retriever.py       ← Búsqueda semántica en ChromaDB
│   └── generator.py       ← Llama a Gemini con el contexto recuperado
├── pdfs/                  ← PDFs subidos por el usuario (ignorado por git)
├── chroma_db/             ← Base de datos vectorial (se crea automáticamente)
├── requirements.txt
├── .env                   ← API keys (nunca va a git)
└── .gitignore
```

### Variables de entorno

En `.env` guardamos la API key de Gemini. La librería `python-dotenv` la carga automáticamente al arrancar la app.

```
GEMINI_API_KEY=AIza...
```

**Nunca commitear este archivo.** Por eso está en `.gitignore`.

---

## Paso 2 — Ingestión de PDFs (`app/ingest.py`)

Este es el módulo más importante para entender RAG. Hace 4 cosas:

### 2.1 Extraer texto del PDF

```python
def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)
```

`pypdf` lee cada página y extrae el texto plano. Simple.

### 2.2 Dividir en chunks

```python
def split_into_chunks(text: str, chunk_size=500, overlap=50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]
```

**¿Por qué dividir en chunks?**
- Los LLMs tienen un límite de tokens en el contexto. No podemos mandarle un PDF de 200 páginas.
- La búsqueda semántica funciona mejor en textos cortos y enfocados.
- Solo mandamos los pedazos *relevantes*, no todo.

**¿Por qué overlap (solapamiento)?**
- Si una idea importante cae justo en el límite entre dos chunks, sin overlap la perderíamos.
- Con 50 caracteres de overlap, el final de un chunk se repite al inicio del siguiente.

### 2.3 Generar embeddings

```python
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(chunks).tolist()
```

**¿Qué es un embedding?**
Es una representación numérica de un texto — un vector de 384 números en este caso.
El modelo convierte "¿cuánto cuesta el producto?" en `[0.12, -0.45, 0.89, ...]`.

Lo importante: textos con significado *similar* producen vectores *cercanos* en el espacio.
"precio del artículo" y "¿cuánto vale?" terminan cerca. "receta de pasta" termina lejos.

`all-MiniLM-L6-v2` es un modelo liviano (~90MB) que corre en CPU sin problema.
Se descarga la primera vez y queda en caché local.

### 2.4 Guardar en ChromaDB

```python
collection.upsert(
    ids=ids,
    embeddings=embeddings,
    documents=chunks,
    metadatas=metadatas,
)
```

ChromaDB guarda:
- `ids`: identificadores únicos de cada chunk
- `embeddings`: los vectores (para buscar)
- `documents`: el texto original del chunk (para devolverlo)
- `metadatas`: info extra (doc_id, índice del chunk)

`upsert` = insert + update: si el chunk ya existe, lo actualiza. Así podemos re-indexar un documento sin duplicar.

---

## Paso 3 — Retrieval (`app/retriever.py`)

```python
def retrieve(query: str, doc_id: str | None = None, top_k: int = 4) -> list[str]:
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where={"doc_id": doc_id} if doc_id else None,
    )
    return results["documents"][0]
```

**¿Qué pasa acá?**
1. Convertimos la pregunta del usuario en un embedding (mismo proceso que los chunks)
2. ChromaDB compara ese vector contra todos los vectores almacenados
3. Devuelve los `top_k=4` chunks cuyo vector sea más cercano al de la pregunta

La "cercanía" se mide con **similitud coseno** — el ángulo entre dos vectores.
Cuanto menor el ángulo (vectores apuntando en la misma dirección), más similares son semánticamente.

El parámetro `where` permite filtrar por documento. Así podemos preguntar sobre un PDF específico.

---

## Paso 4 — Generación (`app/generator.py`)

```python
prompt = f"""Eres un asistente que responde preguntas basándose ÚNICAMENTE en el contexto provisto.
Si la respuesta no está en el contexto, responde: "No encontré información sobre eso en el documento."

CONTEXTO:
{context}

PREGUNTA:
{question}

RESPUESTA:"""

response = get_model().generate_content(prompt)
```

**¿Por qué este prompt?**
Sin la instrucción "basándose ÚNICAMENTE en el contexto", el LLM responde con su conocimiento general,
que puede ser incorrecto o inventado para *tu* documento específico.

Esto se llama **prompt engineering** — guiar al modelo con instrucciones precisas.

La instrucción de decir "No encontré información" evita **alucinaciones**: cuando el modelo inventa
respuestas con confianza pero sin base real.

---

## Paso 5 — API (`app/main.py`)

Dos endpoints:

### POST /upload
```
PDF file → doc_id + chunks_indexed
```
Recibe el archivo, lo guarda en disco, llama a `ingest_pdf()`, devuelve el `doc_id` para usarlo en consultas.

### POST /ask
```json
{ "question": "¿Cuál es el precio?", "doc_id": "abc12345" }
→
{ "answer": "...", "doc_id": "abc12345", "chunks_used": 4 }
```
Llama a `retrieve()` con la pregunta y el doc_id, luego a `generate_answer()` con los chunks.

---

## Cómo correr el proyecto localmente

```bash
# 1. Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar API key en .env
# GEMINI_API_KEY=tu_key_aqui

# 4. Correr el servidor
uvicorn app.main:app --reload

# 5. Abrir docs interactivas en el browser
# http://localhost:8000/docs
```

---

## Paso 6 — Mejora del chunking (palabras en lugar de caracteres)

El chunking original cortaba por cantidad de caracteres, lo que partía palabras a la mitad.
Ejemplo del problema: `"identif"` en un chunk, `"icar fugas"` en el siguiente.
Eso degrada la calidad de los embeddings porque el modelo recibe texto incompleto.

**Solución:** chunking por palabras.

```python
# ANTES — chunking por caracteres (malo)
def split_into_chunks(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])   # corta en cualquier punto
        start += chunk_size - overlap
    return chunks

# DESPUÉS — chunking por palabras (mejor)
def split_into_chunks(text, chunk_size=150, overlap=20):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk_words = words[start:start + chunk_size]
        chunks.append(" ".join(chunk_words))  # siempre palabras completas
        start += chunk_size - overlap
    return chunks
```

**Parámetros actuales:** 150 palabras por chunk, 20 palabras de overlap.
150 palabras ≈ 750 caracteres promedio, con contexto suficiente para cada chunk.

**Cuando cambiar el chunking hay que re-indexar:** los chunks viejos siguen en ChromaDB.
Hay que volver a hacer `POST /upload` con el mismo PDF para regenerar los embeddings.

---

## Qué aprendimos probando en producción

Probamos con dos PDFs reales (roadmap técnico y ebook de finanzas).
Estos son los patrones que encontramos:

| Tipo de pregunta | Resultado | Explicación |
|---|---|---|
| Vocabulario exacto del doc | ✅ Responde bien | Alta similitud semántica |
| Dato numérico específico | ✅ Responde bien | El número está en el contexto |
| Info que no está en el doc | ✅ "No encontré" | No alucina — comportamiento correcto |
| Lenguaje coloquial ≠ vocabulario del doc | ⚠️ "No encontré" | Gap semántico |

**El caso coloquial explicado:**
Pregunta: *"¿Qué hago si me quedo sin dinero?"*
El doc habla de: *"fondo de emergencia"*, *"imprevistos"*, *"deudas activas"*
El modelo de embeddings no conecta ambas formulaciones → no recupera los chunks relevantes.

**Solución futura — Query Rewriting:**
Antes de buscar, usar el LLM para reformular la pregunta del usuario
con el vocabulario del dominio del documento.

---

## Conceptos clave para la entrevista

| Concepto | Explicación corta |
|---|---|
| **RAG** | Combinar búsqueda semántica con LLM para responder sobre documentos propios |
| **Embedding** | Vector numérico que representa el significado semántico de un texto |
| **Chunk** | Fragmento de texto del documento; unidad básica de indexación y retrieval |
| **Vector DB** | Base de datos optimizada para buscar por similitud entre vectores |
| **Similitud coseno** | Métrica para medir qué tan parecidos son dos vectores semánticamente |
| **Prompt engineering** | Diseño del prompt para guiar el comportamiento del LLM |
| **Alucinación** | Cuando un LLM genera información falsa con aparente confianza |
| **Grounding** | Anclar las respuestas del LLM a hechos concretos (en este caso, el documento) |
| **Query rewriting** | Reformular la pregunta del usuario para mejorar el retrieval semántico |
| **Chunking** | Estrategia de división del texto; afecta directamente la calidad del retrieval |
