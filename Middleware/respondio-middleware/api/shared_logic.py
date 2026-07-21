import json
import os
import logging

logger = logging.getLogger(__name__)

_compliance_scripts = None

def get_compliance_scripts():
    """Load and cache compliance scripts from JSON."""
    global _compliance_scripts
    if _compliance_scripts is None:
        try:
            # Use absolute path for reliability
            script_path = os.path.join(os.path.dirname(__file__), "compliance_scripts.json")
            if os.path.exists(script_path):
                with open(script_path, "r", encoding="utf-8") as f:
                    _compliance_scripts = json.load(f)
                logger.info("Compliance scripts loaded successfully")
            else:
                logger.warning(f"Compliance scripts file not found at {script_path}")
                _compliance_scripts = {}
        except Exception as e:
            logger.error(f"Error loading compliance scripts: {str(e)}")
            _compliance_scripts = {}
    return _compliance_scripts

def resolve_script_text(script_text: str) -> str:
    """If script_text is a script code (e.g. 'SC 018' or 'SC.018'), resolve it to full text from compliance_scripts.json."""
    if not script_text:
        return ""
    comp_scripts = get_compliance_scripts()
    clean = script_text.strip()
    clean_dot = clean.replace(" ", ".")
    if clean_dot in comp_scripts:
        return comp_scripts[clean_dot]
    if clean in comp_scripts:
        return comp_scripts[clean]
    return script_text


def get_db_connection():
    """
    Establishes connection to Supabase database.
    Priority:
    1. SUPABASE_POOLER_URI env var (Transaction mode URI from Supabase Dashboard > Settings > Database > Connection Pooling)
    2. Auto-detect: try multiple Supabase Supavisor pooler regions (IPv4-compatible)
    3. Fallback: direct connection to SUPABASE_URI (may fail on IPv6-only hosts like Render)
    """
    from .config import settings
    import urllib.parse
    import psycopg2
    import socket
    import os

    # ─── Priority 1: explicit pooler URI set in environment ────────────────────
    pooler_uri = os.environ.get("SUPABASE_POOLER_URI", "")
    if pooler_uri:
        logger.info("🔌 Connecting via SUPABASE_POOLER_URI (explicit pooler)...")
        try:
            conn = psycopg2.connect(pooler_uri, connect_timeout=8, sslmode="require")
            logger.info("✅ Connected via SUPABASE_POOLER_URI successfully!")
            return conn
        except Exception as e:
            logger.warning(f"⚠️ SUPABASE_POOLER_URI connection failed: {e}. Trying auto-detect...")

    # ─── Priority 2: auto-detect pooler region ─────────────────────────────────
    uri = settings.SUPABASE_URI
    if not uri:
        raise ValueError("SUPABASE_URI setting is not configured")

    parsed = urllib.parse.urlparse(uri)
    hostname = parsed.hostname

    if hostname and "supabase.co" in hostname:
        project_ref = hostname.split('.')[1]  # db.PROJECT_REF.supabase.co
        pooler_user = f"{parsed.username}.{project_ref}"
        pooler_port = 6543
        dbname = parsed.path.lstrip('/')

        # Try each AWS region Supabase supports
        regions = [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-central-1",
            "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
            "ca-central-1", "sa-east-1"
        ]
        for region in regions:
            pooler_host = f"aws-0-{region}.pooler.supabase.com"
            logger.info(f"🔌 Trying pooler region {region}: {pooler_host}:{pooler_port} as {pooler_user}...")
            try:
                conn = psycopg2.connect(
                    host=pooler_host,
                    database=dbname,
                    user=pooler_user,
                    password=parsed.password,
                    port=pooler_port,
                    sslmode="require",
                    connect_timeout=4
                )
                logger.info(f"✅ Connected via Supabase pooler (region: {region})!")
                return conn
            except Exception as region_err:
                logger.debug(f"  Region {region} failed: {region_err}")

        logger.warning("⚠️ All pooler regions failed. Falling back to direct connection...")

    # ─── Priority 3: direct connection (may fail on IPv6-only Render hosts) ────
    ip_address = hostname
    if hostname:
        try:
            ip_address = socket.gethostbyname(hostname)
        except Exception as dns_err:
            logger.warning(f"Failed to resolve host '{hostname}': {dns_err}")

    dbname = parsed.path.lstrip('/')
    user = parsed.username
    password = parsed.password
    port = parsed.port or 5432

    return psycopg2.connect(
        host=ip_address,
        database=dbname,
        user=user,
        password=password,
        port=port,
        sslmode="require"
    )

