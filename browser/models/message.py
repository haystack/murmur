from __future__ import unicode_literals, print_function, division
import typing as t  # noqa: F401 ignore unused we use it for typing

class Message(object):

    # the descriptors we are cacheing for each message 
    _descriptors = ['FLAGS']  # type: t.List[t.Text]

    def __init__(self):
        # the uid of the message which will stay constant while the message is cached
        self._uid = None  # type: int

        # the flags on the message
        self._flags = None  # type: t.List[t.AnyStr]
        
        # the message sequence number of the message
        self._msn = None  # type: int

        