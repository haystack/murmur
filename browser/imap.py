import sys
import traceback
try:
    from StringIO import StringIO
except ImportError:
    import io
import contextlib
from smtp_handler.utils import *
from smtp_handler.Pile import *
from email import message_from_string,message
from http_handler.settings import BASE_URL, DEFAULT_FROM_EMAIL, WEBSITE, IMAP_SECRET
from engine.google_auth import *
from Crypto.Cipher import AES

def authenticate(imap_account):
    res = {'status' : False, 'imap_error': False}

    try:  
        imap = IMAPClient(imap_account.host, use_uid=True)
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
                res['status'] = True
            else:
                res['code'] = "Can't authenticate your email"
        except IMAPClient.Error, e:  
            res['code'] = "Can't authenticate your email"

            # Delete this ImapAccount information so that it requires user to reauthenticate
            imap_account.delete()

            # TODO email to the user that there is error at authenticating email
        except Exception, e:
            # TODO add exception
            print e
            res['code'] = msg_code['UNKNOWN_ERROR']

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

def interpret(imap, code, search_creteria, is_test=False):
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

        def get_sender():
            return pile.get_senders()[0]

        def get_content():
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

        def mark_read(is_seen):
            if not is_test: 
                pile.mark_read(is_seen, messages)
                
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

        def get_body_test(messages):
            # raw=email.message_from_bytes(data[0][1])
            response = imap.fetch(messages, ['BODY[TEXT]'])
            bodys = []
            for msgid, data in response.items():
                body = email.message_from_string(data[b'BODY[TEXT]'].decode('utf-8'))
                bodys.append( get_body(body) )
                # print (body)

            # self.mark_read(False, unreads)
            
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

        # print "code"
        # print code
        try:
            exec code in globals(), locals()
        except Exception as e:
            catch_exception(e)

        if not res['imap_error']:
            res['imap_log'] = s.getvalue()

        return res

    
        

        