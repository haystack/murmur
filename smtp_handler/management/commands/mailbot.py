from django.core.management.base import BaseCommand, CommandError
from smtp_handler.utils import *
from http_handler.settings import BASE_URL, DEFAULT_FROM_EMAIL, WEBSITE
from schema.models import *
from datetime import datetime, timedelta
from browser.imap import *
from imapclient import IMAPClient

class Command(BaseCommand):
    args = ''
    help = 'Process email'

    def handle(self, *args, **options):
        imapAccounts = ImapAccount.objects.filter().exclude(code="")
        for imapAccount in imapAccounts:
            res = {'status' : False, 'imap_error': False}
            print "RUN MAILbot of ", imapAccount.email

            try:    
                imap = IMAPClient(imapAccount.host, use_uid=True)
                if imapAccount.is_oauth:
                    # TODO if access_token is expired, then get a new token
                    imap.oauth2_login(imapAccount.email, imapAccount.access_token)
                else:
                    imap.login(imapAccount.email, imapAccount.password)

                new_uid = fetch_latest_email_id(imapAccount, imap)
            except IMAPClient.Error, e:
                res['code'] = "Can't authenticate your email"
            except Exception, e:
                # TODO add exception
                print e
                res['code'] = msg_code['UNKNOWN_ERROR']
            
            try:
                # execute user's rule only when there is a new email arrive
                if new_uid > imapAccount.newest_msg_id:
                    imap.select_folder("INBOX")

                    res = interpret(imap, imapAccount.code, imap.search("UID %d:%d") % (imapAccount.newest_msg_id +1, new_uid))
                
                    imapAccount.newest_msg_id = new_uid
                    imapAccount.save()

                    # TODO save log 
                    print res['imap_log']

                # TODO send the error msg via email to the user
                #if res['imap_error']:
                #    imapAccount.save()
            except IMAPClient.Error, e:
                res['code'] = e
            except Exception, e:
                # TODO add exception
                print e
                res['code'] = msg_code['UNKNOWN_ERROR']

            res['status'] = True

                    
            