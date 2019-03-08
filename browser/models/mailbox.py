from __future__ import unicode_literals, print_function, division
from imapclient import IMAPClient  # noqa: F401 ignore unused we use it for typing
from event import Event
import logging
import typing as t  # noqa: F401 ignore unused we use it for typing
from schema.youps import ImapAccount, FolderSchema, MailbotMode  # noqa: F401 ignore unused we use it for typing
from folder import Folder
import Queue

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
        self.new_message_handler = Event()  # type: Event

        self.event_data_queue = Queue.Queue()  # type: Queue

    def __str__(self):
        # type: () -> t.AnyStr
        """Produce a string representation of the mailbox

        Returns:
            str: string representation of the mailbox
        """

        return "mailbox: %s" % (self._imap_account.email)

    def _sync(self):
        # type: () -> None
        """Synchronize the mailbox with the imap server.
        """

        assert len(set(self._list_selectable_folders())) == len(list(self._list_selectable_folders()))

        supports_cond_store = self._supports_cond_store()
        logger.info("supports cond store: %s" % supports_cond_store)

        # should do a couple things based on
        # https://stackoverflow.com/questions/9956324/imap-synchronization
        # and https://tools.ietf.org/html/rfc4549
        # TODO for future work per folder might be highest common denominator for parallelizing
        for folder in self._list_selectable_folders():
            # response contains folder level information such as
            # uid validity, uid next, and highest mod seq
            response = self._imap_client.select_folder(folder.name)
            if 'HIGHESTMODSEQ' not in response:
                logger.critical("%s Missing HIGHESTMODSEQ information" % folder)
            else:
                logger.info("%s HIGHESTMODSEQ %d" % (folder, response['HIGHESTMODSEQ']))
            if 'NOMODSEQ' not in response:
                logger.critical("%s does not support cond store" % folder)


            # our algorithm doesn't work without these
            if not ('UIDNEXT' in response and 'UIDVALIDITY' in response):
                logger.critical("%s Missing UID Information" % folder)
                continue

            uid_next, uid_validity = response['UIDNEXT'], response['UIDVALIDITY']
            highest_mod_seq = response.get('HIGHESTMODSEQ')

            # check if we are doing a total refresh or just a normal refresh
            # total refresh occurs the first time we see a folder and
            # when the UIDVALIDITY changes
            if folder._should_completely_refresh(uid_validity):
                folder._completely_refresh_cache()
            else:
                folder._refresh_cache(uid_next, highest_mod_seq, self.event_data_queue)

            # update the folder's uid next and uid validity
            folder._uid_next = uid_next
            folder._uid_validity = uid_validity


    def _supports_cond_store(self):
        # type: () -> bool
        """True if the imap server support RFC4551 which has 
        things like HIGHESTMODSEQ

        Returns:
            bool: whether or not the imap server supports cond store
        """
        return self._imap_client.has_capability('CONDSTORE')

    def _run_user_code(self):
        from browser.sandbox import interpret
        code = self._imap_account.current_mode.code
        res = interpret(self, code)
        if res['imap_log']:
            logger.info('user output: %s' % res['imap_log'])
        return res


    def _find_or_create_folder(self, name):
        # type: (t.AnyStr) -> Folder
        """Return a reference to the folder with the given name.

        Returns:
            Folder: Folder associated with the passed in name
        """

        folder_schema = None  # type: FolderSchema
        try:
            folder_schema = FolderSchema.objects.get(
                imap_account=self._imap_account, name=name)
        except FolderSchema.DoesNotExist:
            folder_schema = FolderSchema(
                imap_account=self._imap_account, name=name)
            folder_schema.save()
            logger.debug("created folder %s in database" % name)

        return Folder(folder_schema, self._imap_client)

    def _list_selectable_folders(self, root=''):
        # type: (t.Text) -> t.Generator[Folder]
        """Generate all the folders in the Mailbox
        """

        # we want to avoid listing all the folders
        # https://www.imapwiki.org/ClientImplementation/MailboxList
        # we basically only want to list folders when we have to
        for (flags, delimiter, name) in self._imap_client.list_folders('', root + '%'):
            # TODO check if the user is using the gmail
            # If it is gmail, then skip All Mail folder
            if name == "[Gmail]/All Mail":
                continue
            folder = self._find_or_create_folder(name)  # type: Folder

            # TODO maybe fire if the flags have changed
            folder.flags = flags

            # assume there are children unless specifically told otherwise
            recurse_children = True

            # we look at all the flags here
            if '\\HasNoChildren' in flags:
                recurse_children = False

            # do depth first search and return child folders if they exist
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
