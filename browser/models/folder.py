from __future__ import unicode_literals, print_function, division
from imapclient import IMAPClient  # noqa: F401 ignore unused we use it for typing
import typing as t  # noqa: F401 ignore unused we use it for typing
import logging 
from .message import Message
from schema.youps import MessageSchema

logger = logging.getLogger('youps')  # type: logging.Logger

class Folder():
    def __init__(self, name, imap):
        # type: (t.Text, IMAPClient) -> Folder

        # the connection to the server
        self._imap = imap  # type: IMAPClient

        # if this changes then there is new mail
        self._uid_next = -1  # type: int

        # if this changes we need to resync the entire folder
        self._uid_validity = -1  # type: int

        # should contain the full path to the folder i.e. "work/projects/youps"
        self.name = name  # type: t.Text 

        # the last seen uid that we know about
        self._last_seen_uid = -1  # type: int

    def _completely_refresh_cache(self):
        """Called when the uid_validity has changed or first time seeing the folder.

        Should completely remove any messages stored in this folder and rebuild
        the cache of messages from scratch.
        """
        raise NotImplementedError("complete refresh not implemented")

    def _should_completely_refresh(self, uid_validity):
        """Determine if the folder should completely refresh it's cache.
        
        Args:
            uid_validity (int): UIDVALIDITY returned from select command
        
        Returns:
            bool: True if the folder should completely refresh
        """

        # type: (int) -> bool
        if self._uid_validity == -1:
            logger.info("folder %s seen for first time" % self.name)
            return True
        if self._uid_validity != uid_validity:
            logger.critical('folder %s uid_validity changed must rebuild cache' % self.name)
            return True
        return False


    def _refresh_cache(self, uid_next):
        # type: (int) -> None
        """Called during normal synchronization to refresh the cache.

        Should get new messages and build message number to UID map for the
        new messages.

        Should update cached flags on old messages, find out which old messages
        got expunged, build a message number to UID map for old messages.

        Args:
            uid_next (int): UIDNEXT returned from select command
        """

        # if the uid has not changed then we don't need to get new messages
        if uid_next != self._uid_next:
            # get all the descriptors for the new messages
            fetch_data = self._imap.fetch('%d:*' % self._last_seen_uid + 1, Message._descriptors)  # type: t.Dict[int, t.Dict[str, t.Any]]
            
            for uid in fetch_data:
                # TODO create a new message
                # TODO maybe trigger the user
                pass

        # get all the flags for the old messages
        fetch_data = self._imap.fetch('1:%d' % self._last_seen_uid, ['FLAGS'])  # type: t.Dict[int, t.Dict[str, t.Any]] 
        
        for message in search_messages.where(uid <= self._last_seen_uid):
            # remove any cached messages which are not returned by the server
            if message._uid not in fetch_data:
                message._remove_from_cache()
            message.update_flags(fetch_data[b'FLAGS'])
            message._refresh_cache(fetch_data[message._uid])
            # TODO maybe tell the user that flags changed?
