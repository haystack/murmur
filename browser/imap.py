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
            logstr = 'Error during executing your code'
            for each in estr:
                logstr += '{0}; '.format(each.strip('\n'))

            logstr = "%s \n %s" % (logstr, str(e))

            # Send this error msg to the user
            res['code'] = logstr
            res['imap_error'] = True

        def print_test():   
            print "print test"

        def create_folder(inFolderName):
            imap.create_folder(inFolderName)

        def select_folder(inFolderName):
            imap.select_folder(inFolderName)

        print "code"
        print code
        d = dict(locals(), **globals())
        # exec( code, d, d )
        try:
            exec code in globals(), locals()
        except Exception as e:
            catch_exception(e)

        if not res['imap_error']:
            res['code'] = s.getvalue()

        return res

    
        

        