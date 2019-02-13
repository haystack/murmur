from celery.decorators import task
from celery.utils.log import get_task_logger

from schema.youps import ImapAccount

logger = get_task_logger(__name__)


@task(name="send_feedback_email_task")
def add_task(imap_account, mode):
    """sends an email when feedback form is filled successfully"""
    logger.info("Sent feedback email")

    # determine it is periodic or not 
    # callback to user profile to make sure we are not running out-dated code
    print(imap_account.email)
    return imap_account.email

@on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    # Calls test('world') every 30 seconds
    sender.add_periodic_task(30.0, test.s('world'), expires=10)

@task
def test(arg):
    print("TEST TASK  " + arg)