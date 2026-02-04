# Hades API

Backend FastAPI para Hades Web.

## 🚀 Inicio Rápido

### Desarrollo Local (sin Docker)

1. **Instalar dependencias:**
```bash
cd hades_api
pip install -r requirements.txt
```

2. **Configurar variables de entorno:**
```bash
cp ../.env.example ../.env
# Editar .env con tus credenciales
```

3. **Iniciar servidor:**
```bash
uvicorn hades_api.main:app --reload
```

4. **Acceder a la documentación:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Desarrollo con Docker Compose

1. **Configurar .env:**
```bash
cp .env.example .env
# Editar .env
```

2. **Iniciar stack completo:**
```bash
docker-compose up -d
```

3. **Ver logs:**
```bash
docker-compose logs -f api
```

4. **Detener:**
```bash
docker-compose down
```

## 📁 Estructura

```
hades_api/
├── auth/              # Autenticación Keycloak
│   ├── keycloak.py    # Verificación JWT
│   └── dependencies.py # FastAPI dependencies
├── models/            # Modelos SQLAlchemy
│   └── job.py
├── routes/            # Endpoints
│   ├── health.py      # Health check
│   ├── jobs.py        # CRUD de jobs
│   └── admin.py       # Panel admin
├── schemas/           # Pydantic schemas
│   └── job.py
├── config.py          # Configuración
├── database.py        # SQLAlchemy setup
└── main.py            # App principal
```

## 🔐 Autenticación

Usa Keycloak SSO con JWT tokens.

### Obtener Token

```bash
curl -X POST "https://keycloak-server/realms/your-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=hades-web" \
  -d "client_secret=your-secret" \
  -d "grant_type=password" \
  -d "username=user@example.com" \
  -d "password=password"
```

### Usar Token

```bash
curl -X GET "http://localhost:8000/jobs" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📊 Endpoints

### Health
- `GET /health` - Health check
- `GET /` - Info de la API

### Jobs
- `POST /jobs` - Crear análisis (requiere imagen)
- `GET /jobs/{id}` - Ver resultado
- `GET /jobs` - Listar jobs del usuario
- `DELETE /jobs/{id}` - Eliminar job

### Admin (solo admins)
- `GET /admin/stats` - Estadísticas generales
- `GET /admin/jobs` - Ver todos los jobs
- `GET /admin/users` - Estadísticas de usuarios

## 🔑 Roles

- `hades_admin` - Acceso completo
- `hades_analyst` - Crear y ver sus análisis
- `hades_viewer` - Solo visualizar

## 🗄️ Base de Datos

PostgreSQL con SQLAlchemy.

### Modelo Job

```python
{
    "id": "uuid",
    "user_id": "keycloak-user-id",
    "status": "queued|processing|completed|failed",
    "result": {...},  # JSON completo del análisis
    "country_detected": "MX",
    "semaforo": "verde",
    "score": 5,
    "created_at": "2026-02-03T09:00:00",
    "completed_at": "2026-02-03T09:00:05"
}
```

## 🧪 Testing

```bash
# Instalar pytest
pip install pytest pytest-asyncio httpx

# Correr tests
pytest tests/
```

## 📝 Variables de Entorno

Ver `.env.example` para la lista completa.

Principales:
- `DATABASE_URL` - PostgreSQL connection string
- `KEYCLOAK_SERVER_URL` - URL de Keycloak
- `KEYCLOAK_REALM` - Realm de Keycloak
- `KEYCLOAK_CLIENT_ID` - Client ID
- `GEMINI_API_KEY` - API key de Gemini
