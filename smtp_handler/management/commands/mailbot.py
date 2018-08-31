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

class Command(BaseCommand):
    args = ''
    help = 'Process email'

    def handle(self, *args, **options):
        imapAccounts = ImapAccount.objects.filter(is_running=True)
        for imapAccount in imapAccounts:
            if not imapAccount.current_mode:
                continue

            res = {'status' : False, 'imap_error': False}
            print "RUN MAILbot of ", imapAccount.email

            auth_res = authenticate( imapAccount )
            if not auth_res['status']:
                continue

            imap = auth_res['imap']

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
                        code = imapAccount.current_mode.code
                        res = interpret(imap, code, "UID %d" % (i))

                        if res['imap_log'] != "":
                            now = datetime.datetime.now()
                            now_format = now.strftime("%m/%d/%Y %H:%M:%S") + " "
                            execution_logs = now_format + " " + res['imap_log'] + "\n" + execution_logs
                
                    imapAccount.newest_msg_id = new_uid
                    
                    print execution_logs
                    if execution_logs != "":
                        # append(imap, "Murmur mailbot log", res['imap_log'])
                        imapAccount.execution_log = execution_logs + imapAccount.execution_log 

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

                    
            
