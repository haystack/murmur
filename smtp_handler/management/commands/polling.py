from django.core.management.base import BaseCommand
from smtp_handler.utils import send_email
from schema.youps import ImapAccount
from datetime import datetime
from browser.imap import authenticate, fetch_latest_email_id, interpret
from imapclient import IMAPClient
from engine.constants import msg_code
from smtp_handler.Pile import Pile
from http_handler.settings import WEBSITE, BASE_URL

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
                    print "Attempt to auth ", imapAccount.email
                    auth_res = {'status' : False, 'imap': None}
                    auth_res = authenticate( imapAccount )
                    if not auth_res['status']:
                        continue

                    imap = auth_res['imap']
                    imap_dict[imapAccount.email] = imap

                    print "Reauth ", imapAccount.email

                    new_uid = -1

                try:
                    new_uid = fetch_latest_email_id(imapAccount, imap_dict[imapAccount.email])
                    processing_subject = ""

                    processed = False
                    p = Pile(imap_dict[imapAccount.email], "UID %d" % (new_uid))
                    if p.has_label("YouPS"):
                        continue

                    # execute user's rule only when there is a new email arrives
                    if not processed:
                        imap_dict[imapAccount.email].select_folder("INBOX")
                        execution_logs = ""
                        start_uid = imapAccount.newest_msg_id +1 if imapAccount.newest_msg_id +1 < new_uid else new_uid

                        for i in range(start_uid, new_uid+1):
                            # when the message get deleted
                            if len(imap_dict[imapAccount.email].search("UID %d" % (i))) == 0:
                                continue

                            print "Processing email UID", i

                            p = Pile(imap_dict[imapAccount.email], "UID %d" % (i))
                            if not p.check_email():
                                continue


                            # if it's the email from admin, then skip it
                            if WEBSITE in p.get_sender():
                                p.add_flags(['YouPS'])
                                continue

                            print "Sender of new email is", p.get_sender()
                            processing_subject = p.get_subject()

                            code = imapAccount.current_mode.code
                            res = interpret(imapAccount, imap_dict[imapAccount.email], code, "UID %d" % (i))

                            if res['imap_log'] != "":
                                print "Polling: " + res['imap_log']
                                now = datetime.now()
                                now_format = now.strftime("%m/%d/%Y %H:%M:%S") + " "
                                execution_logs = now_format + " " + res['imap_log'] + "\n" + execution_logs

                        imapAccount.newest_msg_id = new_uid

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
                            body += "\nTo fix the error and re-activate your engine, visit " + WEBSITE + ".csail.mit.edu/editor"
                            send_email(subject, WEBSITE + "@" + BASE_URL, imapAccount.email, body)

                except IMAPClient.Error, e:
                    res['code'] = e

                    # remove the imap object if error occurs, so that it will re-authenticate
                    imap_dict.pop(imapAccount.email, None)

                except Exception, e:
                    # TODO add exception
                    print e
                    # if error occurs just skip the email
                    if new_uid > 0:
                        msgs = imap_dict[imapAccount.email].search( "UID %d" % (new_uid) )
                        imap_dict[imapAccount.email].add_flags(msgs, ['YouPS'])
                        imapAccount.newest_msg_id = new_uid +1
                        imapAccount.save()

                    res['code'] = msg_code['UNKNOWN_ERROR']

                res['status'] = True



