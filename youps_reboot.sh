#!/bin/sh
sudo service apache2 restart
celery multi restart new_user-worker -A http_handler -l info --concurrency=1 -l INFO -Q new_user --pidfile=logs/new_user-worker.pid --logfile=logs/new_user-worker.log
celery multi restart loop_sync-worker -A http_handler -l info --concurrency=1 -l INFO -Q loop_sync --pidfile=logs/loop_sync-worker.pid --logfile=logs/loop_sync-worker.log
celery multi restart default-worker -A http_handler -l info -l INFO -Q default --pidfile=logs/default-worker.pid --logfile=logs/default-worker.log
