from langchain_neo4j import Neo4jGraph
from llm_ollama import load_cypher_llm, load_llm_with_api_key, load_cypher_llm_ollama
from rag_chain_neo4j import build_rag_chain
from utils import base_utils as bu
from langchain.prompts import PromptTemplate

# Prompt para a geração da query Cypher
CYPHER_GENERATION_TEMPLATE = bu.load_prompts()["cypher_prompt.txt"] 
CYPHER_GENERATION_PROMPT = PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)
# Prompt para a resposta da query
QA_PROMPT = bu.load_prompts()["qa_prompt.txt"] 
qa_prompt = PromptTemplate(template=QA_PROMPT, input_variables=["context", "question"], ) #from_template(QA_PROMPT)

graph = Neo4jGraph( url="bolt://localhost:7687", username="neo4j",password="diripar8$")
    
llm = load_cypher_llm() #load_llm()
print(f"🔷 Using model {llm.model_name} for QA result")
cypher_llm = load_cypher_llm() #load_cypher_llm_ollama
print(f"🔷 Using model {cypher_llm.model_name} for Generate Cypher statement")
print("✅ Successfully load LLM")

chain = build_rag_chain(
    llm=llm,
    cypher_llm=cypher_llm,
    graph=graph,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    qa_prompt=qa_prompt
)

def main():
    question = input("❓ Pergunta: ")
    out = chain.invoke({ "query": question})
    print("\n✅ Resposta:", out["result"])
      
if __name__ == "__main__":
    main()
