import os
import httplib2
import json

import api
from engine.main import update_blacklist_whitelist
from http_handler.settings import BASE_URL, WEBSITE
from schema.models import CredentialsModel, FlowModel

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

@login_required
@render_to("gmail_setup_start.html")
def index(request):
    is_done = False

    is_done = (request.path_info == '/gmail_setup/done')

    if 'group' not in request.GET:
        return {'group_name': None}

    group_name = request.GET['group']
    forward_address = group_name + '@' + BASE_URL

    user = request.user
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    credential = storage.get()

    is_authorized = False
    # Used for Squadbox only:
    gmail_forwarding_verified = False
    if credential and not credential.invalid:
        is_authorized = True
        http = httplib2.Http()
        http = credential.authorize(http)
        service_mail = build('gmail', 'v1', http=http)
        gmail_forwarding_verified = api.check_forwarding_address(service_mail, forward_address)

    return {'website': WEBSITE, 'user': user, 'is_authorized': is_authorized, 'gmail_forwarding_verified': gmail_forwarding_verified, 'is_done': is_done, 'group_name': group_name, 'forward_address': forward_address}

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

@login_required
def import_start(request):
    user = request.user
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    credential = storage.get()
    http = httplib2.Http()
    http = credential.authorize(http)
    service_people = build('people', 'v1', http=http)
    service_mail = build('gmail', 'v1', http=http)

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

        for email in emails_to_add:
            # add these to whitelist / create form here!
            res = update_blacklist_whitelist(user, group_name, email, True, False)

        forward_address = group_name + '@' + BASE_URL

        if WEBSITE == "squadbox":
            res = api.create_gmail_filter(service_mail, emails_to_add, forward_address, user, group_name)
        return HttpResponseRedirect('/gmail_setup/done?group=' + group_name)
    else:
        # generate form objects for first load here
        group_name = request.GET.get('group', None)
        # TODO: combine multiple email addresses for same contact in contacts view
        return render(request, 'gmail_setup_import.html', {'website': WEBSITE, 'user': user, 'contacts_names_emails': contacts_names_emails, 'sorted_gmail_list': sorted_gmail_list, 'group_name': group_name, 'max_frequency': max_frequency, 'min_frequency': min_frequency, 'frequency_list': frequency_list, 'freq_contacted' : freq_contacted})
