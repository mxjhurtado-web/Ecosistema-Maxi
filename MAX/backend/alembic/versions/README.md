# Alembic Versions Directory

This directory contains database migration scripts.

Migrations are automatically generated and applied using Alembic.

## Usage

```bash
# Create a new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```
