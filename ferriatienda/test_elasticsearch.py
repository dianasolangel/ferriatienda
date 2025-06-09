from elasticsearch import Elasticsearch

# Conéctate a Elasticsearch en el contenedor
es = Elasticsearch("http://localhost:9200")

# Verifica si está disponible
if es.ping():
    print("✅ Elasticsearch está vivo!")
else:
    print("❌ No se pudo conectar a Elasticsearch.")