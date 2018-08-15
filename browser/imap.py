import sys
import traceback
try:
    from StringIO import StringIO
except ImportError:
    import io
import contextlib

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

    
        

        