import os
import reflex as rx
from reflex_base.plugins.sitemap import SitemapPlugin
from reflex_components_radix.plugin import RadixThemesPlugin

db_url = os.getenv("DATABASE_URL", "").strip()
if not db_url or "dpg-" in db_url or os.getenv("FORCE_SQLITE", "true").lower() in ("1", "true", "yes"):
    db_url = "sqlite:///temis.db"
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

config = rx.Config(
    app_name="temis_web",
    db_url=db_url,
    telemetry_enabled=False,
    show_built_with_reflex=False,
    plugins=[RadixThemesPlugin()],
    disable_plugins=[SitemapPlugin],
)
