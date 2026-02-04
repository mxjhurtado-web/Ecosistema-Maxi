"""
Configuración del Worker de Celery.
"""

from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    """Configuración del worker"""
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Database
    DATABASE_URL: str
    
    # Gemini
    GEMINI_API_KEY: str
    
    # Worker
    WORKER_CONCURRENCY: int = 4
    WORKER_PREFETCH_MULTIPLIER: int = 1
    WORKER_MAX_TASKS_PER_CHILD: int = 100
    
    # Timeouts
    TASK_TIME_LIMIT: int = 300  # 5 minutos
    TASK_SOFT_TIME_LIMIT: int = 240  # 4 minutos
    
    # Retry
    TASK_MAX_RETRIES: int = 3
    TASK_RETRY_DELAY: int = 60  # segundos
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = WorkerSettings()
