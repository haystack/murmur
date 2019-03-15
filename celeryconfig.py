# CELERY STUFF
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = "amqp"
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

from kombu import Queue

CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = (
    Queue('default', routing_key='default.#'),
    Queue('new_user', routing_key='new_user.#'),
    Queue('loop_sync', routing_key='loop_sync.#'),
)

CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'task.default'

from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'loop_sync_celery_beat': {
        'task': 'loop_sync_user_inbox',
        'schedule': timedelta(seconds=5),
        'args': (),
        'options': {'queue' : 'loop_sync', 'routing_key' : 'loop_sync.import'} 
    },
}

CELERY_TIMEZONE = 'UTC'