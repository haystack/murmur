import sys
import traceback
try:
    from StringIO import StringIO
except ImportError:
    import io
import contextlib
from smtp_handler.utils import *
from smtp_handler.Pile import *
from email import message_from_string

def fetch_latest_email_id(imap_account, imap_client):
    imap_client.select_folder("INBOX")
    uid_list = []

    if imap_account.newest_msg_id == -1:
        uid_list = imap_client.search("UID 99999:*")

    else:
        uid_list = imap_client.search("UID %d:*" % imap_account.newest_msg_id)

    return max(uid_list)

def interpret(imap, code, search_creteria):
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

        def print_test():   
            print "print test"

        def copy(src_folder, dst_folder):
            select_folder(src_folder)
            return imap.copy(messages, dst_folder)

        def move(src_folder, dst_folder):
            select_folder(src_folder)

            copy(src_folder, dst_folder)
            delete()

        def delete():
            imap.delete_messages(messages)

        def mark_read(is_seen):
            pile.mark_read(is_seen, messages)

        def get_sender():
            return pile.get_senders()[0]

        def get_recipient():
            return pile.get_recipients()[0]

        def get_content():
            return pile.get_contents()[0]

        def get_date():
            return pile.get_dates()[0]

        def get_attachment():    
            pass

        def get_subject():
            return pile.get_subjects()[0]

        def get_flag():        
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

        def get_flags():        
            return pile.get_flags()

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
            imap.create_folder(folder)
            print "Create folder name " + folder 

        def list_folders(directory=u'', pattern=u'*'):
            return imap.list_folders(directory, pattern)

        def select_folder(folder):
            imap.select_folder(folder)
            print "Select a folder " + folder 

        def rename_folder(old_name, new_name):
            imap.rename_folder(old_name, new_name)
            print "Rename " + old_name + " to " + new_name

        # print "code"
        # print code
        try:
            exec code in globals(), locals()
        except Exception as e:
            catch_exception(e)

        if not res['imap_error']:
            res['imap_log'] = s.getvalue()

        return res

    
        

        