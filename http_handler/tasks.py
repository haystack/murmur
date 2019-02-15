from celery.decorators import task, periodic_task
from celery.utils.log import get_task_logger

from schema.youps import ImapAccount

logger = get_task_logger(__name__)


@task(name="add_task")
def add_task(imap_account, mode):
    """sends an email when feedback form is filled successfully"""
    logger.info("ADD TASK performed!")

    # determine it is periodic or not 
    # callback to user profile to make sure we are not running out-dated code
    print("ADD TASK performed!" + imap_account.email)
    return imap_account.email

# this is for static task scheduling
# @on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     # Calls test('hello') every 10 seconds.
#     sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

#     # Calls test('world') every 30 seconds
#     sender.add_periodic_task(30.0, test.s('world'), expires=10)

# TODO try to add simple task and see how to print out task, try to call this from somewhere 

@task
def test(arg):
    print("TEST TASK  " + arg)


# @periodic_task(run_every=(crontab(minute='*/15')), name="some_task", ignore_result=True)
# def some_task():
#     # do something
#     logger.info("Saved image from Flickr")
#     print ("perioid task")