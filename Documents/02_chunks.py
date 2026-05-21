from collections import defaultdict
from neo4j import GraphDatabase

# ============================================================
# Parámetros de construcción de chunks
# ============================================================

CHUNK_SIZE = 5          # Número de sentencias por chunk
CHUNK_OVERLAP = 1       # Sentencias compartidas entre chunks consecutivos
BATCH_SIZE = 500

# Dejar en False para no borrar chunks previos accidentalmente.
# Cambiar a True solo si quieres reconstruir todos los chunks.
RESET_CHUNKS = False


# ============================================================
# Conexión a Neo4j
# ============================================================

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "diripar8$"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ============================================================
# Utilidades
# ============================================================

def batch(rows, size=BATCH_SIZE):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def clean_text(text):
    if text is None:
        return ""
    return " ".join(str(text).split())


# ============================================================
# Crear restricciones e índices
# ============================================================

def create_constraints():
    queries = [
        """
        CREATE CONSTRAINT textchunk_id IF NOT EXISTS
        FOR (c:TextChunk) REQUIRE c.id IS UNIQUE
        """,
        """
        CREATE INDEX textchunk_document_id IF NOT EXISTS
        FOR (c:TextChunk) ON (c.document_id)
        """,
        """
        CREATE INDEX textchunk_dataset_split IF NOT EXISTS
        FOR (c:TextChunk) ON (c.dataset_split)
        """
    ]

    with driver.session() as session:
        for query in queries:
            session.run(query)


# ============================================================
# Opcional: borrar chunks anteriores
# ============================================================

def reset_chunks():
    query = """
    MATCH (c:TextChunk)
    DETACH DELETE c
    """

    with driver.session() as session:
        session.run(query)


# ============================================================
# Leer sentencias desde Neo4j
# ============================================================

def fetch_sentences():
    query = """
    MATCH (d:Document)-[:HAS_SENTENCE]->(s:Sentence)
    RETURN
        d.id AS document_id,
        s.id AS sentence_id,
        s.text AS text,
        s.sentence_number AS sentence_number,
        s.dataset_split AS dataset_split
    ORDER BY document_id, sentence_number
    """

    sentences = []

    with driver.session() as session:
        result = session.run(query)

        for record in result:
            sentence_number = record["sentence_number"]

            if sentence_number is None:
                continue

            sentences.append({
                "document_id": record["document_id"],
                "sentence_id": record["sentence_id"],
                "text": clean_text(record["text"]),
                "sentence_number": int(sentence_number),
                "dataset_split": record["dataset_split"],
            })

    return sentences


# ============================================================
# Construir chunks por documento
# ============================================================

def build_chunks(sentences):
    sentences_by_document = defaultdict(list)

    for sentence in sentences:
        sentences_by_document[sentence["document_id"]].append(sentence)

    chunks = []

    step = CHUNK_SIZE - CHUNK_OVERLAP

    if step <= 0:
        raise ValueError("CHUNK_OVERLAP debe ser menor que CHUNK_SIZE.")

    for document_id, document_sentences in sentences_by_document.items():
        document_sentences = sorted(
            document_sentences,
            key=lambda x: x["sentence_number"]
        )

        for start_idx in range(0, len(document_sentences), step):
            group = document_sentences[start_idx:start_idx + CHUNK_SIZE]

            if not group:
                continue

            sentence_start_number = group[0]["sentence_number"]
            sentence_end_number = group[-1]["sentence_number"]

            sentence_start_id = group[0]["sentence_id"]
            sentence_end_id = group[-1]["sentence_id"]

            chunk_text = " ".join(
                sentence["text"]
                for sentence in group
                if sentence["text"]
            )

            if not chunk_text.strip():
                continue

            chunk_id = (
                f"{document_id}::chunk::"
                f"{sentence_start_number}-{sentence_end_number}"
            )

            chunks.append({
                "id": chunk_id,
                "document_id": document_id,
                "text": chunk_text,
                "sentence_start_number": sentence_start_number,
                "sentence_end_number": sentence_end_number,
                "sentence_start_id": sentence_start_id,
                "sentence_end_id": sentence_end_id,
                "num_sentences": len(group),
                "dataset_split": group[0]["dataset_split"],
                "source_sentence_ids": [
                    sentence["sentence_id"]
                    for sentence in group
                ],
            })

    return chunks


# ============================================================
# Cargar chunks a Neo4j
# ============================================================

def load_chunks(chunks):
    query = """
    UNWIND $rows AS row

    MATCH (d:Document {id: row.document_id})

    MERGE (c:TextChunk {id: row.id})
    SET c.document_id = row.document_id,
        c.text = row.text,
        c.sentence_start_number = row.sentence_start_number,
        c.sentence_end_number = row.sentence_end_number,
        c.sentence_start_id = row.sentence_start_id,
        c.sentence_end_id = row.sentence_end_id,
        c.num_sentences = row.num_sentences,
        c.dataset_split = row.dataset_split,
        c.source_sentence_ids = row.source_sentence_ids

    MERGE (d)-[:HAS_CHUNK]->(c)

    WITH c, row
    UNWIND row.source_sentence_ids AS sentence_id
    MATCH (s:Sentence {id: sentence_id})
    MERGE (c)-[:CONTAINS_SENTENCE]->(s)
    """

    with driver.session() as session:
        for rows in batch(chunks):
            session.run(query, rows=rows)


# ============================================================
# Conectar chunks con entidades del KG
# ============================================================

def link_chunks_to_entities(chunks):
    query = """
    UNWIND $rows AS row

    MATCH (c:TextChunk {id: row.id})

    UNWIND row.source_sentence_ids AS sentence_id
    MATCH (:Sentence {id: sentence_id})-[:MENTIONS_ENTITY]->(e:KGEntity)

    MERGE (c)-[:MENTIONS_ENTITY]->(e)
    """

    with driver.session() as session:
        for rows in batch(chunks):
            session.run(query, rows=rows)


# ============================================================
# Reporte de verificación
# ============================================================

def print_summary():
    queries = {
        "documents": "MATCH (d:Document) RETURN count(d) AS total",
        "sentences": "MATCH (s:Sentence) RETURN count(s) AS total",
        "chunks": "MATCH (c:TextChunk) RETURN count(c) AS total",
        "chunks_with_entities": """
            MATCH (c:TextChunk)-[:MENTIONS_ENTITY]->(:KGEntity)
            RETURN count(DISTINCT c) AS total
        """,
        "chunk_entity_links": """
            MATCH (:TextChunk)-[r:MENTIONS_ENTITY]->(:KGEntity)
            RETURN count(r) AS total
        """
    }

    with driver.session() as session:
        print("\nResumen de carga:")

        for name, query in queries.items():
            result = session.run(query).single()
            print(f"{name}: {result['total']}")


# ============================================================
# Ejecución principal
# ============================================================

def main():
    print("💪 Creando restricciones e índices...")
    create_constraints()

    if RESET_CHUNKS:
        print("Eliminando chunks anteriores...")
        reset_chunks()

    print("🖥️ Leyendo sentencias desde Neo4j...")
    sentences = fetch_sentences()
    print(f"✅ Sentencias leídas: {len(sentences)}")

    if not sentences:
        print("No se encontraron sentencias. Ejecuta primero 01_cargar_sentencias_menciones.py")
        return

    print("🏭 Construyendo chunks...")
    chunks = build_chunks(sentences)
    print(f"✅ Chunks construidos: {len(chunks)}")

    if not chunks:
        print("✖ No se construyeron chunks.")
        return

    print("💾⬆️ Cargando chunks en Neo4j...")
    load_chunks(chunks)

    print("🔄 Conectando chunks con entidades del grafo...")
    link_chunks_to_entities(chunks)

    print_summary()

    print("\n✅ Proceso finalizado correctamente.")


if __name__ == "__main__":
    try:
        main()
    finally:
        driver.close()