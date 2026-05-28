# 🧠 PetroKGraph-RAG Application using OWL Knowledge Graph

## 🔍 Overview
This project presents the design, implementation, and evaluation of the proposed system. It details the methodology for constructing a new domain-specific, question-answering dataset from the knowledge graph and describes the hybrid architecture, which synergizes high-precision structured Cypher queries with flexible semantic similarity search. It uses:

- Neo4j with RDF plugins to store and query the ontology.
- Cypher queries to extract triples.
- Large Language Models (LLMs) to generate answers based on the retrieved context.
- LangChain to orchestrate the entire pipeline.
- Gradio for the user interface (in future).
- The project is designed to be modular and extensible, allowing for easy integration of new components or modifications to existing ones.

## 🏛️ Architecture
The RAG pipeline consists of the following key components:
1. **Knowledge Graph (KG)**: The structured data is stored in an OWL format, which is then imported into Neo4j using RDF plugins.
2. **Retrieval**: Cypher queries are used to extract relevant triples from the KG
3. **Generation**: The retrieved triples are fed into an LLM to generate a coherent answer.
4. **Orchestration**: LangChain is used to manage the flow of data between
the components and ensure that the retrieval and generation steps are executed in the correct order.
5. **Docker**: The entire application is containerized using Docker, making it easy to deploy and scale.

## 🛠️ Requirements

Create a virtual environment Ubuntu and activate it:

```bash
conda create -n PetroGraphRAG python=3.11 -y
conda activate PetroGraphRAG
```

Install the dependencies with:

```bash
pip install -r requirements.txt
```

## 🗄️ Database Setup

### Neo4j

You can use the provided `docker-compose.yml` file to start a Neo4j container easily. Make sure Docker is installed on your system.

1. Copy the example `docker-compose-may.yml` file to your project directory.
2. Start the Neo4j container with:

```bash
docker compose -p petrokgraph-documents -f docker-compose-may.yml up -d
```

3. Access Neo4j at [http://localhost:7474](http://localhost:7474) with the default username and password (`neo4j` / `neo4j`). Change the password on first login.

Make sure to enable the RDF plugin if required for your use case.

## 🚀 Running the Application
To run the application, execute the following command in your terminal:

- For calculate execution accuracy in text-to-cypher approach, using tag for selecting the type of question dataset:

```bash

python evaluate_with_gold_cypher.py --ragas --tag definition

```

- For calculate RAGAS metric in hybrid approach, also using tag for selecting the type of question dataset:

```bash
python evaluate_hybrid_with_ragas.py --ragas --tag definition 

```