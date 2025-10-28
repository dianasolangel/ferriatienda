import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_HOST = "chroma"
CHROMA_PORT = 8000
COLLECTION_NAME = "electric_tools_sample"

print("🔍 Vérification de la collection Chroma...")

# Embeddings identiques à l'ingestion
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Connexion au serveur Chroma
client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
collection = client.get_or_create_collection(COLLECTION_NAME)
print(f"📦 Nombre total de documents : {collection.count()}")

# LangChain wrapper pour tester les recherches
db = Chroma(client=client, collection_name=COLLECTION_NAME, embedding_function=embeddings)

query = "Dame información sobre algún destornillador eléctrico inalámbrico de la marca Truper"
docs = db.similarity_search(query, k=3)

if not docs:
    print("⚠️ Aucun document trouvé.")
else:
    print("\n=== Documents retrouvés ===")
    print(len(docs))
    print("\n=== Documents retrouvés ===")
    for i, d in enumerate(docs):
        print(f"\n--- Document {i+1} ---")
        print("ID :", d.metadata.get("row_index", "N/A"))
        print("Nom :", d.metadata.get("nombre", "N/A"))
        print("Référence :", d.metadata.get("referencia", "N/A"))
        print("Texte :", d.page_content if d.page_content.strip() else "⚠️ Vide")