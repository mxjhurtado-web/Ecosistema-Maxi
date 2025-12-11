"""
API Key Manager for MaxiBot
Simplified version of ATHENAS Lite's API rotation system
Manages rotating API keys per user with local JSON storage
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class APIKeyManager:
    """Manages rotating API keys per user with local JSON storage"""
    
    def __init__(self, storage_file="maxibot_api_keys.json"):
        self.storage_file = storage_file
        self.keys_cache = {}  # {user_email: {keys: [...], current_index: 0, last_reset: date}}
        self._load_storage()
    
    def _load_storage(self):
        """Load API keys from JSON file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.keys_cache = json.load(f)
                print(f"✅ Loaded API keys from {self.storage_file}")
            except Exception as e:
                print(f"⚠️ Error loading API keys: {e}")
                self.keys_cache = {}
        else:
            self.keys_cache = {}
    
    def _save_storage(self):
        """Save API keys to JSON file"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.keys_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving API keys: {e}")
    
    def load_user_keys(self, user_email: str) -> List[Dict]:
        """
        Load user's API keys and check for daily reset.
        Returns list of keys with status.
        """
        if not user_email:
            return []
        
        if user_email not in self.keys_cache:
            self.keys_cache[user_email] = {
                "keys": [],
                "current_index": 0,
                "last_reset": None
            }
        
        user_data = self.keys_cache[user_email]
        
        # Check for daily reset
        today = datetime.now().strftime("%Y-%m-%d")
        if user_data.get("last_reset") != today and user_data["keys"]:
            print(f"📅 New day detected ({today}). Resetting keys for {user_email}")
            for key in user_data["keys"]:
                key["status"] = "active"
            user_data["last_reset"] = today
            user_data["current_index"] = 0
            self._save_storage()
        
        return user_data["keys"]
    
    def add_key(self, user_email: str, api_key: str) -> Tuple[bool, str]:
        """
        Add a new API key for the user.
        Maximum 4 keys allowed.
        Returns: (success, message)
        """
        if not user_email:
            return False, "No hay usuario autenticado"
        
        keys = self.load_user_keys(user_email)
        
        # Check limit
        if len(keys) >= 4:
            return False, "Máximo 4 API keys permitidas"
        
        # Check for duplicates
        if any(k["key"] == api_key for k in keys):
            return False, "Esta API key ya existe"
        
        # Add new key
        keys.append({
            "key": api_key,
            "status": "active",
            "added_at": datetime.now().isoformat()
        })
        
        self.keys_cache[user_email]["keys"] = keys
        self._save_storage()
        
        print(f"✅ Added API key #{len(keys)} for {user_email}")
        return True, f"API key #{len(keys)} agregada exitosamente"
    
    def remove_key(self, user_email: str, key_index: int) -> Tuple[bool, str]:
        """
        Remove an API key by index.
        Returns: (success, message)
        """
        if not user_email:
            return False, "No hay usuario autenticado"
        
        keys = self.load_user_keys(user_email)
        
        if key_index < 0 or key_index >= len(keys):
            return False, "Índice inválido"
        
        # Remove key
        removed_key = keys.pop(key_index)
        self.keys_cache[user_email]["keys"] = keys
        
        # Reset current index if needed
        if self.keys_cache[user_email]["current_index"] >= len(keys):
            self.keys_cache[user_email]["current_index"] = 0
        
        self._save_storage()
        
        print(f"🗑️ Removed API key #{key_index + 1} for {user_email}")
        return True, "API key eliminada exitosamente"
    
    def get_active_key(self, user_email: str) -> Optional[str]:
        """
        Get current active API key for the user.
        Returns None if no active keys available.
        """
        if not user_email:
            return None
        
        keys = self.load_user_keys(user_email)
        
        if not keys:
            return None
        
        # Find first active key
        for key in keys:
            if key["status"] == "active":
                return key["key"]
        
        # No active keys
        print(f"⚠️ No active API keys for {user_email}")
        return None
    
    def rotate_key(self, user_email: str, current_key: str) -> Tuple[bool, Optional[str]]:
        """
        Mark current key as exhausted and rotate to next active key.
        Returns: (success, new_key)
        """
        if not user_email:
            return False, None
        
        keys = self.load_user_keys(user_email)
        
        if not keys:
            return False, None
        
        # Find and mark current key as exhausted
        current_index = -1
        for i, k in enumerate(keys):
            if k["key"] == current_key:
                k["status"] = "exhausted"
                current_index = i
                print(f"🔴 Marked API key #{i + 1} as exhausted")
                break
        
        # Find next active key
        for offset in range(1, len(keys) + 1):
            next_index = (current_index + offset) % len(keys)
            if keys[next_index]["status"] == "active":
                self.keys_cache[user_email]["current_index"] = next_index
                self._save_storage()
                print(f"🔄 Rotated to API key #{next_index + 1} for {user_email}")
                return True, keys[next_index]["key"]
        
        # No active keys left
        print(f"⚠️ All API keys exhausted for {user_email}")
        self._save_storage()
        return False, None
    
    def get_keys_status(self, user_email: str) -> Dict:
        """
        Get status of all keys for UI display.
        Returns: {total, active, exhausted, keys: [...]}
        """
        if not user_email:
            return {"total": 0, "active": 0, "exhausted": 0, "keys": []}
        
        keys = self.load_user_keys(user_email)
        
        active_count = sum(1 for k in keys if k["status"] == "active")
        
        # Mask keys for security (show first 4 and last 4 chars)
        masked_keys = []
        for i, k in enumerate(keys):
            key_str = k["key"]
            if len(key_str) > 8:
                preview = f"{key_str[:4]}...{key_str[-4:]}"
            else:
                preview = "***"
            
            masked_keys.append({
                "index": i,
                "preview": preview,
                "status": k["status"],
                "added_at": k.get("added_at", "")
            })
        
        return {
            "total": len(keys),
            "active": active_count,
            "exhausted": len(keys) - active_count,
            "keys": masked_keys
        }
    
    def reset_all_keys(self, user_email: str) -> Tuple[bool, str]:
        """
        Reset all keys to active status (manual reset).
        Returns: (success, message)
        """
        if not user_email:
            return False, "No hay usuario autenticado"
        
        keys = self.load_user_keys(user_email)
        
        if not keys:
            return False, "No hay keys para resetear"
        
        # Reset all to active
        for key in keys:
            key["status"] = "active"
        
        # Update reset date
        today = datetime.now().strftime("%Y-%m-%d")
        self.keys_cache[user_email]["last_reset"] = today
        self.keys_cache[user_email]["current_index"] = 0
        
        self._save_storage()
        
        print(f"🔄 Reset all API keys for {user_email}")
        return True, f"Se resetearon {len(keys)} API keys a estado activo"


# Global instance
_api_key_manager = None

def get_api_key_manager():
    """Get or create singleton instance of APIKeyManager"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager
