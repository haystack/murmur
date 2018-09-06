import base64, email, hashlib, json, logging, random, re, requests, sys, time

from bleach import clean
from cgi import escape
from datetime import timedelta
from django.utils.timezone import utc
from django.db.models import Q
from email.utils import parseaddr
from html2text import html2text
from lamson.mail import MailResponse
from pytz import utc

from browser.util import *
from browser.imap import *
from constants import *
from engine.google_auth import *
from engine.constants import extract_hash_tags, ALLOWED_MESSAGE_STATUSES
from gmail_setup.api import update_gmail_filter, untrash_message
from gmail_setup.views import build_services
from http_handler.settings import BASE_URL, WEBSITE, AWS_STORAGE_BUCKET_NAME, PERSPECTIVE_KEY, IMAP_SECRET
from s3_storage import upload_attachments, download_attachments, download_message
from schema.models import *
from smtp_handler.utils import *

from Crypto.Cipher import AES
from imapclient import IMAPClient
import string
import random

def list_groups(user=None):
    groups = []
    pub_groups = Group.objects.filter(Q(public=True, active=True)).order_by('name')
    for g in pub_groups:
        admin = False
        mod = False
        member = False
        
        if user != None:
            membergroup = MemberGroup.objects.filter(member=user, group=g)
            if membergroup.count() == 1:
                member = True
                admin = membergroup[0].admin
                mod = membergroup[0].moderator
            
        groups.append({'name':g.name, 
                       'desc': escape(g.description), 
                       'member': member, 
                       'admin': admin, 
                       'mod': mod,
                       'created': g.timestamp,
                       'count': g.membergroup_set.count()
                       })
    return groups

def group_info_page(user, group_name):
    res = {}
    try:
        group = Group.objects.get(name=group_name)

        res['group'] = group
        res['members'] = []
        res['members_pending'] = []
        res['lists'] = []
        res['whitelist'] = []
        res['blacklist'] = []
        res['admin'] = False
        res['moderator'] = False
        res['subscribed'] = False
        res['active'] = group.active

        mg = MemberGroup.objects.get(group=group, member=user)

        res['admin'] = mg.admin
        res['moderator'] = mg.moderator
        res['subscribed'] = True

        if mg.admin:
    
            for m in MemberGroup.objects.filter(group=group):
                res['members'].append({ 'id':m.id,
                                        'email': m.member.email,
                                        'joined': m.timestamp,
                                        'admin': m.admin, 
                                        'mod': m.moderator,
                                    })

            for mp in MemberGroupPending.objects.filter(group=group):
                res['members_pending'].append({ 'id':mp.id,
                                                'email': mp.member.email,
                                                'admin': False,
                                                'mod': False, 
                                            })

            for l in ForwardingList.objects.filter(group=group):
                res['lists'].append({   'id' : l.id,
                                        'email' : l.email,
                                        'can_post' : l.can_post,
                                        'can_receive' : l.can_receive,
                                        'added': l.timestamp,
                                        'url' : l.url,
                                    })

            for w in WhiteOrBlacklist.objects.filter(group=group, whitelist=True):
                res['whitelist'].append({   'id' : w.id, 
                                            'email' : w.email,
                                            'timestamp' : w.timestamp,
                                        })


            for b in WhiteOrBlacklist.objects.filter(group=group, blacklist=True):
                res['blacklist'].append({   'id' : b.id, 
                                            'email' : b.email,
                                            'timestamp' : b.timestamp
                                        })


    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
        res['group'] = None

    except MemberGroup.DoesNotExist:
        if not group.public:
            res['code'] = msg_code['NOT_MEMBER']
            res['group'] = None

    except Exception, e:
        res['code'] = msg_code['UNKNOWN_ERROR']
        logging.debug(e)
    
    return res

def check_admin(user, groups):
    res = []
    try:
        for group in groups:
            group_name = group['name']
            group = Group.objects.get(name=group_name)
            membergroups = MemberGroup.objects.filter(group=group).select_related()
            for membergroup in membergroups:
                admin = membergroup.admin
                if user.email == membergroup.member.email:
                    res.append({'name':group_name, 'admin':admin})

    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def list_my_groups(user):
    res = {'status':False}
    try:
        if WEBSITE == 'murmur':
            membergroup = MemberGroup.objects.filter(member=user, group__active=True).select_related()
        else:
            # still want to show deactivated squads
            membergroup = MemberGroup.objects.filter(member=user).select_related()
        res['status'] = True
        res['groups'] = []
        for mg in membergroup:
            res['groups'].append({'name':mg.group.name, 
                                  'desc': escape(mg.group.description), 
                                  'admin': mg.admin, 
                                  'mod': mg.moderator})
            
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res
    
def edit_members_table(group_name, toDelete, toAdmin, toMod, user):
    res = {'status':False}
    try:
        group = Group.objects.get(name=group_name)
        membergroups = MemberGroup.objects.filter(group=group).select_related()
        toDelete_list = toDelete.split(',')
        toAdmin_list = toAdmin.split(',')
        toMod_list = toMod.split(',')
        toDelete_realList = []
        toAdmin_realList = []
        toMod_realList = []
        for item in toDelete_list:
            if item == '':
                continue
            else:
                toDelete_realList.append(int(item))
        for item in toAdmin_list:
            if item == '':
                continue
            else:
                toAdmin_realList.append(int(item))
        for item in toMod_list:
            if item == '':
                continue
            else:
                toMod_realList.append(int(item))
        def email_on_role_change(type, group, email):
            if type == "delete":
                subject = "removed from the group"
            elif type == "admin":
                subject = "made an admin in group"
            elif type == "mod":
                subject = "made a moderator in group"
            mail = MailResponse(From = NO_REPLY, To = email, Subject = "You've been " + subject + " " + group, Html = "You've been " + subject + " " + group + "<br /><br />To manage your mailing lists, subscribe, or unsubscribe from groups, visit <a href='http://%s/groups'>http://%s/my_groups</a>" % (BASE_URL, BASE_URL))
            relay_mailer.deliver(mail, To = [email])
        for membergroup in membergroups:
            if membergroup.id in toDelete_realList:
                membergroup.delete()
                email_on_role_change("delete", membergroup.group.name, membergroup.member.email)
        for membergroup in membergroups:
            if membergroup.id in toAdmin_realList:
                membergroup.admin = True
                membergroup.save()
                email_on_role_change("admin", membergroup.group.name, membergroup.member.email)
        for membergroup in membergroups:
            if membergroup.id in toMod_realList:
                membergroup.moderator = True
                membergroup.save()
                email_on_role_change("mod", membergroup.group.name, membergroup.member.email)
        res['status'] = True
    except Exception, e:
        print e
        logging.debug(e)
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def edit_donotsend_table(group_name, toDelete, user):
    res = {'status':False}
    try:
        group = Group.objects.get(name=group_name)
        
        toDelete_list = toDelete.split(',')
        toDelete_realList = []
        for item in toDelete_list:
            if item == '':
                continue
            else:
                toDelete_realList.append(int(item))
        for toDelete in toDelete_realList:
            u = UserProfile.objects.filter(id=toDelete)
            donotsend = DoNotSendList.objects.filter(group=group, user=user, donotsend_user=u[0])
            if donotsend.exists():
                donotsend[0].delete()
                break

        res['status'] = True
    except Exception, e:
        print e
        logging.debug(e)
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res


def create_group(group_name, group_desc, public, attach, send_rejected, store_rejected, mod_edit_wl_bl, mod_rules, auto_approve, requester):
    res = {'status':False}
    
    
    if not re.match('^[\w-]+$', group_name) is not None:
        res['code'] = msg_code['INCORRECT_GROUP_NAME']
        return res
    
    if len(group_desc) > MAX_GROUP_DESC_LENGTH:
        res['code'] = msg_code['MAX_GROUP_DESC_LENGTH']
        return res
    
    if len(group_name) > MAX_GROUP_NAME_LENGTH or len(group_name) == 0:
        res['code'] = msg_code['MAX_GROUP_NAME_LENGTH']
        return res
    
    try:
        group = Group.objects.get(name=group_name)
        res['code'] = msg_code['DUPLICATE_ERROR']
        
    except Group.DoesNotExist:
        group = Group(name=group_name, active=True, public=public, allow_attachments=attach, send_rejected_tagged=send_rejected, 
            show_rejected_site=store_rejected, description=group_desc, mod_rules=mod_rules, mod_edit_wl_bl=mod_edit_wl_bl,
            auto_approve_after_first=auto_approve)
        group.save()
        
        is_mod = True
        if WEBSITE == 'squadbox':
            is_mod = False

        membergroup = MemberGroup(group=group, member=requester, admin=True, moderator=is_mod)
        membergroup.save()
        
        res['status'] = True
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
        
    logging.debug(res)
    return res

def edit_group_info(old_group_name, new_group_name, group_desc, public, attach, send_rejected, store_rejected, mod_edit, mod_rules, auto_approve, user):
    res = {'status':False}  
    try:
        group = Group.objects.get(name=old_group_name)
        if len(new_group_name) > 0:
            group.name = new_group_name
        group.description = group_desc
        group.public = public
        group.allow_attachments = attach
        group.send_rejected_tagged = send_rejected
        group.show_rejected_site = store_rejected
        group.mod_edit_wl_bl = mod_edit
        group.mod_rules = mod_rules
        group.auto_approve_after_first = auto_approve
        group.save()
        res['status'] = True    
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def get_group_settings(group_name, user):
    res = {'status':False}
    
    try:
        group = Group.objects.get(name=group_name)
        membergroup = MemberGroup.objects.get(group=group, member=user)
        res['following'] = membergroup.always_follow_thread
        res['no_emails'] = membergroup.no_emails
        res['upvote_emails'] = membergroup.upvote_emails
        res['receive_attachments'] = membergroup.receive_attachments
        res['digest'] = membergroup.digest
        res['status'] = True
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['NOT_MEMBER']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
        
    logging.debug(res)
    return res

def edit_group_settings(group_name, following, upvote_emails, receive_attachments, no_emails, digest, user):
    res = {'status':False}
    
    try:
        group = Group.objects.get(name=group_name)
        membergroup = MemberGroup.objects.get(group=group, member=user)
        membergroup.always_follow_thread = following
        membergroup.upvote_emails = upvote_emails
        membergroup.receive_attachments = receive_attachments
        membergroup.no_emails = no_emails
        membergroup.digest = digest
        membergroup.save()
        
        res['status'] = True
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['NOT_MEMBER']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    
    logging.debug(res)
    return res

def activate_group(group_name, user):
    res = {'status':False}
    try:
        group = Group.objects.get(name=group_name)
        membergroup = MemberGroup.objects.get(group=group, member=user)
        if membergroup.admin:
            group.active = True
            group.save()
            res['status'] = True
        else:
            res['code'] = msg_code['PRIVILEGE_ERROR']
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['NOT_MEMBER']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def deactivate_group(group_name, user):
    res = {'status':False}
    try:
        group = Group.objects.get(name=group_name)
        membergroup = MemberGroup.objects.get(group=group, member=user)
        if membergroup.admin:
            group.active = False
            group.save()
            res['status'] = True
        else:
            res['code'] = msg_code['PRIVILEGE_ERROR']
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['NOT_MEMBER']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def delete_group(group_name, user):
    res = {'status':False}
    try:
        group = Group.objects.get(name=group_name)
        membergroup = MemberGroup.objects.get(group=group, member=user)
        if membergroup.admin:
            group.delete()
            res['status'] = True
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['NOT_MEMBER']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def add_list(group_name, email, can_receive, can_post, list_url, user):

    res = {'status' : False }

    try:
        group = Group.objects.get(name=group_name)
        membergroup = MemberGroup.objects.get(group=group, member=user)

        if membergroup.admin:
            email = email.strip()
            list_url = list_url.strip()
            f = ForwardingList(group=group, email=email, url=list_url, can_receive = can_receive, can_post = can_post)
            f.save()
            res['status'] = True
        else:
            res['code'] = msg_code['PRIVILEGE_ERROR']
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['NOT_MEMBER']
    except Exception, e:
        res['error'] = e
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def delete_list(group_name, emails, user):
    res = {'status' : False}
    try:
        group = Group.objects.get(name=group_name)
        membergroup = MemberGroup.objects.get(group=group, member=user)
        if membergroup.admin:
            for email in emails.split(','):
                f = ForwardingList.objects.get(group=group, email=email)
                f.delete()
            res['status'] = True
        else:
            res['code'] = msg_code['PRIVILEGE_ERROR']
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['NOT_MEMBER']
    except Exception, e:
        res['error'] = e
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def adjust_list_can_post(group_name, emails, can_post, user):
    res = {'status' : False}
    try:
        group = Group.objects.get(name=group_name)
        membergroup = MemberGroup.objects.get(group=group, member=user)
        if membergroup.admin:
            for email in emails.split(','):
                f = ForwardingList.objects.get(group=group, email=email)
                f.can_post = can_post
                f.save()
            res['status'] = True
        else:
            res['code'] = msg_code['PRIVILEGE_ERROR']
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['NOT_MEMBER']
    except Exception, e:
        res['error'] = e
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def adjust_list_can_receive(group_name, emails, can_receive, user):

    res = {'status' : False}
    try:
        group = Group.objects.get(name=group_name)
        membergroup = MemberGroup.objects.get(group=group, member=user)
        if membergroup.admin:
            for email in emails.split(','):
                f = ForwardingList.objects.get(group=group, email=email)
                f.can_receive = can_receive
                f.save()
            res['status'] = True
        else:
            res['code'] = msg_code['PRIVILEGE_ERROR']
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['NOT_MEMBER']
    except Exception, e:
        res['error'] = e
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def add_members(group_name, emails, add_as_mods, user):
    res = {'status':False}
    try:
        group = Group.objects.get(name=group_name)
        is_public = group.public
        is_admin = False
        if user:
            membergroup = MemberGroup.objects.get(group=group, member=user)
            is_admin = membergroup.admin
        if is_public or is_admin:
            email_list = emails.strip().lower().split(',')

            for email in email_list:
                _, email = parseaddr(email)
                email_user = UserProfile.objects.filter(email=email)
                member = False
                if email_user.count() == 1:
                    member = MemberGroup.objects.filter(member=email_user[0], group=group).exists() or MemberGroupPending.objects.filter(member=email_user[0], group=group).exists()
                if not member:
                    confirm_code = hashlib.sha1(email+group_name+str(random.random())).hexdigest()
                    confirm_url = 'http://' + BASE_URL + '/subscribe/confirm/' + confirm_code
                    if WEBSITE == "murmur":
                        mail = MailResponse(From = NO_REPLY, 
                                            To = email, 
                                            Subject  = "You've been invited to join %s Mailing List" % (group_name))
                        
                        if email_user.count() == 1:
                            mg,_ = MemberGroupPending.objects.get_or_create(member=email_user[0], group=group, hash=confirm_code)
                            message = "You've been invited to join %s Mailing List. <br />" % (group_name)
                            message += "To confirm your subscription to this list, visit <a href='%s'>%s</a><br />" % (confirm_url, confirm_url)
                            message += "To see posts from this list, visit <a href='http://%s/posts?group_name=%s'>http://%s/posts?group_name=%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
                            message += "To manage your mailing list settings, subscribe, or unsubscribe, visit <a href='http://%s/groups/%s'>http://%s/groups/%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
                        else:
                            pw = password_generator()
                            new_user = UserProfile.objects.create_user(email, pw)
                            mg,_ = MemberGroupPending.objects.get_or_create(group=group, member=new_user, hash=confirm_code)
                            message = "You've been subscribed to %s Mailing List. <br />" % (group_name)
                            message += "To confirm your subscription to this list, visit <a href='%s'>%s</a><br />" % (confirm_url, confirm_url)
                            message += "An account to manage your settings has been created for you at <a href='http://%s'>http://%s</a><br />" % (BASE_URL, BASE_URL)
                            message += "Your username is your email, which is %s and your auto-generated password is %s <br />" % (email, pw)
                            message += "If you would like to change your password, please log in at the link above and then you can change it under your settings. <br />"
                            message += "To see posts from this list, visit <a href='http://%s/posts?group_name=%s'>http://%s/posts?group_name=%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
                            message += "To manage your mailing lists, subscribe, or unsubscribe from groups, visit <a href='http://%s/groups'>http://%s/my_groups</a><br />" % (BASE_URL, BASE_URL)
        
                        mail.Html = message
                        logging.debug('TO LIST: ' + str(email))
                    elif WEBSITE == "squadbox":
                        mail = MailResponse(From = NO_REPLY, 
                                            To = email, 
                                            Subject  = "You've been invited to join %s squad" % (group_name))
                        
                        if email_user.count() == 1:
                            mg,_ = MemberGroupPending.objects.get_or_create(member=email_user[0], group=group, hash=confirm_code)
                            message = "You've been invited to join %s squad. <br />" % (group_name)
                            message += "To confirm your membership of this squad, visit <a href='%s'>%s</a><br />" % (confirm_url, confirm_url)
                            message += "To see posts for this squad, visit <a href='http://%s/posts?group_name=%s'>http://%s/posts?group_name=%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
                            message += "To manage your squad settings, subscribe, or unsubscribe, visit <a href='http://%s/groups/%s'>http://%s/groups/%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
                        else:
                            pw = password_generator()
                            new_user = UserProfile.objects.create_user(email, pw)
                            mg,_ = MemberGroupPending.objects.get_or_create(group=group, member=new_user, hash=confirm_code)
                            message = "You've been added as a moderator to %s squad. <br />" % (group_name)
                            message += "To confirm your membership of this squad, visit <a href='%s'>%s</a><br />" % (confirm_url, confirm_url)
                            message += "An account to manage your settings has been created for you at <a href='http://%s'>http://%s</a><br />" % (BASE_URL, BASE_URL)
                            message += "Your username is your email, which is %s and your auto-generated password is %s <br />" % (email, pw)
                            message += "If you would like to change your password, please log in at the link above and then you can change it under your settings. <br />"
                            message += "To see posts from this squad, visit <a href='http://%s/posts?group_name=%s'>http://%s/posts?group_name=%s</a><br />" % (BASE_URL, group_name, BASE_URL, group_name)
                            message += "To manage your squads, subscribe, or unsubscribe, visit <a href='http://%s/groups'>http://%s/my_groups</a><br />" % (BASE_URL, BASE_URL)
        
                        mail.Html = message
                        logging.debug('TO LIST: ' + str(email))
                    
                    relay_mailer.deliver(mail, To = [email])
            res['status'] = True
        else:
            res['code'] = msg_code['PRIVILEGE_ERROR']
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['NOT_MEMBER']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def subscribe_group(group_name, user):
    res = {'status':False}

    try:
        membergroup = MemberGroup.objects.filter(group__name=group_name, member=user)
        if membergroup.count() == 1:
            user.active=True
            user.save()
            res['status'] = True
        else:
            group = Group.objects.get(name=group_name)
            _ = MemberGroup.objects.create(group=group, member=user)
            res['status'] = True
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def unsubscribe_group(group_name, user):
    res = {'status':False}
    try:
        group = Group.objects.get(name=group_name)
        membergroup = MemberGroup.objects.get(group=group, member=user)
        membergroup.delete()
        res['status'] = True
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['NOT_MEMBER']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def group_info(group_name, user):
    res = {'status':False}
    try:
        group = Group.objects.get(name=group_name)
        membergroups = MemberGroup.objects.filter(group=group).select_related()
        membergroups_pending = MemberGroupPending.objects.filter(group=group).select_related()
        
        res['status'] = True
        res['group_name'] = group_name
        res['active'] = group.active
        res['public'] = group.public
        res['allow_attachments'] = group.allow_attachments
        res['members'] = []
        res['members_pending'] = []
        for membergroup in membergroups:

            admin = membergroup.admin
            mod = membergroup.moderator
            
            if user.email == membergroup.member.email:
                res['admin'] = admin
                res['moderator'] = mod
                res['subscribed'] = True
            
            member_info = {'id': membergroup.id,
                           'email': membergroup.member.email,
                           'group_name': group_name, 
                           'admin': admin, 
                           'member': True, 
                           'moderator': mod, 
                           'active': membergroup.member.is_active}
            
            res['members'].append(member_info)
        for membergroup in membergroups_pending:
            member_info = {'id': membergroup.id,
                           'email': membergroup.member.email,
                           'group_name': group_name, 
                           'admin': False,
                           'member': True,
                           'moderator': False,
                           'active': membergroup.member.is_active}
            res['members_pending'].append(member_info)

    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR'] 
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def donotsend_info(group_name, user):
    res = {'status':False}
    try:
        group = Group.objects.get(name=group_name)
        donotsends = DoNotSendList.objects.filter(group=group, user=user)

        res['status'] = True
        res['group_name'] = group_name
        res['members'] = []
        for donotsend in donotsends:
            member_info = {'id': donotsend.id,
                           'email': donotsend.donotsend_user.email,
                           'group_name': group_name, 
                           'member': True}
            
            res['members'].append(member_info)

            print "fetch donotsend list", donotsend.donotsend_user.email

    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR'] 
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def format_date_time(d):
    return datetime.strftime(d, '%Y/%m/%d %H:%M:%S')

def list_posts_page(threads, group, res, user=None, format_datetime=True, return_replies=True, text_limit=None, return_full_content=True):
    res['threads'] = []
    for t in threads:
        following = False
        muting = False
        u = None 
        not_include_thread = False

        if user:
            u = UserProfile.objects.get(email=user)
            following = Following.objects.filter(thread=t, user=u).exists()
            muting = Mute.objects.filter(thread=t, user=u).exists()
            
            member_group = MemberGroup.objects.filter(member=u, group=group)
            if member_group.exists():
                res['member_group'] = {'no_emails': member_group[0].no_emails,
                                       'always_follow_thread': member_group[0].always_follow_thread}

        posts = Post.objects.filter(thread = t).select_related()
        replies = []
        post = None
        thread_likes = 0
        for p in posts:
            # if the user is at do-not-send list of the author of the post, stop appending replies
            if user:
                if DoNotSendList.objects.filter(group=group, user=p.author, donotsend_user=u).exists():
                    # if none of post is added yet
                    if len(replies) == 0:
                        not_include_thread = True
                    break 

            post_likes = p.upvote_set.count()
            user_liked = False
            if user:
                user_liked = p.upvote_set.filter(user=u).exists()
            thread_likes += post_likes
            attachments = []

            if return_full_content:
                for attachment in Attachment.objects.filter(msg_id=p.msg_id):
                    url = "attachment/" + attachment.hash_filename
                    attachments.append((attachment.true_filename, url))
            
            #text = clean(p.post, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES)
            text = fix_html_and_img_srcs(p.msg_id, p.post)
            if text_limit:
                text = text[:text_limit]
            
            post_dict = {'id': p.id,
                        'msg_id': p.msg_id, 
                        'thread_id': p.thread_id, 
                        'from': p.author.email if p.author else p.poster_email,
                        'to': p.group.name, 
                        'subject': escape(p.subject),
                        'likes': post_likes, 
                        'liked': user_liked,
                        'text': text if return_full_content else text[:40], 
                        'timestamp': format_date_time(p.timestamp) if format_datetime else p.timestamp,
                        'attachments': attachments,
                        'verified': p.verified_sender
                        }
            if p.forwarding_list:
                post_dict['forwarding_list'] = p.forwarding_list.email
            if not p.reply_to:
                post = post_dict
                # if not return_replies:
                #     break
            else:
                replies.append(post_dict)
        
        if not_include_thread:
            continue
        if not post: # assert the post exists 
            continue
        tags = list(Tag.objects.filter(tagthread__thread=t).values('name', 'color'))
        res['threads'].append({'thread_id': t.id, 
                               'post': post, 
                               'num_replies': len(replies),
                               'replies': replies if return_replies else [], 
                               'following': following, 
                               'muting': muting,
                               'tags': tags,
                               'likes': thread_likes,
                               'timestamp': format_date_time(t.timestamp) if format_datetime else t.timestamp})
        res['status'] = True

def list_posts(group_name=None, user=None, timestamp_str=None, return_replies=True, format_datetime=True, return_full_content=True):
    res = {'status':False}
    try:
        t = datetime.min
        if(timestamp_str):
            t = datetime.strptime(timestamp_str, '%Y/%m/%d %H:%M:%S')
        t = t.replace(tzinfo=utc, second = t.second + 1)
        
        if (group_name != None):
            g = Group.objects.filter(name=group_name)
            threads = Thread.objects.filter(timestamp__gt = t, group = g)
        else:
            threads = Thread.objects.filter(timestamp__gt = t)
        
        list_posts_page(threads, g, res, user=user, format_datetime=format_datetime, return_replies=return_replies, return_full_content=return_full_content)
            
    except Exception, e:
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res
    
def load_thread(t, user=None, member=None):

    following = False
    muting = False
    no_emails = False
    always_follow = False
    is_member = False
    total_likes = 0
    if user:
        following = Following.objects.filter(thread=t, user=user).exists()
        muting = Mute.objects.filter(thread=t, user=user).exists()
        if member:
            is_member = True
            no_emails = member.no_emails
            always_follow = member.always_follow_thread
    
    #if WEBSITE == 'murmur':
    posts = Post.objects.filter(thread = t) 
    # elif WEBSITE == 'squadbox':
    #   posts = Post.objects.filter(thread = t, status='P')

    replies = []
    post = None

    print "postS: ", posts
    
    for p in posts:
        post_likes = p.upvote_set.count()
        total_likes += post_likes
        user_liked = False
        if user:
            user_liked = p.upvote_set.filter(user=user).exists()

        print "attachment at load_thread?"
        attachments = []
        for attachment in Attachment.objects.filter(msg_id=p.msg_id):
            url = "attachment/" + attachment.hash_filename
            attachments.append((attachment.true_filename, url))

        post_dict = {
                    'id': str(p.id),
                    'msg_id': p.msg_id, 
                    'thread_id': p.thread_id, 
                    'from': p.author.email if p.author else p.poster_email,
                    'likes': post_likes,
                    'to': p.group.name,
                    'liked': user_liked,
                    'subject': escape(p.subject), 
                    'text' : fix_html_and_img_srcs(p.msg_id, p.post),
                    'timestamp': format_date_time(p.timestamp),
                    'attachments': attachments,
                    'verified': p.verified_sender,
                    'who_moderated' : p.who_moderated,
                    'mod_explanation' : p.mod_explanation,
                    'perspective_data' : p.perspective_data,
                    }

        if p.forwarding_list:
            post_dict['forwarding_list'] = p.forwarding_list.email

        if WEBSITE == 'murmur':
            if not p.reply_to_id:
                post = post_dict
            else:
                replies.append(post_dict)

        elif WEBSITE == 'squadbox':
            if post is None:
                post = post_dict
            elif post['timestamp'] > post_dict['timestamp']:
                post = post_dict
            else:
                replies.append(post_dict)

    tags = list(Tag.objects.filter(tagthread__thread=t).values('name', 'color'))
    
    return {'status': True,
            'thread_id': t.id, 
            'post': post, 
            'replies': replies, 
            'tags': tags,
            'following': following, 
            'muting': muting,
            'member': is_member,
            'no_emails': no_emails,
            'always_follow': always_follow,
            'likes': total_likes,
            'timestamp': format_date_time(t.timestamp)}

def load_post(group_name, thread_id, msg_id):
    res = {'status':False}
    try:
        t = Thread.objects.get(id=thread_id)
        p = Post.objects.get(msg_id=msg_id, thread=t)
        tags = list(Tag.objects.filter(tagthread__thread=t).values('name', 'color'))
        attachments = []
        for attachment in Attachment.objects.filter(msg_id=p.msg_id):
            url = "attachment/" + attachment.hash_filename
            attachments.append((attachment.true_filename, url))
        res['status'] = True
        res['msg_id'] = p.msg_id
        res['thread_id'] = p.thread_id
        res['from'] = p.email
        res['tags'] = json.dumps(tags)
        res['subject'] = escape(p.subject)
        res['text'] = fix_html_and_img_srcs(p.msg_id, p.post)
        res['to'] = p.group.name
        res['attachments'] = attachments
        res['verified'] = p.verified_sender
        if p.forwarding_list:
            res['forwarding_list'] = p.forwarding_list.email
    except Thread.DoesNotExist:
        res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
    except Post.DoesNotExist:
        res['code'] = msg_code['POST_NOT_FOUND_ERROR']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def delete_post(user, post_id, thread_id):
    res = {'status':False}
    try:
        group = Post.objects.get(id=post_id).group
        membergroup = MemberGroup.objects.get(group=group, member=user)
        if membergroup.admin:
            if thread_id != u'0':
                thread = Thread.objects.get(id=thread_id)
                posts = Post.objects.filter(thread=thread)
                for post in posts:
                    post.delete()
                thread.delete()
                res['status'] = True
            else:
                post = Post.objects.get(id=post_id)
                post.delete()
                res['status'] = True
        else:
            res['code'] = msg_code['PRIVILEGE_ERROR']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def _create_tag(group, thread, name):
    t, created = Tag.objects.get_or_create(group=group, name=name)
    if created:
        r = lambda: random.randint(0,255)
        color = '%02X%02X%02X' % (r(),r(),r())
        t.color = color
        t.save()
    tagthread,_ = TagThread.objects.get_or_create(thread=thread, tag=t)

def _create_post(group, subject, message_text, user, sender_addr, msg_id, verified, attachments=None, forwarding_list=None, post_status=None, sender_name=None):

    try:
        message_text = message_text.decode("utf-8")
    except Exception, _:
        logging.debug("guessing this is unicode then")

    message_text = message_text.encode("ascii", "ignore")
    
    stripped_subj = re.sub("\[.*?\]", "", subject).strip()
    
    thread = Thread()
    thread.subject = stripped_subj
    thread.group = group
    thread.save()

    if post_status == None:
        post_status = 'A'

    if attachments:
        upload_attachments(attachments, msg_id)

    perspective_data = None
    if WEBSITE == 'squadbox':
        res = call_perspective_api(message_text)
        if res['status']:
            del res['status']
            perspective_data = res

    p = Post(msg_id=msg_id, author=user, poster_email = sender_addr, forwarding_list = forwarding_list, 
            subject=stripped_subj, post=message_text, group=group, thread=thread, status=post_status, 
            poster_name=sender_name, verified_sender=verified, perspective_data=perspective_data)
    p.save()
    
    if WEBSITE == 'murmur':
        for match in re.findall(r"[^[]*\[([^]]*)\]", subject):
            if match.lower() != group.name:
                _create_tag(group, thread, match)

        tags = list(extract_hash_tags(message_text))
        for tag in tags:
            if tag.lower() != group.name:
                _create_tag(group, thread, tag)

        tag_objs = Tag.objects.filter(tagthread__thread=thread)
        tags = list(tag_objs.values('name', 'color'))

        group_members = MemberGroup.objects.filter(group=group)
        recipients = []
        for m in group_members:
            # print "create post", user.email
            print "donotsend", m.member.email
            dm = DoNotSendList.objects.filter(group=group, user=user, donotsend_user=m.member)
            if dm.exists():
               continue 
            elif not m.no_emails and m.member.email != sender_addr:
                mute_tag = MuteTag.objects.filter(tag__in=tag_objs, group=group, user=m.member).exists()
                if not mute_tag:
                    recipients.append(m.member.email)
            else:
                follow_tag = FollowTag.objects.filter(tag__in=tag_objs, group=group, user=m.member).exists()
                if follow_tag:
                    recipients.append(m.member.email)
        
        if user:
            recipients.append(user.email)
            f = Following(user=user, thread=thread)
            f.save()

    elif WEBSITE == 'squadbox':
        recipients = []
        tags = None
        tag_objs = None
    
    return p, thread, recipients, tags, tag_objs

def insert_post_web(group_name, subject, message_text, user):
    res = {'status':False}
    thread = None

    try:
        group = Group.objects.get(name=group_name)
        user_member = MemberGroup.objects.filter(group=group, member=user)
        if user_member.exists():
            msg_id = base64.b64encode(user.email + str(datetime.now())).lower() + '@' + BASE_URL
            p, thread, recipients, tags, tag_objs = _create_post(group, subject, message_text, user, user.email, msg_id, verified=True)
            res['status'] = True
            
            res['member_group'] = {'no_emails': user_member[0].no_emails,
                                   'always_follow_thread': user_member[0].always_follow_thread}
    
            post_info = {'msg_id': p.msg_id,
                         'thread_id': thread.id,
                         'from': user.email,
                         'to': group_name,
                         'likes': 0,
                         'liked': False,
                         'subject': escape(p.subject),
                         'text': clean(p.post, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES), 
                         'timestamp': format_date_time(p.timestamp),
                        }

            res['threads'] = []
            res['threads'].append({'thread_id': thread.id,
                                   'post': post_info,
                                   'num_replies': 0,
                                   'replies': [],
                                   'likes': 0,
                                   'following': True,
                                   'muting': False,
                                   'tags': tags,
                                   'timestamp': format_date_time(p.timestamp)})
            res['msg_id'] = p.msg_id
            res['thread_id'] = thread.id
            res['post_id'] = p.id
            res['tags'] = tags
            res['tag_objs'] = tag_objs
            res['recipients'] = recipients

        else:
            res['code'] = msg_code['NOT_MEMBER']
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except Exception, e:
        print e
        logging.debug(e)
        if(thread and thread.id):
            thread.delete()
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res


def insert_post(group_name, subject, message_text, user, sender_addr, msg_id, verified, attachments=None, forwarding_list=None, post_status=None, sender_name=None):
    res = {'status' : False}
    thread = None

    try:
        group = Group.objects.get(name=group_name)
        p, thread, recipients, tags, tag_objs = _create_post(group, subject, message_text, user, sender_addr, msg_id, verified, attachments=attachments, forwarding_list=forwarding_list, post_status=post_status, sender_name=sender_name)
        res['status'] = True
        res['post_id'] = p.id
        res['msg_id'] = p.msg_id
        res['thread_id'] = thread.id
        res['tags'] = tags
        res['tag_objs'] = tag_objs
        res['recipients'] = recipients
        res['verified'] = verified

    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']

    except Exception, e:
        logging.debug(e)
        if(thread and thread.id):
            thread.delete()
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res

def insert_squadbox_reply(group_name, subject, message_text, user, sender_addr, msg_id, verified, attachments=None, post_status=None, sender_name=None):
    res = { 'status' : False }
    try:
        group = Group.objects.get(name=group_name)
        original_subject = subject[4:].strip()
        thread, created = Thread.objects.get_or_create(subject=original_subject, group=group)
        thread_posts = Post.objects.filter(thread=thread).order_by('-timestamp')
        if thread_posts.exists():
            replying_to = thread_posts[0]
        else:
            replying_to = None

        res = call_perspective_api(message_text)
        if res['status']:
            del res['status']
            perspective_data = res
        else:
            perspective_data = None

        post = Post(author=user, subject=subject, msg_id=msg_id, post=message_text, group=group, thread=thread, reply_to=replying_to, verified_sender=verified, poster_email=sender_addr, poster_name=sender_name, status=post_status, perspective_data=perspective_data)
        post.save()
        upload_attachments(attachments, msg_id)
        res['post_id'] = post.id
        res['status'] = True

    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']

    return res


def insert_reply(group_name, subject, message_text, user, sender_addr, msg_id, verified, attachments=None, forwarding_list=None, thread_id=None, post_status=None, sender_name=None):
    res = {'status' : False}

    try:
        group = Group.objects.get(name=group_name)
        group_members = UserProfile.objects.filter(membergroup__group=group)

        if user in group_members or forwarding_list:

            orig_post_subj = subject[4:].strip()
            
            post = Post.objects.filter((Q(subject=orig_post_subj) | Q(subject=subject)) & Q(group=group)).order_by('-timestamp')
            if post.count() >= 1:
                post = post[0]
            else:
                post = None
            
            if not thread_id:
                thread = Thread.objects.filter(subject=orig_post_subj, group=group).order_by('-timestamp')
            else:
                thread = Thread.objects.filter(id=thread_id)

            if thread.count() >= 1:
                thread = thread[0]
            else:
                thread = None

            if not thread:
                thread = Thread()
                thread.subject = orig_post_subj
                thread.group = group
                thread.save()

            if attachments:
                upload_attachments(attachments, msg_id)


            tag_objs = Tag.objects.filter(tagthread__thread=thread)
            try:
                message_text = message_text.decode("utf-8")
            except Exception, e:
                logging.debug("guessing this is unicode then")
            
            message_text = message_text.encode("ascii", "ignore")
            r = Post(msg_id=msg_id, author=user, poster_email = sender_addr, forwarding_list = forwarding_list, 
                subject=subject, post = message_text, reply_to=post, group=group, thread=thread, verified_sender=verified, poster_name=sender_name)
            r.save()
            thread.timestamp = datetime.now().replace(tzinfo=utc)
            thread.save()
            
            if not Following.objects.filter(user=user, thread=thread).exists(): 
                if user:
                    f = Following(user=user, thread=thread)
                    f.save()
                
            member_recip = MemberGroup.objects.filter(group=group, always_follow_thread=True, no_emails=False)
            always_follow_members = [member_group.member.email for member_group in member_recip]
            
            #users that have muted the thread and are set to always follow
            muted = Mute.objects.filter(thread=thread).select_related()
            muted_emails = [m.user.email for m in muted if m.user.email in always_follow_members]
            
            #users following the thread and set to not always follow
            following = Following.objects.filter(thread=thread)
            recipients = [f.user.email for f in following if f.user.email not in always_follow_members]
            
            if tag_objs.count() > 0:
                #users muting the tag and are set to always follow
                muted_tag = MuteTag.objects.filter(group=group, tag__in=tag_objs).select_related()
                muted_emails.extend([m.user.email for m in muted_tag if m.user.email in always_follow_members])

                #users following the tag
                follow_tag = FollowTag.objects.filter(group=group, tag__in=tag_objs).select_related()
                recipients.extend([f.user.email for f in follow_tag if f.user.email not in always_follow_members])

            #users that always follow threads in this group. minus those that muted
            recipients.extend([m.member.email for m in member_recip if m.member.email not in muted_emails])

            dissimulate = DoNotSendList.objects.filter(group=group, user=group_members)
            # remove dissimulated user from the recipient list
            if dissimulate.count() > 0:
                for d in dissimulate:
                    recipients = [recip for recip in recipients if recip != d.donotsend_user.email]

            res['status'] = True
            res['recipients'] = list(set(recipients))
            res['tags'] = []
            res['tags'] = list(tag_objs.values('name'))
            res['tag_objs'] = tag_objs
            res['thread_id'] = thread.id
            res['msg_id'] = msg_id
            res['post_id'] = r.id

        else:
            res['code'] = msg_code['NOT_MEMBER']
        
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']

    except Post.DoesNotExist:
        res['code'] = msg_code['POST_NOT_FOUND_ERROR']

    except:
        logging.debug(sys.exc_info())
        res['code'] = msg_code['UNKNOWN_ERROR']
        
    logging.debug(res)
    return res

def upvote(post_id, email=None, user=None):
    p = Post.objects.get(id=int(post_id))
    membergroup = MemberGroup.objects.get(group=p.group, member=user)
    if membergroup:
        authormembergroup = MemberGroup.objects.get(group=p.group, member=p.author)
    if authormembergroup:
        if authormembergroup.upvote_emails:
            body = "Your post, \"" + p.subject + "\" in group [" + p.group.name + "] was upvoted by " + user.email + ".<br /><br /><hr /><br /> You can turn off these notifications in your <a href=\"http://" + BASE_URL + "/groups/" + p.group.name + "/edit_my_settings\">group settings</a>."
            mail = MailResponse(From = NO_REPLY, To = p.poster_email, Subject = '['+p.group.name+'] Your post was upvoted by '+user.email, Html = body)
            relay_mailer.deliver(mail, To = [p.poster_email])

    res = {'status':False}
    p = None
    try:
        p = Post.objects.get(id=int(post_id))
        if email:
            user = UserProfile.objects.get(email=email)
        l = Upvote.objects.get(post=p, user=user)
        res['status'] = True
        res['thread_id'] = p.thread.id
        res['post_name'] = p.subject
        res['post_id'] = p.id
        res['group_name'] = p.group.name

    except UserProfile.DoesNotExist:
        res['code'] = msg_code['USER_DOES_NOT_EXIST'] % email
    except Upvote.DoesNotExist:
        l = Upvote(post=p, user=user)
        l.save()
        res['status'] = True
        res['thread_id'] = p.thread.id
        res['post_name'] = p.subject
        res['post_id'] = p.id
        res['group_name'] = p.group.name
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def unupvote(post_id, email=None, user=None):
    res = {'status':False}
    p = None
    try:
        if email:
            user = UserProfile.objects.get(email=email)
        p = Post.objects.get(id=int(post_id))
        l = Upvote.objects.get(post=p, user=user)
        l.delete()
        res['status'] = True
        res['post_name'] = p.subject
        res['thread_id'] = p.thread.id
        res['post_id'] = p.id
        res['group_name'] = p.group.name
    except UserProfile.DoesNotExist:
        res['code'] = msg_code['USER_DOES_NOT_EXIST'] % email
    except Upvote.DoesNotExist:
        res['status'] = True
        res['thread_id'] = p.thread.id
        res['post_name'] = p.subject
        res['post_id'] = p.id
        res['group_name'] = p.group.name
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def follow_thread(thread_id, email=None, user=None):
    res = {'status':False}
    t = None
    try:
        if email:
            user = UserProfile.objects.get(email=email)
        t = Thread.objects.get(id=int(thread_id))
        f = Following.objects.get(thread=t, user=user)
        res['status'] = True
        res['thread_name'] = t.subject
        res['thread_id'] = t.id
        res['group_name'] = t.group.name
    except UserProfile.DoesNotExist:
        res['code'] = msg_code['USER_DOES_NOT_EXIST'] % email
    except Following.DoesNotExist:
        f = Following(thread=t, user=user)
        f.save()
        res['status'] = True
        res['thread_name'] = t.subject
        res['thread_id'] = t.id
        res['group_name'] = t.group.name
    except Thread.DoesNotExist:
        res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def unfollow_thread(thread_id, email=None, user=None):
    res = {'status':False}
    try:
        if email:
            user = UserProfile.objects.get(email=email)
        t = Thread.objects.get(id=int(thread_id))
        f = Following.objects.filter(thread=t, user=user)
        f.delete()
        res['status'] = True
        res['thread_name'] = t.subject
        res['thread_id'] = t.id
        res['group_name'] = t.group.name
    except UserProfile.DoesNotExist:
        res['code'] = msg_code['USER_DOES_NOT_EXIST'] % email
    except Following.DoesNotExist:
        res['status'] = True
        res['thread_name'] = t.subject
        res['thread_id'] = t.id
        res['group_name'] = t.group.name
    except Thread.DoesNotExist:
        res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
    except Exception, e:
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def mute_thread(thread_id, email=None, user=None):
    res = {'status':False}
    t = None
    try:
        if email:
            user = UserProfile.objects.get(email=email)
        t = Thread.objects.get(id=int(thread_id))
        f = Mute.objects.get(thread=t, user=user)
        res['status'] = True
        res['thread_name'] = t.subject
        res['thread_id'] = t.id
        res['group_name'] = t.group.name
    except UserProfile.DoesNotExist:
        res['code'] = msg_code['USER_DOES_NOT_EXIST'] % email
    except Mute.DoesNotExist:
        f = Mute(thread=t, user=user)
        f.save()
        res['status'] = True
        res['thread_name'] = t.subject
        res['thread_id'] = t.id
        res['group_name'] = t.group.name
    except Thread.DoesNotExist:
        res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def unmute_thread(thread_id, email=None, user=None):
    res = {'status':False}
    try:
        if email:
            user = UserProfile.objects.get(email=email)
        t = Thread.objects.get(id=int(thread_id))
        f = Mute.objects.filter(thread=t, user=user)
        f.delete()
        res['status'] = True
        res['thread_name'] = t.subject
        res['thread_id'] = t.id
        res['group_name'] = t.group.name
    except UserProfile.DoesNotExist:
        res['code'] = msg_code['USER_DOES_NOT_EXIST'] % email
    except Mute.DoesNotExist:
        res['status'] = True
        res['thread_name'] = t.subject
        res['thread_id'] = t.id
        res['group_name'] = t.group.name
    except Thread.DoesNotExist:
        res['code'] = msg_code['THREAD_NOT_FOUND_ERROR']
    except Exception, e:
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def follow_tag(tag_name, group_name, user=None, email=None):
    res = {'status':False}
    g = Group.objects.get(name=group_name)
    tag = None
    try:
        if email:
            user = UserProfile.objects.get(email=email)
        tag = Tag.objects.get(name=tag_name, group=g)
        tag_follow = FollowTag.objects.get(tag=tag, user=user)
        res['tag_name'] = tag_name
        res['status'] = True
    except FollowTag.DoesNotExist:
        f = FollowTag(tag=tag, group=g, user=user)
        f.save()
        res['tag_name'] = tag_name
        res['status'] = True
    except Tag.DoesNotExist:
        res['code'] = msg_code['TAG_NOT_FOUND_ERROR']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def unfollow_tag(tag_name, group_name, user=None, email=None):
    res = {'status':False}
    g = Group.objects.get(name=group_name)
    tag = None
    try:
        if email:
            user = UserProfile.objects.get(email=email)
        tag = Tag.objects.get(name=tag_name, group=g)
        tag_follow = FollowTag.objects.get(tag=tag, user=user)
        tag_follow.delete()
        res['tag_name'] = tag_name
        res['status'] = True
    except FollowTag.DoesNotExist:
        res['tag_name'] = tag_name
        res['status'] = True
    except Tag.DoesNotExist:
        res['code'] = msg_code['TAG_NOT_FOUND_ERROR']
    except Exception, e:
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def mute_tag(tag_name, group_name, user=None, email=None):
    res = {'status':False}
    g = Group.objects.get(name=group_name)
    tag = None
    try:
        if email:
            user = UserProfile.objects.get(email=email)
        tag = Tag.objects.get(name=tag_name, group=g)
        tag_mute = MuteTag.objects.get(tag=tag, user=user)
        res['tag_name'] = tag_name
        res['status'] = True
    except MuteTag.DoesNotExist:
        f = MuteTag(tag=tag, group=g, user=user)
        f.save()
        res['tag_name'] = tag_name
        res['status'] = True
    except Tag.DoesNotExist:
        res['code'] = msg_code['TAG_NOT_FOUND_ERROR']
    except:
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

def unmute_tag(tag_name, group_name, user=None, email=None):
    res = {'status':False}
    g = Group.objects.get(name=group_name)
    tag = None
    try:
        if email:
            user = UserProfile.objects.get(email=email)
        tag = Tag.objects.get(name=tag_name, group=g)
        tag_mute = MuteTag.objects.get(tag=tag, user=user)
        tag_mute.delete()
        res['tag_name'] = tag_name
        res['status'] = True
    except MuteTag.DoesNotExist:
        res['tag_name'] = tag_name
        res['status'] = True
    except Tag.DoesNotExist:
        res['code'] = msg_code['TAG_NOT_FOUND_ERROR']
    except Exception, e:
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']
    logging.debug(res)
    return res

# add a new entry to do-not-send table, or update existing one
# user is the user who is adding them(we need to make sure they are authorized,
# emaild is a string of comma separated addresses to be do-not-send)
# create a Mute instance for do-not-send person 
def update_donotsend_list(user, group_name, emails, push=True):
    res = {'status' : False}

    try:
        g = Group.objects.get(name=group_name)
        mg = MemberGroup.objects.get(member=user, group=g)

        to_insert = []
        not_added_members = []
        u = UserProfile.objects.filter(email=user)
        u = u[0]
        
        for email in emails.split(','):
            email = email.strip()
            if len(email) == 0:
                continue

            email_user = UserProfile.objects.filter(email=email)
            if user.email == email:
                res['code'] = "You can't add yourself to your do-not-send list <br/>"
                continue

            if email_user.count() == 0:
                # given email is not a member of current group
                # don't add to the DoNotSendList then skip 
                not_added_members.append(email)
                continue

            email_user = email_user[0]
            current = DoNotSendList.objects.filter(group=g, user=u, donotsend_user=email_user)
            if not current.exists():
                entry = DoNotSendList(group=g, user=u, donotsend_user=email_user)
                to_insert.append(entry)

        DoNotSendList.objects.bulk_create(to_insert)

        # if push:
        #   get_or_generate_filter_hash(user, group_name)

        res['status'] = True
        res['group_name'] = group_name
        res['emails'] = emails
        if len(not_added_members) > 0:
            if not 'code' in res:
                res['code'] = ''
            res['code'] += msg_code['NOT_MEMBERS'] % ", ".join(not_added_members)

    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']

    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['PRIVILEGE_ERROR']

    except Exception, e:
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res 

def login_imap(user, password, host, is_oauth, push=True):
    res = {'status' : False}

    try:
        imap = IMAPClient(host, use_uid=True)
        email = user.email

        refresh_token = ''
        access_token = ''
        password_original = password
        if is_oauth:
            # TODO If this imap account is already mapped with this account, by pass the login. 
            oauth = GoogleOauth2()
            response = oauth.generate_oauth2_token(password)
            refresh_token = response['refresh_token']
            access_token = response['access_token']

            imap.oauth2_login(email, access_token)

        else:   
            imap.login(email, password)
             
            #encrypt password then save
            aes = AES.new(IMAP_SECRET, AES.MODE_CBC, 'This is an IV456')

            # padding password
            padding = random.choice(string.letters)
            while padding == password[-1]:
                padding = random.choice(string.letters)
                continue
            extra = len(password) % 16
            if extra > 0:
                password = password + (padding * (16 - extra))
            password = aes.encrypt(password)

        # Log out after auth verification
        imap.logout()

        imapAccount = ImapAccount.objects.filter(email=email)
        if not imapAccount.exists():
            imapAccount = ImapAccount(email=email, password=base64.b64encode(password), host=host)
            imapAccount.host = host
            if is_oauth:
                imapAccount.is_oauth = is_oauth
                imapAccount.access_token = access_token
                imapAccount.refresh_token = refresh_token

            imapAccount.save()

            # = imapAccount
        else:
            imapAccount = imapAccount[0]
            res['imap_code'] = imapAccount.code
            res['imap_log'] = imapAccount.execution_log

        

        # u = UserProfile.objects.filter(email=email)
        # if not u.exists():
        #     u = UserProfile.objects.create_user(email, password_original)

        #     res['code'] = "New user"
        # else:
        #     res['code'] = "This account is already logged in!"

        #     # if user has source code running, send it
        #     u = u[0]
        #     imapAccount = u
        #     res['imap_code'] = imapAccount.code
        
        # u.host = host
        # u.imap_password = password

        # u.save()

        res['status'] = True

    except IMAPClient.Error, e:
        res['code'] = e

    except Exception, e:
        # TODO add exception
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res 

def fetch_execution_log(user, email, push=True):
    res = {'status' : False}

    try:
        imapAccount = ImapAccount.objects.get(email=email)
        res['imap_log'] = imapAccount.execution_log

        res['status'] = True

    except ImapAccount.DoesNotExist:
        res['code'] = "Error during authentication. Please refresh"
    except Exception, e:
        # TODO add exception
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res 

def delete_mailbot_mode(user, email, mode_id, push=True):
    res = {'status' : False}

    try:
        imapAccount = ImapAccount.objects.get(email=email)
        mm = MailbotMode.objects.get(uid=mode_id, imap_acoount=imapAccount)

        if imapAccount.current_mode == mm:
            imapAccount.current_mode = None
            imapAccount.is_running = False

        mm.delete()        

        res['status'] = True

    except ImapAccount.DoesNotExist:
        res['code'] = "Error during deleting the mode. Please refresh the page."
    except MailbotMode.DoesNotExist:
        res['code'] = "Error during deleting the mode. Please refresh the page."
    except Exception, e:
        # TODO add exception
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res 

def run_mailbot(user, email, current_mode_id, modes, is_test, is_running, push=True):
    res = {'status' : False, 'imap_error': False}

    try:
        imapAccount = ImapAccount.objects.get(email=email)
        auth_res = authenticate( imapAccount )
        if not auth_res['status']:
            raise ValueError('Something went wrong during authentication. Refresh and try again!')

        imap = auth_res['imap']

        imapAccount.is_test = is_test
        imapAccount.is_running = is_running

        uid = fetch_latest_email_id(imapAccount, imap)
        imapAccount.newest_msg_id = uid

        for key, value in modes.iteritems():
            mode_id = value['id']
            mode_name = value['name']
            code = value['code']
            print value['id']
            print value['name']
            print value['code']
        
            mailbotMode = MailbotMode.objects.filter(uid=mode_id, imap_acoount=imapAccount)
            if not mailbotMode.exists():
                mailbotMode = MailbotMode(uid=mode_id, name=mode_name, code=code, imap_acoount=imapAccount)
                mailbotMode.save()
            else:
                mailbotMode = mailbotMode[0]
                mailbotMode.code = code

        imapAccount.current_mode = MailbotMode.objects.filter(uid=current_mode_id, imap_acoount=imapAccount)[0]
        imapAccount.save()

        if imapAccount.is_running:
            res = interpret(imapAccount, imap, code, "UID %d" % uid, is_test)

            # if the code execute well without any bug, then save the code to DB
            if not res['imap_error']:
                res['imap_log'] = ("[TEST MODE] Your rule is successfully installed. It won't take actual action but simulate your rule. \n" + res['imap_log']) if is_test else ("Your rule is successfully installed. \n" + res['imap_log']) 
                now = datetime.now()
                now_format = now.strftime("%m/%d/%Y %H:%M:%S") + " "
                res['imap_log'] = now_format + res['imap_log']
            else:
                imapAccount.is_running = False
                imapAccount.save()
        else:

            res['imap_log'] = "Your mailbot stops running"

        res['status'] = True
            

    except IMAPClient.Error, e:
        res['code'] = e
    except ImapAccount.DoesNotExist:
        res['code'] = "Not logged into IMAP"
    except Exception, e:
        # TODO add exception
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res 

# add a new entry to whitelist/blacklist table, or update existing one
# user is the user who is adding them(we need to make sure they are authorized,
# emaild is a string of comma separated addresses to be blacklisted/whitelisted)
def update_blacklist_whitelist(user, group_name, emails, whitelist, blacklist, push=True):
    res = {'status' : False}

    # illegal to have both set to true
    if whitelist and blacklist:
        res['code'] = msg_code['REQUEST_ERROR']
        logging.debug("Both whitelist and blacklist cannot be true")
        logging.debug(res)
        return res

    try:
        g = Group.objects.get(name=group_name)
        # if mods can edit wl/bl, check for admin OR mod. if not, just admin. 
        if g.mod_edit_wl_bl:
            mg = MemberGroup.objects.get(Q(member=user, group=g), Q(admin=True) | Q(moderator=True))
        else:
            mg = MemberGroup.objects.get(member=user, group=g, admin=True)

        to_insert = []

        for email in emails.split(','):
            email = email.strip()
            current = WhiteOrBlacklist.objects.filter(group=g, email=email)
            if current.exists():
                entry = current[0]
                entry.whitelist = whitelist
                entry.blacklist = blacklist
                entry.save()
            else:
                entry = WhiteOrBlacklist(group=g, email=email, whitelist=whitelist, blacklist=blacklist)
                to_insert.append(entry)

        WhiteOrBlacklist.objects.bulk_create(to_insert)

        # if push:
        #   get_or_generate_filter_hash(user, group_name)

        res['status'] = True
        res['group_name'] = group_name
        res['emails'] = emails
        res['email_whitelisted'] = whitelist
        res['email_blacklisted'] = blacklist

    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']

    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['PRIVILEGE_ERROR']

    except Exception, e:
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res 

def update_post_status(user, group_name, post_id, new_status, explanation=None, tags=None):
    res = {'status' : False}

    try:
        p = Post.objects.get(id=post_id)
        g = Group.objects.get(name=group_name)
        
        # only admins or moderators of a group can change post statuses
        mg = MemberGroup.objects.get(Q(admin=True) | Q(moderator=True), member=user, group=g)

        if new_status not in ALLOWED_MESSAGE_STATUSES:
            res['code'] = msg_code['INVALID_STATUS_ERROR'] % new_status
        else:
            p.status = new_status
            p.who_moderated = user

            if explanation is not None:
                p.mod_explanation = explanation

            group_tag_names = [t.tag.name for t in TagThread.objects.filter(thread=p.thread)]

            if tags and len(tags) > 0:
                tag_names = tags.split(',')
                for t in tag_names:
                    if t not in group_tag_names:
                        _create_tag(g, p.thread, t)

            if new_status == 'R' and 'rejected' not in group_tag_names:
                _create_tag(g, p.thread, 'rejected')

            p.save()

            res['status'] = True
            res['post_id'] = post_id
            res['new_status'] = new_status

            # now send message on to the intended recipient if it was approved,
            # or if it was rejected but the recipient wants rejected emails with tag
            if new_status == 'A' or (new_status == 'R' and g.send_rejected_tagged):


                mgs = MemberGroup.objects.filter(group=g, admin=True)
                if not mgs.exists():
                    return res
                else: 
                    admin = mgs[0].member

                if new_status == 'A':
                    reason = 'moderator approved'
                    if not check_if_sender_moderated_for_thread(g.name, p.poster_email, p.subject):
                        if g.auto_approve_after_first:
                            hashed = get_sender_subject_hash(p.poster_email, p.subject)
                            ThreadHash.objects.get_or_create(sender_subject_hash=hashed, group=g, moderate=False)

                    try:
                        mail_service = build_services(admin)['mail']
                        logging.debug("MAIL SERVICE:", mail_service)
                        updated_count = untrash_message(mail_service, p.poster_email, p.subject)
                        if updated_count > 0:
                            logging.error("untrashed count: %s" % updated_count)
                            logging.debug(res)
                            return res 
                    except Exception, e:
                        logging.error(e)
                        pass

                elif new_status == 'R':
                    reason = 'moderator rejected'

                tags = [t.tag.name for t in TagThread.objects.filter(thread = p.thread)]

                subject_tags = ''
                for t in tags:
                    subject_tags += '[%s]' % t

                new_subj = subject_tags + ' ' + p.subject

                mail = MailResponse(From = 'no_reply@%s' % HOST, To = admin.email, Subject = '%s: %s' % (p.poster_email, new_subj))
                mail['message-id'] = p.msg_id
                mail['reply-to'] = p.poster_email

                res = download_message(p.id, p.msg_id)
                if not res['status']:
                    logging.error("Error downloading original message")
                else:
                    original_msg = email.message_from_string(res['message'])
                    mail['In-Reply-To'] = original_msg['In-Reply-To']
                    mail['References'] = original_msg['References']
                    mail['Cc'] = original_msg['Cc']

                attachments = download_attachments(p.msg_id)
                for a in attachments:
                    mail.attach(filename=a['name'], data=a['data'])

                orig_subj = p.subject
                if orig_subj.startswith('Re: '):
                    orig_subj = orig_subj[4:]       

                # html_blurb = unicode(ps_squadbox(p.poster_email, reason, group_name, g.auto_approve_after_first, orig_subj, p.who_moderated.email, True))
                # plain_blurb = ps_squadbox(p.poster_email, reason, group_name, g.auto_approve_after_first, orig_subj, p.who_moderated.email, False)
                html_blurb = ''
                plain_blurb = ''

                html_prefix = ''
                if new_status == 'R' and len(p.mod_explanation) > 0:
                    html_prefix = "<p><b>Moderator explanation for rejection</b>: %s </p><b>Message text</b>:<br>" % p.mod_explanation

                message_text = {'html' : html_prefix + p.post}
                message_text['plain'] = html2text(html_prefix + p.post)
                mail.Html = get_new_body(message_text, html_blurb, 'html')
                mail.Body = get_new_body(message_text, plain_blurb, 'plain')

                res = get_or_generate_filter_hash(admin, group_name)
                if res['status']:
                    mail['List-Id'] = '%s@%s' % (res['hash'], BASE_URL)
                else:
                    logging.error("Error getting/generating filter hash")


                relay_mailer.deliver(mail, To = admin.email)

    except Post.DoesNotExist:
        res['code'] = msg_code['POST_NOT_FOUND_ERROR']

    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']

    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['PRIVILEGE_ERROR']

    except Exception, e:
        print e
        res['code'] = msg_code['UNKNOWN_ERROR']

    logging.debug(res)
    return res 

def load_pending_posts(user, group_name):
    res = {'status' : False}
    try:
        mg = MemberGroup.objects.get(member=user, group__name=group_name)
        posts = Post.objects.filter(group__name=group_name, status='P')
        posts_cleaned = fix_posts(posts)
        print "here"
        grouped = group_by_thread(posts_cleaned)
        res['threads'] = grouped
        res['status'] = True

    except MemberGroup.DoesNotExist:
        logging.debug(e)
        res['status'] = False
        res['code'] = msg_code['NOT_MEMBER']
        res['error'] = e

    except Exception, e:
        logging.debug(e)
        res['status'] = False
        res['code'] = msg_code['UNKNOWN_ERROR']
        res['error'] = e

    print "res:!!!!", res
    return res

def load_rejected_posts(user, group_name):
    res = {'status' : False}
    try:
        group = Group.objects.get(name=group_name)
        mg = MemberGroup.objects.get(member=user, group=group)
        if mg.admin or mg.moderator:
            rejected_posts = Post.objects.filter(group=group, status='R')
            res['posts'] = fix_posts(rejected_posts)
            res['group'] = group
            res['status'] = True
        else:
            res['code'] = msg_code['PRIVILEGE_ERROR']
    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']
    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['PRIVILEGE_ERROR']
    except Exception, e:
        logging.debug(e)
        res['code'] = msg_code['UNKNOWN_ERROR']
        res['error'] = e

    return res

def fix_posts(post_queryset):
    posts_fixed = []
    for p in post_queryset:
        post_dict = {'id': str(p.id),
                    'msg_id': p.msg_id, 
                    'from': p.author.email if p.author else p.poster_email,
                    'from_name' : p.poster_name,
                    'to': p.group.name, 
                    'subject': escape(p.subject),
                    'text': html2text(p.post),
                    'thread_id' : p.thread.id, 
                    'timestamp': p.timestamp,
                    'verified': p.verified_sender,
                    'who_moderated' : p.who_moderated,
                    'mod_explanation' : p.mod_explanation,
                    'perspective_data' : p.perspective_data,
                    }
        posts_fixed.append(post_dict)

    return posts_fixed

def group_by_thread(posts_list):
    threads = {}
    for p in posts_list:
        tid = p['thread_id']
        threads[tid] = threads.get(tid, []) + [p]

    thread_data = []
    for t in threads:
        posts = threads[t]

        senders = set()
        for p in posts:
            if p['from_name']:
                name = p['from_name']
                if not isinstance(name, unicode):
                    name = unicode(name, 'utf-8', 'ignore')

                senders.add(name)
            else:
                sender = p['from']
                if not isinstance(sender, unicode):
                    sender = unicode(name, 'utf-8', 'ignore')

                senders.add(sender)

        thread = {
            'id' : t,
            'num_posts' : len(posts),
            'first_timestamp' : posts[0]['timestamp'],
            'first_text' : posts[0]['text'],
            'subject' : posts[0]['subject'],
            'senders' : ', '.join(list(senders)),
        }

        thread_data.append(thread)

    return thread_data

def adjust_moderate_user_for_thread(user, group_name, sender_addr, subject, moderate):

    res = {'status' : False}
    try:
        g = Group.objects.get(name=group_name)
        mg = MemberGroup.objects.get(member=user, group=g)
        if not mg.admin:
            res['code'] = msg_code['PRIVILEGE_ERROR']
        else:
            hashed = get_sender_subject_hash(sender_addr, subject)
            th, _ = ThreadHash.objects.get_or_create(group=g, sender_subject_hash=hashed)
            th.moderate = moderate
            th.save()
            res['status'] = True

    except Group.DoesNotExist:
        res['code'] = msg_code['GROUP_NOT_FOUND_ERROR']

    except MemberGroup.DoesNotExist:
        res['code'] = msg_code['NOT_MEMBER']

    return res

# push - whether to call gmail api and update filter there
# we want to do that every time *except* when we call this during setup. 
# call this function whenever whitelist is changed
def get_or_generate_filter_hash(user, group_name, push=True):
    res = {'status' : False }
    try:
        mg = MemberGroup.objects.get(member=user, group__name=group_name)
        now = datetime.now(utc)
        last_update = mg.last_updated_hash

        if mg.gmail_filter_hash is None: #or now - last_update >  timedelta(hours=24):

            salt = hashlib.sha1(str(random.random())+str(time.time())).hexdigest()
            new_hash = hashlib.sha1(user.email + group_name + salt).hexdigest()[:20]    
            
            mg.gmail_filter_hash = new_hash
            mg.last_updated_hash = now 
            mg.save()
            res['hash'] = new_hash
 
        else:
            res['hash'] = mg.gmail_filter_hash

        # if push:
        #   whitelist_emails = [w.email for w in WhiteOrBlacklist.objects.filter(group__name=group_name, whitelist=True)]
        #   update_gmail_filter(user, group_name, whitelist_emails, res['hash'])

        res['status'] = True

    except MemberGroup.DoesNotExist:
        res['error'] = 'Member group does not exist'

    return res

def call_perspective_api(text):
    res = { 'status' : False }

    # API currently only accepts plaintext  
    text = html2text(text)

    path = ' https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key=%s' % PERSPECTIVE_KEY

    request = {
        'comment' : {'text' : text },
        'requestedAttributes' : {
                                'TOXICITY' : {},
                                # all of these are experimental and
                                # might not be that useful yet 
                                'OBSCENE' : {},
                                'ATTACK_ON_COMMENTER' : {},
                                'INFLAMMATORY' : {},
                                },
        'doNotStore' : True, # don't store text of msg
    }

    response = requests.post(path, json=request)

    if response.status_code == 200:

        data = json.loads(response.text)
        scores_simplified = {}
        spans_simplified = {}
        attribute_scores = data['attributeScores']

        for attr, data in attribute_scores.iteritems():
            if attr == 'ATTACK_ON_COMMENTER':
                attr = 'ATTACK'
            summary = data['summaryScore']
            prob = summary['value']
            scores_simplified[attr] = prob

            spans = data.get('spanScores')
            if spans:
                span_list = []
                for s in spans:
                    span_data = {
                        'start' : s['begin'],
                        'end' : s['end'],
                        'score' : s['score']['value'],
                    }

                    span_list.append(span_data)

                spans_simplified[attr] = span_list

        res['scores'] = scores_simplified
        res['spans'] = spans_simplified
        res['status'] = True

    return res




