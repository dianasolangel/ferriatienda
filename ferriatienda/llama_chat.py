import pandas as pd
import ast
from operator import itemgetter
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings  # NUEVO IMPORT
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
import json
import os
import ast
from datetime import datetime

# Load and prepare data
embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embedding_function,
    collection_name="electric_tools_sample"
)
# Load the vectorstore from the persistent directory
retriever = vectorstore.as_retriever()

# Define primary and fallback LLMs
llm = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-70B-Instruct",
    task="conversational",
    temperature=0.7,
    max_new_tokens=512,
)
chat = ChatHuggingFace(llm=llm)

llm_fallback = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    task="conversational",
    temperature=0.7,
    max_new_tokens=512,
)
chat_fallback = ChatHuggingFace(llm=llm_fallback)

# Step 4: Prompt and chains
prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un asistente experto en herramientas eléctricas de ferretería. Usa el contexto proporcionado., hazlo de manera natural y amable. Si no sabes, di: 'No tengo suficiente información'."),
    ("user", "Contexto: {context}\n\nPregunta: {question}")
])

primary_chain = prompt | chat | StrOutputParser()
fallback_chain = prompt | chat_fallback | StrOutputParser()
main_chain = primary_chain.with_fallbacks([fallback_chain])

rag_chain = RunnableParallel({
    "context": itemgetter("question") | retriever,
    "question": RunnablePassthrough()
}) | main_chain

# Step 5: Chat history support
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

# Step 6: Interactive function

def log_conversation(session_id, question, answer):
    os.makedirs("logs", exist_ok=True)  # ✅ Crea el directorio si no existe
    log_entry = {
        "session_id": session_id,
        "question": question,
        "answer": answer
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

# Step 7: Example usage in terminal
if __name__ == "__main__":
    print("🛠️ Asistente de Ferretería: Pregúntame sobre herramientas eléctricas Truper.")
    while True:
        user_input = input("🔍 Tu pregunta (o 'salir' para terminar): ")
        if user_input.lower() in ["salir", "exit"]:
            print("👋 ¡Hasta luego!")
            break
        respuesta = answer(user_input)
        print("💬 Respuesta:", respuesta)
