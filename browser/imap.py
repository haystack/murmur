

def interpret(code):
    def print_test():
        print "print test"

    print "code"
    print code
    d = dict(locals(), **globals())
    exec( code, d, d )
    #with User(inbox[uid]["monitor"]) as u:
        

        