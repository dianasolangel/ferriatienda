import os
import pandas as pd
import chromadb

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# --- Config connexion
CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# --- 1) Charger les données
electric_tool_truper = pd.read_csv(
    "./data/scrapping/sample_electric_truper_products.csv", sep=";"
)

# Utiliser directement le texte de la colonne 'Descripcion'
texts = electric_tool_truper["Descripcion"].fillna("").astype(str).tolist()

# Vérif rapide
print(f"Nombre de textes trouvés : {len(texts)}")
print(f"Exemple : {texts[0]}")

# --- 2) Préparer les métadonnées
metas = []
ids = []
for i, row in electric_tool_truper.reset_index().iterrows():
    meta = {
        "row_index": int(i),
        "nombre": str(row.get("Nombre", "")),
        "referencia": str(row.get("Referencia", "")),
        "marca": str(row.get("Marca", "")),
    }
    metas.append(meta)
    rid = str(row.get("Referencia", "")).strip()
    ids.append(f"etr_{rid or i}")

# --- 3) Embeddings
embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# --- 4) Connexion au serveur Chroma
client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

collection_name = "electric_tools_sample"

# --- 5) Lier ou créer la collection
vectorstore = Chroma(
    client=client,
    collection_name=collection_name,
    embedding_function=embedding_function,
)

# --- 6) Ajouter les textes avec métadonnées
vectorstore.add_texts(texts=texts, metadatas=metas, ids=ids)

# --- 7) Vérification
col = client.get_or_create_collection(collection_name)
print(f"✅ Ingested. La collection '{collection_name}' contient {col.count()} vecteurs.")