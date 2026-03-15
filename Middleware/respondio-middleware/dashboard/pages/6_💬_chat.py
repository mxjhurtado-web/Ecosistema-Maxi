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

# Helper for base64
import base64

def file_to_base64(uploaded_file):
    if uploaded_file:
        return base64.b64encode(uploaded_file.getvalue()).decode()
    return None

# Main chat interface
st.subheader("💬 Chat with MCP")

# File uploader
uploaded_files = st.file_uploader(
    "📎 Attach files (Image/Audio)", 
    type=["png", "jpg", "jpeg", "mp3", "wav", "ogg"],
    accept_multiple_files=True,
    help="Upload images for ID verification or audio for voice instructions."
)

# Display chat messages
chat_container = st.container()

with chat_container:
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show media if present
            if "media" in message:
                for item in message["media"]:
                    if item["mime_type"].startswith("image/"):
                        st.image(f"data:{item['mime_type']};base64,{item['data']}", width=300)
                    elif item["mime_type"].startswith("audio/"):
                        st.audio(f"data:{item['mime_type']};base64,{item['data']}")
            
            # Show metadata for assistant messages
            if message["role"] == "assistant" and "metadata" in message:
                with st.expander("📊 Response Details"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Latency", f"{message['metadata'].get('latency_ms', 0)} ms")
                    
                    with col2:
                        st.metric("Status", message['metadata'].get('status', 'unknown'))
                    
                    with col3:
                        st.metric("Retries", message['metadata'].get('retry_count', 0))
                    
                    if message['metadata'].get('trace_id'):
                        st.text(f"Trace ID: {message['metadata']['trace_id']}")

# Chat input
user_input = st.chat_input(
    "Type your message here...",
    disabled=not st.session_state.chat_enabled
)

if user_input or (uploaded_files and st.button("🚀 Send Files")):
    # Prepare media
    media_items = []
    if uploaded_files:
        for f in uploaded_files:
            b64_data = file_to_base64(f)
            media_items.append({
                "mime_type": f.type,
                "data": b64_data,
                "file_name": f.name
            })
    
    # Add user message to chat
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input or "Sent files",
        "media": media_items,
        "timestamp": datetime.now().isoformat()
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input or "Sent files")
        for item in media_items:
            if item["mime_type"].startswith("image/"):
                st.image(f"data:{item['mime_type']};base64,{item['data']}", width=200)
            elif item["mime_type"].startswith("audio/"):
                st.audio(f"data:{item['mime_type']};base64,{item['data']}")
    
    # Show loading spinner
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Call the webhook endpoint (simulating Respond.io)
            import requests
            
            try:
                # Get webhook secret from environment
                webhook_secret = os.getenv("WEBHOOK_SECRET", "change-me-in-production")
                
                # Prepare request
                api_url = os.getenv("API_URL", "http://localhost:8000")
                
                response = requests.post(
                    f"{api_url}/webhook",
                    headers={
                        "X-Webhook-Secret": webhook_secret,
                        "Content-Type": "application/json"
                    },
                    json={
                        "conversation_id": f"chat_test_{datetime.now().timestamp()}",
                        "contact_id": "dashboard_user",
                        "channel": channel,
                        "user_text": user_input or "Audio/Image analysis requested",
                        "media": media_items,
                        "metadata": {
                            "source": "dashboard_chat",
                            "test_mode": True,
                            "agent_name": selected_agent if selected_agent != "Auto (Orchestrator)" else None
                        }
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Add assistant response to chat
                    assistant_message = {
                        "role": "assistant",
                        "content": result.get("reply_text", "No response"),
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "status": result.get("status"),
                            "latency_ms": result.get("latency_ms"),
                            "retry_count": result.get("retry_count", 0),
                            "trace_id": result.get("trace_id")
                        }
                    }
                    
                    st.session_state.chat_messages.append(assistant_message)
                    
                    # Display response
                    st.markdown(result.get("reply_text", "No response"))
                    
                    # Show metadata
                    with st.expander("📊 Response Details"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Latency", f"{result.get('latency_ms', 0)} ms")
                        
                        with col2:
                            status = result.get('status', 'unknown')
                            st.metric("Status", status)
                        
                        with col3:
                            st.metric("Retries", result.get('retry_count', 0))
                        
                        if result.get('trace_id'):
                            st.text(f"Trace ID: {result['trace_id']}")
                
                else:
                    error_msg = f"❌ Error: HTTP {response.status_code}"
                    st.error(error_msg)
                    
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().isoformat()
                    })
            
            except requests.exceptions.Timeout:
                error_msg = "❌ Request timeout. The MCP server took too long to respond."
                st.error(error_msg)
                
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().isoformat()
                })
            
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().isoformat()
                })
    
    # Rerun to update chat
    st.rerun()

# Quick test buttons
st.markdown("---")
st.markdown("### 🚀 Quick Tests")

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
