from __future__ import unicode_literals, print_function, division
import typing as t  # noqa: F401 ignore unused we use it for typing
from schema.youps import MessageSchema  # noqa: F401 ignore unused we use it for typing
from imapclient import IMAPClient  # noqa: F401 ignore unused we use it for typing


class Message(object):

    # the descriptors we are cacheing for each message
    _descriptors = ['ALL']  # type: t.List[t.Text]

    def __init__(self, message_schema, imap_client):
        # type: (MessageSchema, IMAPClient) -> Message
       
        self._schema = message_schema  # type: MessageSchema

        # the connection to the server
        self._imap_client = imap_client  # type: IMAPClient


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

        