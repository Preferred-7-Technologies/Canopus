from celery import Celery
from kombu import Exchange, Queue
from ...config import settings
import logging

logger = logging.getLogger(__name__)

# Define queues
default_exchange = Exchange('default', type='direct')
voice_exchange = Exchange('voice', type='direct')
command_exchange = Exchange('command', type='direct')

task_queues = [
    Queue('default', default_exchange, routing_key='default'),
    Queue('voice', voice_exchange, routing_key='voice'),
    Queue('command', command_exchange, routing_key='command'),
]

celery_app = Celery(
    'Canopus',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_queues=task_queues,
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    task_routes={
        'app.tasks.voice.*': {'queue': 'voice'},
        'app.tasks.command.*': {'queue': 'command'},
    },
    task_serializer='pickle',
    accept_content=['pickle', 'json'],
    result_serializer='pickle',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
)

@celery_app.task(bind=True)
def debug_task(self):
    logger.info(f'Request: {self.request!r}')
