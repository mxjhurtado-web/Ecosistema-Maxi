"""
Módulo para consultas de clima directas a Open-Meteo
Sin necesidad de servidor MCP local
"""
import requests
import re


class WeatherTool:
    """Cliente directo para consultas de clima usando Open-Meteo API"""
    
    def __init__(self):
        self.geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
    
    def search(self, query: str, top_k: int = 3):
        """
        Busca información de clima basada en el query.
        Compatible con la interfaz MCP de MaxiBot.
        
        Args:
            query: Texto de búsqueda (ej: "clima en Madrid")
            top_k: Número de resultados (no usado, siempre retorna 1)
        
        Returns:
            Lista de resultados en formato MCP
        """
        # Extraer ciudad del query
        m = re.search(r"clima en ([A-Za-zÁÉÍÓÚáéíóúñÑ ]+)", query, re.IGNORECASE)
        if not m:
            return []
        
        ciudad = m.group(1).strip()
        
        try:
            # Geocoding: obtener coordenadas
            geo_response = requests.get(
                self.geo_url,
                params={"name": ciudad, "count": 1, "language": "es"},
                timeout=10
            )
            geo_data = geo_response.json()
            
            if not geo_data.get("results"):
                return [{
                    "title": f"Ciudad no encontrada: {ciudad}",
                    "content": f"No se pudo encontrar información para '{ciudad}'. Verifica el nombre.",
                    "url": "https://open-meteo.com/",
                    "score": 0.5
                }]
            
            lat = geo_data["results"][0]["latitude"]
            lon = geo_data["results"][0]["longitude"]
            nombre_ciudad = geo_data["results"][0].get("name", ciudad)
            
            # Consultar clima
            weather_response = requests.get(
                self.weather_url,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": True,
                    "daily": ["temperature_2m_max", "temperature_2m_min"],
                    "timezone": "auto",
                },
                timeout=10
            )
            weather_data = weather_response.json()
            
            temp = weather_data["current_weather"]["temperature"]
            wind = weather_data["current_weather"]["windspeed"]
            
            # Información adicional
            daily = weather_data.get("daily", {})
            temp_max = daily.get("temperature_2m_max", [None])[0]
            temp_min = daily.get("temperature_2m_min", [None])[0]
            
            # Formatear respuesta
            text = f"Clima actual en {nombre_ciudad}:\n"
            text += f"- Temperatura: {temp}°C\n"
            text += f"- Viento: {wind} km/h\n"
            
            if temp_max is not None and temp_min is not None:
                text += f"- Máxima hoy: {temp_max}°C\n"
                text += f"- Mínima hoy: {temp_min}°C\n"
            
            text += "\nFuente: Open-Meteo (API pública)"
            
            return [{
                "title": f"Clima en {nombre_ciudad}",
                "content": text,
                "url": "https://open-meteo.com/",
                "score": 1.0
            }]
            
        except requests.RequestException as e:
            return [{
                "title": "Error de conexión",
                "content": f"No se pudo obtener información del clima: {str(e)}",
                "url": "https://open-meteo.com/",
                "score": 0.3
            }]
        except Exception as e:
            return [{
                "title": "Error",
                "content": f"Error al procesar la solicitud: {str(e)}",
                "url": "https://open-meteo.com/",
                "score": 0.3
            }]
    
    def available(self) -> bool:
        """Siempre disponible (API pública)"""
        return True


# Instancia global
weather_tool = WeatherTool()
