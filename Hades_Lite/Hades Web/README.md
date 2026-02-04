# Hades Web

Versión web de Hades Ultimate - Sistema de análisis forense de documentos

## 📋 Estructura del Proyecto

```
hades_web/
├── hades_core/       # Motor de análisis (extraído de Hades Ultimate)
├── hades_api/        # Backend FastAPI
├── hades_worker/     # Celery workers
├── hades_ui/         # Frontend React
├── tests/            # Tests
└── docker-compose.yml
```

## 🎯 Objetivo

Convertir Hades Ultimate a aplicación web manteniendo toda la funcionalidad existente y arreglando el problema de fechas norteamericanas.

## 🚀 Estado del Proyecto

### Fase 1: Core (En Progreso)
- [x] Estructura de carpetas creada
- [ ] Extracción del motor de análisis
- [ ] Módulo de fechas corregido
- [ ] Tests unitarios

### Fase 2: Backend API (Pendiente)
- [ ] Setup FastAPI
- [ ] Endpoints /jobs
- [ ] Celery worker

### Fase 3: Frontend (Pendiente)
- [ ] React app
- [ ] Upload component
- [ ] Result viewer

### Fase 4: Docker (Pendiente)
- [ ] docker-compose.yml
- [ ] Documentación completa

## 📝 Cambios vs Hades Ultimate

### ✅ Mantenido (Sin Cambios)
- Sistema de semáforo (verde/amarillo/rojo)
- Análisis forense completo
- Detección de país
- Extracción de IDs
- Sistema de scoring
- Prompts de Gemini

### 🔧 Modificado
- **Fechas:** Ahora se preserva el formato original del OCR
  - Antes: `01/15/2024` → `15/01/2024` (reformateado)
  - Ahora: `01/15/2024` → `01/15/2024` (preservado)

## 🛠️ Tecnologías

- **Backend:** FastAPI + PostgreSQL + Redis + Celery
- **Frontend:** React + TypeScript
- **Core:** Python 3.11+
- **OCR:** Google Gemini Vision
- **Auth:** Keycloak (preparado)

## 📖 Documentación

Ver [hades_web_plan.md](../../.gemini/antigravity/brain/b1e0be68-c40e-422d-b05a-b219e93e6b49/hades_web_plan.md) para el plan completo de implementación.

---

**Fecha de inicio:** 2026-02-02
