"""
Módulo para consultas de noticias directas usando Google News RSS
Sin necesidad de servidor MCP local ni API Keys
"""
import requests
import xml.etree.ElementTree as ET
import re
from urllib.parse import quote

class NewsTool:
    """Cliente para consultas de noticias usando Google News RSS"""
    
    def __init__(self):
        self.base_url = "https://news.google.com/rss"
        self.search_url = "https://news.google.com/rss/search"
    
    def search(self, query: str, top_k: int = 3):
        """
        Busca noticias basadas en el query.
        Compatible con la interfaz MCP de MaxiBot.
        
        Args:
            query: Texto de búsqueda (ej: "noticias de tecnología")
            top_k: Número de resultados
        
        Returns:
            Lista de resultados en formato MCP
        """
        # 1. Detectar intención de noticias
        # Patrones: "noticias de X", "noticias en X", "noticias sobre X", "últimas noticias"
        match = re.search(r"noticias (?:de|en|sobre|del) (.+)", query, re.IGNORECASE)
        topic = match.group(1).strip() if match else None
        
        if not topic and "noticias" not in query.lower():
            return []

        # Si es solo "noticias" o "últimas noticias", usamos top headlines
        try:
            params = {"hl": "es-419", "gl": "MX", "ceid": "MX:es-419"} # Configurado para México/LatAm
            
            if topic:
                # Búsqueda específica
                url = f"{self.search_url}?q={quote(topic)}"
            else:
                # Top headlines
                url = self.base_url
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return []
                
            # Parsear XML
            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            
            results = []
            count = 0
            
            for item in items:
                if count >= top_k:
                    break
                    
                title = item.find("title").text if item.find("title") is not None else "Sin título"
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                
                # Limpiar título (Google News suele poner " - Fuente" al final)
                source = "Google News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source = parts[1]
                
                snippet = f"Noticia: {title}\nFecha: {pub_date}\nFuente: {source}"
                
                results.append({
                    "title": title,
                    "content": snippet,
                    "url": link,
                    "score": 1.0
                })
                count += 1
            
            return results

        except Exception as e:
            print(f"Error en NewsTool: {e}")
            return [{
                "title": "Error al buscar noticias",
                "content": f"No se pudieron obtener noticias: {str(e)}",
                "url": "https://news.google.com",
                "score": 0.3
            }]

    def available(self) -> bool:
        return True

# Instancia global
news_tool = NewsTool()
