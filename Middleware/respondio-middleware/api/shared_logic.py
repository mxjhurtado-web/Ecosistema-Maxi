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


async def detect_language(user_text: str) -> str:
    """
    Detects the language of the incoming user_text.
    Returns ISO-639-1 language code (e.g. 'es', 'en', 'fr', etc.) or 'es' if default/ambiguous.
    Uses quick heuristic first for English/Spanish, then Gemini if ambiguous.
    """
    if not user_text or len(user_text.strip()) < 3:
        return "es"

    import re
    cleaned = user_text.lower().strip()

    # Common English stopwords/keywords heuristic
    en_words = {
        "the", "my", "please", "is", "are", "have", "can", "need", "want", "money", 
        "status", "send", "sent", "help", "how", "what", "where", "why", "who", "when", 
        "check", "tracking", "claim", "number", "transfer", "receiver", "sender", "hello",
        "hi", "good", "morning", "afternoon", "thanks", "thank", "you"
    }
    # Common Spanish stopwords/keywords
    es_words = {
        "el", "la", "los", "las", "un", "una", "por", "favor", "está", "estan",
        "tengo", "puedo", "necesito", "quiero", "dinero", "estatus", "enviar", "envié",
        "ayuda", "cómo", "como", "qué", "que", "dónde", "donde", "cuándo", "cuando",
        "clave", "rastreo", "remesa", "transferencia", "receptor", "remitente", "hola",
        "buenos", "días", "gracias"
    }

    tokens = set(re.findall(r'\b[a-zñáéíóú]+\b', cleaned))
    en_matches = len(tokens.intersection(en_words))
    es_matches = len(tokens.intersection(es_words))

    if en_matches > es_matches and en_matches >= 2:
        logger.info(f"🌐 Fast heuristic detected English ('en') for input: '{user_text[:50]}...'")
        return "en"
    if es_matches > en_matches:
        return "es"

    # If non-trivial text with 3+ words, query Gemini for language detection
    if len(cleaned.split()) >= 3:
        try:
            import httpx
            from .config import settings
            api_key = settings.GEMINI_API_KEY
            if api_key:
                url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
                prompt = (
                    "Identify the language of this customer message. "
                    "Respond ONLY with the 2-letter ISO 639-1 code (e.g., 'es', 'en', 'fr', 'pt'). "
                    f"Message: \"{user_text[:200]}\""
                )
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        res_json = resp.json()
                        lang_code = res_json["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
                        lang_code = re.sub(r'[^a-z]', '', lang_code)[:2]
                        if lang_code:
                            logger.info(f"🌐 Gemini detected language: '{lang_code}' for user_text")
                            return lang_code
        except Exception as e:
            logger.warning(f"Error in Gemini language detection: {e}")

    return "es"


async def translate_script_if_needed(script_text: str, user_text: str) -> str:
    """
    Detects user_text language. If not Spanish ('es'), translates script_text to target language using Gemini.
    Preserves placeholders, proper names, order numbers, and formal customer service tone.
    """
    if not script_text or not user_text:
        return script_text

    target_lang = await detect_language(user_text)
    if target_lang == "es":
        return script_text

    try:
        import httpx
        import re
        from .config import settings
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("Gemini API key not configured, skipping translation")
            return script_text

        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
        prompt = (
            f"You are an expert customer service translator for a money transfer business.\n"
            f"Translate the following response from Spanish to the ISO language '{target_lang}'.\n\n"
            f"Strict Rules:\n"
            f"1. Preserve polite and formal customer service tone (e.g., formal 'You' / 'Sir/Madam').\n"
            f"2. Keep all transaction codes, order numbers, names, phone numbers, and URLs EXACTLY as they appear.\n"
            f"3. Return ONLY the translated text without quote marks, preambles, or explanations.\n\n"
            f"Spanish response to translate:\n{script_text}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                res_json = resp.json()
                translated = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                if translated:
                    logger.info(f"🌐 Translated script to '{target_lang}' successfully")
                    return translated
            else:
                logger.warning(f"Gemini translation HTTP error status: {resp.status_code}")
    except Exception as e:
        logger.error(f"Error translating script to '{target_lang}': {e}")

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

