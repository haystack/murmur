import base64, email, hashlib, json, logging, random, re, requests, sys, time, traceback

from browser.imap import *

from schema.youps import ImapAccount, MailbotMode

from Crypto.Cipher import AES
from imapclient import IMAPClient
import string
import random

from http_handler.tasks import add_periodic_task

def login_imap(user, password, host, is_oauth, push=True):
    res = {'status' : False}

    try:
        imap = IMAPClient(host, use_uid=True)
        email = user.email

        refresh_token = ''
        access_token = ''
        password_original = password
        if is_oauth:
            # TODO If this imap account is already mapped with this account, by pass the login.
            oauth = GoogleOauth2()
            response = oauth.generate_oauth2_token(password)
            refresh_token = response['refresh_token']
            access_token = response['access_token']

            imap.oauth2_login(email, access_token)

        else:
            imap.login(email, password)

            #encrypt password then save
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

        # Log out after auth verification
        imap.logout()

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


        # u = UserProfile.objects.filter(email=email)
        # if not u.exists():
        #     u = UserProfile.objects.create_user(email, password_original)

        #     res['code'] = "New user"
        # else:
        #     res['code'] = "This account is already logged in!"

        #     # if user has source code running, send it
        #     u = u[0]
        #     imapAccount = u
        #     res['imap_code'] = imapAccount.code

        # u.host = host
        # u.imap_password = password

        # u.save()

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

def run_mailbot(user, email, current_mode_id, modes, is_test, is_running, push=True):
    res = {'status' : False, 'imap_error': False, 'imap_log': ""}

    try:
        imapAccount = ImapAccount.objects.get(email=email)
        auth_res = authenticate( imapAccount )
        if not auth_res['status']:
            raise ValueError('Something went wrong during authentication. Refresh and try again!')

        imap = auth_res['imap']

        imapAccount.is_test = is_test
        imapAccount.is_running = is_running

        uid = fetch_latest_email_id(imapAccount, imap)
        imapAccount.newest_msg_id = uid

        add_periodic_task.delay( 3, imapAccount.id, imap, "print 'PERIODIC TEST'", "UID 10000" )

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

        if imapAccount.is_running:
            res = interpret(imapAccount, imap, code, "UID %d" % uid, is_test)

            # if the code execute well without any bug, then save the code to DB
            if not res['imap_error']:
                res['imap_log'] = ("[TEST MODE] Your rule is successfully installed. It won't take actual action but simulate your rule. \n" + res['imap_log']) if is_test else ("Your rule is successfully installed. \n" + res['imap_log'])
                now = datetime.now()
                now_format = now.strftime("%m/%d/%Y %H:%M:%S") + " "
                res['imap_log'] = now_format + res['imap_log']
            else:
                imapAccount.is_running = False
                imapAccount.save()
        else:

            res['imap_log'] = "Your mailbot stops running"

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
