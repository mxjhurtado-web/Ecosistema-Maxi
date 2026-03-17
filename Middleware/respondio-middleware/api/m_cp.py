from mcp.server.fastmcp import FastMCP
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# 2. CONFIGURACIÓN SUPABASE
# Usamos variable de entorno para seguridad en Render
DB_URI = os.getenv("SUPABASE_URI", "postgresql://postgres:PruebaBoot2025.*@db.tzlomvpugmrpdfatscxe.supabase.co:5432/postgres")

# 1. Inicializamos el servidor MCP con host y puerto para Render
mcp = FastMCP(
    "Maxi-Estatus-Server",
    host="0.0.0.0",
    port=int(os.getenv("PORT", 8000)),
)

def consultar_supabase(clave):
    conn = None
    try:
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
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
    fila = consultar_supabase(clave)

    if fila:
        estatus = fila.get('status', 'No disponible')
        cliente = fila.get('Nombre_Cliente', 'N/A')
        mensaje = fila.get('message_to_user', 'Sin mensajes adicionales.')
        return (f"✅ Registro encontrado para el código {clave}:\n"
                f"- **Cliente**: {cliente}\n"
                f"- **Estatus**: {estatus}\n"
                f"- **Nota**: {mensaje}")

    return f"❌ Código de envío incorrecto o no encontrado: {clave}. Por favor, verifica los datos."

if __name__ == "__main__":
    mcp.run(transport="sse")
