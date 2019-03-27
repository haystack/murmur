import base64
import logging
import random
import string
import traceback

from Crypto.Cipher import AES
from imapclient import IMAPClient

from browser.imap import GoogleOauth2, authenticate
from browser.models.mailbox import MailBox
from browser.sandbox import interpret
from engine.constants import msg_code
from http_handler.settings import IMAP_SECRET
from schema.youps import (FolderSchema, ImapAccount, MailbotMode, MessageSchema, EmailRule)

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

    logger.info('adding new account %s' % email)
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
            res['imap_code'] = ""  # TODO PLEASE REMOVE THIS WOW
            res['imap_log'] = imapAccount.execution_log


        if is_oauth:
            imapAccount.is_oauth = is_oauth
            imapAccount.access_token = access_token
            imapAccount.refresh_token = refresh_token

        imapAccount.is_gmail = imap.has_capability('X-GM-EXT-1')

        imapAccount.save()

        res['status'] = True
        logger.info("added new account %s" % imapAccount.email)

    except IMAPClient.Error, e:
        res['code'] = e
    except Exception, e:
        logger.exception("Error while login %s %s " % (e, traceback.format_exc()))
        res['code'] = msg_code['UNKNOWN_ERROR']

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

def remove_rule(user, email, rule_id):
    """This function remove a EmailRule of user;

        Args:
            user (Model.UserProfile)
            email (string): user's email address
            rule_id (integer): ID of EmailRule to be deleted
    """
    res = {'status' : False, 'imap_error': False}

    try:
        imap_account = ImapAccount.objects.get(email=email)
        er = EmailRule.objects.filter(uid=rule_id, mode__imap_account=imap_account)

        er.delete()

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
    logger = logging.getLogger('youps')  # type: logging.Logger

    # this log is going to stdout but not going to the logging file
    # why are django settings not being picked up
    logger.info("user %s has run, stop, or saved" % email)

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

        for mode_index, mode in modes.iteritems():
            mode_id = mode['id']
            mode_name = mode['name'].encode('utf-8')

            mailbotMode = MailbotMode.objects.filter(uid=mode_id, imap_account=imapAccount)
            if not mailbotMode.exists():
                mailbotMode = MailbotMode(uid=mode_id, name=mode_name, imap_account=imapAccount)
                mailbotMode.save()

            else:
                mailbotMode = mailbotMode[0]

            # Remove old editors to re-save it
            # TODO  dont remove it
            er = EmailRule.objects.filter(mode=mailbotMode)
            er.delete()

            for value in mode['editors']:
                uid = value['uid']
                code = value['code'].encode('utf-8')
                folders = value['folders']
                print mode_id
                print mode_name
                print code
                print folders
                
                er = EmailRule(uid=uid, mode=mailbotMode, type=value['type'], code=code)
                er.save()

                # # Save selected folder for the mode
                for f in folders:
                    folder = FolderSchema.objects.get(imap_account=imapAccount, name=f)
                    er.folders.add(folder)

                er.save()


        imapAccount.current_mode = MailbotMode.objects.filter(uid=current_mode_id, imap_account=imapAccount)[0]
        imapAccount.save()

        if run_request:
            logger.info("user %s run request" % imapAccount.email)

            res = interpret(MailBox(imapAccount, imap), imapAccount.current_mode, is_test)

            # if the code execute well without any bug, then save the code to DB
            if not res['imap_error']:
                pass
                # res['imap_log'] = ("[TEST MODE] Your rule is successfully installed. It won't take actual action but simulate your rule. %s \n" + res['imap_log']) if is_test else ("Your rule is successfully installed. \n" + res['imap_log'])
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
        logger.exception("failed while doing a user code run")
        res['code'] = e
    except ImapAccount.DoesNotExist:
        logger.exception("failed while doing a user code run")
        res['code'] = "Not logged into IMAP"
    except FolderSchema.DoesNotExist:
        logger.exception("failed while doing a user code run")
        logger.debug("Folder is not found, but it should exist!")
    except Exception, e:
        # TODO add exception
        logger.exception("failed while doing a user code run")
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


def folder_recent_messages(user, email, folder_name, N=3):
    res = {'status' : False, 'imap_error': False}

    try:
        imapAccount = ImapAccount.objects.get(email=email)

        messages = MessageSchema.objects.filter(imap_account=imapAccount, folder_schema__name=folder_name).order_by("-date")[:N]

        res['messages'] = [{"id": m.id, "folder": folder_name, "subject": m.subject, "sender": str(m.sender.name), "deadline": str(m.deadline) if m.deadline else "", "task": str(m.task)} for m in messages]
        # 'sender': str(m.sender.name), 
        # 'deadline': str(m.deadline),
        # 
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