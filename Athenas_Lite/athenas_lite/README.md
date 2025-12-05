
# ATHENAS Lite v3.2.1 (Refactored)

Herramienta para el análisis masivo de audios y evaluación automática de calidad utilizando Google Gemini.

## Estructura del Proyecto

El proyecto ha sido modularizado para facilitar su mantenimiento:

- **athenas_lite/**: Paquete principal.
  - **main.py**: Punto de entrada de la aplicación.
  - **config/**: Configuraciones, constantes y logging.
  - **auth/**: Gestión de autenticación con Google.
  - **core/**: Lógica de negocio, reglas de evaluación y scoring.
  - **services/**: Integraciones externas (Gemini, Drive, FFmpeg).
  - **ui/**: Interfaz gráfica (Tkinter).

## Instalación

1.  Asegúrate de tener Python 3.10+ instalado.
2.  Instala las dependencias:
    ```bash
    pip install pandas google-generativeai google-auth google-api-python-client pillow python-dotenv
    ```
3.  Configura las variables de entorno:
    - Copia `athenas_lite/.env.example` a `.env` en la raíz (o en `athenas_lite/`).
    - Rellena los valores necesarios.

## Ejecución

Para iniciar la aplicación, ejecuta el siguiente comando desde la carpeta raíz (`Athenas_Lite`):

```bash
python athenas_lite/main.py
```

## Dependencias Externas

- **FFmpeg**: Se requiere `ffmpeg.exe` y `ffprobe.exe` en la raíz del proyecto (junto a la carpeta `athenas_lite/`) o en el PATH del sistema para procesar audios que no sean WAV/MP3 nativos.
