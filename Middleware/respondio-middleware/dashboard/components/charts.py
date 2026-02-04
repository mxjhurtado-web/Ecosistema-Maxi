"""
Reusable chart components using Plotly.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict


def create_line_chart(data: pd.DataFrame, x: str, y: str, title: str):
    """Create a line chart"""
    fig = px.line(
        data,
        x=x,
        y=y,
        title=title,
        markers=True
    )
    
    fig.update_layout(
        hovermode='x unified',
        showlegend=False,
        height=400
    )
    
    return fig


def create_bar_chart(data: pd.DataFrame, x: str, y: str, title: str):
    """Create a bar chart"""
    fig = px.bar(
        data,
        x=x,
        y=y,
        title=title
    )
    
    fig.update_layout(
        showlegend=False,
        height=400
    )
    
    return fig


def create_histogram(data: List[float], title: str, bins: int = 50):
    """Create a histogram"""
    fig = go.Figure(data=[go.Histogram(
        x=data,
        nbinsx=bins,
        marker_color='rgb(55, 83, 109)'
    )])
    
    fig.update_layout(
        title=title,
        xaxis_title="Latency (ms)",
        yaxis_title="Count",
        height=400
    )
    
    return fig


def create_pie_chart(labels: List[str], values: List[int], title: str):
    """Create a pie chart"""
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3
    )])
    
    fig.update_layout(
        title=title,
        height=400
    )
    
    return fig


def create_area_chart(data: pd.DataFrame, x: str, y_success: str, y_error: str, title: str):
    """Create an area chart for success/error trends"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data[x],
        y=data[y_success],
        fill='tozeroy',
        name='Success',
        line=dict(color='rgb(34, 197, 94)')
    ))
    
    fig.add_trace(go.Scatter(
        x=data[x],
        y=data[y_error],
        fill='tozeroy',
        name='Errors',
        line=dict(color='rgb(239, 68, 68)')
    ))
    
    fig.update_layout(
        title=title,
        hovermode='x unified',
        height=400
    )
    
    return fig


def create_gauge(value: float, title: str, max_value: float = 100):
    """Create a gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={'text': title},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, max_value]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, max_value * 0.6], 'color': "lightgray"},
                {'range': [max_value * 0.6, max_value * 0.8], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    ))
    
    fig.update_layout(height=300)
    
    return fig
