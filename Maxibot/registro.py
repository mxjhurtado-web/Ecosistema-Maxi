import sqlite3
import datetime

# check

def crear_base():
    conn = sqlite3.connect("registro_maxiboot.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accesos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            correo TEXT,
            nombre TEXT,
            fecha TEXT,
            version TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            correo TEXT,
            fuente TEXT,
            tipo_evento TEXT,
            contenido TEXT,
            fecha TEXT
        )
    """)

    conn.commit()
    conn.close()

def registrar_ingreso(correo, nombre, version):
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("registro_maxiboot.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO accesos (correo, nombre, fecha, version)
        VALUES (?, ?, ?, ?)
    """, (correo, nombre, fecha, version))
    conn.commit()
    conn.close()

def registrar_consulta(correo, fuente, pregunta):
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("registro_maxiboot.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO eventos (correo, fuente, tipo_evento, contenido, fecha)
        VALUES (?, ?, 'Consulta', ?, ?)
    """, (correo, fuente, pregunta, fecha))
    conn.commit()
    conn.close()