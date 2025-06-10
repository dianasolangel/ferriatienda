import pandas as pd
import ast
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Load and prepare data
electric_tool_truper = pd.read_csv("notebooks/data/sample_electric_truper_products.csv", sep=";")
electric_tool_truper_des = electric_tool_truper["Descripción"].apply(lambda x: ast.literal_eval(x)["descripcion"]).tolist()
df_desc = pd.DataFrame(electric_tool_truper_des, columns=['Text'])

# Embedding
embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Save to persistent Chroma DB
vectorstore = Chroma.from_texts(
    texts=df_desc["Text"].tolist(),
    embedding=embedding_function,
    persist_directory="./chroma_db",
    collection_name="electric_tools_sample"
)
print("✅ Vectorstore indexed and saved.")