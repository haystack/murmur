from celery.decorators import task, periodic_task
from celery.utils.log import get_task_logger
from http_handler.settings import BASE_URL, WEBSITE, IMAP_SECRET
from schema.youps import Action, ImapAccount, TaskScheduler, PeriodicTask, FolderSchema
from smtp_handler.utils import send_email, codeobject_loads

import json, ujson, types, marshal, random
from browser.models.mailbox import MailBox


import logging

logger = logging.getLogger('youps')  # type: logging.Logger

@task(name="add_periodic_task")
def add_periodic_task(interval, imap_account_id, action_id, search_criteria, folder_name, expires=None):
    """ create a new dynamic periodic task, mainly used for users' set_interval() call.

    Args:
        interval (number): interval of how often to run the code in sec
        the rest args are same as imap.interpret's
    """
    logger.info("ADD TASK performed!")

    code = 'a=Action.objects.get(id=%d)\ncode_object=codeobject_loads(a.code)\ng = type(codeobject_loads)(code_object ,locals())\ng()' % action_id
    args = ujson.dumps( [imap_account_id, code, search_criteria, folder_name] )

    # TODO naming meaningful to distinguish one-off and interval running 
    ptask_name = "%d_%d" % (int(imap_account_id), random.randint(1, 10000))
    TaskScheduler.schedule_every('run_interpret', 'seconds', interval, ptask_name, args, expires=expires)

    imap_account = ImapAccount.objects.get(id=imap_account_id)
    if expires: # set_timeout
        imap_account.status_msg = imap_account.status_msg + "[%s]set_timeout(): will be executed after %d seconds\n" % (ptask_name, interval)
    else:
        imap_account.status_msg = imap_account.status_msg + "[%s]set_interval(): executing every %d seconds\n" % (ptask_name, interval)
    imap_account.save()
    

@task(name="remove_periodic_task")
def remove_periodic_task(imap_account_id, ptask_name=None):
    """ remove a new periodic task. If ptask_name is given, then remove that specific task.
    Otherwise remove all tasks that are associated with the IMAP account ID. 

    Args:
        imap_account_id (number): id of associated ImapAccount object
        ptask_name (string): a name of the specific task to be deleted
    """

    if ptask_name is None:
        ptask_prefix = '%d_' % imap_account_id
        PeriodicTask.objects.filter(name__startswith=ptask_prefix).delete()
        Action.objects.filter(folder__imap_account__id=imap_account_id).delete()      

    else:
        PeriodicTask.objects.filter(name=ptask_name).delete()

    imap_account = ImapAccount.objects.get(id=imap_account_id)
    status_msgs = imap_account.status_msg.split('\n')
    
    # update status msg for the user
    new_msg = "".join([ x+"\n" for x in status_msgs if len(x.strip()) > 0 and not x.startswith( "[%d" % (imap_account_id) )])
    imap_account.status_msg = new_msg
    imap_account.save()

@task(name="run_interpret")
def run_interpret(imap_account_id, code, search_criteria, folder_name=None, is_test=False, email_content=None):
    """ execute the given code object.

    Args:
        imap_account_id (number): id of associated ImapAccount object
        code (code object or string): which code to run
        search_creteria (string): IMAP query. To which email to run the code
        is_test (boolean): True- just printing the log. False- executing the code
        email_content (string): for email shortcut --> potential deprecate  
    """
    logger.info("Task run interpret imap_account: %d %s" % (imap_account_id, folder_name))
    
    if type(code) == str:
        code = codeobject_loads(code)

    # code = marshal.loads(code)
    from browser.imap import interpret, authenticate
    imap_account = ImapAccount.objects.get(id=imap_account_id)
    auth_res = authenticate( imap_account )
    # TODO auth handling
    if not auth_res['status']:
        raise ValueError('Something went wrong during authentication. Refresh and try again!')
        
    imap = auth_res['imap']
    if folder_name is None: 
        imap.select_folder('INBOX')
    else:
        imap.select_folder(folder_name)
    res = interpret(imap_account, imap, code, search_criteria, is_test, email_content)

    logger.info(res['imap_log'])

    # @Luke
    # TODO add logs to users' execution_log
    # we need a setter function that is dealing with text encoding. Every log should be added through the function. 
    # save_exeucution_log(imap_account, res['imap_log'])


# @periodic_task(run_every=(crontab(minute='*/15')), name="some_task", ignore_result=True)
# def some_task():
#     # do something
#     logger.info("Saved image from Flickr")
#     print ("perioid task")

# from browser.imap import authenticate

@task(name="loop_sync_user_inbox")
def loop_sync_user_inbox(imapAccount_email):
    """ execute the given code object.

    Args:
        imapAccount (Model.ImapAccount): user's ImapAccount object
        code (code object or string): which code to run
        search_creteria (string): IMAP query. To which email to run the code
        is_test (boolean): True- just printing the log. False- executing the code
        email_content (string): for email shortcut --> potential deprecate  
    """
    logger.info("Start syncing user's inbox: %s" % (imapAccount_email))
    imapAccount = ImapAccount.objects.get(email=imapAccount_email)

    # authenticate with the user's imap server
    auth_res = authenticate(imapAccount)
    # if authentication failed we can't run anything
    if not auth_res['status']:
        # Stop doing loop
        return

    # get an imapclient which is authenticated
    imap = auth_res['imap']

    # create the mailbox
    mailbox = MailBox(imapAccount, imap)
    # sync the mailbox with imap
    mailbox._sync()
    logger.info("Mailbox sync done")
    # after sync, logout to prevent multi-connection issue
    imap.logout()

    if imapAccount.is_initialized is False:
        #TODO send email to the user that youps is initialized 
        imapAccount.is_initialized = True
        imapAccount.save()

    # The next sync is guaranteed to be executed at some time after 3secs, but not necessarily at that exact time
    loop_sync_user_inbox.delay(imapAccount, countdown=3)