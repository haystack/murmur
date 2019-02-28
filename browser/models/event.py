
# Baed on https://stackoverflow.com/questions/1092531/event-system-in-python/1096614#1096614

class Event:
    """Simple wrapper for a events
    
    Usage:
        > class MockFileWatcher:
        >     def __init__(self):
        >         self.fileChanged = Event()
        > 
        >     def watchFiles(self):
        >         source_path = "foo"
        >         self.fileChanged(source_path)
        > 
        > def log_file_change(source_path):
        >     print "%r changed." % (source_path,)
        > 
        > def log_file_change2(source_path):
        >     print "%r changed!" % (source_path,)
        > 
        > watcher              = MockFileWatcher()
        > watcher.fileChanged += log_file_change2
        > watcher.fileChanged += log_file_change
        > watcher.fileChanged -= log_file_change2
        > watcher.watchFiles()
    """

    def __init__(self):
        self.handlers = set()

    def handle(self, handler):
        self.handlers.add(handler)
        return self

    def unhandle(self, handler):
        try:
            self.handlers.remove(handler)
        except Exception:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.")
        return self

    def fire(self, *args, **kargs):
        for handler in self.handlers:
            handler(*args, **kargs)

    def getHandlerCount(self):
        return len(self.handlers)

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    __len__  = getHandlerCount
