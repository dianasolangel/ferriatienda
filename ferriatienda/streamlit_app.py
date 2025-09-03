import streamlit as st
from datetime import datetime
import base64
import os
import uuid
import json
from ferriatienda.llama_chat import answer

# === CONFIG ===
st.set_page_config(page_title="Experto en Ferreterías", page_icon="💪", layout="centered")

# === CSS GLOBAL ===
with open("ferriatienda/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
# === CONTENEUR PRINCIPAL ===
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

st.markdown("<div class='header-container'>", unsafe_allow_html=True)
# === LOGO ===
logo_path = os.path.join(os.path.dirname(__file__), "images", "logo_ferritienda.jpg")
with open(logo_path, "rb") as image_file:
    logo_bytes = image_file.read()
    encoded = base64.b64encode(logo_bytes).decode()
st.markdown(f"<div id='logo'><img src='data:image/png;base64,{encoded}'></div>", unsafe_allow_html=True)

# === TITRE & BOUTON DANS UNE SECTION ALIGNÉE ===
st.markdown("<div class='title-section'>", unsafe_allow_html=True)
st.markdown("<h1 class='title'>Ferritienda Chatbot</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Pregúntale a un experto sobre los productos de Ferritienda 🔍</p>", unsafe_allow_html=True)

st.markdown("<div class='button-container'>", unsafe_allow_html=True)
if st.button("Nueva sesión"):
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.clear_input = True
    st.rerun()
    
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)  # fin title-section

# === SESSION STATE ===
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "loading" not in st.session_state:
    st.session_state.loading = False
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

# # === NOUVELLE SESSION ===
# if st.button("Nueva sesión"):
#     st.session_state.messages = []
#     st.session_state.session_id = str(uuid.uuid4())
#     st.session_state.clear_input = True
#     st.rerun()

# st.markdown("</div>", unsafe_allow_html=True)

# === CONTENEUR CHAT (classique sans scroll JS) ===
st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    role_class = "user-message" if msg["role"] == "user" else "bot-message"
    st.markdown(f"<div class='{role_class}'>{msg['content']}</div>", unsafe_allow_html=True)
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

# === INPUT FIXÉ EN BAS ===
st.markdown("<div class='input-container'>", unsafe_allow_html=True)
col1, col2 = st.columns([5, 1])
# default_value = "" if st.session_state.clear_input else st.session_state.get("user_input", "")
default_value = st.session_state.get("user_input", "")
with col1:
    user_input = st.text_input(
        "", value=default_value,
        key="user_input", label_visibility="collapsed",
        placeholder="Pregúntale a un experto..."
    )
with col2:
    if st.button("Enviar") and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        st.session_state.loading = True
        if "user_input" in st.session_state:
            del st.session_state["user_input"]  # <-- on force l'effacement du champ
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# === TRAITEMENT DE LA RÉPONSE ===
if st.session_state.get("loading", False):
    last_question = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
    if last_question:
        response = answer(last_question, session_id=st.session_state.session_id)
        st.session_state.messages.append({"role": "bot", "content": response})

        log_path = f"logs/conversacion_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        os.makedirs("logs", exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            json.dump({
                "session_id": st.session_state.session_id,
                "timestamp": datetime.now().isoformat(),
                "question": last_question,
                "response": response
            }, f, ensure_ascii=False)
            f.write("\n")

        st.session_state.loading = False
        st.session_state.clear_input = True
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)  # end main-container
