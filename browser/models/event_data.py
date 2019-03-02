from _future_ import unicode_literals, print_function, division
from abc import ABCMeta, abstractmethod
from event import Event  # noqa: F401 ignore unused we use it for typing
import typing as t  # noqa: F401 ignore unused we use it for typing
from schema.youps import Action, MessageSchema

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
        self.code = Action.objects.filter(trigger="arrival", folder=self._schema)[0] # TODO what if there are many arrival functions in one mode?
        self.search_criteria = search_criteria
        self.folder_schema = folder_schema

    def fire_event(self, event):
        event.fire(self.get_message())

    def get_message(self):
        # TODO more defensive (e.g. what if there is no message filtered?)
        return MessageSchema.obejcts.filter(imap_account=self.imap_account)
