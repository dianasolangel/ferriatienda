from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from sentence_transformers import SentenceTransformer
import pandas as pd
import time
import ast

# Configuración
INDEX_ALIAS = "ferriatienda-electric-products"
VERSIONED_INDEX = f"{INDEX_ALIAS}-v1"
CSV_PATH = "notebooks/data/sample_electric_truper_products.csv"

def wait_for_elasticsearch(es, retries=10, delay=6):
    for i in range(retries):
        try:
            health = es.cluster.health(wait_for_status="yellow", timeout="60s")
            print("✅ Elasticsearch está listo:", health["status"])
            return
        except Exception as e:
            print(f"⏳ Esperando Elasticsearch ({i+1}/{retries}): {type(e).__name__}: {e}")
            time.sleep(delay)
    raise RuntimeError("❌ Elasticsearch no está disponible tras varios intentos.")

def index_data(es, df):
    # Crear el índice versión si no existe
    if not es.indices.exists(index=VERSIONED_INDEX):
        print(f"🛠️ Creando índice: {VERSIONED_INDEX}")
        es.indices.create(
            index=VERSIONED_INDEX,
            mappings={
                "properties": {
                    "text": {"type": "text"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        )
    else:
        print(f"ℹ️ Índice '{VERSIONED_INDEX}' ya existe.")

    # Alias: crear o actualizar
    if not es.indices.exists_alias(name=INDEX_ALIAS):
        es.indices.put_alias(index=VERSIONED_INDEX, name=INDEX_ALIAS)
        print(f"🔗 Alias '{INDEX_ALIAS}' → '{VERSIONED_INDEX}' creado.")
    else:
        current_index = list(es.indices.get_alias(name=INDEX_ALIAS).keys())[0]
        if current_index != VERSIONED_INDEX:
            es.indices.update_aliases({
                "actions": [
                    {"remove": {"index": current_index, "alias": INDEX_ALIAS}},
                    {"add": {"index": VERSIONED_INDEX, "alias": INDEX_ALIAS}}
                ]
            })
            print(f"🔄 Alias actualizado: {INDEX_ALIAS} → {VERSIONED_INDEX}")
        else:
            print(f"✅ Alias '{INDEX_ALIAS}' ya apunta a '{VERSIONED_INDEX}'")

    # Indexación
    print("📤 Indexando documentos...")
    def doc_generator():
        for i, row in df.iterrows():
            yield {
                "_index": VERSIONED_INDEX,
                "_id": i,
                "_source": {
                    "text": row["text"],
                    "embedding": row["embedding"]
                }
            }
    bulk(es, doc_generator())
    print("✅ Indexación completada.")

if __name__ == "__main__":
    print("🔌 Conectando a Elasticsearch...")
    es = Elasticsearch("http://elasticsearch:9200", request_timeout=60)
    wait_for_elasticsearch(es)

    print("🔄 Cargando datos...")
    df = pd.read_csv(CSV_PATH, sep=";")
    df["text"] = df["Descripción"].apply(lambda x: ast.literal_eval(x)["descripcion"])

    print("🔎 Generando embeddings...")
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    df["embedding"] = df["text"].apply(lambda x: model.encode(x).tolist())

    index_data(es, df)