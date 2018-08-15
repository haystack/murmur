

def interpret(imap, code):
    def print_test():
        print "print test"

    def select_folder(inFolder):
        imap.select_folder(inFolder)

    print "code"
    print code
    d = dict(locals(), **globals())
    exec( code, d, d )
    #with User(inbox[uid]["monitor"]) as u:

    
        

        