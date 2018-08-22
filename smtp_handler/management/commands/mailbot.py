import base64

from django.core.management.base import BaseCommand, CommandError
from smtp_handler.utils import *
from http_handler.settings import BASE_URL, DEFAULT_FROM_EMAIL, WEBSITE
from schema.models import *
from datetime import datetime, timedelta
from browser.imap import *
from imapclient import IMAPClient
from engine.constants import *
from smtp_handler.Pile import *
from engine.google_auth import *
from Crypto.Cipher import AES
import datetime

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
                    aes = AES.new(IMAP_SECRET, AES.MODE_CBC, 'This is an IV456')
                    password = aes.decrypt( base64.b64decode(imapAccount.password) )

                    index = 0
                    last_string = password[-1]
                    for c in reversed(password):
                        if last_string != c:
                            password = password[:(-1)*index]
                            break
                        index = index + 1
                    imap.login(imapAccount.email, password)

            except IMAPClient.Error, e:
                # TODO try to renew the access token
                try: 
                    if imapAccount.is_oauth:
                        oauth = GoogleOauth2()
                        response = oauth.RefreshToken(imapAccount.refresh_token)
                        imap.oauth2_login(imapAccount.email, response['access_token'])

                        imapAccount.access_token = response['access_token']
                        imapAccount.save()
                    else:
                        res['code'] = "Can't authenticate your email"
                except IMAPClient.Error, e:  
                    res['code'] = "Can't authenticate your email"
            except Exception, e:
                # TODO add exception
                print e
                res['code'] = msg_code['UNKNOWN_ERROR']
            

            try:
                new_uid = fetch_latest_email_id(imapAccount, imap)

                # execute user's rule only when there is a new email arrive
                if new_uid > imapAccount.newest_msg_id:
                    imap.select_folder("INBOX")
                    execution_logs = ""
                    for i in range(imapAccount.newest_msg_id +1, new_uid+1): 
                        p = Pile(imap, "UID %d" % (i))
                        print "Sender of new email is", p.get_senders()

                        if p.get_senders()[0] == "mailbot-log@murmur.csail.mit.edu":
                            continue
                            
                        print "Processing email UID", i
                        res = interpret(imap, imapAccount.code, "UID %d" % (i))

                        if res['imap_log'] != "":
                            now = datetime.datetime.now()
                            now_format = now.strftime("%m/%d/%Y %H:%M:%S") + " "
                            execution_logs = now_format + " " + res['imap_log']+ execution_logs
                
                    imapAccount.newest_msg_id = new_uid
                    
                    print execution_logs
                    if execution_logs != "":
                        # append(imap, "Murmur mailbot log", res['imap_log'])
                        imapAccount.execution_log = res['imap_log'] + imapAccount.execution_log 

                    imapAccount.save()

                    # TODO send the error msg via email to the user
                    if res['imap_error']:
                        pass

                
                #if res['imap_error']:
                #    imapAccount.save()
            except IMAPClient.Error, e:
                res['code'] = e
            except Exception, e:
                # TODO add exception
                print e
                res['code'] = msg_code['UNKNOWN_ERROR']

            res['status'] = True

                    
            