import json
import os
import logging

logger = logging.getLogger(__name__)

_compliance_scripts = None

def update_compliance_scripts_cache(new_scripts: dict):
    """Update in-memory scripts cache with fresh scripts from Google Sheets or Redis."""
    global _compliance_scripts
    if _compliance_scripts is None:
        _compliance_scripts = {}
    if isinstance(new_scripts, dict):
        _compliance_scripts.update(new_scripts)
        logger.info(f"Updated in-memory compliance scripts cache ({len(new_scripts)} entries)")

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


# Pre-compiled high-quality English translations for core compliance scripts (LNG.01 / LNG.02)
PRECOMPILED_EN_SCRIPTS = {
    "CU.A1": "Thank you for contacting Maxitransfers.\n\nI am Max, your virtual assistant. To begin helping you, could you please provide your full name?\n\nBy continuing in this chat, you accept the processing of your data under our Privacy Policy: (link-coming soon).\n\n• For your security, the session will automatically close after 10 minutes of inactivity.\n• You may end this conversation at any time by sending the word 'End'.\n• If you wish to speak with an advisor, send the message 'Speak with an advisor'.",
    "SC.001": "I did not quite understand your message. Please share the details of your request so I can assist you properly.",
    "SC.002": "I'm sorry, I still can't understand your request. I will transfer your conversation to a customer service representative to assist you directly.",
    "SC.005": "I'm still here to help. Please share the requested information to continue with your inquiry.",
    "SC.006": "To better assist you, could you please provide more information about what you need?",
    "SC.010": "To continue, I need to validate some information. Could you please share the full name of the person who sent the money and the full name of the recipient?",
    "SC.010.1": "To continue, I need to validate some information. Could you please share the full name of the person who made the payment and the name of the company?",
    "SC.010.2": "To continue, I need to validate some information. Could you please share the phone number of the person who made the top-up and the number to which it was sent?",
    "SC.011": "I understand your request. This case requires attention from a specialized department.\n\nI will route your request so an advisor can follow up and contact you as soon as possible.\nThank you for contacting Maxitransfers. Have a great day.",
    "SC.012": "It was not possible to process your request with the provided code. I will transfer you to one of our representatives. Please wait a moment.",
    "SC.013": "I will transfer you to one of our representatives. Please wait a moment.",
    "SC.019": "We understand your inquiry. However, for security reasons, we can only share transaction information with the person who sent the money. We suggest asking them to contact us directly through this channel so we can assist appropriately. Thank you for your understanding.",
    "SC.020": "The timeframe to collect the money transfer has expired. I will transfer you to an advisor. Please wait a moment.",
    "SC.027": "Our representatives are currently unavailable. An advisor will follow up on your request as soon as service resumes. Thank you for your patience.",
    "SC.027.1": "I'm sorry for what happened. Our representatives are currently unavailable.\n\nPlease share the following information:\n1. Your full name.\n2. Details of what occurred with your report.\n\nIf known:\n3. Money transfer code(s).\n4. Agency number from where you are contacting us.\n\nYour request has been registered and an advisor will assist you immediately through this chat as soon as our operational hours begin. Thank you for your patience.",
    "SC.029": "I could not locate the information with the details provided. Please verify and send them again to perform a new search.",
    "SC.030": "Your request is a high priority for us. I will transfer you to one of our representatives. Please wait a moment.",
    "SC.030.1": "I'm sorry for what happened. I will route your request to a specialized department, and an advisor will contact you through a direct channel.\n\nPlease share the following information:\n1. Your full name.\n2. Details of what occurred with your report.\n\nIf known:\n3. Money transfer code(s).\n4. Agency number from where you are contacting us.",
    "SC.030.2": "I'm sorry for what happened. I will route your request to an advisor.\n\nPlease share the following information:\n1. Your full name.\n2. Details of what occurred with your report.\n\nIf known:\n3. Money transfer code(s).\n4. Agency number from where you are contacting us.",
    "SC.031": "For security reasons, this request must be handled in person. Please visit the Maxitransfers agency where you placed your transfer to receive assistance. Thank you for your understanding.",
    "SC.031.1": "For security reasons, this request must be handled in person. Please ask the sender of the transfer to visit the Maxitransfers agency where they made the operation to receive assistance. Thank you for your understanding.",
    "SC.034": "How would you rate the service received today on a scale from 1 to 5, where 5 is excellent and 1 is bad?",
    "SC.035": "Thank you for rating our service. We would appreciate it if you could briefly share what we can improve to provide a better experience.",
    "SC.036": "Thank you for contacting Maxitransfers. Have a great day!"
}


async def detect_language(user_text: str, contact_id: str = None) -> str:
    """
    Detects the language of incoming user_text and persists session preference in Redis (LNG.01 / LNG.02).
    Returns ISO-639-1 language code ('es', 'en', etc.). Default is 'es'.
    """
    if not user_text:
        return "es"

    import re
    from shared.redis_client import get_redis_client
    redis = await get_redis_client()

    cleaned = user_text.strip()
    cleaned_lower = cleaned.lower()

    # 1. Expand Spanish & English keyword dictionaries for reliable detection
    en_words = {
        "the", "my", "please", "is", "are", "have", "can", "need", "want", "money", 
        "status", "send", "sent", "help", "how", "what", "where", "why", "who", "when", 
        "check", "tracking", "claim", "number", "transfer", "receiver", "sender", "hello",
        "hi", "good", "morning", "afternoon", "thanks", "thank", "you", "scam", "fraud"
    }
    es_words = {
        "el", "la", "los", "las", "un", "una", "por", "favor", "está", "estan",
        "tengo", "puedo", "necesito", "quiero", "dinero", "estatus", "envio", "envío", "enviar", "envié",
        "ayuda", "cómo", "como", "qué", "que", "dónde", "donde", "cuándo", "cuando",
        "clave", "rastreo", "remesa", "transferencia", "receptor", "remitente", "hola",
        "buenos", "días", "dias", "gracias", "tardes", "noches", "cancelacion", "modificacion", "agencia"
    }

    tokens = set(re.findall(r'\b[a-zñáéíóú]+\b', cleaned_lower))
    en_matches = len(tokens.intersection(en_words))
    es_matches = len(tokens.intersection(es_words))

    # If current turn has clear Spanish indicators, reset session language to Spanish (LNG.02)
    if es_matches > en_matches or es_matches >= 2 or any(w in cleaned_lower for w in ["gracias", "hola", "buenos días", "buenas tardes", "por favor", "necesito"]):
        if redis and contact_id and contact_id != "-1":
            try:
                await redis.set(f"session_lang:{contact_id}", "es", ex=3600)
            except Exception:
                pass
        return "es"

    # Check Redis for established session language preference if contact_id is provided
    if redis and contact_id and contact_id != "-1":
        try:
            cached_lang = await redis.get(f"session_lang:{contact_id}")
            if cached_lang:
                session_lang_str = cached_lang.decode('utf-8').strip().lower()
                if session_lang_str == "en" and es_matches == 0:
                    return "en"
        except Exception as e:
            logger.warning(f"Error checking session_lang in Redis: {e}")

    # Check for single-word English triggers (LNG.01)
    if any(term in cleaned_lower for term in ["hello", "good morning", "good afternoon", "good evening", "english", "speak english"]):
        if redis and contact_id and contact_id != "-1":
            try:
                await redis.set(f"session_lang:{contact_id}", "en", ex=3600)
            except Exception:
                pass
        logger.info(f"🌐 Instant English trigger detected for: '{cleaned[:30]}'")
        return "en"

    detected_lang = "es"
    if en_matches > es_matches and en_matches >= 2:
        detected_lang = "en"

    # Save to Redis if detected as English
    if detected_lang == "en" and redis and contact_id and contact_id != "-1":
        try:
            await redis.set(f"session_lang:{contact_id}", "en", ex=3600)
        except Exception:
            pass

    return detected_lang


async def translate_script_if_needed(script_text: str, user_text: str, contact_id: str = None) -> str:
    """
    Detects user_text language or active session language. If not Spanish ('es'), translates script_text to target language.
    Uses instant pre-compiled dictionary for official compliance scripts (LNG.01 / LNG.02).
    """
    if not script_text:
        return script_text

    target_lang = await detect_language(user_text or "", contact_id=contact_id)
    if target_lang == "es":
        return script_text

    # 1. Instant lookup in pre-compiled English script dictionary
    if target_lang == "en":
        comp_scripts = get_compliance_scripts()
        for code, full_es_txt in comp_scripts.items():
            if script_text.strip().replace('\r\n', '\n') == full_es_txt.strip().replace('\r\n', '\n'):
                if code in PRECOMPILED_EN_SCRIPTS:
                    logger.info(f"🌐 Fast pre-compiled English script delivered for {code}")
                    return PRECOMPILED_EN_SCRIPTS[code]

    # 2. Translate dynamically using Gemini LLM if not pre-compiled
    try:
        import httpx
        import re
        from .config import settings
        from shared.redis_client import get_redis_client
        redis = await get_redis_client()
        redis_key = await redis.get("config:mcp:gemini_api_key")
        api_key = redis_key.decode('utf-8') if redis_key else settings.GEMINI_API_KEY
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
                    logger.info(f"🌐 Translated script to '{target_lang}' successfully via Gemini")
                    return translated
    except Exception as e:
        logger.error(f"Error translating script to '{target_lang}': {e}")

    return script_text



def get_db_connection():
    """
    Establishes connection to Supabase database.
    Prioritizes SUPABASE_POOLER_URI if set, otherwise tries default pooler and direct host
    with strict 1.5s timeouts to prevent blocking webhooks.
    """
    from .config import settings
    import urllib.parse
    import psycopg2
    import socket
    import os

    # 1. Explicit pooler URI set in environment
    pooler_uri = os.environ.get("SUPABASE_POOLER_URI", "")
    if pooler_uri:
        logger.info("🔌 Connecting via SUPABASE_POOLER_URI...")
        try:
            return psycopg2.connect(pooler_uri, connect_timeout=3, sslmode="require")
        except Exception as e:
            logger.warning(f"⚠️ SUPABASE_POOLER_URI failed: {e}")

    uri = settings.SUPABASE_URI
    if not uri:
        raise ValueError("SUPABASE_URI setting is not configured")

    parsed = urllib.parse.urlparse(uri)
    hostname = parsed.hostname
    dbname = parsed.path.lstrip('/')

    # 2. Try default pooler host (us-east-1) with fast timeout
    if hostname and "supabase.co" in hostname:
        project_ref = hostname.split('.')[1]
        pooler_user = f"{parsed.username}.{project_ref}"
        pooler_host = "aws-0-us-east-1.pooler.supabase.com"
        try:
            return psycopg2.connect(
                host=pooler_host,
                database=dbname,
                user=pooler_user,
                password=parsed.password,
                port=6543,
                sslmode="require",
                connect_timeout=2
            )
        except Exception as pool_err:
            logger.warning(f"⚠️ Primary pooler connection failed: {pool_err}")

    # 3. Direct connection attempt with fast timeout
    ip_address = hostname
    if hostname:
        try:
            ip_address = socket.gethostbyname(hostname)
        except Exception:
            pass

    return psycopg2.connect(
        host=ip_address,
        database=dbname,
        user=parsed.username,
        password=parsed.password,
        port=parsed.port or 5432,
        sslmode="require",
        connect_timeout=2
    )


