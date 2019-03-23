from django.core.management.base import BaseCommand
from schema.youps import ImapAccount
from datetime import datetime
from browser.imap import authenticate
from browser.sandbox import interpret
from browser.models.mailbox import MailBox
from imapclient import IMAPClient
from engine.constants import msg_code
from smtp_handler.Pile import Pile
from smtp_handler.utils import send_email
from http_handler.settings import WEBSITE, BASE_URL
import logging

# Get an instance of a logger
logger = logging.getLogger('youps')  # type: logging.Logger

class Command(BaseCommand):
    args = ''
    help = 'Process email'

    def handle(self, *args, **options):
        
        # iterate over all the user accounts in the database
        imapAccounts = ImapAccount.objects.filter(is_initialized=False)

        for imapAccount in imapAccounts:
            if imapAccount.is_running:
                continue
            imapAccount.is_running = True
            imapAccount.save()

            res = {'status' : False, 'imap_error': False}
            logger.info("run intiail sync for email: %s" % imapAccount.email)

            # authenticate with the user's imap server
            auth_res = authenticate(imapAccount)
            # if authentication failed we can't run anything
            if not auth_res['status']:
                continue

            # get an imapclient which is authenticated
            imap = auth_res['imap']

            try:
                # create the mailbox
                mailbox = MailBox(imapAccount, imap)
                # sync the mailbox with imap
                mailbox._sync()
                logger.info("Mailbox sync done")
                # after sync, logout to prevent multi-connection issue
                imap.logout()
                logger.info("Mailbox logged out to prevent multi-connection issue")
                mailbox._run_user_code()  
            except Exception:
                logger.exception("mailbox task running failed %s " % imapAccount.email)
                send_email("Your YoUPS account is ready!", "no-reply@" + BASE_URL, 'kixlab.rally@gmail.com', "%s register inbox failed "  % imapAccount.email)
                
                continue

            imapAccount.is_initialized = True
            imapAccount.is_running = False
            imapAccount.save()
            send_email("Your YoUPS account is ready!", "no-reply@" + BASE_URL, imapAccount.email, "Start writing your automation rule here! " + BASE_URL)
            res['status'] = True