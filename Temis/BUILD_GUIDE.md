# Guía para Crear Ejecutable de TEMIS

## Requisitos Previos

1. **Instalar PyInstaller**:
   ```powershell
   pip install pyinstaller
   ```

2. **Verificar que todas las dependencias estén instaladas**:
   ```powershell
   pip install -r requirements.txt
   ```

## Opción 1: Usar el archivo .spec (Recomendado)

### Paso 1: Construir el ejecutable
```powershell
cd C:\Users\User\Ecosistema-Maxi\Temis
pyinstaller temis.spec
```

### Paso 2: Encontrar el ejecutable
El archivo `TEMIS.exe` estará en:
```
C:\Users\User\Ecosistema-Maxi\Temis\dist\TEMIS.exe
```

## Opción 2: Comando directo (Sin .spec)

```powershell
pyinstaller --name=TEMIS --onefile --windowed --icon=icon.ico desktop/main.py
```

## Configuración del Ejecutable

### Incluir un Icono (Opcional)
1. Coloca un archivo `icon.ico` en la raíz del proyecto
2. Edita `temis.spec` línea 106:
   ```python
   icon='icon.ico',
   ```

### Crear Distribución de Carpeta (En lugar de un solo .exe)
Si prefieres una carpeta con el .exe y DLLs separadas:

1. Descomenta las líneas 110-118 en `temis.spec`
2. Ejecuta: `pyinstaller temis.spec`
3. La carpeta estará en `dist/TEMIS/`

## Distribución

### Para usar en otra computadora:

1. **Copia el archivo `TEMIS.exe`** a la computadora destino

2. **IMPORTANTE**: El backend debe estar corriendo
   - Opción A: Ejecutar backend en servidor
   - Opción B: Crear otro .exe para el backend (ver abajo)

3. **Configuración inicial**:
   - Primera vez: Configurar API Key de Gemini
   - Configurar URL del backend si no es localhost

## Crear Ejecutable del Backend (Opcional)

Si quieres distribuir también el backend:

```powershell
pyinstaller --name=TEMIS-Backend --onefile backend/main.py
```

Luego distribuye ambos ejecutables:
- `TEMIS.exe` (Frontend)
- `TEMIS-Backend.exe` (Backend)

## Solución de Problemas

### Error: "Module not found"
- Agrega el módulo faltante a `hiddenimports` en `temis.spec`

### Error: "Failed to execute script"
- Ejecuta con consola para ver errores:
  ```python
  console=True,  # En temis.spec línea 100
  ```

### El .exe es muy grande
- Normal para aplicaciones con muchas dependencias
- Tamaño esperado: 50-100 MB

### Antivirus bloquea el .exe
- Es normal con ejecutables nuevos
- Agrega excepción en el antivirus
- O firma el ejecutable con certificado

## Notas Importantes

1. **Base de Datos**: 
   - El .exe creará `temis.db` en la carpeta donde se ejecute
   - Para compartir datos, copia también `temis.db`

2. **Configuración**:
   - Crea un `.env` junto al ejecutable si necesitas configuración personalizada

3. **Google Drive**:
   - Necesitarás configurar las credenciales en cada instalación

4. **Actualizaciones**:
   - Para actualizar, simplemente reemplaza el .exe antiguo con el nuevo

## Distribución Profesional

Para una distribución más profesional:

1. **Crear instalador con Inno Setup**:
   - Descarga: https://jrsoftware.org/isinfo.php
   - Crea un script .iss para instalador Windows

2. **Firmar el ejecutable**:
   - Obtén un certificado de firma de código
   - Usa `signtool.exe` para firmar

3. **Crear paquete portable**:
   - Incluye README.txt
   - Incluye carpeta `docs/`
   - Incluye scripts de inicio
