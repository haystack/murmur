CELERY_IMPORTS=("mailx.tasks",)
CELERY_RESULT_BACKEND = "amqp"
BROKER_URL = "amqp://mailx:mailx@localhost:5672//mailx"
