# TEMIS - Herramienta de Gobierno y Documentación de Proyectos

**Versión**: 1.0.0 (Sprint 1)  
**Stack**: Python + FastAPI + PostgreSQL + Tkinter + Keycloak + Google Drive + Gemini AI

---

## 🎯 Descripción

TEMIS es una herramienta desktop para Windows que acelera la documentación y gobierno de proyectos siguiendo un framework de 7 fases. Integra IA (Gemini) para procesar documentos diarios y generar documentación estructurada automáticamente.

---

## 🚀 Quick Start

### Prerrequisitos

- Python 3.10+
- PostgreSQL 14+
- Cuenta de Keycloak configurada
- Service Account de Google Drive

### Instalación

```bash
# 1. Clonar repositorio
cd C:\Users\User\Ecosistema-Maxi\Temis

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
copy .env.example .env
# Editar .env con tus credenciales

# 5. Inicializar base de datos
alembic upgrade head

# 6. Ejecutar backend
cd backend
uvicorn main:app --reload

# 7. Ejecutar desktop app (otra terminal)
cd desktop
python main.py
```

---

## 📋 Configuración

### Keycloak

Editar `config/keycloak_config.py`:
- URL: `https://sso.maxilabs.net/auth`
- Realm: `zeusDev`
- Client ID: `maxi-business-ai`

### Google Drive

Editar `config/config.py`:
- Service Account (ya configurado)
- Shared Drive ID: `14mUmVpykeakOShvy9XaYBC1K3MeezQbW`

### Gemini API

Configurar desde la UI de TEMIS (Settings).

---

## 🏗️ Arquitectura

```
Desktop App (Tkinter) → Backend API (FastAPI) → PostgreSQL
                      ↓
            Keycloak + Google Drive + Gemini
```

Ver `TEMIS_Architecture_Proposal.md` para detalles completos.

---

## 📚 Documentación

- [Propuesta de Arquitectura](../brain/TEMIS_Architecture_Proposal.md)
- [Estructura del Proyecto](PROJECT_STRUCTURE.md)
- [Sprint 1 Tasks](../brain/task.md)

---

## 🧪 Testing

```bash
# Unit tests
pytest tests/

# Con coverage
pytest --cov=backend --cov=desktop tests/
```

---

## 👥 Equipo

- **Primary Owner**: mxjhurtado@maxillc.com

---

## 📄 Licencia

Propietario: MAXI LLC
