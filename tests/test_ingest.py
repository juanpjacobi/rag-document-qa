from app.ingest import split_into_chunks


def test_chunks_no_vacios():
    """Ningún chunk puede estar vacío."""
    text = "palabra " * 200
    chunks = split_into_chunks(text)
    assert all(c.strip() for c in chunks)


def test_chunks_palabras_completas():
    """Los chunks no deben cortar palabras a la mitad."""
    text = "palabra " * 200
    chunks = split_into_chunks(text)
    for chunk in chunks:
        for word in chunk.split():
            assert word == "palabra"


def test_chunks_cantidad():
    """Con 300 palabras y chunk_size=150, overlap=20 deben generarse 3 chunks."""
    text = "palabra " * 300
    chunks = split_into_chunks(text, chunk_size=150, overlap=20)
    # chunk 0: palabras 0-149
    # chunk 1: palabras 130-279
    # chunk 2: palabras 260-299
    assert len(chunks) == 3


def test_chunks_overlap():
    """Las últimas palabras de un chunk deben aparecer al inicio del siguiente."""
    words = [f"w{i}" for i in range(200)]
    text = " ".join(words)
    chunks = split_into_chunks(text, chunk_size=100, overlap=20)

    last_words_chunk0 = chunks[0].split()[-20:]
    first_words_chunk1 = chunks[1].split()[:20]
    assert last_words_chunk0 == first_words_chunk1


def test_texto_vacio():
    """Texto vacío no debe generar chunks."""
    chunks = split_into_chunks("")
    assert chunks == []


def test_texto_corto():
    """Texto más corto que chunk_size genera un solo chunk."""
    text = "solo diez palabras en este texto de prueba aquí"
    chunks = split_into_chunks(text, chunk_size=150, overlap=20)
    assert len(chunks) == 1
    assert chunks[0] == text
