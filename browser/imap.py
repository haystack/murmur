import sys
import traceback
try:
    from StringIO import StringIO
except ImportError:
    import io
import contextlib
from smtp_handler.utils import send_email, get_body, codeobject_dumps, codeobject_loads
from smtp_handler.Pile import Pile
from email import message, utils, message_from_string
from email.utils import parseaddr
from imapclient import IMAPClient
from http_handler.settings import BASE_URL, WEBSITE, IMAP_SECRET
from engine.google_auth import GoogleOauth2
from Crypto.Cipher import AES
from engine.constants import msg_code
from datetime import datetime, timedelta
from schema.youps import MailbotMode, Action, FolderSchema
import calendar
import base64
import json
import logging

logger = logging.getLogger('youps')

def authenticate(imap_account):
    res = {'status' : False, 'imap_error': False, 'imap_log': "", 'imap': None}
    email_addr = ""
    imap = IMAPClient(imap_account.host, use_uid=True)
    try:
        email_addr = imap_account.email
        if imap_account.is_oauth:
            # TODO if access_token is expired, then get a new token
            imap.oauth2_login(imap_account.email, imap_account.access_token)
        else:
            aes = AES.new(IMAP_SECRET, AES.MODE_CBC, 'This is an IV456')
            password = aes.decrypt( base64.b64decode(imap_account.password) )

            index = 0
            last_string = password[-1]
            for c in reversed(password):
                if last_string != c:
                    password = password[:(-1)*index]
                    break
                index = index + 1

            imap.login(imap_account.email, password)

        res['imap'] = imap
        res['status'] = True
    except IMAPClient.Error, e:
        try:
            logger.debug('try to renew token')
            if imap_account.is_oauth:
                oauth = GoogleOauth2()
                response = oauth.RefreshToken(imap_account.refresh_token)
                imap.oauth2_login(imap_account.email, response['access_token'])

                imap_account.access_token = response['access_token']
                imap_account.save()

                res['imap'] = imap
                res['status'] = True
            else:
                # TODO this is not DRY and not useful error messages
                logger.error("cannot renew token for non-oauth account")
                res['code'] = "Can't authenticate your email"
        except IMAPClient.Error, e:
            logger.exception("failed to authenticate email")
            res['imap_error'] = e
            res['code'] = "Can't authenticate your email"
        except Exception, e:
            logger.exception("failed to authenticate email")
            # TODO add exception
            res['imap_error'] = e
            res['code'] = msg_code['UNKNOWN_ERROR']

    if res['status'] is False:
        # email to the user that there is error at authenticating email
        if len(email_addr) > 0:
            subject = "[" + WEBSITE + "] Authentication error occurs"
            body = "Authentication error occurs! \n" + str(res['imap_error'])
            body += "\nPlease log in again at " + BASE_URL + "/editor"
            send_email(subject, WEBSITE + "@" + BASE_URL, email_addr, body)

        # TODO don't delete
        # Delete this ImapAccount information so that it requires user to reauthenticate
        imap_account.password = ""
        imap_account.access_token = ""

        # turn off the email engine
        imap_account.is_running = False
        imap_account.save()

    return res

def append(imap, subject, content):
    new_message = message.Message()
    new_message["From"] = "mailbot-log@" + BASE_URL
    new_message["Subject"] = subject
    new_message.set_payload(content)

    imap.append('INBOX', str(new_message), ('murmur-log'))

