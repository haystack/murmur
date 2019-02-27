from __future__ import unicode_literals, print_function, division
from imapclient import IMAPClient  # noqa: F401 ignore unused we use it for typing
from event import Event
import logging 
import typing as t


logger = logging.getLogger('youps')  # type: logging.Logger

class MailBox:
    def __init__(self, imap):
        # type: (IMAPClient) -> MailBox 
        """Create a new instance of the client's mailbox using a connection
        to an IMAPClient.
        """
        self.imap = imap  # type: IMAPClient    

        # Events
        self.newMessage = Event()  # type: Event

        self._sync_with_imap()

    def _sync_with_imap(self):
        """Helper method to synchronize with the imap server.
        """
        # should do a couple things based on
        # https://stackoverflow.com/questions/9956324/imap-synchronization
        # and https://tools.ietf.org/html/rfc4549

        for folder_name in self._list_folders():
            response = self.imap.select_folder(folder_name)
            logger.debug("select_folder response: %s" % response)


        
        # loop over all the folders
            # get the last_uid in the folder
            # issue the search command of the form "SEARCH UID 42:*"
            # command = "UID {}:*".format(last_uid)  # type: str
            # self.imap.search()

    def _list_folders(self):
        # type: () -> t.Generator[t.Text]
        """List all the folders in the Mailbox
        """

        # TODO we want to avoid listing all the folders 
        # https://www.imapwiki.org/ClientImplementation/MailboxList
        # we basically only want to list folders when we have to
        for (flags, delimiter, name) in self.imap.list_folders("", "*"):
            logger.debug("folder: %s, flags: %s, delimiter: %s" % (name, flags, delimiter))
            yield name
    
    def _check_for_new_emails(self):
        found_new_emails = False
        if found_new_emails:
            self.newMessage()

    

