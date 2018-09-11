from email.parser import HeaderParser
import heapq
import email
from smtp_handler.utils import *

def get_text(msg):
    if msg.is_multipart():
        return get_text(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)

def format_log(msg, is_error=False, subject = ""):

    s = "Subject: " + subject + " | "
    if is_error:
        return "[Error] " + s + msg
    else:
        return "[Info] " + s + msg

class Pile():
    def __init__(self, imap, search_criteria):
        self.imap = imap
        self.search_criteria = search_criteria
        # print ("info", self.search_criteria)
        self.EMAIL = self.init_email()

    def init_email(self):
        unreads = self.get_unread_emails()

        results = []
        id_results = []
        messages = self.imap.search( self.search_criteria )
        # raw=email.message_from_bytes(data[0][1])
        response = self.imap.fetch(messages, ['RFC822'])
        parser = HeaderParser()

        if response is None:
            return []

        for msgid, data in response.items():
            if b'RFC822' not in data:
                continue
            # print (data[b'BODY[HEADER]'])
            raw_string = data[b'RFC822'].decode("utf-8").encode("ascii", "ignore")
            msg = parser.parsestr( raw_string )
            results.append( msg )
            id_results.append( (msgid, msg) )

        if len(unreads) > 0:
            self.mark_read(False)

        # if not inCludeID:
        #     return results

        return id_results

    #################################
    ### Getter functions
    def get_content(self):
        contents = self.get_contents()
        if len(contents) > 0:
            return self.get_contents()[0]
        else:
            return ""

    def get_date(self):
        return self.get_dates()
        
    def get_notes(self):
        messages = self.imap.search( self.search_criteria )

        flags = {}
        for msgid, data in self.imap.get_flags(messages).items():
            # print('   ID %d: flags=%s ' % (msgid,
            #                                 data))
                  
            flags[msgid] = data

        return flags

    def get_sender(self):
        senders = self.get_senders() 
        if len(senders) > 0:
            return senders[0]
        else:
            return ""

    def get_subject(self):
        subjects = self.get_subjects() 
        if len(subjects) > 0:
            return subjects[0]
        else:
            return ""

    def get_recipients(self):
        return self.get_email('To')

    ### Getter functions
    #################################
    


    def add_flags(self, flags):
        self.imap.add_flags(self.get_IDs(), flags) 
        print ("Successfuly add flags: " + str(flags))

    def add_notes(self, flags, is_test=False):
        if type(flags) is not list:
            raise Exception('add_flags(): args flags must be a list of strings')

        for f in flags:
            if not isinstance(f, str):
                raise Exception('add_flags(): args flags must be a list of strings')
        
        if not is_test: 
            self.add_flags(flags)

        print ("Successfuly add flags: " + str(flags))


    def copy_meta(self, src_folder, dst_folder):
        self.imap.copy(self.get_IDs(), dst_folder)

    def copy(self, dst_folder, is_test=False):
        src_folder = "INBOX"
        if not self.imap.folder_exists(dst_folder):
            self.create_folder_meta(dst_folder)
            print format_log("copy(): destionation folder %s not exist. Just create a new folder %s " % (dst_folder, dst_folder), False, self.get_subject())

        if not is_test: 
            self.imap.select_folder(src_folder)
            self.copy_meta(self.get_IDs(), dst_folder)

        print format_log("copy(): a message from folder %s to %s" % (src_folder, dst_folder), False, self.get_subject())          


    def delete_meta(self):
         self.imap.add_flags(self.get_IDs(), ['\\Deleted'])

    def delete(self, is_test=False):
        if not is_test: 
            self.delete_meta()

        print format_log("delete(): delete a message \n**Warning: your following action might throw erros as you delete the message", False, self.get_subject())


    def mark_read_meta(self, inIsSeen=True):
        # if true, add SEEN flags
        if inIsSeen: 
            self.imap.set_flags(self.get_IDs(), '\\Seen')            
        else: 
            self.imap.remove_notes(self.get_IDs(), '\\Seen')    

    def mark_read(self, is_seen=True, is_test=False):
        if not is_test: 
            self.mark_read(is_seen)

        print format_log("Mark Message a message %s" % ("read" if is_seen else "unread"), False, self.get_subject())  


    def move_meta(self, dst_folder):
        self.copy_meta(dst_folder)
        self.delete_meta()

    def move(self, dst_folder, is_test=False):
        if len(dst_folder) == 0:
            raise Exception('move(): args dst_folder must be but non-empty string but a given value is ' + dst_folder)

        if not self.imap.folder_exists(dst_folder):
            self.create_folder_meta(dst_folder)
            print format_log("Move Message; destination folder %s not exist. Just create a new folder %s" % (dst_folder, dst_folder), False, self.get_subject())  

        src_folder = "INBOX"
        self.imap.select_folder(src_folder)
        if not is_test: 
            self.move_meta(dst_folder)
            
        print format_log("Move Message from %s to %s \n**Warning: your following action might throw erros as you move the message" % (src_folder, dst_folder), False, self.get_subject())          


    def remove_notes_meta(self, flags):
        self.imap.remove_flags(self.get_IDs(), flags)

    def remove_notes(self, flags, is_test=False):
        if type(flags) is not list:
            raise Exception('add_flags(): args flags must be a list of strings')

        for f in flags:
            if not isinstance(f, str):
                raise Exception('add_flags(): args flags must be a list of strings')

        if not is_test: 
            self.remove_notes_meta(self.get_IDs(), flags)

        print format_log("Remove flags %s of a message" % (flags), False, self.get_subject())  


    #################################
    ### Folder functions

    def create_folder_meta(self, folder):
        self.imap.create_folder(folder)

    def create_folder(self, folder, is_test=False):
        if len(folder) == 0:
            raise Exception('create_folder(): args folder_name must be but non-empty string but a given value is ' + folder)

        if self.imap.folder_exists(folder):
            print format_log("create_folder(): folder %s already exist" % folder, True, self.get_subject())  
            return
            
        if not is_test: 
            self.create_folder_meta(folder)

        print format_log("Create a folder %s" % folder, False, self.get_subject())  


    def delete_folder_meta(self, folder):
        self.imap.create_folder(folder)

    def delete_folder(self, folder, is_test=False):
        if len(folder) == 0:
            raise Exception('delete_folder(): args folder_name must be but non-empty string but a given value is ' + folder)

        if not self.imap.folder_exists(folder):
            print format_log("delete_folder(): folder %s not exist" % folder, True, self.get_subject())  
            return
            
        if not is_test: 
            self.create_folder_meta(folder)

        print format_log("Create a folder %s" % folder, False, self.get_subject())  

    
    def list_folders(self, directory=u'', pattern=u'*'):
        return self.imap.list_folders(directory, pattern)

    
    def rename_folder_meta(self, old_name, new_name):
        self.imap.rename_folder(old_name, new_name)

    def rename_folder(self, old_name, new_name, is_test=False):
        if len(old_name) == 0:
            raise Exception('rename_folder(): args folder_name must be but non-empty string but a given value is ' + old_name)

        if len(new_name) == 0:
            raise Exception('rename_folder(): args folder_name must be but non-empty string but a given value is ' + new_name)

        if self.imap.folder_exists(new_name):
            print format_log("rename_folder(); folder %s already exist. Try other name" % new_name, True, self.get_subject())  
            return

        if not is_test: 
            self.rename_folder_meta(old_name, new_name)
        
        print format_log("Rename a folder %s to %s" % (old_name, new_name), False, self.get_subject())


    ### Folder functions
    #################################
    


    def setSearch_criteria(self, search_criteria):
        self.search_criteria = search_criteria

    def get_IDs(self):
        return self.imap.search( self.search_criteria )

    def get_count(self):
        messages = self.imap.search( self.search_criteria )
        print ("info", "Mmail getCount(): " + self.search_criteria + str(len(messages)))
        # print (messages)
        return len(messages)

    

    

    

    

    

    

    def get_dates(self):
        header = 'Date'
        results = []
        for i in range(len(self.EMAIL)):
            msgid, msg = self.EMAIL[i]
            results.append( (msgid, msg[header]) )

        return results

        

    def get_N_latest_emails(self, N): 
        msgids = self.get_IDs()

        return heapq.nlargest(N, msgids)

    def get_subjects(self):
        return self.get_email('Subject')

    def get_senders(self):
        return self.get_email('From')

    

    def get_first_text_block(self,email_message_instance):
        maintype = email_message_instance.get_content_maintype()
        if maintype == 'multipart':
            for part in email_message_instance.get_payload():
                if part.get_content_maintype() == 'text':
                    return part.get_payload()
                return None
        elif maintype == 'text':
            return email_message_instance.get_payload()

    def get_contents(self):
        unreads = self.get_unread_emails()
        messages = self.imap.search( self.search_criteria )
        # raw=email.message_from_bytes(data[0][1])
        response = self.imap.fetch(messages, ['RFC822'])
        bodys = []
        for msgid, data in response.items():
            if b'RFC822' not in data:
                continue

            raw_string = data[b'RFC822'].decode("utf-8").encode("ascii", "ignore")

            body = email.message_from_string(raw_string)
            
            bodys.append( self.get_first_text_block(body) )
            # print (body)

        if len(unreads) > 0:
            self.mark_read(False)

        return bodys

    def get_email(self, header, inCludeID=False):
        results = []
        for i in range(len(self.EMAIL)):

            msgid, msg = self.EMAIL[i]
            results.append( msg[header] )

        return results
        

    def get_unread_emails(self):
        messages = self.imap.search( self.search_criteria )

        flags = self.get_notes()

        if flags is None:
            return []

        read_emails = []

        for msgid, data in flags.items(): 
            if b'\\Seen' not in data:
                read_emails.append(msgid)

        return read_emails



        print format_log("Mark Message %s %s" % (self.search_creteria, "read" if is_seen else "unread"), False, self.get_subject())   


    