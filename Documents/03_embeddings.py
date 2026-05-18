import os
import numpy as np
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

# ============================================================
# Conexión a Neo4j
# ============================================================

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "diripar8$"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ============================================================
# Configuración general
# ============================================================

os.environ["TOKENIZERS_PARALLELISM"] = "false"

MODEL_NAME = "distiluse-base-multilingual-cased-v2"

VECTOR_INDEX_NAME = "textchunk_embedding"
EMBEDDING_PROPERTY = "embedding"

SIMILARITY_FUNCTION = "cosine"

FETCH_LIMIT = 1000
ENCODE_BATCH_SIZE = 32
WRITE_BATCH_SIZE = 200

# Si True, borra embeddings anteriores y los vuelve a generar.
RESET_EMBEDDINGS = False

# Si True, solo genera embeddings para chunks que no tengan embedding.
ONLY_MISSING = True

# ============================================================
# Utilidades
# ============================================================

def batch(rows, size):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def clean_text(text):
    if text is None:
        return ""
    return " ".join(str(text).split())


# ============================================================
# Cargar modelo de embeddings
# ============================================================

def load_embedding_model():
    print(f"⬆️ Cargando modelo de embeddings: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    dimension = model.get_sentence_embedding_dimension()

    print(f"✅ Dimensión del embedding: {dimension}")

    return model, dimension

# ============================================================
# Crear índice vectorial en Neo4j
# ============================================================

def create_vector_index(dimension):
    query = f"""
    CREATE VECTOR INDEX {VECTOR_INDEX_NAME} IF NOT EXISTS
    FOR (c:TextChunk) ON (c.{EMBEDDING_PROPERTY})
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: {dimension},
        `vector.similarity_function`: '{SIMILARITY_FUNCTION}'
      }}
    }}
    """

    with driver.session() as session:
        session.run(query)

    print(f"Índice vectorial verificado: {VECTOR_INDEX_NAME}")


# ============================================================
# Opcional: borrar embeddings anteriores
# ============================================================

def reset_embeddings():
    query = f"""
    MATCH (c:TextChunk)
    REMOVE c.{EMBEDDING_PROPERTY}
    REMOVE c.embedding_model
    REMOVE c.embedding_dimensions
    """

    with driver.session() as session:
        session.run(query)

    print("Embeddings anteriores eliminados.")

# ============================================================
# Contar chunks pendientes
# ============================================================

def count_pending_chunks():
    if ONLY_MISSING:
        query = f"""
        MATCH (c:TextChunk)
        WHERE c.text IS NOT NULL
          AND trim(c.text) <> ''
          AND c.{EMBEDDING_PROPERTY} IS NULL
        RETURN count(c) AS total
        """
    else:
        query = """
        MATCH (c:TextChunk)
        WHERE c.text IS NOT NULL
          AND trim(c.text) <> ''
        RETURN count(c) AS total
        """

    with driver.session() as session:
        return session.run(query).single()["total"]


# ============================================================
# Leer chunks desde Neo4j
# ============================================================

def fetch_chunks(skip=0, limit=FETCH_LIMIT):
    if ONLY_MISSING:
        query = f"""
        MATCH (c:TextChunk)
        WHERE c.text IS NOT NULL
          AND trim(c.text) <> ''
          AND c.{EMBEDDING_PROPERTY} IS NULL
        RETURN
            c.id AS id,
            c.text AS text
        ORDER BY c.id
        SKIP $skip
        LIMIT $limit
        """
    else:
        query = """
        MATCH (c:TextChunk)
        WHERE c.text IS NOT NULL
          AND trim(c.text) <> ''
        RETURN
            c.id AS id,
            c.text AS text
        ORDER BY c.id
        SKIP $skip
        LIMIT $limit
        """

    chunks = []

    with driver.session() as session:
        result = session.run(query, skip=skip, limit=limit)

        for record in result:
            chunks.append({
                "id": record["id"],
                "text": clean_text(record["text"]),
            })

    return chunks

# ============================================================
# Generar embeddings
# ============================================================

def generate_embeddings(model, chunks):
    texts = [chunk["text"] for chunk in chunks]

    vectors = model.encode(
        texts,
        batch_size=ENCODE_BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    rows = []

    for chunk, vector in zip(chunks, vectors):
        vector = np.asarray(vector, dtype=np.float32).tolist()

        rows.append({
            "id": chunk["id"],
            "embedding": vector
        })

    return rows


# ============================================================
# Guardar embeddings en Neo4j
# ============================================================

def write_embeddings(rows, dimension):
    query = f"""
    UNWIND $rows AS row

    MATCH (c:TextChunk {{id: row.id}})
    SET c.{EMBEDDING_PROPERTY} = row.embedding,
        c.embedding_model = $model_name,
        c.embedding_dimensions = $dimension
    """

    with driver.session() as session:
        for part in batch(rows, WRITE_BATCH_SIZE):
            session.run(
                query,
                rows=part,
                model_name=MODEL_NAME,
                dimension=dimension
            )


# ============================================================
# Resumen de verificación
# ============================================================

def print_summary():
    query = f"""
    MATCH (c:TextChunk)
    RETURN
        count(c) AS total_chunks,
        count(c.{EMBEDDING_PROPERTY}) AS chunks_with_embedding
    """

    with driver.session() as session:
        record = session.run(query).single()

    total_chunks = record["total_chunks"]
    chunks_with_embedding = record["chunks_with_embedding"]

    print("\n✅ Resumen:")
    print(f"Total de TextChunk: {total_chunks}")
    print(f"TextChunk con embedding: {chunks_with_embedding}")

    if total_chunks > 0:
        percent = (chunks_with_embedding / total_chunks) * 100
        print(f"Cobertura de embeddings: {percent:.2f}%")

# ============================================================
# Probar búsqueda vectorial
# ============================================================

def test_vector_search(model):
    query_text = "unidades litoestratigráficas constituídas por arenito"

    query_embedding = model.encode(
        query_text,
        normalize_embeddings=True
    ).astype(np.float32).tolist()

    query = """
    CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
    YIELD node, score

    RETURN
        node.id AS chunk_id,
        score,
        left(node.text, 500) AS text
    ORDER BY score DESC
    """

    with driver.session() as session:
        result = session.run(
            query,
            index_name=VECTOR_INDEX_NAME,
            top_k=5,
            embedding=query_embedding
        )

        print("\n✅ Prueba de búsqueda vectorial:")
        print(f"Consulta: {query_text}\n")

        for record in result:
            print("-" * 80)
            print(f"chunk_id: {record['chunk_id']}")
            print(f"score: {record['score']:.4f}")
            print(f"text: {record['text']}")


# ============================================================
# Ejecución principal
# ============================================================

def main():
    model, dimension = load_embedding_model()

    if RESET_EMBEDDINGS:
        reset_embeddings()

    create_vector_index(dimension)

    total_pending = count_pending_chunks()
    print(f"\nChunks pendientes por procesar: {total_pending}")

    if total_pending == 0:
        print("No hay chunks pendientes. No se generaron nuevos embeddings.")
        print_summary()
        test_vector_search(model)
        return

    processed = 0
    skip = 0

    while True:
        chunks = fetch_chunks(skip=skip, limit=FETCH_LIMIT)

        if not chunks:
            break

        print(f"\nProcesando lote de chunks: {len(chunks)}")

        rows = generate_embeddings(model, chunks)
        write_embeddings(rows, dimension)

        processed += len(chunks)

        print(f"Chunks procesados hasta ahora: {processed}")

        if ONLY_MISSING:
            # No se incrementa skip porque los chunks procesados dejan de cumplir
            # la condición c.embedding IS NULL.
            skip = 0
        else:
            skip += FETCH_LIMIT

    print_summary()
    test_vector_search(model)

    print("\n✅ Proceso finalizado correctamente.")


if __name__ == "__main__":
    try:
        main()
    finally:
        driver.close()