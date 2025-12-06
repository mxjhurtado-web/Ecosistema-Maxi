"""
Script de prueba para el módulo news_direct.py
"""
import time
from news_direct import news_tool

def test_news():
    print("📰 Probando News Tool (Google News RSS)...")
    
    queries = [
        "noticias de tecnología",
        "noticias sobre inteligencia artificial",
        "últimas noticias",
        "clima en madrid" # Debería ser ignorado o vacío
    ]

    for q in queries:
        print(f"\n🔎 Buscando: '{q}'")
        results = news_tool.search(q, top_k=2)
        
        if not results:
            print("   ⚠️ No se encontraron resultados (o no es query de noticias).")
        else:
            for i, r in enumerate(results):
                print(f"   {i+1}. {r['title']}")
                print(f"      🔗 {r['url'][:60]}...")
                print(f"      📄 {r['content'][:100]}...")
        
        time.sleep(1) # Respetar rate limits

if __name__ == "__main__":
    test_news()
