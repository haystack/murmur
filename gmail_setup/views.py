import os
import httplib2
import json
import logging

import api
from browser.util import get_groups_links_from_roles
from engine.main import update_blacklist_whitelist, get_or_generate_filter_hash
from gmail_setup.api import create_gmail_filter
from http_handler.settings import BASE_URL, WEBSITE
from schema.models import CredentialsModel, FlowModel, Group

from annoying.decorators import render_to
from apiclient.discovery import build
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.shortcuts import render, render_to_response
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

def build_services(user):
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    credential = storage.get()
    if credential and not credential.invalid:
        http = httplib2.Http()
        http = credential.authorize(http)
        service_people = build('people', 'v1', http=http)
        service_mail = build('gmail', 'v1', http=http)
        return {'mail' : service_mail, 'people' : service_people}

@login_required
@render_to("gmail_setup_start.html")
def index(request):

    user = request.user

    is_done = (request.path_info == '/gmail_setup/done')

    if 'group' not in request.GET:
        return {'group_name': None}

    group_name = request.GET['group']
    forward_address = group_name + '@' + BASE_URL

    services = build_services(user)

    is_authorized = False 
    # Used for Squadbox only:
    gmail_forwarding_verified = False

    if services is not None:
        is_authorized = True
        service_mail = services['mail']
        gmail_forwarding_verified = api.check_forwarding_address(service_mail, forward_address)

    groups = Group.objects.filter(membergroup__member=user).values("name")
    groups_links = get_groups_links_from_roles(user, groups)
    active_group = Group.objects.get(name=group_name)

    return {'website': WEBSITE, 'user': user, 'is_authorized': is_authorized, 'gmail_forwarding_verified': gmail_forwarding_verified, 
        'is_done': is_done, 'group_name': group_name, 'forward_address': forward_address, 'groups' : groups, 'active_group' : active_group,
        'groups_links' : groups_links, 'active_group_role' : 'admin'}

@login_required
def auth(request):
    # use the first REDIRECT_URI if you are developing your app locally, and the second in production
    #REDIRECT_URI = 'http://localhost:8000/gmail_setup/callback'
    REDIRECT_URI = "http://%s%s" % (BASE_URL, reverse("oauth2:return")) 
    #REDIRECT_URI = 'https://' + BASE_URL + '/gmail_setup/callback'
    print "ACCESSING CLIENT SECRETS"
    with open(CLIENT_SECRETS) as json_data:
        d = json.load(json_data)
        print "DATA:", d

    FLOW = flow_from_clientsecrets(
        CLIENT_SECRETS,
        scope='https://www.googleapis.com/auth/contacts.readonly https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.settings.basic',
        redirect_uri=REDIRECT_URI
    )

    FLOW.params['access_type'] = 'offline'

    user = request.user
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    credential = storage.get()
    if not credential or credential.invalid:
        if 'group' in request.GET:
            group_name = request.GET['group']
            FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY, user) + '___' + group_name
            authorize_url = FLOW.step1_get_authorize_url()
            f = FlowModel(id=user, flow=FLOW)
            f.save()
            return HttpResponseRedirect(authorize_url)
        else:
            return HttpResponseRedirect("/gmail_setup")
    else:
        return HttpResponseRedirect("/gmail_setup")
 
@login_required
def auth_return(request):
    user = request.user
    secret = request.REQUEST['state'].split('___')[0]
    group_name = request.REQUEST['state'].split('___')[1]
    if not xsrfutil.validate_token(settings.SECRET_KEY, str(secret), user):
        return HttpResponseBadRequest()
    FLOW = FlowModel.objects.get(id=user).flow
    credential = FLOW.step2_exchange(request.REQUEST)
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    storage.put(credential)
    return HttpResponseRedirect("/gmail_setup?group=" + group_name)

@login_required
def deauth(request):
    user = request.user
    credential = None
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    storage.delete()
    if 'group' in request.GET:
        group_name = request.GET['group']
        return HttpResponseRedirect("authorize?group=" + group_name)
    else:
        return HttpResponseRedirect("authorize")


XML_FILE = """<?xml version='1.0' encoding='UTF-8'?><feed xmlns='http://www.w3.org/2005/Atom' xmlns:apps='http://schemas.google.com/apps/2006'>
    <title>Mail Filters</title>
    <id>tag:mail.google.com,2008:filters:1505317265328,1505323987561</id>
    <updated>2017-09-13T17:44:58Z</updated>
    <entry>
        <category term='filter'></category>
        <title>Mail Filter</title>
        <id>tag:mail.google.com,2008:filter:1505317265328</id>
        <updated>2017-09-13T17:44:58Z</updated>
        <content></content>
        <apps:property name='hasTheWord' value='list:%s@squadbox.csail.mit.edu'/>
        <apps:property name='excludeChats' value='true'/>
        <apps:property name='smartLabelToApply' value='^smartlabel_personal'/>
    </entry>
    <entry>
        <category term='filter'></category>
        <title>Mail Filter</title>
        <id>tag:mail.google.com,2008:filter:1505323987561</id>
        <updated>2017-09-13T17:44:58Z</updated>
        <content></content>
        <apps:property name='doesNotHaveTheWord' value='list:%s@squadbox.csail.mit.edu'/>
        <apps:property name='forwardTo' value='%s@squadbox.csail.mit.edu'/>
        <apps:property name='sizeOperator' value='s_sl'/>
        <apps:property name='sizeUnit' value='s_smb'/>
    </entry>
</feed>"""


@login_required
def initial_filters(request):
    user = request.user
    group_name = request.GET.get('group')
    from schema.models import UserProfile, MemberGroup
    user_email = user.email
    
    u = UserProfile.objects.get(email=user_email)
    mg = MemberGroup.objects.get(member=u, group__name=group_name)
    hash = mg.gmail_filter_hash 
    xml_string = XML_FILE % (hash, hash, group_name)
    
    response = HttpResponse(xml_string, content_type='application/xml')
    response['Content-Disposition'] = 'attachment; filename=gmailfilter.xml'
    return response
    

@login_required
def import_start(request):
    user = request.user
    services = build_services(user)
    service_people = services['people']
    service_mail = services['mail']

    contacts_names_emails = api.parse_contacts(service_people)

    max_frequency = 0
    min_frequency = 0
    frequencies = set()

    sorted_gmail_list = api.parse_gmail(service_mail)
    freq_contacted = {'personal' : [], 'social' : [], 'forums' : [], 'updates' : [], 'promotions' : []}
    if sorted_gmail_list:
        max_frequency = sorted_gmail_list[0][1]
        min_frequency = sorted_gmail_list[-1][1]-1
        for el in sorted_gmail_list:
            freq_contacted[el[3]].append(el)
            frequencies.add(el[1])

    frequency_list = sorted(list(frequencies))

    for cat in freq_contacted:
        freq_contacted[cat].sort(key=lambda c: c[1], reverse=True)
    
    if request.method == 'POST':
        # process submitted form here
        raw_response = request.POST.items()
        emails_to_add = [] 
        group_name = None
        for item in raw_response:
            if item[0] == 'csrfmiddlewaretoken':
                pass
            elif item[0] == 'custom_email_box':
                custom_emails = api.extract_emails_from_csv(item[1])
                for email in custom_emails:
                    if email != '':
                        emails_to_add.append(email)
            elif item[0] == 'group_name':
                group_name = item[1]
            else:
                emails_to_add.append(item[0])

        emails_str = ','.join(emails_to_add)
        res = update_blacklist_whitelist(user, group_name, emails_str, True, False, push=False)

        forward_address = group_name + '@' + BASE_URL

        if WEBSITE == "squadbox":
            filter_hash = get_or_generate_filter_hash(user, group_name, push=False)['hash']
            try:
                api.create_gmail_filter(service_mail, emails_to_add, forward_address, filter_hash)
            except Exception, e:
                logging.error("Exception creating gmail filter - probably hit request limit")
                logging.debug(e)

        return HttpResponseRedirect('/gmail_setup/done?group=' + group_name)
    else:
        # generate form objects for first load here
        group_name = request.GET.get('group')

        groups = Group.objects.filter(membergroup__member=user).values("name")
        groups_links = get_groups_links_from_roles(user, groups)
        active_group = Group.objects.get(name=group_name)
        # TODO: combine multiple email addresses for same contact in contacts view
        return render(request, 'gmail_setup_import.html', {'website': WEBSITE, 'user': user, 
            'contacts_names_emails': contacts_names_emails, 'sorted_gmail_list': sorted_gmail_list, 
            'group_name': group_name, 'max_frequency': max_frequency, 'min_frequency': min_frequency, 
            'frequency_list': frequency_list, 'freq_contacted' : freq_contacted, 'groups': groups, 
            'active_group' : active_group, 'active_group_role' : 'admin', 'groups_links' : groups_links})
