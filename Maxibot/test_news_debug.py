"""
Script de prueba DEBUG para el módulo news_direct.py
"""
import requests
from urllib.parse import quote

def debug_news():
    print("📰 DEBUG News Tool...")
    topic = "tecnologia"
    url = f"https://news.google.com/rss/search?q={quote(topic)}"
    params = {"hl": "es-419", "gl": "MX", "ceid": "MX:es-419"}
    
    print(f"URL: {url}")
    try:
        r = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {r.status_code}")
        print(f"Content length: {len(r.content)}")
        print(f"Content preview: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_news()
