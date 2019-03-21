import logging

from browser.imap import authenticate
from browser.models.mailbox import MailBox
from http_handler.settings import BASE_URL
from schema.youps import ImapAccount
from smtp_handler.utils import send_email
import typing as t  # noqa: F401 ignore unused we use it for typing
import fcntl
logger = logging.getLogger('youps')  # type: logging.Logger



def get_lock(file):
    """Get a lock on the task

    Args:
        file (file): the lock file we are trying to get access to

    Returns:
        bool: True if we get the lock false otherwise
    """

    try:
        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        return False
    return True


def register_inbox():
    """Do the initial sync on an inbox.
    """

    lockFile = 'register_inbox.lock'
    with open(lockFile, 'w') as f:
        have_lock = get_lock(f)
        if not have_lock:
            logger.info('Lock already taken %s' % lockFile)
            return

        for imapAccount in ImapAccount.objects.filter(is_initialized=False):
            try:
                logger.info('first syncing..: %s', imapAccount.email)

                # authenticate with the user's imap server
                auth_res = authenticate(imapAccount)
                # if authentication failed we can't run anything
                if not auth_res['status']:
                    # Stop doing loop
                    # TODO maybe we should email the user
                    continue 

                # get an imapclient which is authenticated
                imap = auth_res['imap']

                # create the mailbox
                mailbox = MailBox(imapAccount, imap)
                # sync the mailbox with imap
                mailbox._sync()

                logger.info("Mailbox sync done: %s" % (imapAccount.email))

                try:
                    mailbox._run_user_code()
                except Exception():
                    logger.exception("Mailbox run user code failed")

                # after sync, logout to prevent multi-connection issue
                imap.logout()

                imapAccount.is_initialized = True
                imapAccount.save()
                send_email("Your YoUPS account is ready!",
                           "no-reply@" + BASE_URL,
                           imapAccount.email,
                           "Start writing your automation rule here! " + BASE_URL)

                logger.info(
                    'Register done for %s', imapAccount.email)
            except ImapAccount.DoesNotExist:
                imapAccount.is_initialized = False
                imapAccount.save()
                logger.exception(
                    "syncing fails Remove periodic tasks. imap_account not exist %s" % (imapAccount.email))

            except Exception as e:
                logger.exception(
                    "User inbox syncing fails %s. Stop syncing %s" % (imapAccount.email, e))


def loop_sync_user_inbox():

    lockFile = 'loop_sync_user_inbox.lock'
    with open(lockFile, 'w') as f:
        have_lock = get_lock(f)
        if not have_lock:
            logger.info('Lock already taken %s' % lockFile)
            return
         
        logger.info('Loop sync start..')
        imapAccounts = ImapAccount.objects.filter(
            is_initialized=True)  # type: t.List[ImapAccount]
        for imapAccount in imapAccounts:
            imapAccount_email = imapAccount.email

            try:
                logger.info('Start syncing %s ', imapAccount_email)

                # authenticate with the user's imap server
                auth_res = authenticate(imapAccount)
                # if authentication failed we can't run anything
                if not auth_res['status']:
                    # Stop doing loop
                    # TODO maybe we should email the user
                    return

                # get an imapclient which is authenticated
                imap = auth_res['imap']

                # create the mailbox
                try:
                    mailbox = MailBox(imapAccount, imap)
                    # sync the mailbox with imap
                    mailbox._sync()
                except Exception:
                    logger.exception("Mailbox sync failed")
                    # TODO maybe we should email the user
                    continue
                logger.debug("Mailbox sync done: %s" % (imapAccount_email))

                try:
                    res = mailbox._run_user_code()
                except Exception():
                    logger.exception("Mailbox run user code failed")

                if res is not None and res.get('imap_log', ''):
                    imapAccount.execution_log = "%s\n%s" % (
                        res['imap_log'], imapAccount.execution_log)
                    imapAccount.save()

                # after sync, logout to prevent multi-connection issue
                imap.logout()

                logger.info(
                    'Sync done for %s', imapAccount_email)
            except ImapAccount.DoesNotExist:
                imapAccount.is_initialized = False
                imapAccount.save()
                logger.exception(
                    "syncing fails Remove periodic tasks. imap_account not exist %s" % (imapAccount_email))

            except Exception as e:
                logger.exception(
                    "User inbox syncing fails %s. Stop syncing %s" % (imapAccount_email, e))
