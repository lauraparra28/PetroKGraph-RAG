from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain.prompts import PromptTemplate

def build_rag_chain(
    llm, 
    cypher_llm, 
    graph: Neo4jGraph,
    cypher_prompt: PromptTemplate,
    qa_prompt: PromptTemplate
    ):
    return GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        qa_prompt=qa_prompt,
        cypher_prompt=cypher_prompt,
        cypher_llm=cypher_llm,
        return_intermediate_steps=True, 
        allow_dangerous_requests=True, 
        verbose=True,
        top_k=10,
    )
