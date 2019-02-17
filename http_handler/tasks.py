from celery.decorators import task, periodic_task
from celery.utils.log import get_task_logger

from schema.youps import ImapAccount, TaskScheduler
from browser.imap import interpret

logger = get_task_logger(__name__)

# celery -A http_handler worker -l debug
# celery -A http_handler beat --max-interval=10 -S djcelery.schedulers.DatabaseScheduler -l debug

@task(name="add_periodic_task")
def add_periodic_task(interval, imap_account_id, imap, code, search_creteria, is_test=False, email_content=None):
    """ create a new periodic task

    Args:
        interval (number): interval of how often to run the code in sec
        the rest args are same as imap.interpret's
    """
    logger.info("ADD TASK performed!")

    # determine it is periodic or not 
    # callback to user profile to make sure we are not running out-dated code
    print("ADD periodic task TASK performed!" + imap_account_id)
    imapAccount = ImapAccount.objects.get(id=imap_account_id)
    TaskScheduler.schedule_every('run_interpret', 'seconds', interval, [imapAccount, imap, code, search_creteria, is_test, email_content])
    return imapAccount

def remove_periodic_task():
    pass

@task(name="run_interpret")
def run_interpret(imap_account, imap, code, search_creteria, is_test=False, email_content=None):
    interpret(imap_account, imap, code, search_creteria, is_test, email_content)


# @periodic_task(run_every=(crontab(minute='*/15')), name="some_task", ignore_result=True)
# def some_task():
#     # do something
#     logger.info("Saved image from Flickr")
#     print ("perioid task")