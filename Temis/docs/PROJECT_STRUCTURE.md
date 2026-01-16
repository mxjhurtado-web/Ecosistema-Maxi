# TEMIS Project Structure

## Recommended Directory Layout

```
Temis/
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── config/
│   ├── __init__.py
│   ├── keycloak_config.py      # ✅ Ya creado
│   ├── config.py                # ✅ Ya creado
│   └── settings.py              # App settings
│
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app
│   ├── database.py              # DB connection
│   ├── dependencies.py          # Auth dependencies
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── group.py
│   │   ├── project.py
│   │   ├── phase.py
│   │   └── daily_log.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   └── auth.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── projects.py
│   │   └── groups.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py
│       ├── drive_service.py
│       └── gemini_service.py
│
├── desktop/
│   ├── __init__.py
│   ├── main.py                  # Entry point
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── login.py
│   │   ├── dashboard.py
│   │   ├── project_wizard.py
│   │   └── components/
│   │       ├── __init__.py
│   │       └── widgets.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── api_client.py
│   │   └── cache.py
│   │
│   └── assets/
│       ├── logo.png
│       └── icon.ico
│
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_drive.py
│   └── test_api.py
│
└── alembic/
    ├── versions/
    └── env.py
```
