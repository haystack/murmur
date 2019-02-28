from __future__ import unicode_literals, print_function, division
from imapclient import IMAPClient  # noqa: F401 ignore unused we use it for typing
from event import Event
import logging 
import typing as t  # noqa: F401 ignore unused we use it for typing
from .folder import Folder
from schema.youps import ImapAccount, FolderSchema


logger = logging.getLogger('youps')  # type: logging.Logger

class MailBox:
    def __init__(self, imap_account, imap_client):
        # type: (ImapAccount, IMAPClient) -> MailBox 
        """Create a new instance of the client's mailbox using a connection
        to an IMAPClient.
        """
        self._imap_client = imap_client  # type: IMAPClient    

        self._imap_account = imap_account  # type: ImapAccount

        # Events
        self.newMessage = Event()  # type: Event


    def _sync(self):
        """Helper method to synchronize with the imap server.
        """
        # should do a couple things based on
        # https://stackoverflow.com/questions/9956324/imap-synchronization
        # and https://tools.ietf.org/html/rfc4549

        for folder_name in self._list_selectable_folders():
            response = self._imap_client.select_folder(folder_name)
            logger.info('select_folder response: %s' % response)

            # log information about flags returned
            if 'HIGHESTMODSEQ' in response:
                # https://wiki.mozilla.org/Thunderbird:IMAP_RFC_4551_Implementation
                logger.debug('server supports rfc 4551')
            if 'EXISTS' in response:
                logger.debug('folder %s contains %d messages' % (folder_name, response['EXISTS']))
            if 'RECENT' in response:
                logger.debug('folder %s contains %d recent messages' % (folder_name, response['RECENT']))
            if 'UIDNEXT' in response:
                logger.debug('folder %s next UID is %d' % (response['UIDNEXT']))
            else:
                logger.critical('folder %s did not return UIDNEXT' % folder_name)
            if 'UIDVALIDITY' in response:
                logger.debug('folder %s UIDVALIDITY %d' % (response['UIDVALIDITY']))
            else:
                logger.critical('folder %s did not return UIDVALIDITY' % folder_name)
            if 'PERMANENTFLAGS' in response and '\\*' in response['PERMANENTFLAGS']:
                logger.debug('folder %s supports custom flags')
            else:
                logger.critical('folder %s does not support custom flags or did not return PERMANENTFLAGS')

            assert 'UIDNEXT' in response and 'UIDVALIDITY' in response, "Missing UID Information"
            uid_next, uid_validity = response['UIDNEXT'], response['UIDVALIDITY']


            # TODO get the folder
            folder = Folder(folder_name, self._imap_client)

            if folder._should_completely_refresh(uid_validity):
                folder._completely_refresh_cache()
            else:
                logger.debug('folder %s normal refresh' % folder_name)
                folder._refresh_cache(uid_next)
            

    def _find_or_create_folder(self, flags, name):
        # type: (t.List[t.AnyStr], t.AnyStr) -> Folder

        # folder_schema = None 
        # try:
        #     folder_schema = FolderSchema.objects.get(imap_account_id=self._imap_account.id, name=name)
        # except FolderSchema.Does
        pass


    def _list_selectable_folders(self, root=''):
        # type: (t.Text) -> t.Generator[t.Text]
        """List all the folders in the Mailbox
        """

        # we want to avoid listing all the folders 
        # https://www.imapwiki.org/ClientImplementation/MailboxList
        # we basically only want to list folders when we have to
        for (flags, delimiter, name) in self._imap_client.list_folders('', root + '%'):
            
            # assume there are children unless specifically told otherwise
            recurse_children = True

            # we look at all the flags here
            logger.info('folder: %s, flags: %s, delimiter: %s' % (name, flags, delimiter))
            if '\\HasNoChildren' in flags:
                logger.debug('folder %s has no children' % name)
                recurse_children = False
            if '\\HasChildren' in flags:
                logger.debug('folder %s has children' % name)
            if '\\Unmarked' in flags:
                logger.debug('folder %s does not have messages' % name)
            if '\\Marked' in flags:
                logger.debug('folder %s marked by server probably contains messages' % name)

            if recurse_children:
                for child_name in self._list_selectable_folders(name + delimiter):
                    yield child_name

            # do not yield folders which are not selectable
            if '\\Noselect' in flags:
                logger.debug('folder %s is not selectable' % name)
                continue

            yield name
    
    def _check_for_new_emails(self):
        found_new_emails = False
        if found_new_emails:
            self.newMessage()



    

