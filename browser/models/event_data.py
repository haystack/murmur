from _future_ import unicode_literals, print_function, division
from abc import ABCMeta, abstractmethod
from event import Event  # noqa: F401 ignore unused we use it for typing
import typing as t  # noqa: F401 ignore unused we use it for typing
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
    def __init__(self, n):
        super(NewMessageData, self).__init__()


    def fire_event(event):
        event.fire(Messagefromuid())


if _name_ == '_main_':
    a = NewMessageData(3)