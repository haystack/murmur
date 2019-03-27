from __future__ import unicode_literals, print_function, division
import typing as t  # noqa: F401 ignore unused we use it for typing
from imapclient import IMAPClient  # noqa: F401 ignore unused we use it for typing
from schema.youps import ContactSchema  # noqa: F401 ignore unused we use it for typing
import logging

logger = logging.getLogger('youps')  # type: logging.Logger

class Contact(object):

    def __init__(self, contact_schema, imap_client):
        # type: (ContactSchema, IMAPClient) -> Contact

        self._schema = contact_schema  # type: ContactSchema

        # the connection to the server
        self._imap_client = imap_client  # type: IMAPClient

    def __str__(self):
        return self.name or self.email

    def __repr__(self):
        return repr("<Contact object %s>" % str(self.name or self.email))

    @property
    def email(self):
        # type: () -> t.AnyStr
        """Get the email address associated with this contact

        Returns:
            str: The email address associated with this contact
        """
        return self._schema.email

    @property
    def name(self):
        # type: () -> t.AnyStr
        """Get the name associated with this contact

        Returns:
            str: The name associated with this contact
        """
        return self._schema.name

    @property
    def organization(self):
        # type: () -> t.AnyStr
        """Get the organization of this contact

        Returns:
            str: The organization associated with this contact
        """
        return self._schema.organization

    @property
    def geolocation(self):
        # type: () -> t.AnyStr
        """Get the location of this contact

        Returns:
            str: The location associated with this contact
        """
        return self._schema.geolocation

    @property
    def messages_to(self):
        # type: () -> t.List[Message]
        """Get the Messages which are to this contact

        Returns:
            t.List[Message]: The messages where this contact is listed in the to field
        """
        from browser.models.message import Message
        return [Message(message_schema, self._imap_client) for message_schema in self._schema.to_messages.all()]
