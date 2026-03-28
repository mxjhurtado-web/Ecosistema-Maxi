import json
import os

CONFIG_FILE = "config.json"

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try: return json.load(f)
            except: pass
    return {"gemini_api_key": "", "recent_files": []}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_recent_files():
    rf = get_config().get("recent_files", [])
    return rf if isinstance(rf, list) else []

def add_recent_file(path):
    c = get_config()
    rf = c.get("recent_files", [])
    if not isinstance(rf, list): rf = []
    if path in rf: rf.remove(path)
    rf.insert(0, path)
    c["recent_files"] = rf[:10]
    save_config(c)
