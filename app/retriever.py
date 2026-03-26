from app.ingest import get_embedding_model, get_chroma_collection

TOP_K = 4  # cantidad de chunks relevantes a recuperar


def retrieve(query: str, doc_id: str | None = None, top_k: int = TOP_K) -> list[str]:
    """
    Busca los chunks más similares a la query en ChromaDB.
    Si se pasa doc_id, filtra solo por ese documento.
    """
    model = get_embedding_model()
    query_embedding = model.encode([query]).tolist()

    collection = get_chroma_collection()

    where = {"doc_id": doc_id} if doc_id else None

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where,
    )

    # results["documents"] es una lista de listas (una por query)
    return results["documents"][0] if results["documents"] else []
