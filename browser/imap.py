

def interpret(imap, code):
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
    exec code in globals(), locals()
    #with User(inbox[uid]["monitor"]) as u:

    
        

        