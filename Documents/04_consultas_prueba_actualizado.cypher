// ============================================================
// 04_consultas_prueba_actualizado.cypher
// Consultas de verificación para la capa documental en Neo4j
// Modelo actualizado SIN EntityMention
//
// Estructura esperada:
//
// (:Document)-[:HAS_SENTENCE]->(:Sentence)
// (:Sentence)-[:MENTIONS_ENTITY {text, ner_label, grafo, local_id, start_char, end_char}]->(:KGEntity)
//
// (:Document)-[:HAS_CHUNK]->(:TextChunk)
// (:TextChunk)-[:CONTAINS_SENTENCE]->(:Sentence)
// (:TextChunk)-[:MENTIONS_ENTITY]->(:KGEntity)
// ============================================================


// ============================================================
// 0. Constraints e índices base
// ============================================================

CREATE CONSTRAINT document_id IF NOT EXISTS
FOR (d:Document) REQUIRE d.id IS UNIQUE;


// ------------------------------------------------------------

CREATE CONSTRAINT sentence_id IF NOT EXISTS
FOR (s:Sentence) REQUIRE s.id IS UNIQUE;


// ------------------------------------------------------------

CREATE CONSTRAINT textchunk_id IF NOT EXISTS
FOR (c:TextChunk) REQUIRE c.id IS UNIQUE;


// ------------------------------------------------------------

CREATE INDEX kgentity_local_id IF NOT EXISTS
FOR (e:KGEntity) ON (e.local_id);


// ------------------------------------------------------------

CREATE INDEX textchunk_document_id IF NOT EXISTS
FOR (c:TextChunk) ON (c.document_id);


// ------------------------------------------------------------

CREATE INDEX textchunk_dataset_split IF NOT EXISTS
FOR (c:TextChunk) ON (c.dataset_split);


// ============================================================
// 1. Preparación de nodos existentes de PetroKGraph
// ============================================================
// Ejecuta este bloque solo si los nodos importados desde RDF/OWL
// tienen propiedad uri y todavía no tienen etiqueta KGEntity/local_id.

MATCH (n)
WHERE n.uri IS NOT NULL
SET n:KGEntity,
    n.local_id = coalesce(n.local_id, split(n.uri, '#')[-1]);


// ------------------------------------------------------------
// Verificar KGEntity con local_id.

MATCH (e:KGEntity)
WHERE e.local_id IS NOT NULL
RETURN
    e.local_id AS local_id,
    e.uri AS uri,
    labels(e) AS labels
LIMIT 20;


// ============================================================
// 2. Verificación general de nodos cargados
// ============================================================

MATCH (d:Document)
RETURN count(d) AS total_documents;


// ------------------------------------------------------------

MATCH (s:Sentence)
RETURN count(s) AS total_sentences;


// ------------------------------------------------------------

MATCH (c:TextChunk)
RETURN count(c) AS total_chunks;


// ------------------------------------------------------------

MATCH (e:KGEntity)
RETURN count(e) AS total_kg_entities;


// ============================================================
// 3. Verificación general de relaciones
// ============================================================

MATCH (:Document)-[r:HAS_SENTENCE]->(:Sentence)
RETURN count(r) AS total_has_sentence;


// ------------------------------------------------------------

MATCH (:Sentence)-[r:MENTIONS_ENTITY]->(:KGEntity)
RETURN count(r) AS total_sentence_mentions_entity;


// ------------------------------------------------------------

MATCH (:Document)-[r:HAS_CHUNK]->(:TextChunk)
RETURN count(r) AS total_has_chunk;


// ------------------------------------------------------------

MATCH (:TextChunk)-[r:CONTAINS_SENTENCE]->(:Sentence)
RETURN count(r) AS total_contains_sentence;


// ------------------------------------------------------------

MATCH (:TextChunk)-[r:MENTIONS_ENTITY]->(:KGEntity)
RETURN count(r) AS total_chunk_mentions_entity;


// ============================================================
// 4. Verificar documentos y sentencias de ejemplo
// ============================================================

MATCH (d:Document)-[:HAS_SENTENCE]->(s:Sentence)
RETURN
    d.id AS document_id,
    d.volume_file AS volume_file,
    d.article_file AS article_file,
    d.dataset_split AS dataset_split,
    s.id AS sentence_id,
    s.sentence_number AS sentence_number,
    s.text AS sentence_text
ORDER BY document_id, sentence_number
LIMIT 20;


// ============================================================
// 5. Verificar sentencias enlazadas directamente con KGEntity
// ============================================================

MATCH (s:Sentence)-[r:MENTIONS_ENTITY]->(e:KGEntity)
RETURN
    s.id AS sentence_id,
    s.sentence_number AS sentence_number,
    s.text AS sentence_text,
    r.mention_id AS mention_id,
    r.text AS mention_text,
    r.ner_label AS ner_label,
    r.grafo AS grafo,
    r.local_id AS relation_local_id,
    e.local_id AS kg_local_id,
    labels(e) AS kg_labels
ORDER BY sentence_id, mention_id
LIMIT 30;


// ------------------------------------------------------------
// Conteo de menciones enlazadas por clase NER.

MATCH (:Sentence)-[r:MENTIONS_ENTITY]->(:KGEntity)
RETURN
    r.ner_label AS ner_label,
    count(r) AS total_mentions,
    count(DISTINCT r.local_id) AS distinct_entities
ORDER BY total_mentions DESC;


// ------------------------------------------------------------
// Sentencias que no quedaron conectadas a ninguna entidad.

MATCH (s:Sentence)
WHERE NOT (s)-[:MENTIONS_ENTITY]->(:KGEntity)
RETURN
    s.id AS sentence_id,
    s.sentence_number AS sentence_number,
    s.text AS sentence_text
ORDER BY sentence_id
LIMIT 30;


// ============================================================
// 6. Verificar chunks de ejemplo
// ============================================================

MATCH (d:Document)-[:HAS_CHUNK]->(c:TextChunk)
RETURN
    d.id AS document_id,
    c.id AS chunk_id,
    c.sentence_start_number AS sentence_start_number,
    c.sentence_end_number AS sentence_end_number,
    c.num_sentences AS num_sentences,
    c.dataset_split AS dataset_split,
    left(c.text, 1000) AS chunk_preview
ORDER BY document_id, sentence_start_number
LIMIT 20;


// ------------------------------------------------------------
// Verificar que cada chunk contenga sentencias.

MATCH (c:TextChunk)-[:CONTAINS_SENTENCE]->(s:Sentence)
RETURN
    c.id AS chunk_id,
    c.sentence_start_number AS chunk_start,
    c.sentence_end_number AS chunk_end,
    count(s) AS total_sentences_in_chunk,
    collect(s.id)[0..10] AS sentence_ids
ORDER BY chunk_id
LIMIT 20;


// ============================================================
// 7. Verificar chunks conectados con entidades del KG
// ============================================================

MATCH (c:TextChunk)-[:MENTIONS_ENTITY]->(e:KGEntity)
RETURN
    c.id AS chunk_id,
    c.dataset_split AS dataset_split,
    c.sentence_start_number AS start_sentence,
    c.sentence_end_number AS end_sentence,
    collect(DISTINCT e.local_id)[0..30] AS mentioned_entities,
    left(c.text, 1000) AS chunk_preview
ORDER BY chunk_id
LIMIT 20;


// ------------------------------------------------------------
// Chunks sin entidades enlazadas.

MATCH (c:TextChunk)
WHERE NOT (c)-[:MENTIONS_ENTITY]->(:KGEntity)
RETURN
    c.id AS chunk_id,
    c.dataset_split AS dataset_split,
    c.sentence_start_number AS start_sentence,
    c.sentence_end_number AS end_sentence,
    left(c.text, 1000) AS chunk_preview
ORDER BY chunk_id
LIMIT 30;


// ============================================================
// 8. Trazabilidad completa: documento -> chunk -> sentencia -> KGEntity
// ============================================================

MATCH (d:Document)-[:HAS_CHUNK]->(c:TextChunk)-[:CONTAINS_SENTENCE]->(s:Sentence)
OPTIONAL MATCH (s)-[r:MENTIONS_ENTITY]->(e:KGEntity)
RETURN
    d.id AS document_id,
    c.id AS chunk_id,
    s.id AS sentence_id,
    s.sentence_number AS sentence_number,
    s.text AS sentence_text,
    collect(DISTINCT {
        mention_id: r.mention_id,
        mention: r.text,
        ner_label: r.ner_label,
        grafo: r.grafo,
        entity: e.local_id
    }) AS linked_mentions
ORDER BY document_id, c.sentence_start_number, sentence_number
LIMIT 30;


// ============================================================
// 9. Consultar evidencia textual asociada a una entidad del grafo
// ============================================================
// Cambia el valor por una entidad existente en tu grafo.

:param entity_local_id => 'sandstone';


// ------------------------------------------------------------
// Sentencias donde aparece la entidad.

MATCH (e:KGEntity {local_id: $entity_local_id})
MATCH (e)<-[r:MENTIONS_ENTITY]-(s:Sentence)
RETURN
    e.local_id AS entity,
    r.text AS mention_text,
    r.ner_label AS ner_label,
    r.grafo AS grafo,
    s.id AS sentence_id,
    s.sentence_number AS sentence_number,
    s.text AS sentence_text
ORDER BY sentence_id
LIMIT 30;


// ------------------------------------------------------------
// Chunks que mencionan la entidad.

MATCH (e:KGEntity {local_id: $entity_local_id})
MATCH (e)<-[:MENTIONS_ENTITY]-(c:TextChunk)
RETURN
    e.local_id AS entity,
    c.id AS chunk_id,
    c.dataset_split AS dataset_split,
    c.sentence_start_number AS start_sentence,
    c.sentence_end_number AS end_sentence,
    left(c.text, 1200) AS chunk_text
ORDER BY chunk_id
LIMIT 30;


// ------------------------------------------------------------
// Entidad -> sentencias -> chunks que contienen esas sentencias.

MATCH (e:KGEntity {local_id: $entity_local_id})
MATCH (e)<-[r:MENTIONS_ENTITY]-(s:Sentence)<-[:CONTAINS_SENTENCE]-(c:TextChunk)
RETURN
    e.local_id AS entity,
    r.text AS mention_text,
    r.ner_label AS ner_label,
    s.id AS sentence_id,
    c.id AS chunk_id,
    left(c.text, 1200) AS chunk_text
ORDER BY chunk_id, sentence_id
LIMIT 30;


// ============================================================
// 10. Distribución por partición experimental
// ============================================================

MATCH (d:Document)
RETURN
    d.dataset_split AS dataset_split,
    count(d) AS total_documents
ORDER BY dataset_split;


// ------------------------------------------------------------

MATCH (s:Sentence)
RETURN
    s.dataset_split AS dataset_split,
    count(s) AS total_sentences
ORDER BY dataset_split;


// ------------------------------------------------------------

MATCH (c:TextChunk)
RETURN
    c.dataset_split AS dataset_split,
    count(c) AS total_chunks
ORDER BY dataset_split;


// ============================================================
// 11. Entidades del KG más mencionadas en sentencias y chunks
// ============================================================

MATCH (:Sentence)-[r:MENTIONS_ENTITY]->(e:KGEntity)
RETURN
    e.local_id AS entity,
    collect(DISTINCT r.text)[0..10] AS mention_forms,
    count(r) AS sentence_mentions
ORDER BY sentence_mentions DESC
LIMIT 30;


// ------------------------------------------------------------

MATCH (:TextChunk)-[:MENTIONS_ENTITY]->(e:KGEntity)
RETURN
    e.local_id AS entity,
    count(*) AS chunk_mentions
ORDER BY chunk_mentions DESC
LIMIT 30;


// ============================================================
// 12. Verificar embeddings en TextChunk
// ============================================================

MATCH (c:TextChunk)
RETURN
    count(c) AS total_chunks,
    count(c.embedding) AS chunks_with_embedding;


// ------------------------------------------------------------

MATCH (c:TextChunk)
WHERE c.embedding IS NOT NULL
RETURN
    c.id AS chunk_id,
    c.embedding_model AS embedding_model,
    c.embedding_dimensions AS embedding_dimensions,
    size(c.embedding) AS vector_size,
    left(c.text, 700) AS chunk_preview
ORDER BY chunk_id
LIMIT 20;


// ------------------------------------------------------------
// Verificar que el índice vectorial exista y esté online.

SHOW INDEXES
YIELD name, type, entityType, labelsOrTypes, properties, state
WHERE name = 'textchunk_embedding'
RETURN
    name,
    type,
    entityType,
    labelsOrTypes,
    properties,
    state;


// ============================================================
// 13. Crear índice full-text para pruebas sin embeddings
// ============================================================

CREATE FULLTEXT INDEX textchunk_text_fulltext IF NOT EXISTS
FOR (c:TextChunk)
ON EACH [c.text];


// ------------------------------------------------------------
// Búsqueda textual simple.

CALL db.index.fulltext.queryNodes('textchunk_text_fulltext', 'arenito')
YIELD node, score
RETURN
    node.id AS chunk_id,
    score,
    node.dataset_split AS dataset_split,
    left(node.text, 1200) AS chunk_text
ORDER BY score DESC
LIMIT 10;


// ============================================================
// 14. Búsqueda textual + entidades mencionadas
// ============================================================

CALL db.index.fulltext.queryNodes('textchunk_text_fulltext', 'arenito')
YIELD node AS chunk, score

OPTIONAL MATCH (chunk)-[:MENTIONS_ENTITY]->(e:KGEntity)

RETURN
    chunk.id AS chunk_id,
    score,
    chunk.dataset_split AS dataset_split,
    collect(DISTINCT e.local_id)[0..30] AS mentioned_entities,
    left(chunk.text, 1200) AS chunk_text
ORDER BY score DESC
LIMIT 10;


// ============================================================
// 15. Búsqueda textual + sentencias + entidades
// ============================================================

CALL db.index.fulltext.queryNodes('textchunk_text_fulltext', 'arenito')
YIELD node AS chunk, score

OPTIONAL MATCH (chunk)-[:CONTAINS_SENTENCE]->(s:Sentence)
OPTIONAL MATCH (s)-[r:MENTIONS_ENTITY]->(e:KGEntity)

RETURN
    chunk.id AS chunk_id,
    score,
    left(chunk.text, 1200) AS chunk_text,
    collect(DISTINCT {
        sentence_id: s.id,
        sentence_number: s.sentence_number,
        mention: r.text,
        ner_label: r.ner_label,
        entity: e.local_id
    })[0..50] AS sentence_level_entities
ORDER BY score DESC
LIMIT 10;


// ============================================================
// 16. Búsqueda vectorial
// ============================================================
// Requiere el parámetro $query_embedding.
// El embedding de la pregunta se genera en Python, no directamente en Cypher.
//
// Ejemplo conceptual:
// :param query_embedding => [0.0123, -0.0441, ...]

CALL db.index.vector.queryNodes('textchunk_embedding', 5, $query_embedding)
YIELD node AS chunk, score
RETURN
    chunk.id AS chunk_id,
    score,
    chunk.dataset_split AS dataset_split,
    left(chunk.text, 1200) AS chunk_text
ORDER BY score DESC;


// ============================================================
// 17. Búsqueda vectorial + entidades mencionadas
// ============================================================
// También requiere $query_embedding.

CALL db.index.vector.queryNodes('textchunk_embedding', 5, $query_embedding)
YIELD node AS chunk, score

OPTIONAL MATCH (chunk)-[:MENTIONS_ENTITY]->(e:KGEntity)

RETURN
    chunk.id AS chunk_id,
    score,
    chunk.dataset_split AS dataset_split,
    collect(DISTINCT e.local_id)[0..30] AS mentioned_entities,
    left(chunk.text, 1200) AS chunk_text
ORDER BY score DESC;


// ============================================================
// 18. Búsqueda híbrida por vector + vecindario del grafo
// ============================================================
// También requiere $query_embedding.

CALL db.index.vector.queryNodes('textchunk_embedding', 5, $query_embedding)
YIELD node AS chunk, score

OPTIONAL MATCH (chunk)-[:MENTIONS_ENTITY]->(e:KGEntity)
OPTIONAL MATCH (e)-[rel]-(neighbor:KGEntity)

RETURN
    chunk.id AS chunk_id,
    score,
    left(chunk.text, 1200) AS chunk_text,
    collect(DISTINCT e.local_id)[0..30] AS mentioned_entities,
    collect(DISTINCT {
        entity: e.local_id,
        relation: type(rel),
        neighbor: neighbor.local_id
    })[0..50] AS graph_context
ORDER BY score DESC;


// ============================================================
// 19. Diagnóstico de calidad de carga
// ============================================================

CALL {
    MATCH (d:Document)
    RETURN count(d) AS total_documents
}
CALL {
    MATCH (s:Sentence)
    RETURN count(s) AS total_sentences
}
CALL {
    MATCH (s:Sentence)-[r:MENTIONS_ENTITY]->(:KGEntity)
    RETURN count(r) AS total_sentence_entity_links
}
CALL {
    MATCH (s:Sentence)-[:MENTIONS_ENTITY]->(:KGEntity)
    RETURN count(DISTINCT s) AS sentences_with_entities
}
CALL {
    MATCH (c:TextChunk)
    RETURN count(c) AS total_chunks
}
CALL {
    MATCH (c:TextChunk)-[:MENTIONS_ENTITY]->(:KGEntity)
    RETURN count(DISTINCT c) AS chunks_with_entities
}
CALL {
    MATCH (c:TextChunk)
    WHERE c.embedding IS NOT NULL
    RETURN count(c) AS chunks_with_embeddings
}
RETURN
    total_documents,
    total_sentences,
    total_sentence_entity_links,
    sentences_with_entities,
    total_chunks,
    chunks_with_entities,
    chunks_with_embeddings,
    CASE
        WHEN total_sentences = 0 THEN 0
        ELSE round(100.0 * sentences_with_entities / total_sentences, 2)
    END AS pct_sentences_with_entities,
    CASE
        WHEN total_chunks = 0 THEN 0
        ELSE round(100.0 * chunks_with_entities / total_chunks, 2)
    END AS pct_chunks_with_entities,
    CASE
        WHEN total_chunks = 0 THEN 0
        ELSE round(100.0 * chunks_with_embeddings / total_chunks, 2)
    END AS pct_chunks_with_embeddings;


// ============================================================
// 20. Diagnóstico de relaciones antiguas
// ============================================================
// Debe retornar cero si ya estás usando el modelo nuevo.

MATCH (m:EntityMention)
RETURN count(m) AS old_entitymention_nodes;


// ------------------------------------------------------------

MATCH (:Sentence)-[r:HAS_MENTION]->(:EntityMention)
RETURN count(r) AS old_has_mention_relations;


// ------------------------------------------------------------

MATCH (:EntityMention)-[r:REFERS_TO]->(:KGEntity)
RETURN count(r) AS old_refers_to_relations;


// ============================================================
// 21. Limpieza opcional del modelo anterior
// ============================================================
// Ejecutar solo si estás seguro de que ya no necesitas EntityMention.
// Por seguridad, está comentado.
//
// MATCH (m:EntityMention)
// DETACH DELETE m;
// ============================================================
