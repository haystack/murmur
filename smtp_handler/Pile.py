from email.parser import HeaderParser
import heapq
import email
from smtp_handler.utils import logging

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
        """create a new pile

        Args:
            imap (imapclient.IMAPClient): connection to an imap server
            search_criteria (Union[str, List[str]]): string or list of strings
                of search criteria to search the imap server
        """

        self.imap = imap
        self.search_criteria = search_criteria
        # print ("info", self.search_criteria)
        self.is_valid = True
        self.EMAIL = []
        self.EMAIL = self.init_email()

    def init_email(self):
        """Get all emails passing the search criteria and return them

        Returns:
            List[Tuple[int, message]]: List of email uids and messages
                which pass self.search_criteria
        """

        unreads = self.get_unread_emails()

        id_results = []
        messages = self.imap.search( self.search_criteria )
        response = self.imap.fetch(messages, ['RFC822'])

        parser = HeaderParser()

        if response is None:
            self.is_valid = False
            return []

        for msgid, data in response.items():
            if b'RFC822' not in data:
                continue
            new_text = ''
            if isinstance(data[b'RFC822'], unicode):
                logging.debug("it's unicode, no need to change")
                new_text = data[b'RFC822']

            else:
                logging.debug("not unicode, convert using utf-8")
                new_text = unicode(data[b'RFC822'], "utf-8", "ignore")

            raw_string = new_text.decode("utf-8").encode("ascii", "ignore")
            msg = parser.parsestr( raw_string )
            id_results.append( (msgid, msg) )

        if len(unreads) > 0:
            self.mark_read_meta(False)


        return id_results

    def check_email(self):
        return self.is_valid

    #################################
    ### Getter functions
    def get_content(self):
        contents = self.get_contents()
        if len(contents) > 0:
            return contents[0]
        else:
            return ""

    def get_date(self):
        dates = self.get_dates()
        if len(dates) > 0:
            return dates[0]
        else:
            return ""


    def get_notes_meta(self):
        """Get flags for all emails which pass the search critera

        Returns:
            Dict[str, Tuple[str]]: Dictionary of msgid: (flag1, flag2, flag3)
        """

        return self.imap.get_flags(self.get_IDs())

    def get_notes(self):
        flags = []
        for msgid, data in self.get_notes_meta().items():
            # print('   ID %d: flags=%s ' % (msgid,
            #                                 data))
            for f in data:
                if "YouPS" == f:
                    continue
                flags.append( f )

        return flags

    def get_labels(self):
        return self.get_notes()

    def get_gmail_labels(self):
        flags = []
        for msgid, data in self.imap.get_gmail_labels( self.get_IDs() ).items():
            # print('   ID %d: flags=%s ' % (msgid,
            #                                 data))
            for f in data:
                if "YouPS" == f:
                    continue
                flags.append( f )

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

    def add_gmail_labels_meta(self, flags):
        self.imap.add_gmail_labels(self.get_IDs(), flags)

    def add_gmail_labels(self, flags, is_test=False):
        if not is_test:
            self.add_gmail_labels_meta(flags)

        print format_log("add_gmail_labels(): add gmail labels to a message %s" % str(flags), False, self.get_subject())

    def add_flags(self, flags):
        self.imap.add_flags(self.get_IDs(), flags)

    def add_labels(self, flags, is_test=False):
        self.add_notes(flags, is_test)

    def add_notes(self, flags, is_test=False):
        if type(flags) is not list:
            raise Exception('add_notes(): args flags must be a list of strings')

        for f in flags:
            if not isinstance(f, str):
                raise Exception('add_notes(): args flags must be a list of strings')

        for f in range(len(flags)):
            flags[f] = flags[f].strip()

        if not is_test:
            self.add_flags(flags)

        print ("Successfuly add notes: " + str(flags))


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


    def has_label(self, label):
        for msgid, data in self.get_notes_meta().items():
            for f in data:
                if f == label:
                    return True

        return False

    def mark_read_meta(self, inIsSeen=True):
        # if true, add SEEN flags
        if inIsSeen:
            self.imap.set_flags(self.get_IDs(), '\\Seen')
        else:
            self.imap.remove_flags(self.get_IDs(), '\\Seen')

    def mark_read(self, is_seen=True, is_test=False):
        if not is_test:
            self.mark_read_meta(is_seen)

        print format_log("Mark Message a message %s" % ("read" if is_seen else "unread"), False, self.get_subject())


    def move_meta(self, dst_folder):
        self.imap.move(self.get_IDs(), dst_folder)

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

    def remove_labels(self, flags, is_test=False):
        self.remove_notes(flags, is_test)

    def remove_notes(self, flags, is_test=False):
        if type(flags) is not list:
            raise Exception('remove_labels(): args flags must be a list of strings')

        for f in flags:
            if not isinstance(f, str):
                raise Exception('remove_labels(): args flags must be a list of strings')

        if not is_test:
            self.remove_notes_meta(flags)

        print format_log("Remove labels %s of a message" % (flags), False, self.get_subject())


    def remove_gmail_labels(self, flags, is_test=False):
        if type(flags) is not list:
            raise Exception('remove_gmail_labels(): args flags must be a list of strings')

        for f in flags:
            if not isinstance(f, str):
                raise Exception('remove_gmail_labels(): args flags must be a list of strings')

        if not is_test:
            self.imap.remove_gmail_labels(self.get_IDs(), flags)

        print format_log("Remove labels %s of a message" % (flags), False, self.get_subject())

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
        self.imap.delete_folder(folder)

    def delete_folder(self, folder, is_test=False):
        if len(folder) == 0:
            raise Exception('delete_folder(): args folder_name must be but non-empty string but a given value is ' + folder)

        if not self.imap.folder_exists(folder):
            print format_log("delete_folder(): folder %s not exist" % folder, True, self.get_subject())
            return

        if not is_test:
            self.delete_folder_meta(folder)

        print format_log("delete_folder(): Delete a folder %s" % folder, False, self.get_subject())


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




    def get_N_latest_emails(self, N):
        msgids = self.get_IDs()

        return heapq.nlargest(N, msgids)

    def get_subjects(self):
        return self.get_email('Subject')

    def get_senders(self):
        return self.get_email('From')

    def get_dates(self):
        return self.get_email('Date')



    def get_first_text_block(self, email_message_instance):
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
        response = self.imap.fetch(messages, ['RFC822'])
        bodys = []
        for msgid, data in response.iteritems():
            if b'RFC822' not in data:
                continue

            # print "PARSING CONTENTS"

            email_message = email.message_from_string(data[b'RFC822'])

            # keys ['Delivered-To', 'Received', 'X-Received', 'ARC-Seal',
            # 'ARC-Message-Signature', 'ARC-Authentication-Results',
            # 'Return-Path', 'Received', 'Received-SPF',
            # 'Authentication-Results', 'DKIM-Signature',
            # 'X-Google-DKIM-Signature', 'X-Gm-Message-State',
            # 'X-Google-Smtp-Source', 'X-Received', 'MIME-Version', 'From',
            # 'Date', 'Message-ID', 'Subject', 'To', 'Content-Type']

            # print 'id', msgid
            # print 'keys', str(email_message.keys())
            # print 'from', email_message.get('From')
            # print 'to', email_message.get('To')
            # print 'subject', email_message.get('Subject')
            # print 'date', email_message.get('Date')

            text = ""
            html = ""
            for part in email_message.walk():
                if part.is_multipart():
                    continue
                else:
                    decoded = part.get_payload(decode=True)
                    charset = part.get_content_charset()
                    if charset is not None:
                        decoded = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

                    content_type = part.get_content_type()
                    if content_type == 'text/plain':
                        text += decoded
                    elif content_type == 'text/html':
                        html += decoded
                    else:
                        # TODO should be a log but idk where logs go... LSM
                        print 'unknown content type', content_type

            bodys.append(text if text != "" else html)

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
        """Return uids of messages which pass the search critera and are not flagged as seen.

        Returns:
            List[int]: unique ids of messages which pass the search critera and are not flagged as seen.
        """

        flags = self.get_notes_meta()

        if flags is None:
            return []

        unread_emails = []

        for msgid, data in flags.items():
            if b'\\Seen' not in data:
                unread_emails.append(msgid)

        return unread_emails

class Folder_wrapper():
    def __init__(self, imap, search_criteria):
        """create a new pile

        Args:
            imap (imapclient.IMAPClient): connection to an imap server
            search_criteria (Union[str, List[str]]): string or list of strings
                of search criteria to search the imap server
        """

        pass