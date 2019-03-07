from __future__ import unicode_literals, print_function, division
import typing as t  # noqa: F401 ignore unused we use it for typing
from schema.youps import MessageSchema  # noqa: F401 ignore unused we use it for typing
from imapclient import IMAPClient  # noqa: F401 ignore unused we use it for typing
from datetime import datetime  # noqa: F401 ignore unused we use it for typing
from browser.models.contact import Contact
import logging
from collections import Sequence

userLogger = logging.getLogger('youps.user')  # type: logging.Logger
logger = logging.getLogger('youps')  # type: logging.Logger

class Message(object):

    # the descriptors we are cacheing for each message
    _descriptors = ['FLAGS', 'INTERNALDATE', 'RFC822.SIZE', 'ENVELOPE']  # type: t.List[t.Text]

    def __init__(self, message_schema, imap_client):
        # type: (MessageSchema, IMAPClient) -> Message

        self._schema = message_schema  # type: MessageSchema

        # the connection to the server
        self._imap_client = imap_client  # type: IMAPClient

    def __str__(self):
        # type: () -> t.AnyStr
        return "Message %d" % self._uid

    @property
    def _uid(self):
        # type: () -> int
        return self._schema.uid

    @_uid.setter
    def _uid(self, value):
        # type: (int) -> None
        self._schema.uid = value
        self._schema.save()

    @property
    def _msn(self):
        # type: () -> int
        return self._schema.msn

    @_msn.setter
    def _msn(self, value):
        # type: (int) -> None
        self._schema.msn = value
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
    def subject(self):
        # type: () -> t.AnyStr
        """Get the Subject of the message

        Returns:
            str: The subject of the message
        """
        return self._schema.subject

    @property
    def date(self):
        # type: () -> datetime
        """Get the date and time that the message was sent

        Returns:
            datetime: The date and time the message was sent
        """
        return self._schema.date

    @property
    def is_read(self):
        # type: () -> bool
        """Get if the message has been read

        Returns:
            bool: True if the message has been read
        """
        return '\\Seen' in self.flags

    @property
    def is_deleted(self):
        # type: () -> bool
        """Get if the message has been deleted

        Returns:
            bool: True if the message has been deleted
        """
        return '\\Deleted' in self.flags

    @property
    def is_recent(self):
        # type: () -> bool
        """Get if the message is recent

        Returns:
            bool: True if the message is recent
        """
        # TODO we will automatically remove the RECENT flag unless we make our imapclient ReadOnly
        return '\\Recent' in self.flags

    @property
    def to(self):
        # type: () -> t.List[Contact]
        """Get the Contacts the message is addressed to

        Returns:
            t.List[Contact]: The contacts in the to field of the message
        """
        return [Contact(contact_schema, self._imap_client) for contact_schema in self._schema.to.all()]

    @property
    def from_(self):
        # type: () -> t.List[Contact]
        """Get the Contacts the message is addressed from 

        Returns:
            t.List[Contact]: The contacts in the from field of the message
        """
        return [Contact(contact_schema, self._imap_client) for contact_schema in self._schema.from_.all()]

    @property
    def sender(self):
        # type: () -> t.List[Contact]
        """Get the Contacts the message is sent from 

        Returns:
            t.List[Contact]: The contacts in the sender field of the message
        """
        return [Contact(contact_schema, self._imap_client) for contact_schema in self._schema.sender.all()]

    @property
    def reply_to(self):
        # type: () -> t.List[Contact]
        """Get the Contacts the message is replied to 

        Returns:
            t.List[Contact]: The contacts in the reply_to field of the message
        """
        return [Contact(contact_schema, self._imap_client) for contact_schema in self._schema.reply_to.all()]

    @property
    def cc(self):
        # type: () -> t.List[Contact]
        """Get the Contacts the message is cced to 

        Returns:
            t.List[Contact]: The contacts in the cc field of the message
        """
        return [Contact(contact_schema, self._imap_client) for contact_schema in self._schema.cc.all()]

    @property
    def bcc(self):
        # type: () -> t.List[Contact]
        """Get the Contacts the message is bcced to 

        Returns:
            t.List[Contact]: The contacts in the bcc field of the message
        """
        return [Contact(contact_schema, self._imap_client) for contact_schema in self._schema.bcc.all()]

    def add_labels(self, flags):
        # type: (t.Iterable[t.AnyStr]) -> None
        """Add each of the flags in a list of flags to the message

        Raises:
            TypeError: flags is not an iterable or a string
            TypeError: any flag is not a string
        """
        ok, flags = self._check_flags(flags)
        if not ok:
            return
        if self._is_gmail():
            self._imap_client.add_gmail_labels(self._uid, flags)
        else:
            self._imap_client.add_flags(self._uid, flags)

    def remove_labels(self, flags):
        # type: (t.Iterable[t.AnyStr]) -> None
        """Remove each of the flags in a list of flags from the message

        Raises:
            TypeError: flags is not an iterable or a string
            TypeError: any flag is not a string
        """
        ok, flags = self._check_flags()
        if not ok:
            return
        if self._is_gmail():
            self._imap_client.remove_gmail_labels(self._uid, flags)
        else:
            self._imap_client.remove_flags(self._uid, flags)


    def copy(self, dst_folder):
        # type: (t.AnyStr) -> None
        """Copy the message to another folder.
        """
        self._check_folder(dst_folder)
        self._imap_client.copy(self.uid, dst_folder)

    def delete(self):
        # type: () -> None
        """Mark a message as deleted, the imap server will move it to the deleted messages.
        """
        self._imap_client.add_flags(self._uid, '\\Deleted')

    def mark_read(self):
        # type: () -> None
        """Mark a message as read.
        """
        self._imap_client.add_flags(self._uid, '\\Seen')

    def mark_unread(self):
        # type: () -> None
        """Mark a message as unread
        """
        self._imap_client.remove_flags(self._uid, '\\Seen')

    def move(self, dst_folder):
        # type: (t.AnyStr) -> None
        """Copy the message to another folder.
        """
        self._check_folder(dst_folder)
        self._imap_client.move(self.uid, dst_folder)

    def _check_folder(self, dst_folder):
        if not isinstance(dst_folder, basestring):
            raise TypeError("folder named must be a string")
        if not self._imap_client.folder_exists(dst_folder):
            userLogger.info("folder %s does not exist creating it for you" % dst_folder)
            self._imap_client.create_folder(dst_folder)


    def _check_flags(self, flags):
        # type: (t.Iterable[t.AnyStr]) -> bool, t.Iterable[t.AnyStr]
        ok = True
        # allow user to pass in a string
        if isinstance(flags, basestring):
            flags = [flags]
        elif not isinstance(flags, Sequence):
            raise TypeError("flags must be a sequence")
        # make sure all flags are strings
        for flag in flags:
            if not isinstance(flag, basestring):
                raise TypeError("each flag must be string")
        # remove extraneous white space
        flags = [flag.strip() for flag in flags]
        # remove empty strings
        flags = [flag for flag in flags if flag]
        if not flags:
            ok = False
            userLogger.info("No valid flags passed")
        return ok, flags

    def _is_gmail(self):
        # type: () -> bool
        """Use heuristic to determine if we are connected to a gmail server

        Returns:
            bool: true if we think we are connected to a gmail server
        """
        return self._imap_client.has_capability('X-GM-EXT-1')
