import sys
import traceback
try:
    from StringIO import StringIO
except ImportError:
    import io
import contextlib
from smtp_handler.utils import *
from smtp_handler.Pile import *
from email import message_from_string,message, utils
from imapclient import IMAPClient
from http_handler.settings import BASE_URL, DEFAULT_FROM_EMAIL, WEBSITE, IMAP_SECRET
from engine.google_auth import *
from Crypto.Cipher import AES
from engine.constants import *
from datetime import datetime, time, timedelta
import calendar

def authenticate(imap_account):
    res = {'status' : False, 'imap_error': False}
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
            print "try to renew token"
            if imap_account.is_oauth:
                oauth = GoogleOauth2()
                response = oauth.RefreshToken(imap_account.refresh_token)
                imap.oauth2_login(imap_account.email, response['access_token'])

                imap_account.access_token = response['access_token']
                imap_account.save()

                auth_res['imap'] = imap
                res['status'] = True
            else:
                res['code'] = "Can't authenticate your email"
        except IMAPClient.Error, e:  
            res['imap_error'] = e
            res['code'] = "Can't authenticate your email"

        except Exception, e:
            # TODO add exception
            res['imap_error'] = e
            print e
            res['code'] = msg_code['UNKNOWN_ERROR']

    if res['status'] == False:
        # email to the user that there is error at authenticating email
        if len(email_addr) > 0:
            subject = "[" + WEBSITE + "] Authentication error occurs"
            body = "Authentication error occurs! \n" + res['imap_error']
            body += "\nPlease log in again at " + BASE_URL + "/editor"
            send_email(subject, WEBSITE + "@" + BASE_URL, email_addr, body)

        # TODO don't delete
        # Delete this ImapAccount information so that it requires user to reauthenticate
        imap_account.password = ""
        imap_account.save()

    return res

def append(imap, subject, content):
    new_message = message.Message()
    new_message["From"] = "mailbot-log@murmur.csail.mit.edu"
    new_message["Subject"] = subject
    new_message.set_payload(content)
    
    imap.append('INBOX', str(new_message), ('murmur-log'))

def fetch_latest_email_id(imap_account, imap_client):
    imap_client.select_folder("INBOX")
    uid_list = []

    if imap_account.newest_msg_id == -1:
        uid_list = imap_client.search("UID 99999:*")

    else:
        uid_list = imap_client.search("UID %d:*" % imap_account.newest_msg_id)

    return max(uid_list)

def format_log(msg, is_error=False):
    if is_error:
        return "[Error] " + msg
    else:
        return "[Info] " + msg

def wrapper(imap_account, imap, code, search_creteria, is_test=False, email_content=None):
    interpret(imap_account, imap, code, search_creteria, is_test, email_content)

def interpret(imap_account, imap, code, search_creteria, is_test=False, email_content=None):
    res = {'status' : False, 'imap_error': False}
    pile = Pile(imap, search_creteria)
    messages = imap.search( search_creteria )

    @contextlib.contextmanager
    def stdoutIO(stdout=None):
        old = sys.stdout
        if stdout is None:
            stdout = StringIO()
        sys.stdout = stdout
        yield stdout
        sys.stdout = old

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

        def add_notes(flags): 
            if not is_test: 
                pile.add_flags(flags)

            print format_log("Add %s to Message %s" % (flags, search_creteria), False) 
            
        def copy(src_folder, dst_folder):
            if not imap.folder_exists(src_folder):
                format_log("Copy Message; source folder %s not exist" % src_folder, True)  
                return

            if not is_test: 
                select_folder(src_folder)
                imap.copy(messages, dst_folder)

            print format_log("Copy Message %s from folder %s to %s" % (search_creteria, src_folder, dst_folder), False)  

        def delete():
            if not is_test: 
                imap.delete_messages(messages)

            print format_log("Delete Message %s" % (search_creteria), False)  

        def get_history(email, hours=24, cond=True):
            if len(email) == 0:
                raise Exception('get_history(): email address is not provided') 
            
            if hours <= 0:
                raise Exception('get_history(): hours must be bigger than 0') 

            # get uid of emails within interval
            now = datetime.now()
            start_time = now - timedelta(hours = hours) 
            today_email = Pile(imap, 'SINCE "%d-%s-%d"' % (start_time.day, calendar.month_abbr[start_time.month], start_time.year))
            min_msgid = 99999
            logging.debug("before get dates")
            emails = []
            for msg in today_email.get_dates():
                msgid, t = msg
                date_tuple = utils.parsedate_tz(t)
                if date_tuple:
                    local_date = datetime.fromtimestamp(
                        utils.mktime_tz(date_tuple))

                    if start_time < local_date:
                        emails.append( msgid )

            received_cnt = 0
            sent_cnt = 0
            cond_cnt = 0
            for i in range(len(emails)):
                p = Pile(imap, "UID %d" % (emails[i]))

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
                    if cond == True:
                        cond_cnt = cond_cnt + 1
                    else:
                        if cond(p):
                            cond_cnt = cond_cnt + 1

            r = {'received_emails': received_cnt, 'sent_emails': sent_cnt, 'cond': cond_cnt}

            return r

        def get_sender():
            return pile.get_senders()[0]

        def get_content():
            if email_content:
                return email_content
            else:
                return pile.get_contents()[0]

        def get_date():
            return pile.get_dates()[0][1]

        def get_attachment():    
            pass

        def get_subject():
            return pile.get_subjects()[0]

        def get_note():        
            return pile.get_flags()[0]


        def get_senders():
            return pile.get_senders()

        def get_recipients():
            return pile.get_recipients()

        def get_contents():
            return pile.get_contents()

        def get_dates():
            return pile.get_dates()

        def get_attachments():    
            pass

        def get_subjects():
            return pile.get_subjects()

        def get_notes():        
            return pile.get_flags()

        def mark_read(is_seen=True):
            if not is_test: 
                pile.mark_read(is_seen)
                
            print format_log("Mark Message %s %s" % (search_creteria, "read" if is_seen else "unread"), False)  

        def move(src_folder, dst_folder):
            if not imap.folder_exists(src_folder):
                format_log("Move Message; source folder %s not exist" % src_folder, True)  
                return

            if not is_test: 
                select_folder(src_folder)
                copy(src_folder, dst_folder)
                delete()
            
            print format_log("Move Message from %s to %s" % (search_creteria, src_folder, dst_folder), False)  

        def remove_notes(flags): 
            if not is_test: 
                pile.remove_flags(flags)

            print format_log("Remove flags %s of Message %s" % (flags, search_creteria), False)  

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
                body = email.message_from_string(data[b'BODY[TEXT]'].decode('utf-8'))
                bodys.append( get_body(body) )
                # print (body)
            
            # email_message = email.message_from_string(str(message))
            # msg_text = get_body(email_message)

            return bodys

        def create_folder(folder):
            if imap.folder_exists(folder):
                format_log("Create folder; folder %s already exist" % folder, True)  
                return
            
            if not is_test: 
                imap.create_folder(folder)

            print format_log("Create a folder %s" % folder, False)  

        def list_folders(directory=u'', pattern=u'*'):
            return imap.list_folders(directory, pattern)

        def select_folder(folder):
            if not imap.folder_exists(folder):
                format_log("Select folder; folder %s not exist" % folder, True)  
                return

            imap.select_folder(folder)
            print "Select a folder " + folder 

        def rename_folder(old_name, new_name):
            if imap.folder_exists(new_name):
                format_log("Rename folder; folder %s already exist. Try other name" % new_name, True)  
                return

            if not is_test: 
                imap.rename_folder(old_name, new_name)
        
            print format_log("Rename a folder %s to %s" % (old_name, new_name), False)

        def get_mode():
            if imap_account.current_mode:
                return imap_account.current_mode.uid

            else:
                return None

        def set_mode(mode_index):
            mm = MailbotMode.objects.filter(uid=mode_index, imap_account=imap_account)
            if mm.exists():
                mm = mm[0]
                if not is_test: 
                    imap_account.current_mode = mm

                print format_log("Set your mail mode to %s (%d)" % (mm.name, mode_index), False)  
                return True
            else:
                print format_log("A mode ID %d not exist!" % (mode_index), True)  
                return False

        try:
            exec code in globals(), locals()
        except Exception as e:
            catch_exception(e)

        if not res['imap_error']:
            res['imap_log'] = s.getvalue()

        return res

    
        

        