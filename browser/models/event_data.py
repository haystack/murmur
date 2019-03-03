from __future__ import unicode_literals, print_function, division
from abc import ABCMeta, abstractmethod
from event import Event  # noqa: F401 ignore unused we use it for typing
import typing as t  # noqa: F401 ignore unused we use it for typing
from schema.youps import Action, MessageSchema

import logging

logger = logging.getLogger('youps')  # type: logging.Logger

# class Abstract:
#     _metaclass_ = ABCMeta

#     @abstractmethod
#     def fire_event(self):
#         pass

class AbstractEventData(object):
    _metaclass_ = ABCMeta

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def fire_event(self, event):
        # type : (Event) -> None
        """Takes in the appropriate event for the EventData object and fires it
        """
        pass

class NewMessageData(AbstractEventData):
    def __init__(self, imap_account, search_criteria, folder_schema):
        super(NewMessageData, self).__init__()
        self.imap_account = imap_account
        
        actions = Action.objects.filter(trigger="arrival", folder=folder_schema)
        if actions.exists():
            # TODO what if there are many arrival functions in one mode?
            actions = actions[0]
            # TODO replace newMessage with the right Message object
            self.code = 'newMessage="TODO REPLACE THIS"\na=Action.objects.filter(id=%d)[0]\ncode_object=co_loads(a.code)\ng = type(co_loads)(code_object ,locals())\ng(newMessage)' % actions.id
        else: 
            self.code = ""
        self.search_criteria = search_criteria
        self.folder_schema = folder_schema
        logger.debug("event data created %s Folder: %s" % (self.search_criteria, self.folder_schema.name))

    def fire_event(self, event):
        logger.debug("event data about to be fired %s Folder: %s" % (self.search_criteria, self.folder_schema.name))
        event.fire(imap_account_id=self.imap_account.id, code=self.code, search_criteria=self.search_criteria, folder_name=self.folder_schema.name)

    def get_message(self):
        # return MessageSchema.objects.filter(imap_account=self.imap_account)
        pass
