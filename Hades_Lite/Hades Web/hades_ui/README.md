# Hades UI - Frontend React

Interfaz web para Hades - Sistema de análisis forense de documentos.

## 🚀 Stack Tecnológico

- **React 18** + **TypeScript**
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **React Router** - Routing
- **React Query** - Server state
- **Zustand** - Client state
- **Keycloak** - Authentication
- **Axios** - HTTP client

## 📦 Instalación

```bash
npm install
```

## 🛠️ Desarrollo

```bash
npm run dev
```

Abre [http://localhost:5173](http://localhost:5173)

## 🏗️ Build

```bash
npm run build
```

## 🌐 Variables de Entorno

Crear archivo `.env`:

```bash
VITE_API_URL=http://localhost:8000
VITE_KEYCLOAK_URL=https://keycloak.example.com
VITE_KEYCLOAK_REALM=hades
VITE_KEYCLOAK_CLIENT_ID=hades-web
```

## 📁 Estructura

```
src/
├── components/     # Componentes reutilizables
├── pages/          # Páginas de la aplicación
├── services/       # API clients
├── hooks/          # Custom hooks
├── store/          # Zustand stores
├── types/          # TypeScript types
└── utils/          # Utilidades
```

## 🎨 Componentes Principales

- **Upload** - Subir documentos
- **Results** - Visualizar análisis
- **History** - Historial de análisis
- **Admin** - Panel de administración

## 🔐 Autenticación

La aplicación usa Keycloak para SSO. Los usuarios deben autenticarse antes de acceder.

## 📊 Features

- ✅ Upload de imágenes (drag & drop)
- ✅ Análisis en tiempo real
- ✅ Visualización de resultados
- ✅ Indicador de semáforo (verde/amarillo/rojo)
- ✅ Historial con filtros
- ✅ Panel de administración
- ✅ Exportación a Google Drive

## 🧪 Testing

```bash
npm run test
```

## 📝 Licencia

Propietario - Maxi Hurtado
