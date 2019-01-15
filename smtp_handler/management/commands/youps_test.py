# -*- coding: utf-8 -*-
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
        
        if len(args) == 0:
            print "give recipients address as an argument!"
            return

        to_addr = args[0]
        test_cases = [
            {
                'subject': 'test email',
                'from_addr': 'test@youps.csail.mit.edu',
                'body_plain': 'hello world',
                'body_html': 'hi'
            },
            {
                'subject': 'test email with emoji 🤷‍♀️',
                'from_addr': 'test@youps.csail.mit.edu',
                'body_plain': 'hello world',
                'body_html': '😎'
            },
        ]

        for t in test_cases:
            send_email()(t['subject'], t['from_addr'], to_addr, t['body_plain'], t['body_html'])

                    
            
