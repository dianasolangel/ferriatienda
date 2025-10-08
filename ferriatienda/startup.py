# ferriatienda/startup.py
import os
import chromadb
import streamlit as st
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from ferriatienda.embeddings.build_vector_db import build_chroma_vectorstore

@st.cache_resource(show_spinner=True)
def get_or_build_retriever():
    CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
    COLLECTION_NAME = "electric_tools_sample"
    #we initialize the client chroma
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    #we look if it already exists
    try:
        collection = client.get_collection(COLLECTION_NAME)
        print(f"✅ Chroma collection '{COLLECTION_NAME}' already exists with {collection.count()} vectors.")
    except Exception:
        print(f"⚙️ Collection '{COLLECTION_NAME}' not found. Creating...")
        build_chroma_vectorstore()
        collection = client.get_collection(COLLECTION_NAME)
        
    #embedding function
    embedding_function = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    print("embeddings ok")
    #embeddings + vectorstore
    vectorstore = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_function,
    )
    print("vectorstore ok")
    return vectorstore.as_retriever()