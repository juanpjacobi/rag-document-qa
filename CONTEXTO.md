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
Stack gratuito al 100% (sin tarjeta de crédito).

## Proyecto: RAG Q&A sobre documentos PDF

El usuario carga o elige un PDF, hace preguntas en lenguaje natural,
el sistema responde basándose en el contenido real del documento.

## Stack definido (todo gratuito)

| Pieza | Tecnología | Por qué |
|---|---|---|
| LLM | Google Gemini API | tier gratuito, sin tarjeta |
| Embeddings | sentence-transformers (HuggingFace) | corre local, sin costo |
| Vector DB | ChromaDB | local, simple, ideal para empezar |
| API | FastAPI | ya lo domina |
| Deploy | Render | ya lo domina |

## Roadmap personal 2025-2026 (reordenado)

1. ✅ Proyecto diabetes (completado)
2. 🔄 Proyecto RAG — en curso
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