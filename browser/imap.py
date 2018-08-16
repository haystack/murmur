import sys
import traceback
try:
    from StringIO import StringIO
except ImportError:
    import io
import contextlib
from smtp_handler.utils import *
from email import message_from_string

def interpret(imap, code):
    res = {'status' : False, 'imap_error': False}

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

        # return a list of email UIDs
        def search(criteria=u'ALL', charset=None):
            return self.imap.search(criteria, charset)

        def get_body_test(messages):
            # raw=email.message_from_bytes(data[0][1])
            response = self.imap.fetch(messages, ['BODY[TEXT]'])
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

    
        

        