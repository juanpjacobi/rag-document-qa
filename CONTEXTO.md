# Contexto del proyecto — RAG Q&A System

## Quién es el usuario

Juan Pablo Jacobi. Perfil híbrido backend + ML/IA.
- Backend sólido (experiencia real)
- Data Science: terminó diplomatura, practicando con proyectos propios
- Objetivo inmediato: trabajo remoto ~800-900 USD/mes, se va a Brasil
- Mercado objetivo: hispanohablante + anglófono remoto
- LinkedIn activo con proyectos, CV en español/inglés/portugués (optimizado ATS)

## Proyecto anterior completado

**DiabetesPredictor** — en producción.
- Backend: FastAPI + scikit-learn (RandomForest, 95% accuracy, clasificación multiclase 0/1/2)
- Frontend: Angular 19 (standalone components, reactive forms)
- Deploy: Render (backend) + Netlify (frontend), auto-deploy en push
- CI: GitHub Actions (pytest, 14 tests pasando)
- Extras implementados: model_metadata.json, Pydantic range validation, structured logging + request IDs, SQLite + /metrics endpoint
- Repos: github.com/juanpjacobi/diabetes-ml-api / diabetes-ml-frontend

## Por qué este proyecto

RAG es el caso de uso empresarial más demandado de IA generativa hoy.
Complementa el perfil: diabetes = ML Engineer, RAG = AI Engineer.

## Proyecto: RAG Q&A sobre documentos PDF

El usuario carga un PDF, hace preguntas en lenguaje natural,
el sistema responde basándose en el contenido real del documento.

## Estado actual — Backend COMPLETADO ✅

### Stack final implementado

| Pieza | Tecnología | Notas |
|---|---|---|
| LLM | Google Gemini 2.5 Flash | SDK: google-genai==1.9.0 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | corre local, sin costo |
| Vector DB | ChromaDB | persistente en disco |
| API | FastAPI | 4 endpoints |
| CI | GitHub Actions | pytest en cada push |
| Deploy | Railway (pago) | backend en producción |

### URLs de producción
- **Backend:** https://rag-document-qa-production-c235.up.railway.app
- **Docs interactivas:** https://rag-document-qa-production-c235.up.railway.app/docs
- **Repo:** https://github.com/juanpjacobi/rag-document-qa

### Endpoints implementados
- `GET /health`
- `POST /upload` — sube y indexa un PDF
- `POST /ask` — pregunta sobre un documento
- `GET /documents` — lista PDFs indexados

### Decisiones técnicas importantes
- **Chunking por palabras** (150 palabras, 20 overlap) — no por caracteres para no cortar palabras
- **13 tests** pasando (pytest) — lógica de chunking + endpoints mockeados
- **Manejo de errores**: 429 cuando Gemini se queda sin quota, 404 si no hay chunks, 400 para inputs inválidos
- **ChromaDB es efímero en Railway** — datos se pierden en restart, hay que re-subir el PDF (aceptable para demo)

### Lo que aprendimos probando
- Preguntas con vocabulario exacto del documento → responde bien
- Preguntas con lenguaje coloquial ≠ vocabulario del doc → "No encontré info" (gap semántico)
- Mejora futura: query rewriting antes del retrieval

## Próximo paso — Frontend Angular 19

**Objetivo:** interfaz visual para el portfolio (igual que diabetes).

**Diseño planeado:**
- Upload de PDF con drag & drop
- Interfaz tipo chat (historial de preguntas/respuestas)
- Indicador "pensando..." mientras espera Gemini
- Deploy en Netlify con auto-deploy en push

## Roadmap personal 2025-2026

1. ✅ Proyecto diabetes (completado)
2. 🔄 Proyecto RAG — backend completo, frontend pendiente
3. MLflow / MLOps práctico
4. Agentes IA
5. MCP (cuando el mercado lo pida más)
6. Go (al final, para microservicios)
7. ❌ n8n — descartado (no suma al perfil)

## Cómo trabajamos

- Claude explica los conceptos a medida que se construye, no antes
- Aprendizaje haciendo, no cursos teóricos primero
- Mismo estilo que el proyecto diabetes: implementación paso a paso con explicaciones
- El usuario entiende cada pieza antes de avanzar a la siguiente
