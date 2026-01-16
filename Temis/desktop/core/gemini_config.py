#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gemini configuration manager for desktop app
"""

import os
import json


class GeminiConfig:
    """Gemini API configuration manager"""

    CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".temis_config.json")

    @classmethod
    def save_api_key(cls, api_key: str) -> bool:
        """Save Gemini API key"""
        try:
            config = cls.load_config()
            config["gemini_api_key"] = api_key
            
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            
            return True
        except Exception as e:
            print(f"Error saving API key: {e}")
            return False

    @classmethod
    def get_api_key(cls) -> str:
        """Get Gemini API key"""
        config = cls.load_config()
        return config.get("gemini_api_key", "")

    @classmethod
    def load_config(cls) -> dict:
        """Load configuration"""
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        
        return {}

    @classmethod
    def has_api_key(cls) -> bool:
        """Check if API key is configured"""
        return bool(cls.get_api_key())
