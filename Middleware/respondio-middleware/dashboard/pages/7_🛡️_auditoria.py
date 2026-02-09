"""
🛡️ Audit Log Page
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.auth import require_auth
from components.api_client import api_client
from components.page_setup import setup_page

# Setup page with ORBIT theme
setup_page("Audit Log", "🛡️")

# Require authentication (Admins only for this page)
require_auth()
if st.session_state.get('role') != 'admin':
    st.warning("⚠️ Access Denied: Admin role required.")
    st.stop()

st.title("🛡️ Registro de Auditoría")
st.markdown("Historial completo de acciones administrativas y de supervisión en el sistema.")

# Filters
col1, col2 = st.columns([2, 1])

with col1:
    limit = st.selectbox(
        "Mostrar últimos registros",
        [50, 100, 200, 500, 1000],
        index=1
    )

with col2:
    st.write("") # Spacer
    if st.button("🔄 Actualizar", use_container_width=True):
        st.rerun()

st.markdown("---")

# Fetch Logs
with st.spinner("Cargando registros de auditoría..."):
    logs = api_client.get_audit_logs(limit=limit)

if logs:
    # Convert to DataFrame for better display
    df = pd.DataFrame(logs)
    
    # Format timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Search filter
    search = st.text_input("🔍 Filtrar por usuario o acción", placeholder="Ej: admin, export_data...")
    
    if search:
        df = df[
            df['username'].str.contains(search, case=False) | 
            df['action'].str.contains(search, case=False) |
            df['details'].str.contains(search, case=False)
        ]

    # Map actions to emojis
    action_icons = {
        "login": "🔑",
        "config_change": "⚙️",
        "user_management": "👤",
        "export_data": "📥",
        "cache_clear": "🧹",
        "circuit_reset": "🛡️",
        "system_maintenance": "🔧"
    }

    # Display as a table with styling
    st.subheader(f"📊 {len(df)} Registros encontrados")
    
    for _, row in df.iterrows():
        icon = action_icons.get(row['action'], "📝")
        with st.expander(f"{icon} {row['timestamp']} - {row['username']} ({row['role']}) - {row['action'].title()}"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Usuario:** `{row['username']}`")
                st.markdown(f"**Rol:** `{row['role']}`")
                st.markdown(f"**IP:** `{row['ip_address'] if row['ip_address'] else 'N/A'}`")
            with col_b:
                st.markdown(f"**Acción:** `{row['action']}`")
                st.markdown(f"**Detalles:**")
                st.info(row['details'])

    # Export option for Audit Log itself
    st.markdown("---")
    csv = df.to_csv(index=False)
    st.download_button(
        "📥 Descargar log de auditoría completo (CSV)",
        data=csv,
        file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.info("No se encontraron registros de auditoría.")

# Footer
st.markdown("---")
st.caption(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
