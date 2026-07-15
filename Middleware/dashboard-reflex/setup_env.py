import os
import glob
import json

def setup():
    # Determine the API URL at runtime
    api_url = os.getenv("API_URL", "")
    hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "")
    
    if api_url:
        new_url = api_url.rstrip('/')
    elif hostname:
        new_url = f"https://{hostname}"
    else:
        new_url = "http://localhost:8000"
        
    new_ws_url = new_url.replace("https://", "wss://").replace("http://", "ws://")
    
    print(f"Configuring Reflex client frontend at startup:")
    print(f"  - HTTP Base: {new_url}")
    print(f"  - WS Base: {new_ws_url}")
    
    # 1. Update compiled JS asset files
    js_files = glob.glob("/app/.web/build/client/assets/reflex-env-*.js")
    for fp in js_files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace URLs
            content = content.replace("http://localhost:8000", new_url)
            content = content.replace("ws://localhost:8000", new_ws_url)
            
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  - Updated JS asset: {os.path.basename(fp)}")
        except Exception as e:
            print(f"  - Error updating {fp}: {e}")
            
    # 2. Update .web/env.json if present
    env_json_paths = [
        "/app/.web/env.json",
        "/app/.web/build/client/env.json" # in case it's copied
    ]
    for fp in env_json_paths:
        if os.path.exists(fp):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Update keys
                for key in ["PING", "UPLOAD", "AUTH_CODESPACE", "HEALTH", "ALL_ROUTES"]:
                    if key in data and "localhost:8000" in data[key]:
                        data[key] = data[key].replace("http://localhost:8000", new_url)
                if "EVENT" in data and "localhost:8000" in data["EVENT"]:
                    data["EVENT"] = data["EVENT"].replace("ws://localhost:8000", new_ws_url)
                    
                with open(fp, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                print(f"  - Updated JSON config: {fp}")
            except Exception as e:
                print(f"  - Error updating env.json {fp}: {e}")

if __name__ == "__main__":
    setup()
