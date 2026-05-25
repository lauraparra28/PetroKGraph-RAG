from neo4j import GraphDatabase
import numpy as np

# ==========================
# 1) Conexión a Neo4j
# ==========================
URI = "bolt://localhost:7687"   # Cambia si usas Aura o puerto distinto
USER = "neo4j"
PASSWORD = "diripar8$"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
print("✅ Successfully connection to Neo4j Graph")

# 📌 Lista de labels y relaciones
NODE_LABELS = [
    "Resource",
    "Class",
    "well",
    "field",
    "basin",
    "lithostratigraphic_unit",
    "geological_time_interval",
    "geological_structure",
    "textura"
]

REL_TYPES = [
    "located_in",
    "constituted_by",
    "part_of",
    "crosses",
    "has_age",
    "carrier_of",
    "participates_in"
]

# ==========================
# 2) Proyectar el grafo en memoria
# ==========================

def project_graph():
    print("📌 Creando proyección del grafo...")
    query = """
    CALL gds.graph.project(
        'miniKGraph',
        $node_labels,
        $rel_types
    )
    """
    with driver.session() as session:
        session.run("CALL gds.graph.drop('miniKGraph', false) YIELD graphName")  # Limpia si ya existe
        session.run(query, node_labels=NODE_LABELS, rel_types=REL_TYPES)
    print("✅ Grafo proyectado en memoria.")
    
# ==========================
# 4) Ejecutar Node2Vec y guardar embeddings en los nodos
# ==========================

def run_node2vec_and_store():
    print("📌 Ejecutando Node2Vec...")
    query = """
    CALL gds.node2vec.stream('miniKGraph', {
      embeddingDimension: 512,
      randomSeed: 42
    })
    YIELD nodeId, embedding
    WITH gds.util.asNode(nodeId) AS n, embedding
    SET n.embedding = embedding
    """
    with driver.session() as session:
        session.run(query)
    print("✅ Embeddings generados y guardados en los nodos.")

# =================================
# 4) Extraer embeddings a NumPy
# =================================
def extract_embeddings():
    query = """
    MATCH (n)
    WHERE n.embedding IS NOT NULL
    RETURN elementId(n) AS nodeElementId, n.embedding AS embedding
    ORDER BY nodeElementId
    """
    with driver.session() as session:
        result = session.run(query)
        node_ids = []
        embeddings = []
        for record in result:
            node_ids.append(record["nodeElementId"])
            embeddings.append(record["embedding"])
    embeddings_array = np.array(embeddings, dtype=np.float32)
    print("✅ Embeddings extraídos:", embeddings_array.shape)
    return node_ids, embeddings_array

# 📌 Ejecución
if __name__ == "__main__":
    project_graph()
    run_node2vec_and_store()
    node_ids, embeddings_array = extract_embeddings()

    # Guardar como archivo .npy
    np.save("embeddings.npy", embeddings_array)
    print("💾 Embeddings guardados en 'embeddings.npy'")

    print(f"✅ Extracción completa: {len(node_ids)} nodos con embeddings")
    print("IDs de nodos:", node_ids[:3])  # Muestra los primeros 3 IDs
    print("Primer embedding:", embeddings_array[0])