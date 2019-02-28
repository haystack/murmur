from __future__ import unicode_literals, print_function, division
from imapclient import IMAPClient  # noqa: F401 ignore unused we use it for typing
import typing as t  # noqa: F401 ignore unused we use it for typing
import logging 
from message import Message
from schema.youps import MessageSchema, FolderSchema  # noqa: F401 ignore unused we use it for typing

logger = logging.getLogger('youps')  # type: logging.Logger

class Folder():

    def __init__(self, folder_schema, imap_client):
        # type: (FolderSchema, IMAPClient) -> Folder

        self._schema = folder_schema  # type: FolderSchema

        # the connection to the server
        self._imap_client = imap_client  # type: IMAPClient

    def __str__(self):
        # type: () -> t.AnyStr
        return self.name

    @property
    def _uid_next(self):
        # type: () -> int
        return self._schema.uid_next

    @_uid_next.setter
    def _uid_next(self, value):
        # type: (int) -> None
        self._schema.uid_next = value
        self._schema.save()

    @property
    def _uid_validity(self):
        # type: () -> int
        return self._schema.uid_validity

    @_uid_validity.setter
    def _uid_validity(self, value):
        # type: (int) -> None
        self._schema.uid_validity = value
        self._schema.save()

    @property
    def name(self):
        # type: () -> t.Text
        return self._schema.name

    @name.setter
    def name(self, value):
        # type: (t.Text) -> None
        self._schema.name = value
        self._schema.save()

    @property
    def flags(self):
        # type: () -> t.List[t.AnyStr]
        return self._schema.flags

    @flags.setter
    def flags(self, value):
        # type: (t.List[t.AnyStr]) -> None
        self._schema.flags = value
        self._schema.save()

    @property
    def _last_seen_uid(self):
        # type: () -> int
        return self._schema.last_seen_uid

    @_last_seen_uid.setter
    def _last_seen_uid(self, value):
        # type: (int) -> None
        self._schema.last_seen_uid = value
        self._schema.save()

    @property
    def _is_selectable(self):
        # type: () -> bool 
        return self._schema.is_selectable

    @_is_selectable.setter
    def _is_selectable(self, value):
        # type: (bool) -> None
        self._schema.is_selectable = value
        self._schema.save()


    def _completely_refresh_cache(self):
        """Called when the uid_validity has changed or first time seeing the folder.

        Should completely remove any messages stored in this folder and rebuild
        the cache of messages from scratch.
        """

        logger.debug("folder %s completely refreshing cache" % self)

        # delete any messages already stored in the folder
        MessageSchema.objects.filter(folder_schema=self._schema).delete()

        # get new messages starting from the last seen uid of 0
        self._get_new_messages(0)

    def _get_new_messages(self, last_seen_uid):
        logger.debug("folder %s getting new messages" % self)
        fetch_data = self._imap_client.fetch('%d:*' % (last_seen_uid + 1), Message._descriptors)

        for uid in fetch_data:
            message_data = fetch_data[uid]
            if 'SEQ' not in message_data:
                logger.critical('Missing SEQ in message data')
            if 'FLAGS' not in message_data:
                logger.critical('Missing FLAGS in message data')

            message_schema = MessageSchema(imap_account=self._schema.imap_account,
                                           folder_schema=self._schema,
                                           uid=uid,
                                           msn=message_data['SEQ'],
                                           flags=message_data['FLAGS'])
            message_schema.save()
            logger.debug("folder %s saved new message" % self)


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
            fetch_data = self._imap_client.fetch('%d:*' % self._last_seen_uid + 1, Message._descriptors)  # type: t.Dict[int, t.Dict[str, t.Any]]
            
            for uid in fetch_data:
                # TODO create a new message
                # TODO maybe trigger the user
                pass

        # get all the flags for the old messages
        fetch_data = self._imap_client.fetch('1:%d' % self._last_seen_uid, ['FLAGS'])  # type: t.Dict[int, t.Dict[str, t.Any]] 
        
        for message in search_messages.where(uid <= self._last_seen_uid):
            # remove any cached messages which are not returned by the server
            if message._uid not in fetch_data:
                message._remove_from_cache()
            message.update_flags(fetch_data[b'FLAGS'])
            message._refresh_cache(fetch_data[message._uid])
            # TODO maybe tell the user that flags changed?
