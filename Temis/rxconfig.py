import os
import reflex as rx
from reflex_base.plugins.sitemap import SitemapPlugin

db_url = os.getenv("DATABASE_URL", "sqlite:///temis.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

config = rx.Config(
    app_name="temis_web",
    db_url=db_url,
    telemetry_enabled=False,
    disable_plugins=[SitemapPlugin],
)
