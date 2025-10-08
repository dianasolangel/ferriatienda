import streamlit as st
from datetime import datetime
import base64
import os
import uuid
import json
from ferriatienda.llama_chat import answer
from ferriatienda.utils import send_conversation_email


# === CONFIG ===
st.set_page_config(page_title="Experto en Ferreterías", page_icon="💪", layout="centered")

# === CSS GLOBAL ===
with open("ferriatienda/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === SESSION STATES ===
st.session_state.setdefault("messages", [])
st.session_state.setdefault("session_id", str(uuid.uuid4()))
st.session_state.setdefault("loading", False)
st.session_state.setdefault("clear_input", False)
st.session_state.setdefault("show_email_form", False)
st.session_state.setdefault("email_sent", False)

# === CONTENEUR PRINCIPAL ===
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

# === HEADER avec logo ===
st.markdown("<div class='header-container'>", unsafe_allow_html=True)
logo_path = os.path.join(os.path.dirname(__file__), "images", "logo_ferritienda.jpg")
with open(logo_path, "rb") as image_file:
    logo_bytes = image_file.read()
    encoded = base64.b64encode(logo_bytes).decode()
st.markdown(f"<div id='logo'><img src='data:image/png;base64,{encoded}'></div>", unsafe_allow_html=True)

# === TITRE & SOUS-TITRE ===
st.markdown("<div class='title-section'>", unsafe_allow_html=True)
st.markdown("<h1 class='title'>Ferritienda Chatbot </h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Pregúntale a un experto sobre los productos de Ferritienda 🔍</p>", unsafe_allow_html=True)

# === SIDEBAR ===
with st.sidebar:
    st.header("🛠️ Opciones") 
    if st.button("🚀 Nueva sesión"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.clear_input = True
        st.rerun()
    if st.button("📧 Recibir conversación por correo"):
        st.session_state.show_email_form = True

# === AFFICHAGE DU CHAT ===
st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    role_class = "user-message" if msg["role"] == "user" else "bot-message"
    st.markdown(f"<div class='{role_class}'>{msg['content']}</div>", unsafe_allow_html=True)

# === SPINNER SI EN ATTENTE DE RÉPONSE ===
if st.session_state.get("loading", False):
    st.markdown("""
        <div class='bot-message spinner-container'>
            ✍️ El experto está redactando su respuesta...
            <div class="dot-flashing"></div>
            <div class="dot-flashing"></div>
            <div class="dot-flashing"></div>
        </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)  # Fin chat-wrapper

# === CHAMP D’INPUT FIXÉ EN BAS ===
st.markdown("<div class='input-container'>", unsafe_allow_html=True)
col1, col2 = st.columns([5, 1])

default_value = "" if st.session_state.clear_input else st.session_state.get("user_input", "")
with col1:
    user_input = st.text_input(
        label="Pregunta", value=default_value, key="user_input",
        label_visibility="collapsed", placeholder="Pregúntale a un experto..."
    )
with col2:
    if st.button("Enviar") and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        st.session_state.loading = True
        st.session_state.clear_input = True
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)  # Fin input-container

# === TRAITEMENT DE LA RÉPONSE ===
if st.session_state.get("loading", False):
    last_question = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), None)
    if last_question:
        response = answer(last_question, session_id=st.session_state.session_id)
        st.session_state.messages.append({"role": "bot", "content": response})

        # Enregistrement dans un fichier log
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
        st.session_state.clear_input = False  # reset pour permettre l’édition future
        st.rerun()

# === ENVOI PAR EMAIL ===
if st.session_state.show_email_form and not st.session_state.email_sent:
    st.markdown("<div class='email-popup'>", unsafe_allow_html=True)
    st.subheader("¿Quieres recibir esta conversación por correo electrónico?")
    with st.form("email_form"):
        recipient_email = st.text_input("Introduce tu correo electrónico")
        col1, col2 = st.columns([1, 1])
        with col1:
            submit_email = st.form_submit_button("Enviar")
        with col2:
            cancel_email = st.form_submit_button("Cerrar")

        if cancel_email:
            st.session_state.show_email_form = False
            st.rerun()

        if submit_email:
            if not recipient_email:
                st.error("Por favor, introduce un correo válido.")
            else:
                sent = send_conversation_email(
                    recipient_email,
                    subject="Resumen de tu conversación con Ferritienda",
                    messages=st.session_state.messages
                )
                if sent:
                    st.session_state.email_sent = True
                    st.success("¡Correo enviado con éxito!")
                    st.session_state.show_email_form = False
                    st.rerun()
                else:
                    st.error("Error al enviar el correo.")
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.email_sent:
    st.success("El resumen de la conversación fue enviado con éxito.")

st.markdown("</div>", unsafe_allow_html=True)  # Fin main-container