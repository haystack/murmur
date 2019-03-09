YoUPS
=

YoUPS is sharing a codebase of Murmur. Check out [Murmur](https://github.com/haystack/murmur/blob/master/README.md) to host YoUPS at your server. 

# Execute users' email rules

YoUPS uses [Celery 3.1](http://docs.celeryproject.org/en/3.1/index.html) to execute YoUPS users' email rules. Every time users execute their email rules (e.g., calling `set_interval()` or `on_message_arrival()`), YoUPS internally saves those as 'Task' in our database. For periodic tasks, we extend a [Celery's default class](http://docs.celeryproject.org/en/3.1/userguide/periodic-tasks.html) to allow adding and removing task/cron jobs dynamically. 

## Install & Set up

`pip install django-celery`\
`python manage.py migrate djcelery`

## Run Celery

`celery -A http_handler worker -l [info|debug]`\
`celery -A http_handler beat --max-interval=10 -S djcelery.schedulers.DatabaseScheduler -l [info|debug]`

Run as daemon, \
`celery multi [start|restart|stopwait] new_user-worker -A http_handler -l info -concurrency=1 -l INFO -Q new_user --pidfile=logs/new_user-worker.pid --logfile=logs/new_user-worker.log`\
`celery multi [start|restart|stopwait] loop_sync-worker -A http_handler -l info -concurrency=1 -l INFO -Q loop_sync --pidfile=logs/loop_sync-worker.pid --logfile=logs/loop_sync-worker.log`\
`celery multi [start|restart|stopwait] default-worker -A http_handler -l info -l INFO -Q default --pidfile=logs/loop_sync-worker.pid --logfile=logs/default-worker.log`\
`celery -A http_handler beat --max-interval=10 -S djcelery.schedulers.DatabaseScheduler -l info --detach -f logs/beat.log`


## Database

1. Check out a how-to-setup instruction of [Murmur](https://github.com/haystack/murmur#setup-the-database) to learn how to set up the database on a new server.
2. If you make any change to the database, you should migrate those change like this:\
`python manage.py schemamigration schema --auto`\
`python manage.py migrate schema`

