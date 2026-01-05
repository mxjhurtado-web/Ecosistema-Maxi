# MAX - Guía Rápida de Inicio

## 🚀 Para Probar en Otra Computadora

### **Paso 1: Clonar el Proyecto**
```bash
cd c:\Users\User\Ecosistema-Maxi\MAX
```

### **Paso 2: Iniciar Frontend**
```bash
cd frontend
npm install  # Solo la primera vez
npm run dev
```

**URL**: http://localhost:3000

### **Paso 3: Ver la Aplicación**
Abre tu navegador en **http://localhost:3000**

Deberías ver:
- ✅ Pantalla de login moderna
- ✅ Logo de MAX (círculo azul con "M")
- ✅ Botón "Sign in with SSO"
- ✅ Diseño limpio con Tailwind CSS

---

## ⚠️ Nota Importante

**El botón de login no funcionará completamente** hasta que tengas:
1. Keycloak corriendo en `http://localhost:8081`
2. Backend corriendo en `http://localhost:8000`

Pero **podrás ver toda la interfaz** y navegar por las pantallas.

---

## 📁 Estructura del Proyecto

```
MAX/
├── backend/          ✅ FastAPI + SQLAlchemy + Keycloak
├── frontend/         ✅ React + Vite + Tailwind
├── docs/             ✅ 10 documentos de arquitectura
├── UI_UX_DESIGN.md   ✅ Wireframes y diseño
└── PROJECT_STATUS.md ✅ Estado completo
```

---

## 🎯 Lo Que Funciona Ahora

### **Frontend (Sin Backend)**
- ✅ Pantalla de login
- ✅ Layout del inbox con sidebar
- ✅ Navegación básica
- ✅ Diseño responsive
- ✅ Íconos y estilos

### **Backend (Necesita Docker)**
- ✅ Modelos de base de datos (20 modelos)
- ✅ API endpoints definidos
- ✅ Autenticación Keycloak configurada
- ✅ Migraciones de Alembic listas

---

## 📝 Próximos Pasos

### **1. Probar Frontend** (5 minutos)
```bash
cd frontend
npm run dev
```
Abre http://localhost:3000

### **2. Instalar Docker** (si no lo tienes)
Descarga: https://www.docker.com/products/docker-desktop/

### **3. Iniciar Backend** (10 minutos)
```bash
cd c:\Users\User\Ecosistema-Maxi\MAX
docker compose up -d
```

### **4. Crear Base de Datos** (5 minutos)
```bash
docker compose exec backend alembic upgrade head
```

### **5. Probar Flujo Completo** (15 minutos)
1. Frontend: http://localhost:3000
2. Backend API: http://localhost:8000/docs
3. Login con Keycloak
4. Ver inbox funcionando

---

## 🐛 Solución de Problemas

### **Frontend no carga**
```bash
# Limpiar caché
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### **Puerto ocupado**
El frontend usa puerto 3000. Si está ocupado, edita `vite.config.js`:
```javascript
server: {
  port: 3001, // Cambiar a otro puerto
}
```

### **Error de Tailwind**
Si ves errores de CSS, verifica que `tailwind.config.js` y `postcss.config.js` existan.

---

## 📊 Estadísticas del Proyecto

- **Archivos creados**: 50+
- **Líneas de código**: ~3,500
- **Modelos de DB**: 20
- **Componentes React**: 3 páginas
- **Documentos**: 12
- **Tiempo de desarrollo**: 4 horas

---

## ✨ Características Implementadas

### **Autenticación**
- ✅ Keycloak SSO
- ✅ JWT tokens
- ✅ Auto-refresh
- ✅ Protected routes

### **Frontend**
- ✅ React 18 + Vite
- ✅ Tailwind CSS
- ✅ React Router
- ✅ Zustand (state)
- ✅ Axios (HTTP)

### **Backend**
- ✅ FastAPI async
- ✅ SQLAlchemy async
- ✅ Alembic migrations
- ✅ Celery workers
- ✅ Redis cache

---

## 🎨 Diseño

**Colores**:
- Primary: #2563EB (Blue)
- Success: #10B981 (Green)
- Warning: #F59E0B (Orange)
- Error: #EF4444 (Red)

**Tipografía**: System fonts (Inter-like)

---

## 📞 Contacto

Si tienes problemas, revisa:
1. `PROJECT_STATUS.md` - Estado completo
2. `frontend/README.md` - Guía del frontend
3. `backend/README.md` - Guía del backend
4. `UI_UX_DESIGN.md` - Diseño y wireframes

---

**¡Listo para probar!** 🚀

Cuando estés en la otra computadora, solo ejecuta:
```bash
cd c:\Users\User\Ecosistema-Maxi\MAX\frontend
npm run dev
```

Y abre http://localhost:3000 en tu navegador.
