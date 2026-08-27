import reflex as rx

config = rx.Config(
    app_name="temis_web",
    db_url="sqlite:///temis.db",
    telemetry_enabled=False,
    disable_plugins=["sitemap"],
)
