from email.parser import HeaderParser
import heapq
import email
from smtp_handler.utils import *

def get_text(msg):
    if msg.is_multipart():
        return get_text(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)

class Pile():
    def __init__(self, imap, search_criteria):
        self.imap = imap
        self.search_criteria = search_criteria
        # print ("info", self.search_criteria)

    def add_flags(self, flags):
        if type(flags) is not list:
            raise Exception('add_flags(): args flags must be a list of strings')

        for f in flags:
            if not isinstance(f, str):
                raise Exception('add_flags(): args flags must be a list of strings')

        self.imap.add_flags(self.get_IDs(), flags) 
        print ("Successfuly add flags: " + str(flags))

    def setSearch_criteria(self, search_criteria):
        self.search_criteria = search_criteria

    def get_IDs(self):
        return self.imap.search( self.search_criteria )

    def get_count(self):
        messages = self.imap.search( self.search_criteria )
        print ("info", "Mmail getCount(): " + self.search_criteria + str(len(messages)))
        # print (messages)
        return len(messages)

    def get_date(self):
        return self.get_dates()

    def get_note(self):
        return get_flags()

    def get_subject(self):
        return self.get_subjects()

    def get_sender(self):
        return self.get_senders()

    def get_recipient(self):
        return self.get_recipients()

    def get_content(self):
        return self.get_contents()

    def remove_note(self, flags):
        return self.remove_flags(self.get_IDs(), flags)

    def get_dates(self):
        return self.get_email('Date', True)

    def get_flags(self):
        messages = self.imap.search( self.search_criteria )

        flags = {}
        for msgid, data in self.imap.get_flags(messages).items():
            # print('   ID %d: flags=%s ' % (msgid,
            #                                 data))
                  
            flags[msgid] = data

        return flags

    def get_N_latest_emails(self, N): 
        msgids = self.get_IDs()

        return heapq.nlargest(N, msgids)

    def get_subjects(self):
        return self.get_email('Subject')

    def get_senders(self):
        return self.get_email('From')

    def get_recipients(self):
        return self.get_email('To')

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
            body = email.message_from_string(data[b'RFC822'].decode('utf-8'))
            bodys.append( self.get_first_text_block(body) )
            # print (body)

        # self.mark_read(False, unreads)

        return bodys

    def get_email(self, header, inCludeID=False):
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
            # print (data[b'BODY[HEADER]'])
            msg = parser.parsestr(data[b'RFC822'].decode("utf-8"))
            results.append( msg[header] )
            id_results.append( (msgid, msg[header]) )

        # self.mark_read(False, unreads)
        if not inCludeID:
            return results

        return id_results

    def get_unread_emails(self):
        messages = self.imap.search( self.search_criteria )

        flags = self.get_flags()

        if flags is None:
            return []

        read_emails = []

        for msgid, data in flags.items(): 
            if b'\\Seen' not in data:
                read_emails.append(msgid)

        return read_emails

    def mark_read(self, inIsSeen):
        # if true, add SEEN flags
        if inIsSeen: 
            self.imap.set_flags(self.get_IDs(), '\\Seen')            
        else: 
            self.imap.remove_flags(self.get_IDs(), '\\Seen')     
    

    def remove_flags(self, flags):
        self.imap.remove_flags(self.get_IDs(), flags)