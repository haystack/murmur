import base64

from django.core.management.base import BaseCommand, CommandError
from smtp_handler.utils import *
from schema.models import *
from datetime import datetime, timedelta
from browser.imap import *
from imapclient import IMAPClient
from engine.constants import *
from smtp_handler.Pile import *
import datetime
from http_handler.settings import WEBSITE

class Command(BaseCommand):
    args = ''
    help = 'Process email'

    def handle(self, *args, **options):
        imapAccounts = ImapAccount.objects.filter(is_running=True)
        
        
        send_email()

                    
            
