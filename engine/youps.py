import base64
import logging
import random
import traceback
from browser.imap import GoogleOauth2
from http_handler.settings import IMAP_SECRET
from schema.youps import ImapAccount, MailbotMode, Action
from Crypto.Cipher import AES
from imapclient import IMAPClient
from engine.constants import msg_code
from browser.imap import authenticate, interpret
import string
from browser.models.mailbox import MailBox

from http_handler.tasks import remove_periodic_task, loop_sync_user_inbox

import logging

logger = logging.getLogger('youps')  # type: logging.Logger

def login_imap(email, password, host, is_oauth):
    """This function is called only once per each user when they first attempt to login to YoUPS.
    check if we are able to login to the user's imap using given credientials.
    if we can, encrypt and store credientials on our DB. 

        Args:
            email (string): user's email address
            password (string): if is_oauth True, then it contains oauth token. Otherwise, it is plain password
            host (string): IMAP host address
            is_oauth (boolean): if the user is using oauth or not
    """

    res = {'status' : False}

    try:
        imap = IMAPClient(host, use_uid=True)

        refresh_token = ''
        access_token = ''
        if is_oauth:
            # TODO If this imap account is already mapped with this account, bypass the login.
            oauth = GoogleOauth2()
            response = oauth.generate_oauth2_token(password)
            refresh_token = response['refresh_token']
            access_token = response['access_token']

            imap.oauth2_login(email, access_token)

        else:
            imap.login(email, password)

            # encrypt password then save
            aes = AES.new(IMAP_SECRET, AES.MODE_CBC, 'This is an IV456')

            # padding password
            padding = random.choice(string.letters)
            while padding == password[-1]:
                padding = random.choice(string.letters)
                continue
            extra = len(password) % 16
            if extra > 0:
                password = password + (padding * (16 - extra))
            password = aes.encrypt(password)

        imapAccount = ImapAccount.objects.filter(email=email)
        if not imapAccount.exists():
            imapAccount = ImapAccount(email=email, password=base64.b64encode(password), host=host)
            imapAccount.host = host

            # = imapAccount
        else:
            imapAccount = imapAccount[0]
            res['imap_code'] = imapAccount.current_mode.code
            res['imap_log'] = imapAccount.execution_log


        if is_oauth:
            imapAccount.is_oauth = is_oauth
            imapAccount.access_token = access_token
            imapAccount.refresh_token = refresh_token

        imapAccount.save()

        """this procedure is required when a new user first register to YoUPS
        1) Scrape folder using IMAP list_folders() to register Folder instances belong to the user
        2) Scrape contacts using scrape_contacts to register Contacts instances belong to the user
        """
        # create the mailbox
        mailbox = MailBox(imapAccount, imap)
        # sync the mailbox with imap
        mailbox._sync()
        logger.info("Mailbox sync done")
        # after sync, logout to prevent multi-connection issue
        imap.logout()

        # now user can use youps
        imapAccount.is_initialized = True
        imapAccount.save()

        # start keeping eye on users' inbox
        loop_sync_user_inbox.delay(imapAccount)

        # TODO notify the user that their account is ready to be used

        res['status'] = True

    except IMAPClient.Error, e:
        res['code'] = e

    except Exception, e:
        # TODO add exception
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res

def fetch_execution_log(user, email, push=True):
    res = {'status' : False}

    try:
        imapAccount = ImapAccount.objects.get(email=email)
        res['imap_log'] = imapAccount.execution_log
        res['user_status_msg'] = imapAccount.status_msg
        res['status'] = True

    except ImapAccount.DoesNotExist:
        res['code'] = "Error during authentication. Please refresh"
    except Exception, e:
        # TODO add exception
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res

def delete_mailbot_mode(user, email, mode_id, push=True):
    res = {'status' : False}

    try:
        imapAccount = ImapAccount.objects.get(email=email)
        mm = MailbotMode.objects.get(uid=mode_id, imap_account=imapAccount)

        if imapAccount.current_mode == mm:
            imapAccount.current_mode = None
            imapAccount.is_running = False

        mm.delete()

        res['status'] = True

    except ImapAccount.DoesNotExist:
        res['code'] = "Error during deleting the mode. Please refresh the page."
    except MailbotMode.DoesNotExist:
        res['code'] = "Error during deleting the mode. Please refresh the page."
    except Exception, e:
        # TODO add exception
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res

def run_mailbot(user, email, current_mode_id, modes, is_test, run_request, push=True):
    """This function is called everytime users hit "run", "stop" or "save" their scripts.

        Args:
            user (Model.UserProfile)
            email (string): user's email address
            current_mode_id (integer): ID of currently selected/running mode
            modes (list): a list of dicts that each element is information about each user's mode
            is_test (boolean): if is_test is True, then it just simulates the user's script and prints out log but not actually execute it.  
            run_request (boolean): potentially deprecated as we move toward one-off running fashion. 
    """
    res = {'status' : False, 'imap_error': False, 'imap_log': ""}

    try:
        imapAccount = ImapAccount.objects.get(email=email)
        auth_res = authenticate( imapAccount )
        if not auth_res['status']:
            raise ValueError('Something went wrong during authentication. Refresh and try again!')

        imap = auth_res['imap']  # noqa: F841 ignore unused

        imapAccount.is_test = is_test
        imapAccount.is_running = run_request

        # TODO these don't work anymore
        # uid = fetch_latest_email_id(imapAccount, imap)
        # imapAccount.newest_msg_id = uid

        # remove all user's tasks of this user to keep tasks up-to-date
        Action.objects.filter(folder__imap_account=imapAccount).delete()
        remove_periodic_task.delay( imapAccount.id )

        for key, value in modes.iteritems():
            mode_id = value['id']
            mode_name = value['name'].encode('utf-8')
            code = value['code'].encode('utf-8')
            print mode_id
            print mode_name
            print code

            mailbotMode = MailbotMode.objects.filter(uid=mode_id, imap_account=imapAccount)
            if not mailbotMode.exists():
                mailbotMode = MailbotMode(uid=mode_id, name=mode_name, code=code, imap_account=imapAccount)
                mailbotMode.save()
            else:
                mailbotMode = mailbotMode[0]
                mailbotMode.code = code
                mailbotMode.save()

        imapAccount.current_mode = MailbotMode.objects.filter(uid=current_mode_id, imap_account=imapAccount)[0]
        imapAccount.save()

        if run_request:
            # TODO run it several times over for the selected folders
            # TODO change with appropriate search_criteria
            imap.select_folder("INBOX")
            # TODO replace this with the right search criteria 
            res = interpret(imapAccount, imap, code, "UID %d:*" % 90000, is_test)

            # if the code execute well without any bug, then save the code to DB
            if not res['imap_error']:
                res['imap_log'] = ("[TEST MODE] Your rule is successfully installed. It won't take actual action but simulate your rule. \n" + res['imap_log']) if is_test else ("Your rule is successfully installed. \n" + res['imap_log'])
        #         now = datetime.now()
        #         now_format = now.strftime("%m/%d/%Y %H:%M:%S") + " "
        #         res['imap_log'] = now_format + res['imap_log']
        #     else:
        #         imapAccount.is_running = False
        #         imapAccount.save()
        # else:

        #     res['imap_log'] = "Your mailbot stops running"

        res['status'] = True


    except IMAPClient.Error, e:
        res['code'] = e
    except ImapAccount.DoesNotExist:
        res['code'] = "Not logged into IMAP"
    except Exception, e:
        # TODO add exception
        print e
        print (traceback.format_exc())
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res

def save_shortcut(user, email, shortcuts, push=True):
    res = {'status' : False, 'imap_error': False}

    try:
        imapAccount = ImapAccount.objects.get(email=email)

        imapAccount.shortcuts = shortcuts
        imapAccount.save()

        res['status'] = True


    except IMAPClient.Error, e:
        res['code'] = e
    except ImapAccount.DoesNotExist:
        res['code'] = "Not logged into IMAP"
    except Exception, e:
        # TODO add exception
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res
