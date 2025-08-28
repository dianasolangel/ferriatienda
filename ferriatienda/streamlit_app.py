import streamlit as st
from ferriatienda.llama_chat import answer, get_chat_history

# === CONFIGURATION ===
st.set_page_config(page_title="Expero en Ferreterias", page_icon="🛠️", layout="centered")

# === CSS ===
with open("ferriatienda/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === Logo ===
st.markdown("<div id='logo'><img src='https://upload.wikimedia.org/wikipedia/commons/3/3a/Truper_logo.png' width='250'></div>", unsafe_allow_html=True)

# === Titre ===
st.title(" Ferritienda Chatbot")
st.markdown("Pregúntale a un experto sobre los productos de Ferritienda 🔍")

# === SESSION ===
if "messages" not in st.session_state:
    st.session_state.messages = []

# === AFFICHER L'HISTORIQUE ===
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-message'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-message'>{msg['content']}</div>", unsafe_allow_html=True)

# === SAISIE UTILISATEUR ===
user_input = st.text_input("Pregúntale a un experto:", key="user_input")

if user_input:
    # Ajouter le message de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Obtenir la réponse via ton RAG
    response = answer(user_input, session_id="streamlit")

    # Ajouter la réponse
    st.session_state.messages.append({"role": "bot", "content": response})

    # Rafraîchir la page pour afficher le nouveau message
    st.experimental_rerun()