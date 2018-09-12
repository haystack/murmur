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
from http_handler.settings import WEBSITE, BASE_URL
from smtp_handler.utils import *

class Command(BaseCommand):
    args = ''
    help = 'Process email'

    def handle(self, *args, **options):
        imap_dict = {}
        while True:
            imapAccounts = ImapAccount.objects.filter(is_running=True)
            
            for imapAccount in imapAccounts:
                if not imapAccount.current_mode:
                    continue

                res = {'status' : False, 'imap_error': False}
                
                
                if imapAccount.email not in imap_dict:
                    auth_res = {'status' : False, 'imap': None}
                    auth_res = authenticate( imapAccount )
                    if not auth_res['status']:
                        continue

                    imap = auth_res['imap']
                    imap_dict[imapAccount.email] = imap

                    print "Reauth ", imapAccount.email

                try:
                    new_uid = fetch_latest_email_id(imapAccount, imap_dict[imapAccount.email])
                    processing_subject = ""

                    processed = False
                    for msgid, edata in imap_dict[imapAccount.email].get_flags([latest_email_uid]).items():
                        if "YouPS" in edata:
                            processed = True
                            break

                    # execute user's rule only when there is a new email arrives
                    if not processed:
                        imap_dict[imapAccount.email].select_folder("INBOX")
                        execution_logs = ""
                        for i in range(imapAccount.newest_msg_id +1, new_uid+1): 
                            # when the message get deleted
                            if len(imap_dict[imapAccount.email].search("UID %d" % (i))) == 0:
                                continue

                            p = Pile(imap_dict[imapAccount.email], "UID %d" % (i))
                            if not p.check_email():
                                continue

                            print "Sender of new email is", p.get_sender()
                            # if it's the email from admin, then skip it
                            if WEBSITE in p.get_sender():
                                continue
                            processing_subject = p.get_subject()
                                
                            print "Processing email UID", i
                            code = imapAccount.current_mode.code
                            res = interpret(imapAccount, imap_dict[imapAccount.email], code, "UID %d" % (i))

                            if res['imap_log'] != "":
                                now = datetime.now()
                                now_format = now.strftime("%m/%d/%Y %H:%M:%S") + " "
                                execution_logs = now_format + " " + res['imap_log'] + "\n" + execution_logs
                    
                        imapAccount.newest_msg_id = new_uid
                        
                        print execution_logs
                        if execution_logs != "":
                            # append(imap, "Murmur mailbot log", res['imap_log'])
                            imapAccount.execution_log = execution_logs + imapAccount.execution_log 

                        imapAccount.save()

                        if res['imap_error']:
                            imapAccount.is_running = False
                            imapAccount.save()

                            # send_error_email()
                            subject = "[" + WEBSITE + "] Error during executing your email engine"
                            body = "Following error occurs during executing your email engine of email " + processing_subject + "\n"+ res['imap_log']
                            body += "\nTo fix the error and re-activate your engine, visit " + BASE_URL + "/editor"
                            send_email(subject, WEBSITE + "@" + BASE_URL, imapAccount.email, body)
                    
                except IMAPClient.Error, e:
                    res['code'] = e

                    # remove the imap object if error occurs, so that it will re-authenticate
                    imap_dict.pop(imapAccount.email, None)

                except Exception, e:
                    # TODO add exception
                    print e
                    res['code'] = msg_code['UNKNOWN_ERROR']

                res['status'] = True

                    
            
