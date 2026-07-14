import reflex as rx
from dashboard_reflex.components.sidebar import sidebar
from dashboard_reflex.components.navbar import navbar
from dashboard_reflex.components.styling import CONTENT_LAYOUT

def protected_layout(content: rx.Component, page_title: str, url_route: str) -> rx.Component:
    """Wrapper that wraps the content with Sidebar, Navbar, and layout styles."""
    return rx.box(
        # Sidebar (navigation)
        sidebar(url_route),
        
        # Main content area
        rx.box(
            # Topbar (health checks / metrics refresh)
            navbar(page_title),
            
            # Page-specific content
            content,
            style=CONTENT_LAYOUT
        ),
        style={
            "background_color": "#080B16",
            "min_height": "100vh",
            "width": "100%"
        }
    )
