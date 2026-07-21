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
    Attempts connecting via the IPv4 Supavisor Pooler (port 6543) first to prevent 
    'Network is unreachable' on IPv6-only direct connection hosts on platforms like Render.
    Falls back to direct connection if pooler connection fails.
    """
    from .config import settings
    import urllib.parse
    import psycopg2
    import socket
    
    uri = settings.SUPABASE_URI
    if not uri:
        raise ValueError("SUPABASE_URI setting is not configured")
        
    parsed = urllib.parse.urlparse(uri)
    hostname = parsed.hostname
    
    # Check if this is a supabase host
    if hostname and "supabase.co" in hostname:
        project_ref = hostname.split('.')[1]  # db.PROJECT_REF.supabase.co
        # Supavisor pooler host (AWS us-east-1 is the region for this project)
        pooler_host = "aws-0-us-east-1.pooler.supabase.com"
        # Supavisor user format: [username].[project-ref]
        pooler_user = f"{parsed.username}.{project_ref}"
        pooler_port = 6543
        
        logger.info(f"🔌 Attempting connection via Supabase IPv4 Pooler: {pooler_host}:{pooler_port} as {pooler_user}...")
        try:
            conn = psycopg2.connect(
                host=pooler_host,
                database=parsed.path.lstrip('/'),
                user=pooler_user,
                password=parsed.password,
                port=pooler_port,
                sslmode="require",
                connect_timeout=5
            )
            logger.info("✅ Connected to Supabase via IPv4 pooler successfully!")
            return conn
        except Exception as pool_err:
            logger.warning(f"⚠️ Connection via IPv4 pooler failed: {pool_err}. Falling back to direct connection...")
            
    # Fallback to direct hostname resolution (IPv4 standard socket gethostbyname)
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
