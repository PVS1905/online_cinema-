from celery import Celery
from src.config.settings import CelerySettings

setq = CelerySettings()
celery_src = Celery(
    'tasks',
    broker=setq.CELERY_BROKER_URL,
    backend=setq.CELERY_RESULT_BACKEND,
    include=['src.celery_app.tasks']
)

celery_src.conf.beat_schedule = {
    'delete-expired-tokens': {
        'task': 'src.celery_app.tasks.delete_expired_tokens',
        'schedule': 86400,
    }
}
