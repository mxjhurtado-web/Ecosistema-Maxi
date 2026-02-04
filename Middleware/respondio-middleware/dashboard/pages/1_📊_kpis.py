"""
📊 KPIs & Analytics Page
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.auth import require_auth
from components.api_client import api_client
from components.page_setup import setup_page
from components.charts import (
    create_line_chart,
    create_histogram,
    create_pie_chart,
    create_area_chart
)
from components.metrics import create_stats_dataframe, aggregate_hourly_stats

# Setup page with ORBIT theme
setup_page("KPIs & Analytics", "📊")

# Require authentication
require_auth()

# Time range selector
col1, col2 = st.columns([3, 1])
with col1:
    time_range = st.selectbox(
        "Time Range",
        ["Last 24 Hours", "Last 7 Days", "Last 30 Days"],
        index=0
    )
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# Map time range to hours
hours_map = {
    "Last 24 Hours": 24,
    "Last 7 Days": 168,
    "Last 30 Days": 720
}
hours = hours_map[time_range]

# Fetch data
with st.spinner("Loading data..."):
    summary = api_client.get_summary()
    stats = api_client.get_stats(hours=hours)
    recent_requests = api_client.get_recent_requests(limit=1000)

# ============================================================
# Today's Metrics
# ============================================================

st.subheader("📈 Today's Metrics")

if summary:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Requests",
            f"{summary.get('total_requests', 0):,}",
            help="Total number of requests processed today"
        )
    
    with col2:
        success_rate = summary.get('success_rate', 0)
        st.metric(
            "Success Rate",
            f"{success_rate:.1f}%",
            delta=f"{success_rate - 95:.1f}%" if success_rate < 95 else None,
            delta_color="normal" if success_rate >= 95 else "inverse",
            help="Percentage of successful requests"
        )
    
    with col3:
        avg_latency = summary.get('avg_latency_ms', 0)
        st.metric(
            "Avg Latency",
            f"{avg_latency} ms",
            delta=f"{avg_latency - 1000} ms" if avg_latency > 1000 else None,
            delta_color="inverse" if avg_latency > 1000 else "normal",
            help="Average response time"
        )
    
    with col4:
        st.metric(
            "Errors",
            f"{summary.get('error_count', 0):,}",
            help="Total number of errors"
        )
else:
    st.warning("⚠️ Unable to fetch summary data")

st.markdown("---")

# ============================================================
# Request Volume Chart
# ============================================================

st.subheader("📊 Request Volume")

if stats:
    df = create_stats_dataframe(stats)
    
    if not df.empty:
        # Format hour for display
        df['hour_display'] = df['hour'].dt.strftime('%m-%d %H:%M')
        
        fig = create_line_chart(
            df,
            x='hour_display',
            y='total_requests',
            title=f'Request Volume ({time_range})'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for the selected time range")
else:
    st.warning("⚠️ Unable to fetch statistics")

# ============================================================
# Latency Distribution
# ============================================================

st.subheader("⏱️ Latency Distribution")

if recent_requests:
    latencies = [r.get('latency_ms', 0) for r in recent_requests if r.get('latency_ms')]
    
    if latencies:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = create_histogram(
                latencies,
                title='Latency Distribution (ms)',
                bins=50
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Percentiles")
            
            # Calculate percentiles
            sorted_latencies = sorted(latencies)
            p50 = sorted_latencies[len(sorted_latencies) // 2]
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
            
            st.metric("P50 (Median)", f"{p50} ms")
            st.metric("P95", f"{p95} ms")
            st.metric("P99", f"{p99} ms")
            st.metric("Max", f"{max(latencies)} ms")
    else:
        st.info("No latency data available")
else:
    st.warning("⚠️ Unable to fetch request data")

st.markdown("---")

# ============================================================
# Success Rate Trend
# ============================================================

st.subheader("🎯 Success Rate Trend")

if stats:
    df = create_stats_dataframe(stats)
    
    if not df.empty:
        df['hour_display'] = df['hour'].dt.strftime('%m-%d %H:%M')
        
        fig = create_area_chart(
            df,
            x='hour_display',
            y_success='success_count',
            y_error='error_count',
            title='Success vs Errors Over Time'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available")
else:
    st.warning("⚠️ Unable to fetch statistics")

# ============================================================
# Channel Distribution
# ============================================================

st.subheader("🌍 Channel Distribution")

if recent_requests:
    # Count by channel
    channels = {}
    for req in recent_requests:
        channel = req.get('channel', 'unknown')
        channels[channel] = channels.get(channel, 0) + 1
    
    if channels:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = create_pie_chart(
                labels=list(channels.keys()),
                values=list(channels.values()),
                title='Requests by Channel'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Channel Stats")
            for channel, count in sorted(channels.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(recent_requests)) * 100
                st.metric(channel.title(), f"{count:,} ({percentage:.1f}%)")
    else:
        st.info("No channel data available")
else:
    st.warning("⚠️ Unable to fetch request data")

st.markdown("---")

# ============================================================
# MCP Performance
# ============================================================

st.subheader("⚡ MCP Performance")

if recent_requests:
    # Filter requests with MCP latency
    mcp_latencies = [
        r.get('mcp_latency_ms', 0) 
        for r in recent_requests 
        if r.get('mcp_latency_ms') and r.get('mcp_latency_ms') > 0
    ]
    
    if mcp_latencies:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Avg MCP Latency", f"{int(sum(mcp_latencies) / len(mcp_latencies))} ms")
        
        with col2:
            st.metric("Min MCP Latency", f"{min(mcp_latencies)} ms")
        
        with col3:
            st.metric("Max MCP Latency", f"{max(mcp_latencies)} ms")
        
        with col4:
            # Calculate uptime based on successful calls
            successful = len([r for r in recent_requests if r.get('status') == 'ok'])
            uptime = (successful / len(recent_requests)) * 100 if recent_requests else 0
            st.metric("MCP Uptime", f"{uptime:.2f}%")
    else:
        st.info("No MCP performance data available")
else:
    st.warning("⚠️ Unable to fetch request data")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
