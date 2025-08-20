import os
import ast
import pandas as pd
import chromadb

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

"""SCRIPT TO CREATE / INGEST INTO CHROMA SERVER COLLECTION"""

# --- Env config (works with docker-compose)
CHROMA_HOST = os.getenv("CHROMA_HOST", "127.0.0.1")  # in compose, use "chroma"
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# 1) Load and prepare data
electric_tool_truper = pd.read_csv(
    "./data/scrapping/sample_electric_truper_products.csv", sep=";"
)
# Descripción column contains a dict-as-string; we extract "descripcion"
def safe_get_descripcion(x):
    try:
        d = ast.literal_eval(x)
        return d.get("descripcion", "")
    except Exception:
        return ""

texts = electric_tool_truper["Descripcion"].apply(safe_get_descripcion).tolist()

# Optional: keep metadata & stable ids (helps dedup and tracing)
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
    # Prefer a stable id if you have SKU/reference; fallback to incremental
    rid = str(row.get("Referencia", "")).strip()
    ids.append(f"etr_{rid or i}")

# 2) Embeddings (client-side) — must match the model you’ll query with
embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# 3) HTTP client to the Chroma server
client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

# 4) Bind to (or create) the server collection via LangChain wrapper
collection_name = "electric_tools_sample"
vectorstore = Chroma(
    client=client,
    collection_name=collection_name,
    embedding_function=embedding_function,
)

# 5) Upsert vectors to the server collection
#    If you may re-run this script, consider filtering out IDs that already exist.
vectorstore.add_texts(texts=texts, metadatas=metas, ids=ids)

# 6) Quick sanity print (server-side count)
col = client.get_or_create_collection(collection_name)
print(f"✅ Ingested. Server collection '{collection_name}' now has {col.count()} vectors.")