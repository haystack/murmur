from django.core.management.base import BaseCommand, CommandError
from smtp_handler.utils import *
from http_handler.settings import BASE_URL, DEFAULT_FROM_EMAIL, WEBSITE

class Command(BaseCommand):
    args = ''
    help = 'Export data to remote server'

    def handle(self, *args, **options):
        # do something here
        print "DIGEST cron"
        send_email("Cron test", DEFAULT_FROM_EMAIL, "soyapark2535@gmail.com", "test")