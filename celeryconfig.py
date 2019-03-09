# CELERY STUFF
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = "amqp"
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

from kombu import Queue

CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = (
    Queue('default'),
    Queue('init_sync'),
    Queue('loop_sync'),
)

# from datetime import timedelta

# CELERYBEAT_SCHEDULE = {
#     'add-every-30-seconds': {
#         'task': 'tasks.add',
#         'schedule': timedelta(seconds=30),
#         'args': (16, 16),
#         'options': {'queue' : 'loop_sync'} 
#     },
# }

# CELERY_TIMEZONE = 'UTC'