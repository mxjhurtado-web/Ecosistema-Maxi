"""
📜 Request History Page
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Setup page with ORBIT theme
setup_page("Request History", "📜")

# Require authentication
require_auth()

# Initialize session state for filters if not present
if "filter_start_date" not in st.session_state:
    st.session_state.filter_start_date = (datetime.now() - timedelta(days=7)).date()
if "filter_end_date" not in st.session_state:
    st.session_state.filter_end_date = datetime.now().date()
if "filter_status" not in st.session_state:
    st.session_state.filter_status = "All"

# Filters
col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

with col1:
    limit = st.selectbox(
        "Number of Requests",
        [50, 100, 200, 500, 1000],
        index=1
    )

with col2:
    status_filter = st.selectbox(
        "Status Filter",
        ["All", "ok", "degraded", "error"],
        key="filter_status"
    )

with col3:
    # Date Range Filter
    start_date = st.date_input("Start Date", key="filter_start_date")
    end_date = st.date_input("End Date", key="filter_end_date")

with col4:
    st.write("") # Spacer
    st.write("") # Spacer
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
    if st.button("🧹 Clear", use_container_width=True):
        st.session_state.filter_start_date = (datetime.now() - timedelta(days=7)).date()
        st.session_state.filter_end_date = datetime.now().date()
        st.session_state.filter_status = "All"
        st.rerun()

# Search
search_query = st.text_input(
    "🔍 Search by Trace ID or Text",
    placeholder="Enter trace ID or search text..."
)

st.markdown("---")

# Fetch requests
from datetime import timedelta # Ensure timedelta is available
with st.spinner("Loading requests..."):
    status_param = None if status_filter == "All" else status_filter
    requests = api_client.get_recent_requests(limit=limit, status=status_param)

if requests:
    # Filter by Date
    filtered_requests = []
    for r in requests:
        try:
            # Parse timestamp (assuming format 'YYYY-MM-DD HH:MM:SS')
            req_date = datetime.strptime(r.get('timestamp', '').split(' ')[0], '%Y-%m-%d').date()
            if start_date <= req_date <= end_date:
                filtered_requests.append(r)
        except Exception:
            # Fallback for requests without proper timestamp
            filtered_requests.append(r)
    
    requests = filtered_requests

    # Filter by search query
    if search_query:
        requests = [
            r for r in requests
            if search_query.lower() in r.get('trace_id', '').lower()
            or search_query.lower() in r.get('user_text', '').lower()
            or search_query.lower() in r.get('mcp_response', '').lower()
        ]
    
    # Display stats
    st.subheader(f"📊 Showing {len(requests)} requests")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total = len(requests)
        st.metric("Total", f"{total:,}")
    
    with col2:
        success = len([r for r in requests if r.get('status') == 'ok'])
        st.metric("Success", f"{success:,}")
    
    with col3:
        errors = len([r for r in requests if r.get('status') == 'error'])
        st.metric("Errors", f"{errors:,}")
    
    with col4:
        if requests:
            avg_latency = sum(r.get('latency_ms', 0) for r in requests) / len(requests)
            st.metric("Avg Latency", f"{int(avg_latency)} ms")
    
    st.markdown("---")
    
    # Display requests
    for req in requests:
        with st.expander(
            f"{'✅' if req.get('status') == 'ok' else '❌'} "
            f"{req.get('timestamp', 'N/A')} - "
            f"{req.get('channel', 'unknown').title()} - "
            f"{req.get('latency_ms', 0)} ms"
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Request Details**")
                st.text(f"Trace ID: {req.get('trace_id', 'N/A')}")
                st.text(f"Conversation: {req.get('conversation_id', 'N/A')}")
                st.text(f"Contact: {req.get('contact_id', 'N/A')}")
                st.text(f"Channel: {req.get('channel', 'N/A')}")
                st.text(f"Status: {req.get('status', 'N/A')}")
                
                st.markdown("**User Text**")
                st.info(req.get('user_text', 'N/A'))
            
            with col2:
                st.markdown("**Performance**")
                st.text(f"Total Latency: {req.get('latency_ms', 0)} ms")
                st.text(f"MCP Latency: {req.get('mcp_latency_ms', 'N/A')} ms")
                st.text(f"Retry Count: {req.get('retry_count', 0)}")
                st.text(f"Timestamp: {req.get('timestamp', 'N/A')}")
                
                st.markdown("**MCP Response**")
                if req.get('mcp_response'):
                    st.success(req.get('mcp_response'))
                else:
                    st.error(req.get('error_message', 'No response'))
            
            # JSON view
            if st.checkbox(f"Show JSON", key=f"json_{req.get('trace_id')}"):
                st.json(req)
    
    st.markdown("---")
    
    # Export options
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export as CSV
        if requests:
            df = pd.DataFrame(requests)
            csv = df.to_csv(index=False)
            
            if st.download_button(
                label="📄 Download CSV",
                data=csv,
                file_name=f"requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            ):
                api_client.log_export(f"Downloaded Request History as CSV ({len(requests)} records)")
    
    with col2:
        # Export as JSON
        if requests:
            json_str = json.dumps(requests, indent=2)
            
            if st.download_button(
                label="📋 Download JSON",
                data=json_str,
                file_name=f"requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            ):
                api_client.log_export(f"Downloaded Request History as JSON ({len(requests)} records)")

else:
    st.warning("⚠️ No requests found")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
