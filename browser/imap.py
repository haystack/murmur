import sys
import traceback

def interpret(imap, code):
    res = {'status' : False}

    def catch_exception(e):   
        etype, evalue = sys.exc_info()[:2]
        estr = traceback.format_exception_only(etype, evalue)
        logstr = 'Error during executing your code'
        for each in estr:
            logstr += '{0}; '.format(each.strip('\n'))

        logstr = "Execution error %s \n %s" % (str(e), logstr)
        # writeLog( "critical", logstr )

        # Send this error msg to the user
        res['code'] = logstr

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

    return res
    #with User(inbox[uid]["monitor"]) as u:

    
        

        