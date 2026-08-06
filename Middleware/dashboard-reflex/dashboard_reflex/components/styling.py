import reflex as rx

# --- DESIGN SYSTEM COLOR PALETTE ---
BG_COLOR = rx.color_mode_cond("#F8FAFC", "#090D16")          # Soft slate gray vs Deep cosmic black
ACCENT_BLUE = "#38BDF8"       # Electric cyan (Tailwind Sky 400)
ACCENT_PURPLE = "#A855F7"     # Accent violet (Purple 500)
TEXT_COLOR = rx.color_mode_cond("#0F172A", "#F8FAFC")        # Dark slate 900 vs Slate 50
TEXT_MUTED = rx.color_mode_cond("#64748B", "#94A3B8")        # Slate 500 vs Slate 400 (High contrast)
CARD_BG = rx.color_mode_cond("#FFFFFF", "rgba(15, 23, 42, 0.75)")  # Clean white vs dark slate glass
BORDER_COLOR = rx.color_mode_cond("#E2E8F0", "rgba(56, 189, 248, 0.2)") # Neutral light border vs subtle cyan glow

# --- CSS HELPER PROPERTIES ---
GLASS_EFFECT = {
    "background_color": CARD_BG,
    "backdrop_filter": "blur(12px)",
    "border": rx.color_mode_cond("1px solid #E2E8F0", "1px solid rgba(56, 189, 248, 0.2)"),
    "box_shadow": rx.color_mode_cond("0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05)", "0 8px 32px 0 rgba(0, 0, 0, 0.4)"),
    "border_radius": "14px",
    "color": TEXT_COLOR,
}

SIDEBAR_STYLE = {
    "width": "260px",
    "height": "100vh",
    "position": "fixed",
    "left": "0",
    "top": "0",
    "background_color": rx.color_mode_cond("#FFFFFF", "#0B0F19"),
    "border_right": rx.color_mode_cond("1px solid #E2E8F0", "1px solid rgba(56, 189, 248, 0.15)"),
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
