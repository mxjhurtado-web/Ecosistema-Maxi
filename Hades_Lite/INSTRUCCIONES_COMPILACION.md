# Instrucciones para Compilar HADES Lite 2.2 a EXE

## Requisitos Previos

1. **Instalar PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Verificar que todos los archivos estén presentes:**
   - `hadeslite_2.2.py` - Script principal
   - `keycloak_auth.py` - Módulo de autenticación
   - `keycloak_config.py` - Configuración de Keycloak
   - `flama2.png` - Imagen de flama
   - `Logo_Hades.png` - Logo de HADES
   - `Hades_ico.ico` - Ícono del ejecutable
   - `hadeslite_2.2.spec` - Archivo de configuración de PyInstaller

## Pasos para Compilar

### Opción 1: Usar el archivo .spec (Recomendado)

```bash
# Navegar al directorio de HADES Lite
cd "d:\zyzen 3\Documents\Ecosistema-Maxi\Hades_Lite"

# Compilar usando el archivo .spec
pyinstaller hadeslite_2.2.spec
```

### Opción 2: Compilación directa (sin .spec)

```bash
pyinstaller --onefile --windowed --icon=Hades_ico.ico --add-data "flama2.png;." --add-data "Logo_Hades.png;." --add-data "Hades_ico.ico;." --name "HADES_Lite_2.2" hadeslite_2.2.py
```

## Resultado

Después de la compilación exitosa:
- El ejecutable estará en: `dist/HADES_Lite_2.2.exe`
- Los archivos temporales estarán en: `build/`

## Notas Importantes

1. **Tamaño del ejecutable:** El archivo .exe será grande (~100-200 MB) porque incluye:
   - Python runtime
   - Todas las librerías (tkinter, PIL, pandas, google-api, etc.)
   - Imágenes embebidas

2. **Primera ejecución:** La primera vez que se ejecute puede tardar un poco más en iniciar.

3. **Antivirus:** Algunos antivirus pueden marcar el .exe como sospechoso (falso positivo). Esto es normal con PyInstaller.

4. **Distribución:** Para distribuir el ejecutable:
   - Solo necesitas el archivo `HADES_Lite_2.2.exe` de la carpeta `dist/`
   - Las imágenes ya están embebidas, no necesitas copiarlas
   - Los usuarios NO necesitan tener Python instalado

## Solución de Problemas

### Error: "Module not found"
```bash
# Reinstalar dependencias
pip install -r requirements.txt
```

### Error con tkinterdnd2
```bash
# Instalar tkinterdnd2 si no está
pip install tkinterdnd2
```

### El ejecutable no inicia
- Ejecutar desde la terminal para ver errores:
  ```bash
  cd dist
  .\HADES_Lite_2.2.exe
  ```

### Reducir tamaño del ejecutable
- Editar `hadeslite_2.2.spec` y agregar más módulos a `excludes`
- Usar `upx=True` (ya está activado)

## Verificación Post-Compilación

Después de compilar, verificar que:
1. ✅ El ejecutable inicia correctamente
2. ✅ El logo de HADES se muestra
3. ✅ La animación de flama funciona
4. ✅ El ícono de la ventana es correcto
5. ✅ La autenticación de Keycloak funciona
6. ✅ El OCR con Gemini funciona

## Comandos Útiles

```bash
# Limpiar compilaciones anteriores
rmdir /s /q build dist
del *.spec

# Recompilar desde cero
pyinstaller hadeslite_2.2.spec --clean

# Ver información detallada durante compilación
pyinstaller hadeslite_2.2.spec --log-level=DEBUG
```
