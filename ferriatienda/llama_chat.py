import os
import json
from datetime import datetime
from operator import itemgetter

import pandas as pd
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain_ollama import ChatOllama
from langchain_huggingface.chat_models import ChatHuggingFace
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.caches import InMemoryCache
from langchain.globals import set_llm_cache
# to start chroma client
from ferriatienda.startup import get_or_build_retriever

# === LangChain Cache ===
set_llm_cache(InMemoryCache())

# === Retriever ===
retriever = get_or_build_retriever()

# === LLM Setup ===
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

# Primary model: HF via API
llm = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    task="conversational",
    temperature=0.7,
    max_new_tokens=512,
)
chat = ChatHuggingFace(llm=llm)

# Fallback model: Ollama
chat_fallback = ChatOllama(
    model="qwen2.5:0.5b",
    base_url=OLLAMA_BASE,
    temperature=0.3,
    num_ctx=2048,
    num_predict=300,
    keep_alive="30m",
    request_timeout=120,
)

# === Prompt & RAG Chain ===
prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un asistente experto en herramientas eléctricas de ferretería. "
               "Responde SÓLO usando la información del contexto con un tono de service client. "
               "Si el contexto no tiene suficiente información, responde EXACTAMENTE: "
               "'No tengo suficiente información'. Responde SIEMPRE en español neutro."),
    ("user", "Contexto:\n{context}\n\nPregunta: {question}")
])

primary_chain = prompt | chat | StrOutputParser()
fallback_chain = prompt | chat_fallback | StrOutputParser()
main_chain = primary_chain.with_fallbacks([fallback_chain])

def format_docs(docs):
    return "\n\n".join(f"- {d.page_content[:400]}" for d in docs)

rag_chain = (
    RunnableParallel({
        "context": itemgetter("question") | retriever | RunnableLambda(format_docs),
        "question": RunnablePassthrough()
    })
    | main_chain
)

# === Chat History for RunnableWithMessageHistory (optional) ===
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

# === Chat Memory for ConversationalRetrievalChain ===
sessions_memory = {}
def get_memory(session_id):
    if session_id not in sessions_memory:
        sessions_memory[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    return sessions_memory[session_id]

# === Logging ===
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

# === Final Answer Function ===
def answer(query, session_id="default"):
    memory = get_memory(session_id)
    rag = ConversationalRetrievalChain.from_llm(
        llm=chat,
        retriever=retriever,
        memory=memory,
        return_source_documents=False,
    )
    response = rag.invoke({"question": query})
    log_conversation(session_id, query, response["answer"])
    return response["answer"]