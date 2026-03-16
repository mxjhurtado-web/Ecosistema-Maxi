"""
💬 Chat Interface Page - Test MCP in Real-Time
"""

import streamlit as st
from datetime import datetime
import sys
import os

# Add project root to path with high priority
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from components.auth import require_auth
from components.api_client import api_client
from components.page_setup import setup_page

# Setup page with ORBIT theme
setup_page("Chat Interface", "💬")

# Require authentication
require_auth()

if st.session_state.get("role") == "supervisor":
    st.warning("⚠️ Access Denied: Supervisors do not have access to the test chat.")
    st.switch_page("pages/1_📊_kpis.py")
    st.stop()

# Initialize chat history in session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "chat_enabled" not in st.session_state:
    st.session_state.chat_enabled = True

# --- PREMIUM STYLING (GLASSMORPHISM & WHATSAPP THEME) ---
st.markdown("""
<style>
    /* Global Background & Glassmorphism */
    .main {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    .stApp {
        background: transparent;
    }
    
    /* Chat Container Stylings */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        border-left: 4px solid #00f2fe;
        background: rgba(0, 242, 254, 0.05);
    }
    
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        border-left: 4px solid #4facfe;
        background: rgba(79, 172, 254, 0.05);
    }

    /* Input Bar Integration */
    .stChatInput {
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding-top: 20px;
    }
    
    /* Hide the default uploader label to make it compact */
    .stFileUploader label {
        display: none;
    }
    
    /* Make the uploader feel like a "plus" menu */
    .stFileUploader {
        border: 1px dashed rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.02);
        padding: 5px;
    }

    /* Neon details */
    h1, h2, h3 {
        color: #ffffff;
        text-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
    }
    
    /* Audio Recorder Styling */
    .recorder-container {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 10px;
        padding: 10px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        backdrop-filter: blur(5px);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar controls
with st.sidebar:
    st.subheader("💬 Chat Settings")
    
    # --- Agent Selector ---
    agents = api_client.get_agents()
    agent_options = ["Auto (Orchestrator)"] + [a['name'] for a in agents]
    
    selected_agent = st.selectbox(
        "Active Agent",
        agent_options,
        index=0,
        help="Choose 'Auto' for Orchestrator or a specific agent to test directly."
    )
    
    # Channel simulator
    channel = st.selectbox(
        "Simulate Channel",
        ["whatsapp", "telegram", "messenger", "webchat"],
        help="Simulate different channels for testing"
    )
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()
    
    st.markdown("---")
    
    # Stats
    st.markdown("### 📊 Session Stats")
    st.metric("Messages Sent", len([m for m in st.session_state.chat_messages if m["role"] == "user"]))
    st.metric("Responses", len([m for m in st.session_state.chat_messages if m["role"] == "assistant"]))

# --- HELPERS ---
import base64
import requests

def file_to_base64(uploaded_file):
    if uploaded_file:
        return base64.b64encode(uploaded_file.getvalue()).decode()
    return None

def audio_recorder():
    st.markdown("### 🎙️ Grabadora de Voz")
    recorder_html = """
    <div class="recorder-container">
        <button id="recordBtn" style="background:#ff4b4b; border:none; color:white; padding:10px 20px; border-radius:50%; cursor:pointer; font-size:20px;">🎙️</button>
        <div id="status" style="color:white; font-size:14px;">Presiona para grabar</div>
        <div id="timer" style="color:#00f2fe; font-weight:bold;">00:00</div>
    </div>
    <script>
        let mediaRecorder;
        let audioChunks = [];
        let startTime;
        let timerInterval;

        const recordBtn = document.getElementById('recordBtn');
        const status = document.getElementById('status');
        const timer = document.getElementById('timer');

        recordBtn.onclick = async () => {
            if (mediaRecorder && mediaRecorder.state === "recording") {
                mediaRecorder.stop();
                clearInterval(timerInterval);
                recordBtn.style.background = "#ff4b4b";
                status.innerText = "Grabación lista!";
                return;
            }

            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.start();
                recordBtn.style.background = "#00f2fe";
                status.innerText = "Grabando...";
                startTime = Date.now();
                timerInterval = setInterval(() => {
                    const elapsed = Math.floor((Date.now() - startTime) / 1000);
                    const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
                    const secs = String(elapsed % 60).padStart(2, '0');
                    timer.innerText = `${mins}:${secs}`;
                }, 1000);
            } catch (err) {
                status.innerText = "Error: Sin acceso al micro";
                console.error(err);
            }
        };
    </script>
    """
    st.components.v1.html(recorder_html, height=120)

# --- MAIN CHAT UI ---
st.subheader("💬 Chat with MCP")

# WhatsApp-style Action Bar (Media + Audio)
with st.container():
    col_media, col_audio = st.columns([2, 1])
    with col_media:
        uploaded_files = st.file_uploader(
            "Clip", 
            type=["png", "jpg", "jpeg", "mp3", "wav", "ogg"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            help="Arrastra imágenes o audios aquí"
        )
    with col_audio:
        audio_recorder()

# Display historical messages from session state
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "media" in message:
                for item in message["media"]:
                    if item.get("mime_type", "").startswith("image/"):
                        st.image(f"data:{item['mime_type']};base64,{item['data']}", width=300)
                    elif item.get("mime_type", "").startswith("audio/"):
                        st.audio(f"data:{item['mime_type']};base64,{item['data']}")
            
            # Metadata detail view
            if message["role"] == "assistant" and "metadata" in message:
                with st.expander("📊 Detalles"):
                    m = message["metadata"]
                    st.caption(f"Latencia: {m.get('latency_ms', 0)}ms | Status: {m.get('status')} | Reintentos: {m.get('retry_count', 0)}")

# Chat Input & Processing
user_input = st.chat_input(
    "Escribe un mensaje...",
    disabled=not st.session_state.chat_enabled
)

# Execution Logic
if user_input or (uploaded_files and st.button("🚀 Enviar Archivos")):
    media_items = []
    if uploaded_files:
        for f in uploaded_files:
            b64_data = file_to_base64(f)
            media_items.append({
                "mime_type": f.type,
                "data": b64_data,
                "file_name": f.name
            })
    
    # Store and display user message immediately
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input or "📎 Archivos enviados",
        "media": media_items,
        "timestamp": datetime.now().isoformat()
    })
    
    # Process Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Orbit pensando..."):
            try:
                webhook_secret = os.getenv("WEBHOOK_SECRET", "change-me-in-production")
                api_url = os.getenv("API_URL", "http://localhost:8000")
                
                response = requests.post(
                    f"{api_url}/webhook",
                    headers={"X-Webhook-Secret": webhook_secret, "Content-Type": "application/json"},
                    json={
                        "conversation_id": f"chat_test_{datetime.now().timestamp()}",
                        "contact_id": "dashboard_user",
                        "channel": channel,
                        "user_text": user_input or "Análisis multimedia",
                        "media": media_items,
                        "metadata": {
                            "source": "dashboard_chat",
                            "agent_name": selected_agent if selected_agent != "Auto (Orchestrator)" else None
                        }
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assistant_msg = {
                        "role": "assistant",
                        "content": result.get("reply_text", "Sin respuesta"),
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "status": result.get("status"),
                            "latency_ms": result.get("latency_ms"),
                            "retry_count": result.get("retry_count", 0),
                            "trace_id": result.get("trace_id")
                        }
                    }
                    st.session_state.chat_messages.append(assistant_msg)
                    st.markdown(assistant_msg["content"])
                else:
                    st.error(f"Error HTTP: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.rerun()

# Footer & Export
st.markdown("---")
if st.session_state.chat_messages:
    chat_text = "\n".join([f"[{m['timestamp']}] {'Tú' if m['role']=='user' else 'Orbit'}: {m['content']}" for m in st.session_state.chat_messages])
    st.download_button("📥 Descargar Historial", chat_text, f"chat_{datetime.now().strftime('%H%M%S')}.txt")
st.caption(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📰 Test News", use_container_width=True):
        st.session_state.chat_messages.append({
            "role": "user",
            "content": "noticias de tecnología",
            "timestamp": datetime.now().isoformat()
        })
        st.rerun()

with col2:
    if st.button("👋 Test Greeting", use_container_width=True):
        st.session_state.chat_messages.append({
            "role": "user",
            "content": "hola",
            "timestamp": datetime.now().isoformat()
        })
        st.rerun()

with col3:
    if st.button("❓ Test Help", use_container_width=True):
        st.session_state.chat_messages.append({
            "role": "user",
            "content": "ayuda",
            "timestamp": datetime.now().isoformat()
        })
        st.rerun()

# Export chat
st.markdown("---")

if st.session_state.chat_messages:
    # Export as text
    chat_text = ""
    for msg in st.session_state.chat_messages:
        role = "You" if msg["role"] == "user" else "MCP"
        chat_text += f"[{msg['timestamp']}] {role}: {msg['content']}\n\n"
    
    st.download_button(
        label="📥 Download Chat History",
        data=chat_text,
        file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
