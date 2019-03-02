from django.core.management.base import BaseCommand
from schema.youps import ImapAccount
from datetime import datetime
from browser.imap import fetch_latest_email_id, authenticate, interpret
from browser.models.mailbox import MailBox
from imapclient import IMAPClient
from engine.constants import msg_code
from smtp_handler.Pile import Pile
from http_handler.settings import WEBSITE
import logging

# Get an instance of a logger
logger = logging.getLogger('youps')  # type: logging.Logger

class Command(BaseCommand):
    args = ''
    help = 'Process email'

    def handle(self, *args, **options):

        # iterate over all the user accounts in the database
        imapAccounts = ImapAccount.objects.filter(is_running=True)
        for imapAccount in imapAccounts:
            if not imapAccount.current_mode:
                continue

            res = {'status' : False, 'imap_error': False}
            logger.info("run mailbot for email: %s" % imapAccount.email)

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
            except Exception:
                logger.exception("mailbox sync failed")

            try:
                mailbox = MailBox(imapAccount, imap)
                # after sync, logout to prevent multi-connection issue
                imap.logout()
                mailbox._run_user_code()  
            except Exception:
                logger.exception("mailbox task running failed")

            continue

            try:
                # get the UID of the latest message received by the user
                new_uid = fetch_latest_email_id(imapAccount, imap)

                # execute user's rule only when there is new mail 
                if new_uid > imapAccount.newest_msg_id:
                    imap.select_folder("INBOX")

                    # execution logs to display to the user
                    execution_logs = ""

                    # iterate over the new messages
                    for i in range(imapAccount.newest_msg_id +1, new_uid+1):
                        p = Pile(imap, "UID %d" % (i))
                        logger.debug('new email sender: %s' % p.get_senders())

                        # TODO why are we ignoring this
                        if len(p.get_senders()) != 0 and p.get_senders()[0] == WEBSITE + "@murmur.csail.mit.edu":
                            continue

                        # get the code the user is going to run
                        logger.debug('new email UID: %s' % i)
                        code = imapAccount.current_mode.code

                        # run the user's code
                        res = interpret(imapAccount, imap, code, "UID %d" % (i))

                        # append to the execution logs 
                        if res['imap_log'] != "":
                            now = datetime.now()
                            now_format = now.strftime("%m/%d/%Y %H:%M:%S") + " "
                            execution_logs = now_format + " " + res['imap_log'] + "\n" + execution_logs

                    imapAccount.newest_msg_id = new_uid
                    logger.info(execution_logs) 
                    if execution_logs != "":
                        # append(imap, "Murmur mailbot log", res['imap_log'])
                        imapAccount.execution_log = execution_logs + imapAccount.execution_log

                    imapAccount.save()

                    # TODO send the error msg via email to the user
                    if res['imap_error']:
                        imapAccount.is_running = False
                        # send_error_email()

                # log out of the user's account
                imap.logout()

            except IMAPClient.Error, e:
                logger.exception("failure in fetch or user code")
                res['code'] = e
            except Exception, e:
                logger.exception("failure in fetch or user code")
                res['code'] = msg_code['UNKNOWN_ERROR']

            res['status'] = True