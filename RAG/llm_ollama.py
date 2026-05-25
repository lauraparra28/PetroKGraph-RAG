from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os, requests

load_dotenv()

def load_llm_with_api_key(model_name="gpt-4o-mini"): #gpt-4.1-2025-04-14 #gpt-4.1-mini-2025-04-14
    return ChatOpenAI(
        model_name=model_name,
        temperature=0.0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )   

def load_llm(model_name="llama3:8b"): # MI PC: deepseek-r1:1.5b  qwen2.5:1.5b gemma3:1b
    return OllamaLLM(
        model=model_name,
        temperature=0.0,
        max_tokens=128,
        base_url="http://127.0.0.1:11434"
    )
    
def load_cypher_llm(model_cypher="gpt-4o-mini"): #gpt-4.1-2025-04-14
    return ChatOpenAI(
        model_name=model_cypher,
        temperature=0.0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )  
    
def load_cypher_llm_ollama(model_cypher="qwen2.5-coder:7b"): #qwen2.5:7b
    return OllamaLLM(
        model=model_cypher,
        temperature=0.0,
        max_tokens=512,
        base_url="https://epistolic-noninstrumentally-ardis.ngrok-free.dev"  # http://192.168.128.1:11500
    )