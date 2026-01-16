# Backend Auto-Start para TEMIS

## Cómo Funciona el Backend en el .exe

### Solución Implementada: **Backend Embebido**

Cuando ejecutas `TEMIS.exe`:

1. **El .exe inicia automáticamente el backend** en segundo plano
2. **El backend corre en `localhost:8000`** (solo accesible en tu computadora)
3. **Al cerrar TEMIS, el backend se cierra automáticamente**

### Ventajas:
- ✅ Usuario solo ejecuta un archivo
- ✅ No necesita configuración técnica
- ✅ Backend se cierra automáticamente
- ✅ Funciona sin conexión a internet (excepto Gemini API)

### Desventajas:
- ❌ Cada usuario necesita su propia copia
- ❌ No se puede compartir datos entre computadoras fácilmente
- ❌ Usa más recursos (backend + frontend)

## Alternativa: Backend Centralizado (Para Equipos)

Si quieres que varios usuarios compartan el mismo backend:

### Opción A: Servidor Dedicado
1. Instala el backend en un servidor/computadora central
2. Ejecuta: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
3. Configura TEMIS.exe para conectarse a esa IP

### Opción B: Cloud (Render, Railway, etc.)
1. Sube el backend a un servicio cloud
2. Configura TEMIS.exe con la URL del servidor

## Configuración del .exe Actual

El `temis.spec` ya está configurado para:
- ✅ Incluir todo el código del backend
- ✅ Incluir todas las dependencias
- ✅ No mostrar ventana de consola
- ✅ Crear un solo archivo .exe

## Tamaño Esperado del .exe

- **Sin optimizar**: 80-120 MB
- **Con UPX**: 50-80 MB
- **Incluye**: Python, Tkinter, FastAPI, SQLAlchemy, todas las librerías

## Notas Importantes

1. **Base de Datos**: 
   - Se crea `temis.db` en la carpeta donde ejecutas el .exe
   - Cada instalación tiene su propia BD

2. **Google Drive**:
   - Necesitas configurar credenciales en cada instalación
   - O compartir el archivo de credenciales

3. **Gemini API**:
   - Cada usuario configura su propia API key
   - O puedes hardcodear una key (no recomendado)

4. **Actualizaciones**:
   - Para actualizar, reemplaza el .exe
   - La BD (`temis.db`) se mantiene
