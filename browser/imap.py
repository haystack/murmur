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
from http_handler.tasks import add_periodic_task
import marshal, ujson
import logging

logger = logging.getLogger('youps')

def authenticate(imap_account):
    res = {'status' : False, 'imap_error': False, 'imap_log': "", 'imap': None}
    email_addr = ""
    try:
        imap = IMAPClient(imap_account.host, use_uid=True)
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

def fetch_latest_email_id(imap_account, imap_client):
    imap_client.select_folder("INBOX")
    uid_list = []

    # init
    if imap_account.newest_msg_id == -1:
        uid_list = imap_client.search("UID 199510:*")

    else:
        uid_list = imap_client.search("UID %d:*" % imap_account.newest_msg_id)

    # error handling for empty inbox
    if len(uid_list) == 0:
        uid_list = [1]

    return max(uid_list)

def wrapper(imap_account, imap, code, search_creteria, is_test=False, email_content=None):
    interpret(imap_account, imap, code, search_creteria, is_test, email_content)

def interpret(imap_account, imap, code, search_creteria, is_test=False, email_content=None):
    res = {'status' : False, 'imap_error': False, 'imap_log': ""}
    messages = imap.search( search_creteria )
    is_valid = True

    if len(messages) == 0:
        is_valid = False

    pile = Pile(imap, search_creteria)
    if not pile.check_email():
        is_valid = False

    @contextlib.contextmanager
    def stdoutIO(stdout=None):
        old = sys.stdout
        if stdout is None:
            stdout = StringIO()
        sys.stdout = stdout
        yield stdout
        sys.stdout = old

    logger = logging.getLogger('youps.user')

    with stdoutIO() as s:
        def catch_exception(e):
            etype, evalue = sys.exc_info()[:2]
            estr = traceback.format_exception_only(etype, evalue)
            logstr = 'Error during executing your code \n'
            for each in estr:
                logstr += '{0}; '.format(each.strip('\n'))

            logstr = "%s \n %s" % (logstr, str(e))

            # Send this error msg to the user
            res['imap_log'] = logstr
            res['imap_error'] = True

        def on_message_arrival(func=None):
            if not func or type(func).__name__ != "function":
                raise Exception('on_message_arrival(): requires callback function but it is %s ' % type(func).__name__)
                
            if func.func_code.co_argcount != 1:
                raise Exception('on_message_arrival(): your callback function should have only 1 argument, but there are %d argument(s)' % func.func_code.co_argcount)

            # TODO warn users if it conatins send() and their own email (i.e., it potentially leads to infinite loops) 

            # TODO replace with the right folder
            current_folder_schema = FolderSchema.objects.filter(imap_account=imap_account, name="INBOX")[0]
            action = Action(trigger="arrival", code=codeobject_dumps(func.func_code), folder=current_folder_schema)
            action.save()

        def set_interval(interval=None, func=None):
            if not interval:
                raise Exception('set_interval(): requires interval (in second)')

            if interval < 1:
                raise Exception('set_interval(): requires interval larger than 1 sec')

            if not func or type(func).__name__ != "function":
                raise Exception('set_interval(): requires callback function but it is %s ' % type(func).__name__)
                
            if func.func_code.co_argcount != 0:
                raise Exception('set_interval(): your callback function should have only 0 argument, but there are %d argument(s)' % func.func_code.co_argcount)

            # TODO replace with the right folder
            current_folder_schema = FolderSchema.objects.filter(imap_account=imap_account, name="INBOX")[0]
            action = Action(trigger="interval", code=codeobject_dumps(func.func_code), folder=current_folder_schema)
            action.save()
            add_periodic_task.delay( interval=interval, imap_account_id=imap_account.id, action_id=action.id, search_criteria=search_creteria, folder_name=current_folder_schema.name)

        def set_timeout(delay=None, func=None):
            if not delay:
                raise Exception('set_timeout(): requires delay (in second)')

            if delay < 1:
                raise Exception('set_timeout(): requires delay larger than 1 sec')

            if not func:
                raise Exception('set_timeout(): requires code to be executed periodically')

            args = ujson.dumps( [imap_account.id, marshal.dumps(func.func_code), search_creteria, is_test, email_content] )
            add_periodic_task.delay( delay, args, delay * 2 - 0.5 ) # make it expire right before 2nd execution happens 

        def send(subject="", to_addr="", body=""):
            if len(to_addr) == 0:
                raise Exception('send(): recipient email address is not provided')

            if not is_test:
                send_email(subject, imap_account.email, to_addr, body)
            logger.debug("send(): sent a message to  %s" % str(to_addr))

        def add_gmail_labels(flags):
            pile.add_gmail_labels(flags, is_test)

        def add_labels(flags):
            add_notes(flags)

        def add_notes(flags):
            pile.add_notes(flags, is_test)

        def copy(dst_folder):
            pile.copy(dst_folder, is_test)

        def delete():
            pile.delete(is_test)

        def get_history(email, hours=24, cond=True):
            if len(email) == 0:
                raise Exception('get_history(): email address is not provided')

            if hours <= 0:
                raise Exception('get_history(): hours must be bigger than 0')

            # get uid of emails within interval
            now = datetime.now()
            start_time = now - timedelta(hours = hours)
            heuristic_id = imap_account.newest_msg_id -100 if imap_account.newest_msg_id -100 > 1 else 1
            name, sender_addr = parseaddr(get_sender().lower())
            today_email_ids = imap.search( 'FROM %s SINCE "%d-%s-%d"' % (sender_addr, start_time.day, calendar.month_abbr[start_time.month], start_time.year) )

            # today_email = Pile(imap, 'UID %d:* SINCE "%d-%s-%d"' % (heuristic_id, start_time.day, calendar.month_abbr[start_time.month], start_time.year))
            # min_msgid = 99999
            # logging.debug("before get dates")

            received_cnt = 0
            sent_cnt = 0
            cond_cnt = 0
            for msgid in reversed(today_email_ids):
                p = Pile(imap, 'UID %d' % (msgid))

                t = p.get_date()
                date_tuple = utils.parsedate_tz(t)
                if date_tuple:
                    local_date = datetime.fromtimestamp(
                        utils.mktime_tz(date_tuple))

                    if start_time > local_date:
                        break

                    rs = p.get_recipients()
                    ss = p.get_senders()

                    with_email = False

                    # check if how many msg sent to this email
                    for j in range(len(rs)):
                        if email in rs[j] and imap_account.email in ss[0]:
                            sent_cnt = sent_cnt + 1
                            with_email = True
                            break

                    for j in range(len(ss)):
                        if email in ss[j]:
                            received_cnt = received_cnt + 1
                            with_email = True
                            break

                    if with_email:
                        if cond is True:
                            cond_cnt = cond_cnt + 1
                        else:
                            if cond(p):
                                cond_cnt = cond_cnt + 1

            # for msg in today_email.get_dates():
            #     msgid, t = msg
            #     date_tuple = utils.parsedate_tz(t)
            #     if date_tuple:
            #         local_date = datetime.fromtimestamp(
            #             utils.mktime_tz(date_tuple))

            #         if start_time < local_date:
            #             emails.append( msgid )


            # for i in range(len(emails)):
            #     p = Pile(imap, "UID %d" % (emails[i]))

            #     rs = p.get_recipients()
            #     ss = p.get_senders()

            #     with_email = False

            #     # check if how many msg sent to this email
            #     for j in range(len(rs)):
            #         if email in rs[j] and imap_account.email in ss[0]:
            #             sent_cnt = sent_cnt + 1
            #             with_email = True
            #             break

            #     for j in range(len(ss)):
            #         if email in ss[j]:
            #             received_cnt = received_cnt + 1
            #             with_email = True
            #             break

            #     if with_email:
            #         if cond == True:
            #             cond_cnt = cond_cnt + 1
            #         else:
            #             if cond(p):
            #                 cond_cnt = cond_cnt + 1

            r = {'received_emails': received_cnt, 'cond': cond_cnt}

            return r

        def get_sender():
            return pile.get_sender()

        def get_content():
            logger.debug("call get_content")
            if email_content:
                return email_content
            else:
                return pile.get_content()

        def get_date():
            return pile.get_date()

        def get_attachment():
            pass

        def get_subject():
            return pile.get_subject()

        def get_recipients():
            return pile.get_recipients()


        def get_attachments():
            pass

        def get_labels():
            return get_notes()

        def get_notes():
            return pile.get_notes()

        def get_gmail_labels():
            return pile.get_gmail_labels()

        def mark_read(is_seen=True):
            pile.mark_read(is_seen, is_test)


        def move(dst_folder):
            pile.move(dst_folder, is_test)

        def remove_labels(flags):
            remove_notes(flags)

        def remove_notes(flags):
            pile.remove_notes(flags, is_test)

        def remove_gmail_labels(flags):
            pile.remove_gmail_labels(flags, is_test)

        # return a list of email UIDs
        def search(criteria=u'ALL', charset=None, folder=None):
            # TODO how to deal with folders
            # iterate through all the functions
            if folder is None:
                pass

            # iterate through a folder of list of folder
            else:
                # if it's a list iterate
                pass
                # else it's a string search a folder

            select_folder('INBOX')
            return imap.search(criteria, charset)

        def get_body_test(m):
            # raw=email.message_from_bytes(data[0][1])
            response = imap.fetch(m, ['BODY[TEXT]'])
            bodys = []
            for msgid, data in response.items():
                body = message_from_string(data[b'BODY[TEXT]'].decode('utf-8'))
                bodys.append( get_body(body) )
                # print (body)

            # email_message = email.message_from_string(str(message))
            # msg_text = get_body(email_message)

            return bodys

        def create_folder(folder):
            pile.create_folder(folder, is_test)

        def delete_folder(folder):
            pile.delete_folder(folder, is_test)

        def list_folders(directory=u'', pattern=u'*'):
            return pile.list_folders(directory, pattern)

        def select_folder(folder):
            if not imap.folder_exists(folder):
                logger.error("Select folder; folder %s not exist" % folder)
                return

            imap.select_folder(folder)
            logger.debug("Select a folder %s" % folder)

        def rename_folder(old_name, new_name):
            pile.rename_folder(old_name, new_name, is_test)


        def get_mode():
            if imap_account.current_mode:
                return imap_account.current_mode.uid
            else:
                return None

        def set_mode(mode_index):
            try:
                mode_index = int(mode_index)
            except ValueError:
                raise Exception('set_mode(): args mode_index must be a index (integer)')


            mm = MailbotMode.objects.filter(uid=mode_index, imap_account=imap_account)
            if mm.exists():
                mm = mm[0]
                if not is_test:
                    imap_account.current_mode = mm
                    imap_account.save()

                logger.debug("Set mail mode to %s (%d)" % (mm.name, mode_index))
                return True
            else:
                logger.error("A mode ID %d not exist!" % (mode_index))
                return False

        try:
            if is_valid:
                exec code in globals(), locals()
                pile.add_flags(['YouPS'])
                res['status'] = True
        except Action.DoesNotExist:
            logger.debug("An action is not existed right now. Maybe you change your script after this action was added to the queue.")
        except Exception as e:
            catch_exception(e)

        res['imap_log'] = s.getvalue() + res['imap_log']

        return res




