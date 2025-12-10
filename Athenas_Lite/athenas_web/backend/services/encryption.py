"""
Encryption utilities for API keys
Uses Fernet symmetric encryption with a master key
"""
from cryptography.fernet import Fernet
import os
import base64
from pathlib import Path

# Master key file location
MASTER_KEY_FILE = Path(__file__).parent.parent / "config" / ".master_key"

def get_or_create_master_key() -> bytes:
    """
    Get existing master key or create a new one.
    The master key is used to encrypt/decrypt API keys.
    """
    if MASTER_KEY_FILE.exists():
        with open(MASTER_KEY_FILE, "rb") as f:
            return f.read()
    else:
        # Generate new master key
        key = Fernet.generate_key()
        
        # Ensure config directory exists
        MASTER_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Save master key
        with open(MASTER_KEY_FILE, "wb") as f:
            f.write(key)
        
        # Set restrictive permissions (Unix-like systems)
        try:
            os.chmod(MASTER_KEY_FILE, 0o600)
        except:
            pass  # Windows doesn't support chmod
        
        return key

def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key using the master key.
    Returns base64-encoded encrypted string.
    """
    master_key = get_or_create_master_key()
    cipher = Fernet(master_key)
    
    encrypted = cipher.encrypt(api_key.encode())
    return base64.b64encode(encrypted).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt an API key using the master key.
    Takes base64-encoded encrypted string, returns plaintext API key.
    """
    master_key = get_or_create_master_key()
    cipher = Fernet(master_key)
    
    encrypted_bytes = base64.b64decode(encrypted_key.encode())
    decrypted = cipher.decrypt(encrypted_bytes)
    return decrypted.decode()
