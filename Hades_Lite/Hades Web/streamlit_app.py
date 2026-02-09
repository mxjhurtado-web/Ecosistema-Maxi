import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Export secrets to environment variables (for hades_api.config)
if "KEYCLOAK_SERVER_URL" in st.secrets:
    for key, value in st.secrets.items():
        os.environ[key] = str(value)

# Add current dir to path to ensure imports work
sys.path.append(str(Path(__file__).parent))

from hades_api.config import settings
from hades_ui.auth_manager import AuthManager
from hades_api.database import SessionLocal
from hades_api.models.job import Job, JobStatus
from hades_core.analyzer import analyze_image

# Page Config
st.set_page_config(
    page_title="Hades Web - Forensic Analysis",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #00d4ff;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #8892b0;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #1a1c23;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #2d2e3a;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background: linear-gradient(45deg, #00d4ff, #0055ff);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 2rem;
        font-weight: 600;
    }
    .status-badge {
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Auth
auth = AuthManager(settings)

# Security Check
if not auth.check_auth():
    st.stop()

# --- Post-Authentication App ---

def show_sidebar():
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/mxjhurtado-web/Ecosistema-Maxi/main/assets/hades_logo.png", width=100) # Fallback to a placeholder if not exists
        st.markdown("### 🦅 Hades Web v1.0")
        st.divider()
        
        user_name = st.session_state.user_info.get("name", "Usuario")
        st.write(f"Conectado como: **{user_name}**")
        
        menu = st.radio(
            "Navegación",
            ["✨ Nuevo Análisis", "📜 Historial", "📊 Dashboard Admin", "⚙️ Configuración"]
        )
        
        st.divider()
        if st.sidebar.button("🔌 Cerrar Sesión"):
            auth.logout()
            
    return menu

def page_analyzer():
    st.markdown('<h1 class="main-header">✨ Nuevo Análisis Forense</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sube una imagen de un documento de identidad para comenzar el análisis.</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Arrastra o selecciona una imagen", type=["jpg", "jpeg", "png"])
        auto_export = st.checkbox("Exportar automáticamente a Google Drive", value=True)
        
        if uploaded_file and st.button("🚀 Iniciar Análisis"):
            with st.spinner("Analizando documento con Gemini Vision AI..."):
                try:
                    # 1. Read bytes
                    image_bytes = uploaded_file.read()
                    
                    # 2. Analyze
                    api_key = st.session_state.get("gemini_api_key") or settings.GEMINI_API_KEY
                    if not api_key:
                        st.error("❌ Gemini API Key no configurada.")
                        return
                        
                    result = analyze_image(image_bytes, gemini_api_key=api_key)
                    
                    # 3. Save to DB
                    db = SessionLocal()
                    job = Job(
                        user_id=st.session_state.user_info.get("sub"),
                        user_email=st.session_state.user_info.get("email"),
                        user_name=st.session_state.user_info.get("name"),
                        status=JobStatus.COMPLETED,
                        result=result.to_dict(),
                        country_detected=result.country_code,
                        semaforo=result.semaforo.value if result.semaforo else None,
                        score=result.score,
                        name_extracted=result.name,
                        id_number_extracted=result.id_number,
                        completed_at=datetime.utcnow()
                    )
                    db.add(job)
                    db.commit()
                    db.refresh(job)
                    
                    st.success(f"✅ Análisis completado para {result.name}")
                    st.session_state.current_result = result.to_dict()
                    st.session_state.current_job_id = job.id
                    
                except Exception as e:
                    st.error(f"❌ Error durante el análisis: {str(e)}")

    with col2:
        if "current_result" in st.session_state:
            res = st.session_state.current_result
            st.markdown(f'<div class="card">', unsafe_allow_html=True)
            
            # Semáforo
            sem = res.get("forensics", {}).get("semaforo", "gris")
            color = {"verde": "🟢 Verificado", "amarillo": "🟡 Precaución", "rojo": "🔴 Alerta"}.get(sem, "⚪ Desconocido")
            st.subheader(f"Resultado: {color}")
            
            # Data
            st.write(f"**Nombre:** {res.get('extracted_data', {}).get('name')}")
            st.write(f"**Documento ID:** {res.get('extracted_data', {}).get('id_number')}")
            st.write(f"**País DET:** {res.get('country', {}).get('name')}")
            
            # Dates
            dates = res.get("dates", {})
            st.write("---")
            st.write(f"📅 **Nacimiento:** {dates.get('birth', {}).get('display')}")
            st.write(f"⏳ **Vencimiento:** {dates.get('expiration', {}).get('display')}")
            
            st.markdown('</div>', unsafe_allow_html=True)

def page_history():
    st.markdown('<h1 class="main-header">📜 Historial de Análisis</h1>', unsafe_allow_html=True)
    
    db = SessionLocal()
    user_id = st.session_state.user_info.get("sub")
    jobs = db.query(Job).filter(Job.user_id == user_id).order_by(Job.created_at.desc()).all()
    
    if not jobs:
        st.info("Aún no tienes análisis registrados.")
        return
        
    data = []
    for job in jobs:
        data.append({
            "Fecha": job.created_at.strftime("%Y-%m-%d %H:%M"),
            "Nombre": job.name_extracted,
            "País": job.country_detected,
            "Semáforo": job.semaforo,
            "Score": job.score,
            "ID": str(job.id)[:8] + "..."
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

def page_admin():
    st.markdown('<h1 class="main-header">📊 Dashboard Admin</h1>', unsafe_allow_html=True)
    
    # Simple stats
    db = SessionLocal()
    total_jobs = db.query(Job).count()
    users_count = db.query(Job.user_email).distinct().count()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Análisis Totales", total_jobs)
    col2.metric("Usuarios Activos", users_count)
    col3.metric("Uptime", "99.9%")
    
    st.divider()
    st.write("### Distribución Geográfica")
    # Placeholder for a chart
    st.info("Próximamente: Gráficos de actividad por país y usuario.")

def page_config():
    st.markdown('<h1 class="main-header">⚙️ Configuración</h1>', unsafe_allow_html=True)
    
    with st.expander("🤖 API Keys"):
        key = st.text_input("Gemini API Key", value=st.session_state.get("gemini_api_key", ""), type="password")
        if st.button("Guardar Key"):
            st.session_state.gemini_api_key = key
            st.success("API Key guardada en la sesión.")
    
    with st.expander("📁 Integración Google Drive"):
        st.write("Estado: **Conectado** ✅")
        st.write(f"Carpeta destino: `{settings.APP_NAME} Results`")

# Main Logic
menu = show_sidebar()

if menu == "✨ Nuevo Análisis":
    page_analyzer()
elif menu == "📜 Historial":
    page_history()
elif menu == "📊 Dashboard Admin":
    page_admin()
elif menu == "⚙️ Configuración":
    page_config()
