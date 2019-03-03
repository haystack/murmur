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
`celery multi [start|restart|stopwait] worker1 -A http_handler --pidfile=logs/worker1.pid --logfile=logs/worker1.log`
`celery -A http_handler beat --max-interval=10 -S djcelery.schedulers.DatabaseScheduler -l [info|debug] --detach -f logs/beat.log`