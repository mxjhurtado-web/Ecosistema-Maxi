from mcp.server.fastmcp import FastMCP
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# 1. Inicializamos el servidor MCP
mcp = FastMCP("Maxi-Estatus-Server")

# 2. CONFIGURACIÓN SUPABASE
# Usamos variable de entorno para seguridad en Render
DB_URI = os.getenv("SUPABASE_URI", "postgresql://postgres:PruebaBoot2025.*@db.tzlomvpugmrpdfatscxe.supabase.co:5432/postgres")

def consultar_supabase(clave):
    conn = None
    try:
        # Conexión a PostgreSQL (Supabase)
        conn = psycopg2.connect(DB_URI)
        # RealDictCursor nos permite usar los nombres de las columnas como claves
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Búsqueda por la columna específica confirmada: "Codigo_de_envio"
        query = 'SELECT * FROM "Base_completa" WHERE "Codigo_de_envio" = %s'
        cursor.execute(query, (clave.strip(),))
        
        resultado = cursor.fetchone()
        cursor.close()
        return resultado
    except Exception as e:
        print(f"❌ Error al conectar con Supabase: {e}")
        return None
    finally:
        if conn:
            conn.close()

# 3. HERRAMIENTA MCP
@mcp.tool()
def obtener_estatus_envio(clave: str) -> str:
    """
    Consulta el estatus, cliente y mensaje en la base de datos de Supabase usando el Código de Envío.
    """
    # 1. Intentamos obtener la fila de la base de datos
    fila = consultar_supabase(clave)
    
    # 2. Si la fila existe (encontró el código)
    if fila:
        estatus = fila.get('status', 'No disponible')
        cliente = fila.get('Nombre_Cliente', 'N/A')
        mensaje = fila.get('message_to_user', 'Sin mensajes adicionales.')
        
        return (f"✅ Registro encontrado para el código {clave}:\n"
                f"- **Cliente**: {cliente}\n"
                f"- **Estatus**: {estatus}\n"
                f"- **Nota**: {mensaje}")
    
    # 3. SI NO EXISTE: Devolvemos un mensaje claro
    return f"❌ Código de envío incorrecto o no encontrado: {clave}. Por favor, verifica los datos."

if __name__ == "__main__":
    mcp.run()
