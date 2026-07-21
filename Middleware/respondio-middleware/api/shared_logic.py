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
    """Establishes connection to Supabase database forcing IPv4 resolution to prevent 'Network is unreachable' on IPv6 platforms."""
    from .config import settings
    import socket
    import urllib.parse
    import psycopg2
    
    uri = settings.SUPABASE_URI
    if not uri:
        raise ValueError("SUPABASE_URI setting is not configured")
        
    parsed = urllib.parse.urlparse(uri)
    hostname = parsed.hostname
    
    ip_address = hostname
    if hostname:
        try:
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET)
            if addr_info:
                ip_address = addr_info[0][4][0]
                logger.info(f"Resolved Supabase host '{hostname}' to IPv4 '{ip_address}'")
        except Exception as e:
            logger.warning(f"Failed to resolve IPv4 for host '{hostname}': {e}. Using raw hostname.")
            
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
