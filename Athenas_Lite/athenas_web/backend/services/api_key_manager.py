"""
API Key Manager Service
Manages rotating API keys for Gemini with encryption and user persistence
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from .encryption import encrypt_api_key, decrypt_api_key

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Manages rotating API keys per user with encryption"""
    
    def __init__(self, storage_service):
        self.storage = storage_service
        self.keys_cache = {}  # Cache: {user_id: {keys, current_index}}
    
    async def load_user_keys(self, user_id: int) -> List[Dict]:
        """
        Load user's API keys from database.
        Automatically resets status if it's a new day.
        Returns list of decrypted keys with status.
        """
        # Check cache first
        if user_id in self.keys_cache:
            return self.keys_cache[user_id]["keys"]
        
        # Load from database
        encrypted_keys = await self.storage.get_user_api_keys(user_id)
        
        # Decrypt keys
        keys = []
        for ek in encrypted_keys:
            try:
                decrypted_key = decrypt_api_key(ek["api_key_encrypted"])
                keys.append({
                    "id": ek["id"],
                    "key": decrypted_key,
                    "status": ek["status"],
                    "key_index": ek["key_index"],
                    "last_used_at": ek.get("last_used_at")
                })
            except Exception as e:
                logger.error(f"Error decrypting key {ek['id']}: {e}")
                continue
        
        # Check for daily reset
        today = datetime.now().strftime("%Y-%m-%d")
        last_reset = await self.storage.get_user_last_reset_date(user_id)
        
        if last_reset != today and keys:
            logger.info(f"📅 New day detected ({today}). Resetting keys for user {user_id}")
            for key in keys:
                key["status"] = "active"
            
            # Update all keys in database
            for key in keys:
                await self.storage.update_api_key_status(key["id"], "active")
            
            await self.storage.update_user_reset_date(user_id, today)
        
        # Cache
        self.keys_cache[user_id] = {
            "keys": keys,
            "current_index": 0
        }
        
        return keys
    
    async def add_key(self, user_id: int, api_key: str) -> Tuple[bool, str]:
        """
        Add a new API key for the user.
        Returns: (success, message)
        """
        keys = await self.load_user_keys(user_id)
        
        # Check limit (max 4 keys)
        if len(keys) >= 4:
            return False, "Maximum 4 API keys allowed"
        
        # Check for duplicates (compare decrypted keys)
        if any(k["key"] == api_key for k in keys):
            return False, "This API key already exists"
        
        # Encrypt the key
        try:
            encrypted_key = encrypt_api_key(api_key)
        except Exception as e:
            logger.error(f"Error encrypting API key: {e}")
            return False, "Error encrypting API key"
        
        # Determine next index
        next_index = len(keys)
        
        # Save to database
        try:
            key_id = await self.storage.add_user_api_key(
                user_id=user_id,
                encrypted_key=encrypted_key,
                key_index=next_index
            )
            
            # Add to cache
            keys.append({
                "id": key_id,
                "key": api_key,
                "status": "active",
                "key_index": next_index,
                "last_used_at": None
            })
            
            self.keys_cache[user_id]["keys"] = keys
            
            logger.info(f"✅ Added API key #{next_index + 1} for user {user_id}")
            return True, "API key added successfully"
            
        except Exception as e:
            logger.error(f"Error saving API key: {e}")
            return False, f"Error saving API key: {str(e)}"
    
    async def remove_key(self, user_id: int, key_id: int) -> Tuple[bool, str]:
        """
        Remove an API key by its ID.
        Returns: (success, message)
        """
        keys = await self.load_user_keys(user_id)
        
        # Find key to remove
        key_to_remove = None
        for k in keys:
            if k["id"] == key_id:
                key_to_remove = k
                break
        
        if not key_to_remove:
            return False, "API key not found"
        
        # Remove from database
        try:
            await self.storage.delete_user_api_key(key_id)
            
            # Remove from cache
            keys = [k for k in keys if k["id"] != key_id]
            self.keys_cache[user_id]["keys"] = keys
            
            logger.info(f"🗑️ Removed API key {key_id} for user {user_id}")
            return True, "API key removed successfully"
            
        except Exception as e:
            logger.error(f"Error removing API key: {e}")
            return False, f"Error removing API key: {str(e)}"
    
    async def get_active_key(self, user_id: int) -> Optional[str]:
        """
        Get the current active API key for the user.
        Returns None if no active keys available.
        """
        keys = await self.load_user_keys(user_id)
        
        if not keys:
            return None
        
        # Find first active key
        for key in keys:
            if key["status"] == "active":
                # Update last_used_at
                try:
                    await self.storage.update_api_key_last_used(key["id"])
                except:
                    pass
                
                return key["key"]
        
        # No active keys
        logger.warning(f"⚠️ No active API keys for user {user_id}")
        return None
    
    async def rotate_key(self, user_id: int, current_key: str) -> Tuple[bool, Optional[str]]:
        """
        Mark current key as exhausted and rotate to next active key.
        Returns: (success, new_key)
        """
        keys = await self.load_user_keys(user_id)
        
        if not keys:
            return False, None
        
        # Find and mark current key as exhausted
        current_key_id = None
        current_index = -1
        
        for i, k in enumerate(keys):
            if k["key"] == current_key:
                current_key_id = k["id"]
                current_index = i
                k["status"] = "exhausted"
                break
        
        if current_key_id:
            try:
                await self.storage.update_api_key_status(current_key_id, "exhausted")
            except Exception as e:
                logger.error(f"Error updating key status: {e}")
        
        # Find next active key
        found = False
        next_key = None
        
        # Start searching from next index
        for offset in range(1, len(keys) + 1):
            next_index = (current_index + offset) % len(keys)
            if keys[next_index]["status"] == "active":
                next_key = keys[next_index]["key"]
                found = True
                logger.info(f"🔄 Rotated to API key #{next_index + 1} for user {user_id}")
                break
        
        if not found:
            logger.warning(f"⚠️ All API keys exhausted for user {user_id}")
            return False, None
        
        # Update cache
        self.keys_cache[user_id]["keys"] = keys
        
        return True, next_key
    
    async def get_keys_status(self, user_id: int) -> Dict:
        """
        Get status of all keys for UI display.
        Returns: {total, active, exhausted, max_keys, keys: [...]}
        """
        keys = await self.load_user_keys(user_id)
        
        active_count = sum(1 for k in keys if k["status"] == "active")
        exhausted_count = len(keys) - active_count
        
        # Mask keys for security (show first 4 and last 4 chars)
        masked_keys = []
        for k in keys:
            key_str = k["key"]
            if len(key_str) > 8:
                preview = f"{key_str[:4]}...{key_str[-4:]}"
            else:
                preview = "***"
            
            masked_keys.append({
                "id": k["id"],
                "key_preview": preview,
                "status": k["status"],
                "last_used_at": k.get("last_used_at")
            })
        
        return {
            "total": len(keys),
            "active": active_count,
            "exhausted": exhausted_count,
            "max_keys": 4,
            "keys": masked_keys
        }
    
    async def reset_all_keys(self, user_id: int) -> Tuple[bool, str]:
        """
        Reset all keys to active status (admin function).
        Returns: (success, message)
        """
        keys = await self.load_user_keys(user_id)
        
        if not keys:
            return False, "No keys to reset"
        
        try:
            # Update all keys to active
            for key in keys:
                await self.storage.update_api_key_status(key["id"], "active")
                key["status"] = "active"
            
            # Update cache
            self.keys_cache[user_id]["keys"] = keys
            
            # Update reset date
            today = datetime.now().strftime("%Y-%m-%d")
            await self.storage.update_user_reset_date(user_id, today)
            
            logger.info(f"🔄 Reset all API keys for user {user_id}")
            return True, f"Reset {len(keys)} API keys to active"
            
        except Exception as e:
            logger.error(f"Error resetting keys: {e}")
            return False, f"Error resetting keys: {str(e)}"

# Global instance
_api_key_manager = None

def get_api_key_manager(storage_service):
    """Get or create singleton instance of APIKeyManager"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager(storage_service)
    return _api_key_manager
