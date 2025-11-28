# AGORA: Asistente de Entrenamiento Inteligente

Este proyecto es una plataforma de entrenamiento para agentes telefónicos que utiliza IA para simular clientes y evaluar el desempeño.

## Estructura del Proyecto

- `backend/`: Servidor Node.js + Express + Socket.io + MongoDB.
- `frontend/`: Aplicación React + Vite + TailwindCSS.

## Requisitos Previos

- Node.js (v16 o superior)
- MongoDB (local o Atlas)

## Instrucciones de Instalación

### 1. Configuración del Backend

1. Navega a la carpeta `backend`:
   ```bash
   cd backend
   ```
2. Instala las dependencias:
   ```bash
   npm install
   ```
3. Crea un archivo `.env` basado en `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Edita el archivo `.env` y asegúrate de tener una URI de MongoDB válida.
   - Si tienes MongoDB local: `MONGO_URI=mongodb://localhost:27017/agora_db`
5. Inicia el servidor:
   ```bash
   npm run dev
   ```
   El servidor correrá en `http://localhost:5000`.

### 2. Configuración del Frontend

1. Navega a la carpeta `frontend`:
   ```bash
   cd frontend
   ```
2. Instala las dependencias:
   ```bash
   npm install
   ```
3. Inicia el servidor de desarrollo:
   ```bash
   npm run dev
   ```
   La aplicación estará disponible en `http://localhost:5173`.

## Uso de la Aplicación

1. **Registro**: Abre la app y regístrate con un nuevo usuario.
2. **Admin**: Para acceder a funciones de administrador, puedes editar manualmente tu usuario en la base de datos (MongoDB) y cambiar el campo `role` de `"agent"` a `"admin"`.
3. **Escenarios**: Como admin, ve a "Gestionar Escenarios" y crea uno nuevo.
4. **Simulación**: Ve al Dashboard, selecciona un escenario y comienza a hablar (o escribir).
5. **Evaluación**: Al terminar la llamada, verás un reporte detallado.

## Notas de Desarrollo

- **IA Mock**: Por defecto, el sistema usa un adaptador "Mock" que responde con frases predefinidas. Para usar Gemini u OpenAI, edita `backend/src/adapters/ai.adapter.js` y configura las variables de entorno.
- **Audio**: La captura de audio real requiere integración con Web Speech API o un servicio de STT en el backend. La versión actual simula el audio mediante texto para facilitar las pruebas iniciales.
