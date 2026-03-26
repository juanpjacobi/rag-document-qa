import os
from google import genai
from google.genai import errors as genai_errors
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def generate_answer(question: str, context_chunks: list[str]) -> str:
    """
    Genera una respuesta basada únicamente en los chunks recuperados.
    Si la respuesta no está en el contexto, lo dice explícitamente.
    """
    context = "\n\n---\n\n".join(context_chunks)

    prompt = f"""Eres un asistente que responde preguntas basándose ÚNICAMENTE en el contexto provisto.
Si la respuesta no está en el contexto, responde: "No encontré información sobre eso en el documento."
No inventes ni agregues información externa.

CONTEXTO:
{context}

PREGUNTA:
{question}

RESPUESTA:"""

    try:
        response = get_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except genai_errors.ClientError as e:
        if e.status_code == 429:
            raise HTTPException(status_code=429, detail="Límite de requests de Gemini alcanzado. Esperá unos segundos y reintentá.")
        raise HTTPException(status_code=502, detail=f"Error al contactar Gemini: {e}")
