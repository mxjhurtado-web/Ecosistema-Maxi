"""
Aplicación de Celery para procesamiento asíncrono.
"""

from celery import Celery
from .config import settings

# Crear app de Celery
celery_app = Celery(
    "hades_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configuración
celery_app.conf.update(
    # Serialización
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Retry y acknowledgment
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Timeout
    task_time_limit=settings.TASK_TIME_LIMIT,
    task_soft_time_limit=settings.TASK_SOFT_TIME_LIMIT,
    
    # Resultados
    result_expires=3600,  # 1 hora
    result_backend_transport_options={
        'master_name': 'mymaster'
    },
    
    # Worker
    worker_prefetch_multiplier=settings.WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=settings.WORKER_MAX_TASKS_PER_CHILD,
    
    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['hades_worker'])
