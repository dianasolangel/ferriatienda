import os, json
from datetime import datetime
from operator import itemgetter

import pandas as pd 
import ast

from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory

import os
import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# =========================
# 1) Embeddings & Vector DB : We get the DB
# =========================
# embedding_function = HuggingFaceEmbeddings(
#     model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# )

# vectorstore = Chroma(
#     persist_directory="./chroma_db",
#     collection_name="electric_tools_sample",
#     embedding_function=embedding_function
# )
# retriever = vectorstore.as_retriever() 

# --- Config via env (works in Docker compose & locally)
CHROMA_HOST = os.environ.get("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))


embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Cliente HTTP al servidor Chroma
chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

# Vectorstore apuntando a la colección del servidor
vectorstore = Chroma(
    client=chroma_client,
    collection_name="electric_tools_sample",
    embedding_function=embedding_function,
)

# Retriever (MMR recomendado)
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "fetch_k": 12, "lambda_mult": 0.6},
)

# =========================
# 2) LLMs via Ollama (primary + fallback)
# =========================
# When running this code inside Docker, set base_url="http://host.docker.internal:11434"
OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")

chat = ChatOllama(
    model="qwen2.5:1.5b",  #qwen2.5:3b              # good Spanish + quality
    base_url=OLLAMA_BASE,
    temperature=0.0,                  # deterministic & faster for RAG
    num_ctx=2048,
    num_predict=160,                  # cap output length to reduce latency
    keep_alive="30m",
    request_timeout=120,
)

chat_fallback = ChatOllama(
    model="qwen2.5:1.5b",             # faster fallback
    base_url=OLLAMA_BASE,
    temperature=0.0,
    num_ctx=2048,
    num_predict=140,
    keep_alive="30m",
    request_timeout=120,
)

# =========================
# 3) Prompt & Chains
# =========================
prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un asistente experto en herramientas eléctricas de ferretería. "
               "Usa el contexto proporcionado de manera natural y amable. "
               "Si no sabes, di: 'No tengo suficiente información'. "
               "Responde SIEMPRE en español neutro."),
    ("user", "Contexto:\n{context}\n\nPregunta: {question}")
])

primary_chain = prompt | chat | StrOutputParser()
fallback_chain = prompt | chat_fallback | StrOutputParser()
main_chain = primary_chain.with_fallbacks([fallback_chain])

# --- format retrieved docs into plain text
def format_docs(docs):
    # docs is a List[Document]; join only the text
    return "\n\n".join(f"- {d.page_content}" for d in docs)

rag_chain = (
    RunnableParallel({
        "context": itemgetter("question") | retriever | RunnableLambda(format_docs),
        "question": RunnablePassthrough()
    })
    | main_chain
)

# =========================
# 4) Chat history
# =========================
chat_histories = {}

def get_chat_history(session_id: str = "default") -> BaseChatMessageHistory:
    if session_id not in chat_histories:
        chat_histories[session_id] = InMemoryChatMessageHistory()
    return chat_histories[session_id]

rag_with_memory = RunnableWithMessageHistory(
    rag_chain,
    get_chat_history,
    input_messages_key="question",
    history_messages_key="history"
)

# =========================
# 5) Logging + Answer function
# =========================
def log_conversation(session_id, question, answer):
    os.makedirs("logs", exist_ok=True)
    log_entry = {
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "timestamp": datetime.now().isoformat()
    }
    with open("logs/conversations.jsonl", "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def answer(query, session_id="default"):
    response = rag_with_memory.invoke(
        {"question": query},
        config={"configurable": {"session_id": session_id}}
    )
    log_conversation(session_id, query, response)
    return response

# =========================
# 6) Terminal UI
# =========================
if __name__ == "__main__":
    print("🛠️ Asistente de Ferretería : Pregúntame sobre  productos de Ferritienda.")
    session_id = "default"
    while True:
        user_input = input("🔍 Tu pregunta (o 'salir' para terminar): ")
        if user_input.lower() in ["salir", "exit"]:
            print("👋 ¡Hasta luego!")
            break
        respuesta = answer(user_input, session_id=session_id)
        print("💬 Respuesta:", respuesta)

        history = get_chat_history(session_id).messages
        print("\n🧾 Historial:")
        for msg in history:
            print(f"{msg.type.upper()}: {msg.content}")