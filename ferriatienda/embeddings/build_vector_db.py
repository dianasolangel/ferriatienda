import os
import pandas as pd
import chromadb

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def build_chroma_vectorstore():
    print("Lancement de l’ingestion dans ChromaDB...")

    # --- Config connexion
    CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
    CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
    print(f"Connexion à Chroma sur {CHROMA_HOST}:{CHROMA_PORT}")

    # Charger les données
    data_path = "../data/scrapping/sample_electric_truper_products.csv"
    print(f"Chargement du fichier : {data_path}")
    if not os.path.exists(data_path):
        print("Fichier introuvable.")
        return

    df = pd.read_csv(data_path, sep=";")
    print(f"Fichier chargé avec {len(df)} lignes")

    texts = df["Descripcion"].fillna("").astype(str).tolist()
    if not texts:
        print("Aucun texte à indexer")
        return

    # Préparer les métadonnées
    metas = []
    ids = []
    for i, row in df.reset_index().iterrows():
        meta = {
            "row_index": int(i),
            "nombre": str(row.get("Nombre", "")),
            "referencia": str(row.get("Referencia", "")),
            "marca": str(row.get("Marca", "")),
        }
        metas.append(meta)
        rid = str(row.get("Referencia", "")).strip()
        ids.append(f"etr_{rid or i}")

    print(f"{len(texts)} textes à vectoriser")

    #  Embeddings
    embedding_function = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    # Connexion au serveur Chroma
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    collection_name = "electric_tools_sample"
    vectorstore = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embedding_function,
    )

    print("Ajout des vecteurs à la collection...")
    vectorstore.add_texts(texts=texts, metadatas=metas, ids=ids)

    col = client.get_or_create_collection(collection_name)
    print(f"Ingestion terminée. La collection '{collection_name}' contient {col.count()} vecteurs.")

# if __name__ == "__main__":
#     build_chroma_vectorstore()