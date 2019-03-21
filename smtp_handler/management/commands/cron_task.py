from django.core.management.base import BaseCommand
import logging
import http_handler.tasks as tasks

logger = logging.getLogger('youps')  # type: logging.Logger

class Command(BaseCommand):
    help = 'Run cron tasks'
    args = '<task_name>'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise Exception('You must specify one task name')

        task_name = args[0]

        if task_name == "register":
            tasks.register_inbox()
        elif task_name == "sync":
            tasks.loop_sync_user_inbox()
        else:
            raise Exception('Valid tasks are register, sync')
