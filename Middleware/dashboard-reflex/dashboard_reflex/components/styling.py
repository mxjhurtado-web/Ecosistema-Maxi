import reflex as rx

# --- DESIGN SYSTEM COLOR PALETTE ---
BG_COLOR = rx.color_mode_cond("#F4F6F9", "#080B16")          # Soft gray-blue vs Deep cosmic black
ACCENT_BLUE = "#00D9FF"       # Electric cyan
ACCENT_PURPLE = "#7C3AED"     # Accent violet
TEXT_COLOR = rx.color_mode_cond("#1A202C", "#FFFFFF")        # Dark slate vs White
TEXT_MUTED = rx.color_mode_cond("#5A6A85", "#8E9BB8")        # Dark gray-blue vs Soft blue-gray
CARD_BG = rx.color_mode_cond("rgba(255, 255, 255, 0.85)", "rgba(16, 20, 38, 0.6)")  # White glass vs dark glass
BORDER_COLOR = rx.color_mode_cond("rgba(0, 217, 255, 0.25)", "rgba(0, 217, 255, 0.15)") # Cyan border highlight

# --- CSS HELPER PROPERTIES ---
GLASS_EFFECT = {
    "background_color": CARD_BG,
    "backdrop_filter": "blur(12px)",
    "border": rx.color_mode_cond("1px solid rgba(0, 217, 255, 0.25)", "1px solid rgba(0, 217, 255, 0.15)"),
    "box_shadow": rx.color_mode_cond("0 8px 32px 0 rgba(0, 0, 0, 0.05)", "0 8px 32px 0 rgba(0, 0, 0, 0.37)"),
    "border_radius": "16px",
    "color": TEXT_COLOR,
}

SIDEBAR_STYLE = {
    "width": "260px",
    "height": "100vh",
    "position": "fixed",
    "left": "0",
    "top": "0",
    "background_color": rx.color_mode_cond("#FFFFFF", "#0C0F1D"),
    "border_right": rx.color_mode_cond("1px solid rgba(0, 217, 255, 0.25)", "1px solid rgba(0, 217, 255, 0.15)"),
    "padding": "24px 16px",
    "z_index": "100",
    "color": TEXT_COLOR,
}

CONTENT_LAYOUT = {
    "margin_left": "260px",
    "padding": "32px",
    "min_height": "100vh",
    "background_color": BG_COLOR,
    "color": TEXT_COLOR,
}

# --- REUSABLE CUSTOM STYLED CONTAINERS ---
def glass_container(*children, **kwargs) -> rx.Component:
    """Wrapper that returns a container styled with glassmorphism."""
    custom_style = GLASS_EFFECT.copy()
    if "style" in kwargs:
        custom_style.update(kwargs.pop("style"))
    return rx.box(*children, style=custom_style, **kwargs)

def gradient_heading(text: str, size: str = "7") -> rx.Component:
    """Returns a heading with a sleek metallic gradient effect."""
    return rx.heading(
        text,
        size=size,
        style={
            "background": f"linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_PURPLE} 100%)",
            "background_clip": "text",
            "-webkit-background-clip": "text",
            "-webkit-text-fill-color": "transparent",
            "font_weight": "800",
            "letter_spacing": "-0.02em",
        }
    )

def status_badge(status: rx.Var) -> rx.Component:
    """Returns a badge according to state variable value."""
    color = rx.cond(
        (status == "healthy") | (status == "online") | (status == "success") | (status == "ok") | (status == "paid") | (status == "pagado"),
        "green",
        rx.cond(
            (status == "warning") | (status == "circuit breaker: open") | (status == "unclaimed hold") | (status == "stand by"),
            "amber",
            "ruby"
        )
    )
    return rx.badge(
        status,
        color_scheme=color,
        variant="soft",
        size="2",
        style={"border_radius": "9999px", "font_weight": "bold"}
    )
