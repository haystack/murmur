from __future__ import unicode_literals, print_function, division
from imapclient import IMAPClient  # noqa: F401 ignore unused we use it for typing
from event import Event
import logging 
import typing as t  # noqa: F401 ignore unused we use it for typing
from schema.youps import ImapAccount, FolderSchema  # noqa: F401 ignore unused we use it for typing
from folder import Folder

logger = logging.getLogger('youps')  # type: logging.Logger

class MailBox(object):
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

        return

        for folder in self._list_selectable_folders():
            response = self._imap_client.select_folder(folder.name)
            logger.debug('select_folder response: %s' % response)

        #     # log information about flags returned
        #     if 'HIGHESTMODSEQ' in response:
        #         # https://wiki.mozilla.org/Thunderbird:IMAP_RFC_4551_Implementation
        #         logger.debug('server supports rfc 4551')
        #     if 'EXISTS' in response:
        #         logger.debug('folder %s contains %d messages' % (folder, response['EXISTS']))
        #     if 'RECENT' in response:
        #         logger.debug('folder %s contains %d recent messages' % (folder, response['RECENT']))
        #     if 'UIDNEXT' in response:
        #         logger.debug('folder %s next UID is %d' % (response['UIDNEXT']))
        #     else:
        #         logger.critical('folder %s did not return UIDNEXT' % folder)
        #     if 'UIDVALIDITY' in response:
        #         logger.debug('folder %s UIDVALIDITY %d' % (response['UIDVALIDITY']))
        #     else:
        #         logger.critical('folder %s did not return UIDVALIDITY' % folder)
        #     if 'PERMANENTFLAGS' in response and '\\*' in response['PERMANENTFLAGS']:
        #         logger.debug('folder %s supports custom flags')
        #     else:
        #         logger.critical('folder %s does not support custom flags or did not return PERMANENTFLAGS')

            if not ('UIDNEXT' in response and 'UIDVALIDITY' in response):
                logger.critical("Missing UID Information for folder %s" % folder)

            assert 'UIDNEXT' in response and 'UIDVALIDITY' in response, "Missing UID Information"
            uid_next, uid_validity = response['UIDNEXT'], response['UIDVALIDITY']


            logger.info("folder %s: uid_next %d uid_validity %d" % (folder, folder._uid_next, folder._uid_validity))
            logger.info("uid_next %d, uid_validity %d" % (uid_next, uid_validity))

            if folder._should_completely_refresh(uid_validity):
                logger.debug('folder %s should completely refresh' % folder)
                folder._completely_refresh_cache()
            else:
                folder._refresh_cache(uid_next)

            folder._uid_next = uid_next
            assert folder._uid_next == uid_next
            folder._uid_validity = uid_validity
            assert folder._uid_validity == uid_validity
            logger.info("folder %s: uid_next %d uid_validity %d" % (folder, folder._uid_next, folder._uid_validity))
            logger.info("folder schema %s: uid_next %d uid_validity %d" % (folder, folder._schema.uid_next, folder._schema.uid_validity))
            


    def _find_or_create_folder(self, name):
        # type: (t.AnyStr) -> Folder

        folder_schema = None  # type: FolderSchema
        try:
            folder_schema = FolderSchema.objects.get(imap_account = self._imap_account, name = name)
            logger.debug("found folder %s" % name)
        except FolderSchema.DoesNotExist:
            folder_schema = FolderSchema(imap_account=self._imap_account, name=name)
            folder_schema.save()
            logger.debug("created folder %s" % name)

        return Folder(folder_schema, self._imap_client)


    def _list_selectable_folders(self, root=''):
        # type: (t.Text) -> t.Generator[Folder]
        """List all the folders in the Mailbox
        """

        # we want to avoid listing all the folders 
        # https://www.imapwiki.org/ClientImplementation/MailboxList
        # we basically only want to list folders when we have to
        for (flags, delimiter, name) in self._imap_client.list_folders('', root + '%'):

            folder = self._find_or_create_folder(name)  # type: Folder

            # TODO maybe fire if the flags have changed
            folder.flags = flags
            
            # assume there are children unless specifically told otherwise
            recurse_children = True

            # we look at all the flags here
            logger.debug('folder: %s, flags: %s, delimiter: %s' % (name, flags, delimiter))
            if '\\HasNoChildren' in flags:
                recurse_children = False

            if recurse_children:
                for child_folder in self._list_selectable_folders(name + delimiter):
                    yield child_folder

            # do not yield folders which are not selectable
            if '\\Noselect' in flags:
                folder._is_selectable = False
                continue
            else:
                # TODO we should verify this in the return from select_folder
                folder._is_selectable = True

            yield folder




    

