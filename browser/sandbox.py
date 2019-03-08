from __future__ import unicode_literals, print_function, division

import logging
import Queue
import sys
import typing as t  # noqa: F401 ignore unused we use it for typing
from StringIO import StringIO

from imapclient import IMAPClient  # noqa: F401 ignore unused we use it for typing

from browser.models.event_data import NewMessageData
from browser.models.mailbox import MailBox  # noqa: F401 ignore unused we use it for typing
from schema.youps import Action  # noqa: F401 ignore unused we use it for typing

logger = logging.getLogger('youps')  # type: logging.Logger


def interpret(mailbox, code, is_test=False):
    # type: (Mailbox, unicode, bool) -> t.Dict[t.AnyStr, t.Any]

    # assert we actually got a mailbox
    assert isinstance(mailbox, MailBox)
    # assert the code is unicode
    assert isinstance(code, unicode)
    assert mailbox.new_message_handler is not None

    # set up the default result
    res = {'status': True, 'imap_error': False, 'imap_log': ""}

    # get the logger for user output
    userLogger = logging.getLogger('youps.user')  # type: logging.Logger
    # get the stream handler associated with the user output
    userLoggerStreamHandlers = filter(lambda h: isinstance(h, logging.StreamHandler), userLogger.handlers)
    userLoggerStream = userLoggerStreamHandlers[0].stream if userLoggerStreamHandlers else None
    assert userLoggerStream is not None

    # create a string buffer to store stdout
    user_std_out = StringIO()

    # define user methods
    def on_message_arrival(func):
        mailbox.new_message_handler += func

    # execute user code
    try:
        # set the stdout to a string
        sys.stdout = user_std_out

        # set the user logger to
        userLoggerStream = user_std_out

        # define the variables accessible to the user
        user_environ = {
            'new_message_handler': mailbox.new_message_handler,
            'on_message_arrival': on_message_arrival
        }

        # execute the user's code
        exec(code, user_environ)

        # fire new message events
        while True:
            try:
                event_data = mailbox.event_data_queue.get_nowait()
                if isinstance(event_data, NewMessageData):
                    event_data.fire_event(mailbox.new_message_handler)
            except Queue.Empty:
                break

    except Exception:
        res['status'] = False
        userLogger.exception("failure running user %s code" %
                             mailbox._imap_account.email)
    finally:
        # set the stdout back to what it was
        sys.stdout = sys.__stdout__
        userLoggerStream = sys.__stdout__
        res['imap_log'] = user_std_out.getvalue() + res['imap_log']
        user_std_out.close()
        return res

    # with stdoutIO() as s:
    #     def catch_exception(e):
    #         etype, evalue = sys.exc_info()[:2]
    #         estr = traceback.format_exception_only(etype, evalue)
    #         logstr = 'Error during executing your code \n'
    #         for each in estr:
    #             logstr += '{0}; '.format(each.strip('\n'))

    #         logstr = "%s \n %s" % (logstr, str(e))

    #         # Send this error msg to the user
    #         res['imap_log'] = logstr
    #         res['imap_error'] = True

    #     def on_message_arrival(func=None):
    #         if not func or type(func).__name__ != "function":
    #             raise Exception('on_message_arrival(): requires callback function but it is %s ' % type(func).__name__)

    #         if func.func_code.co_argcount != 1:
    #             raise Exception('on_message_arrival(): your callback function should have only 1 argument, but there are %d argument(s)' % func.func_code.co_argcount)

    #         # TODO warn users if it conatins send() and their own email (i.e., it potentially leads to infinite loops)

    #         # TODO replace with the right folder
    #         current_folder_schema = FolderSchema.objects.filter(imap_account=imap_account, name="INBOX")[0]
    #         action = Action(trigger="arrival", code=codeobject_dumps(func.func_code), folder=current_folder_schema)
    #         action.save()

    #     from http_handler.tasks import add_periodic_task

    #     def set_interval(interval=None, func=None):
    #         if not interval:
    #             raise Exception('set_interval(): requires interval (in second)')

    #         if interval < 1:
    #             raise Exception('set_interval(): requires interval larger than 1 sec')

    #         if not func or type(func).__name__ != "function":
    #             raise Exception('set_interval(): requires callback function but it is %s ' % type(func).__name__)

    #         if func.func_code.co_argcount != 0:
    #             raise Exception('set_interval(): your callback function should have only 0 argument, but there are %d argument(s)' % func.func_code.co_argcount)

    #         # TODO replace with the right folder
    #         current_folder_schema = FolderSchema.objects.filter(imap_account=imap_account, name="INBOX")[0]
    #         action = Action(trigger="interval", code=codeobject_dumps(func.func_code), folder=current_folder_schema)
    #         action.save()
    #         add_periodic_task.delay( interval=interval, imap_account_id=imap_account.id, action_id=action.id, search_criteria=search_creteria, folder_name=current_folder_schema.name)

    #     def set_timeout(delay=None, func=None):
    #         if not delay:
    #             raise Exception('set_timeout(): requires delay (in second)')

    #         if delay < 1:
    #             raise Exception('set_timeout(): requires delay larger than 1 sec')

    #         if not func:
    #             raise Exception('set_timeout(): requires code to be executed periodically')

    #         args = ujson.dumps( [imap_account.id, marshal.dumps(func.func_code), search_creteria, is_test, email_content] )
    #         add_periodic_task.delay( delay, args, delay * 2 - 0.5 ) # make it expire right before 2nd execution happens

    #     def send(subject="", to_addr="", body=""):
    #         if len(to_addr) == 0:
    #             raise Exception('send(): recipient email address is not provided')

    #         if not is_test:
    #             send_email(subject, imap_account.email, to_addr, body)
    #         logger.debug("send(): sent a message to  %s" % str(to_addr))

    #     def get_content():
    #         logger.debug("call get_content")
    #         if email_content:
    #             return email_content
    #         else:
    #             return pile.get_content()

    #     def get_attachment():
    #         pass

    #     def get_attachments():
    #         pass

    #     # return a list of email UIDs
    #     def search(criteria=u'ALL', charset=None, folder=None):
    #         # TODO how to deal with folders
    #         # iterate through all the functions
    #         if folder is None:
    #             pass

    #         # iterate through a folder of list of folder
    #         else:
    #             # if it's a list iterate
    #             pass
    #             # else it's a string search a folder

    #         select_folder('INBOX')
    #         return imap.search(criteria, charset)

    #     def create_folder(folder):
    #         pile.create_folder(folder, is_test)

    #     def delete_folder(folder):
    #         pile.delete_folder(folder, is_test)

    #     def list_folders(directory=u'', pattern=u'*'):
    #         return pile.list_folders(directory, pattern)

    #     def select_folder(folder):
    #         if not imap.folder_exists(folder):
    #             logger.error("Select folder; folder %s not exist" % folder)
    #             return

    #         imap.select_folder(folder)
    #         logger.debug("Select a folder %s" % folder)

    #     def rename_folder(old_name, new_name):
    #         pile.rename_folder(old_name, new_name, is_test)

    #     def get_mode():
    #         if imap_account.current_mode:
    #             return imap_account.current_mode.uid
    #         else:
    #             return None

    #     def set_mode(mode_index):
    #         try:
    #             mode_index = int(mode_index)
    #         except ValueError:
    #             raise Exception('set_mode(): args mode_index must be a index (integer)')

    #         mm = MailbotMode.objects.filter(uid=mode_index, imap_account=imap_account)
    #         if mm.exists():
    #             mm = mm[0]
    #             if not is_test:
    #                 imap_account.current_mode = mm
    #                 imap_account.save()

    #             logger.debug("Set mail mode to %s (%d)" % (mm.name, mode_index))
    #             return True
    #         else:
    #             logger.error("A mode ID %d not exist!" % (mode_index))
    #             return False

    #     try:
    #         if is_valid:
    #             exec code in globals(), locals()
    #             pile.add_flags(['YouPS'])
    #             res['status'] = True
    #     except Action.DoesNotExist:
    #         logger.debug("An action is not existed right now. Maybe you change your script after this action was added to the queue.")
    #     except Exception as e:
    #         catch_exception(e)

    #     res['imap_log'] = s.getvalue() + res['imap_log']

    #     return res
