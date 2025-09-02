import streamlit as st
from ferriatienda.llama_chat import answer
from datetime import datetime
import base64
import os
import uuid
import json

st.markdown("<div class='main-container'>", unsafe_allow_html=True)
# === CONFIGURATION ===
st.set_page_config(page_title="Experto en Ferreterías", page_icon="💪", layout="centered")

# === CSS ===
with open("ferriatienda/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    

# === LOGO ===
logo_path = os.path.join(os.path.dirname(__file__), "images", "logo_ferritienda.jpg")
with open(logo_path, "rb") as image_file:
    logo_bytes = image_file.read()
    encoded = base64.b64encode(logo_bytes).decode()

st.markdown(
    f"<div id='logo'><img src='data:image/png;base64,{encoded}' width='300'></div>",
    unsafe_allow_html=True,
)

# === TITRE ===
st.title("Ferritienda Chatbot")
st.markdown("Pregúntale a un experto sobre los productos de Ferritienda 🔍")

# === INIT SESSION STATE ===
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "loading" not in st.session_state:
    st.session_state.loading = False

if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

# === BOUTON NOUVELLE SESSION ===
if st.button("Nueva sesión"):
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.clear_input = True
    st.rerun()

# === AFFICHAGE HISTORIQUE DES MESSAGES ===
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    role_class = "user-message" if msg["role"] == "user" else "bot-message"
    st.markdown(f"<div class='{role_class}'>{msg['content']}</div>", unsafe_allow_html=True)

# === Spinner affiché comme message ===
if st.session_state.get("loading", False):
    st.markdown("""
    <div class='bot-message spinner-container'>
        ✍️ El experto está redactando su respuesta...
        <div class="dot-flashing"></div>
        <div class="dot-flashing"></div>
        <div class="dot-flashing"></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# === ZONE D'INPUT UTILISATEUR EN BAS ===
st.markdown("<div class='input-container'>", unsafe_allow_html=True)
col1, col2 = st.columns([5, 1])

# Valeur par défaut de l'input
default_value = "" if st.session_state.clear_input else st.session_state.get("user_input", "")

with col1:
    user_input = st.text_input(
        "",
        key="user_input",
        label_visibility="collapsed",
        value=default_value,
        placeholder="Pregúntale a un experto..."
    )

with col2:
    if st.button("Enviar") and user_input.strip():
        question = user_input.strip()
        session_id = st.session_state.session_id

        # Ajoute la question
        st.session_state.messages.append({"role": "user", "content": question})

        # Active les flags
        st.session_state.loading = True
        st.session_state.clear_input = True

        st.rerun()

st.markdown("</div>", unsafe_allow_html=True) 

# === GÉNÉRATION DE LA RÉPONSE ===
if st.session_state.get("loading", False):
    last_question = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
    session_id = st.session_state.session_id

    if last_question:
        response = answer(last_question, session_id=session_id)

        # Supprime le spinner
        if st.session_state.messages and "redactando su respuesta" in st.session_state.messages[-1]["content"]:
            st.session_state.messages.pop()

        # Ajoute la réponse
        st.session_state.messages.append({"role": "bot", "content": response})

        # Log la conversation
        date = datetime.now().strftime("%Y-%m-%d")
        log_path = f"logs/conversacion_{date}.jsonl"
        os.makedirs("logs", exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            json.dump({
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "question": last_question,
                "response": response
            }, f, ensure_ascii=False)
            f.write("\n")

        # Nettoyage
        st.session_state.loading = False
        st.session_state.clear_input = True

        st.markdown("</div>", unsafe_allow_html=True)  # ✅ Fermeture correcte AVANT rerun
        st.rerun()
        
# st.markdown("</div>", unsafe_allow_html=True)