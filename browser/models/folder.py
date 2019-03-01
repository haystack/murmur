from __future__ import unicode_literals, print_function, division
from imapclient import IMAPClient  # noqa: F401 ignore unused we use it for typing
import typing as t  # noqa: F401 ignore unused we use it for typing
import logging 
from message import Message
from schema.youps import MessageSchema, FolderSchema  # noqa: F401 ignore unused we use it for typing
from django.db.models import Max

logger = logging.getLogger('youps')  # type: logging.Logger

class Folder(object):

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
        logger.info("SAVED uid_validity")

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

        # save new messages starting from the last seen uid of 0
        self._save_new_messages(0)
        # TODO maybe trigger the user

        self._update_last_seen_uid()


    def _update_last_seen_uid(self):
        max_uid = MessageSchema.objects.filter(folder_schema=self._schema).aggregate(Max('uid'))
        logger.info('folder %s: updated max_uid %d' % (self, max_uid))
        self._last_seen_uid = max_uid

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

        logger.debug('folder %s normal refresh' % self)

        # if the uid has not changed then we don't need to get new messages
        if uid_next != self._uid_next:
            # get all the descriptors for the new messages
            self._save_new_messages(self._last_seen_uid)
            # TODO maybe trigger the user

        self._update_cached_message_flags()
        self._update_last_seen_uid()

    def _should_completely_refresh(self, uid_validity):
        """Determine if the folder should completely refresh it's cache.

        Args:
            uid_validity (int): UIDVALIDITY returned from select command

        Returns:
            bool: True if the folder should completely refresh
        """

        # type: (int) -> bool
        if self._uid_validity == -1:
            logger.debug("folder %s seen for first time" % self.name)
            return True
        if self._uid_validity != uid_validity:
            logger.critical('folder %s uid_validity changed must rebuild cache' % self.name)
            return True
        return False

    def _update_cached_message_flags(self):
        logger.debug("folder %s updating cached message flags" % self)

        # get all the flags for the old messages
        fetch_data = self._imap_client.fetch('1:%d' % (self._last_seen_uid), ['FLAGS'])  # type: t.Dict[int, t.Dict[str, t.Any]] 
        # update flags in the cache 
        for message_schema in MessageSchema.objects.filter(folder_schema=self._schema):
            # if we don't get any information about the message we have to remove it from the cache
            if message_schema.uid not in fetch_data:
                message_schema.delete()
            message_data = fetch_data[message_schema.uid]
            if 'SEQ' not in message_data:
                logger.critical('Missing SEQ in message data')
            if 'FLAGS' not in message_data:
                logger.critical('Missing FLAGS in message data')
            message_schema.flags = message_data['FLAGS'] 
            message_schema.msn = message_data['SEQ']
            message_schema.save()
            # TODO maybe trigger the user 
        logger.debug("folder %s updated cached messages" % self)

    def _save_new_messages(self, last_seen_uid):
        logger.debug("folder %s getting new messages" % self)
        fetch_data = self._imap_client.fetch('%d:*' % (last_seen_uid + 1), Message._descriptors)

        max_uid = self._last_seen_uid
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
            if uid > max_uid:
                max_uid = uid

        logger.debug("folder %s saved new messages" % self)
