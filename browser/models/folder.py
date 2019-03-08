from __future__ import unicode_literals, print_function, division
from imapclient import IMAPClient  # noqa: F401 ignore unused we use it for typing
import typing as t  # noqa: F401 ignore unused we use it for typing
import logging
from message import Message
from schema.youps import MessageSchema, FolderSchema, ContactSchema, ImapAccount  # noqa: F401 ignore unused we use it for typing
from django.db.models import Max
from imapclient.response_types import Address  # noqa: F401 ignore unused we use it for typing
from email.header import decode_header
from Queue import Queue  # noqa: F401 ignore unused we use it for typing
from browser.models.event_data import NewMessageData


logger = logging.getLogger('youps')  # type: logging.Logger


class Folder(object):

    def __init__(self, folder_schema, imap_client):
        # type: (FolderSchema, IMAPClient) -> Folder

        self._schema = folder_schema  # type: FolderSchema

        # the connection to the server
        self._imap_client = imap_client  # type: IMAPClient

    def __str__(self):
        # type: () -> t.AnyStr
        return "folder: %s" % (self.name)

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Folder):
            return self._schema == other._schema
        return False


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
    def _highest_mod_seq(self):
        # type: () -> int
        return self._schema.highest_mod_seq

    @_highest_mod_seq.setter
    def _highest_mod_seq(self, value):
        # type: (int) -> None
        self._schema.highest_mod_seq = value
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

    @property
    def _imap_account(self):
        # type: () -> ImapAccount
        return self._schema.imap_account

    def _completely_refresh_cache(self):
        # type: () -> None
        """Called when the uid_validity has changed or first time seeing the folder.

        Should completely remove any messages stored in this folder and rebuild
        the cache of messages from scratch.
        """

        logger.debug("%s completely refreshing cache" % self)

        # delete any messages already stored in the folder
        MessageSchema.objects.filter(folder_schema=self._schema).delete()

        # save new messages starting from the last seen uid of 0
        self._save_new_messages(0)
        # TODO maybe trigger the user

        # finally update our last seen uid (this uses the cached messages to determine last seen uid)
        self._update_last_seen_uid()
        logger.debug("%s finished completely refreshing cache" % self)

    def _update_last_seen_uid(self):
        # type () -> None
        """Updates the last seen uid to be equal to the maximum uid in this folder's cache
        """

        max_uid = MessageSchema.objects.filter(folder_schema=self._schema).aggregate(
            Max('uid'))  # type: t.Dict[t.AnyStr, int]
        max_uid = max_uid['uid__max']
        if max_uid is None:
            max_uid = 0
        if self._last_seen_uid != max_uid:
            self._last_seen_uid = max_uid
            logger.debug('%s updated max_uid %d' % (self, max_uid))

    def _refresh_cache(self, uid_next, highest_mod_seq, event_data_queue):
        # type: (int, int, Queue) -> None
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
            self._save_new_messages(self._last_seen_uid, event_data_queue)
            # TODO maybe trigger the user

        # if the last seen uid is zero we haven't seen any messages
        if self._last_seen_uid != 0:
            self._update_cached_message_flags(highest_mod_seq)

        self._update_last_seen_uid()
        logger.debug("%s finished normal refresh" % (self))

    def _should_completely_refresh(self, uid_validity):
        # type: (int) -> bool
        """Determine if the folder should completely refresh it's cache.

        Args:
            uid_validity (int): UIDVALIDITY returned from select command

        Returns:
            bool: True if the folder should completely refresh
        """

        if self._uid_validity == -1:
            return True
        if self._uid_validity != uid_validity:
            logger.debug(
                'folder %s uid_validity changed must rebuild cache' % self.name)
            return True
        return False

    def _update_cached_message_flags(self, highest_mod_seq):
        # type: (int) -> None
        """Update the flags on any cached messages.
        """

        # we just check the highestmodseq and revert to full sync if they don't match
        # this is kind of what thunderbird does https://wiki.mozilla.org/Thunderbird:IMAP_RFC_4551_Implementation
        if highest_mod_seq is not None:
            if self._highest_mod_seq == highest_mod_seq:
                logger.debug("%s matching highest mod seq no flag update" % self)
                return

        logger.debug("%s started updating flags" % self)

        # get all the flags for the old messages
        fetch_data = self._imap_client.fetch('1:%d' % (self._last_seen_uid), [
                                             'FLAGS'])  # type: t.Dict[int, t.Dict[str, t.Any]]
        # update flags in the cache
        for message_schema in MessageSchema.objects.filter(folder_schema=self._schema):

            # ignore cached messages that we just fetched
            if message_schema.uid > self._last_seen_uid:
                continue
            # if we don't get any information about the message we have to remove it from the cache
            if message_schema.uid not in fetch_data:
                message_schema.delete()
                logger.debug("%s deleted message with uid %d" %
                             (self, message_schema.uid))
                continue
            message_data = fetch_data[message_schema.uid]
            # TODO make this more DRY
            if 'SEQ' not in message_data:
                logger.critical('Missing SEQ in message data')
                logger.critical('Message data %s' % message_data)
                continue
            if 'FLAGS' not in message_data:
                logger.critical('Missing FLAGS in message data')
                logger.critical('Message data %s' % message_data)
                continue
            message_schema.flags = message_data['FLAGS']
            message_schema.msn = message_data['SEQ']
            message_schema.save()
            # TODO maybe trigger the user


        logger.debug("%s updated flags" % self)
        if highest_mod_seq is not None:
            self._highest_mod_seq = highest_mod_seq
            logger.debug("%s updated highest mod seq to %d" % (self, highest_mod_seq))


    def _save_new_messages(self, last_seen_uid, event_data_queue = None):
        # type: (int, Queue) -> None
        """Save any messages we haven't seen before

        Args:
            last_seen_uid (int): the max uid we have stored, should be 0 if there are no messages stored.
        """

        fetch_data = self._imap_client.fetch(
            '%d:*' % (last_seen_uid + 1), Message._descriptors)

        # if there is only one item in the return field
        # and we already have it in our database
        # delete it to be safe and save it again
        if len(fetch_data) == 1 and last_seen_uid in fetch_data:
            already_saved = MessageSchema.objects.filter(folder_schema=self._schema, uid=last_seen_uid)
            if already_saved:
                logger.critical("%s found already saved message, deleting it" % self)
                already_saved[0].delete()

        logger.info("%s saving new messages" % (self))
        for uid in fetch_data:
            message_data = fetch_data[uid]
            logger.debug("Message %d data: %s" % (uid, message_data))
            if 'SEQ' not in message_data:
                logger.critical('Missing SEQ in message data')
                logger.critical('Message data %s' % message_data)
                continue
            if 'FLAGS' not in message_data:
                logger.critical('Missing FLAGS in message data')
                logger.critical('Message data %s' % message_data)
                continue
            if 'INTERNALDATE' not in message_data:
                logger.critical('Missing INTERNALDATE in message data')
                logger.critical('Message data %s' % message_data)
                continue
            if 'RFC822.SIZE' not in message_data:
                logger.critical('Missing RFC822.SIZE in message data')
                logger.critical('Message data %s' % message_data)
                continue
            if 'ENVELOPE' not in message_data:
                logger.critical('Missing ENVELOPE in message data')
                logger.critical('Message data %s' % message_data)
                continue
                
            # this is the date the message was received by the server
            internal_date = message_data['INTERNALDATE']  # type: datetime
            envelope = message_data['ENVELOPE']
            msn = message_data['SEQ']
            flags = message_data['FLAGS']

            logger.debug("message %d envelope %s" % (uid, envelope))

            # create and save the message schema
            message_schema = MessageSchema(imap_account=self._schema.imap_account,
                                           folder_schema=self._schema,
                                           uid=uid,
                                           msn=msn,
                                           flags=flags,
                                           date=envelope.date,
                                           subject=self._parse_email_subject(envelope.subject),
                                           message_id=envelope.message_id,
                                           internal_date=internal_date,
                                           )

            try:
                message_schema.save()
            except Exception:
                logger.critical("%s failed to save message %d" % (self, uid))
                logger.critical("%s stored last_seen_uid %d, passed last_seen_uid %d" % (self, self._last_seen_uid, last_seen_uid))
                logger.critical("number of messages returned %d" % (len(fetch_data)))
                raise
            if last_seen_uid != 0:
                event_data_queue.put(NewMessageData(Message(message_schema, self._imap_client)))

            logger.debug("%s finished saving new messages..:" % self)

            # create and save the message contacts
            if envelope.from_ is not None:
                message_schema.from_.add(*self._find_or_create_contacts(envelope.from_))
            if envelope.sender is not None:
                message_schema.sender.add(*self._find_or_create_contacts(envelope.sender))
            if envelope.reply_to is not None:
                message_schema.reply_to.add(*self._find_or_create_contacts(envelope.reply_to))
            if envelope.to is not None:
                message_schema.to.add(*self._find_or_create_contacts(envelope.to))
            if envelope.cc is not None:
                message_schema.cc.add(*self._find_or_create_contacts(envelope.cc))
            if envelope.bcc is not None:
                message_schema.bcc.add(*self._find_or_create_contacts(envelope.bcc))

            logger.debug("%s saved new message with uid %d" % (self, uid))

    def _parse_email_subject(self, subject):
        # type: (t.AnyStr) -> t.AnyStr
        """This method parses a subject header which can contain unicode

        Args:
            subject (str): email subject header

        Returns:
            t.AnyStr: unicode string or a 8 bit string
        """

        if subject is None:
            return None
        text, encoding = decode_header(subject)[0]
        if encoding:
            if encoding != 'utf-8' and encoding != 'utf8':
                logger.critical('parse_subject non utf8 encoding: %s' % encoding)
            text = text.decode(encoding)
        return text

    def _find_or_create_contacts(self, addresses):
        # type: (t.List[Address]) -> t.List[ContactSchema]
        """Convert a list of addresses into a list of contact schemas.

        Returns:
            t.List[ContactSchema]: List of contacts associated with the addresses
        """
        assert addresses is not None

        contact_schemas = []
        for address in addresses:
            contact_schema = None  # type: ContactSchema
            email = "%s@%s" % (address.mailbox, address.host)
            name = address.name
            try:
                contact_schema = ContactSchema.objects.get(
                    imap_account=self._imap_account, email=email)
            except ContactSchema.DoesNotExist:
                contact_schema = ContactSchema(
                    imap_account=self._imap_account, email=email, name=name)
                contact_schema.save()
                logger.debug("created contact %s in database" % name)
            contact_schemas.append(contact_schema)
        return contact_schemas
