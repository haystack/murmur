import os
import httplib2
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage

from apiclient.discovery import build

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.contrib.sites.models import get_current_site
from annoying.decorators import render_to

from engine.main import update_blacklist_whitelist

from .models import CredentialsModel, FlowModel
import api

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
FORWARD_ADDRESS = 'squadbox@dunkley.me'

@login_required
@render_to("gmail_setup_start.html")
def index(request):
    is_done = False
    if request.path_info == '/gmail_setup/done':
        is_done = True

    user = request.user
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    credential = storage.get()
    http = httplib2.Http()
    http = credential.authorize(http)

    is_authorized = False
    if credential is None or credential.invalid is True:
        pass
    else:
        is_authorized = True
    
    service_mail = build('gmail', 'v1', http=http)
    gmail_forwarding_verified = api.check_forwarding_address(service_mail, FORWARD_ADDRESS)

    return {'is_authorized': is_authorized, 'gmail_forwarding_verified': gmail_forwarding_verified, 'is_done': is_done}

@login_required
def auth(request):
    # use the first REDIRECT_URI if you are developing your app locally, and the second in production
    REDIRECT_URI = 'http://localhost:8000/gmail_setup/callback'
    #REDIRECT_URI = "https://%s%s" % (get_current_site(request).domain, reverse("oauth2:return"))
    FLOW = flow_from_clientsecrets(
        CLIENT_SECRETS,
        scope='https://www.googleapis.com/auth/contacts.readonly https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.settings.basic https://www.googleapis.com/auth/gmail.settings.sharing',
        redirect_uri=REDIRECT_URI
    )
    user = request.user
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid is True:
        FLOW.params['state'] = xsrfutil.generate_token(
            settings.SECRET_KEY, user)
        authorize_url = FLOW.step1_get_authorize_url()
        f = FlowModel(id=user, flow=FLOW)
        f.save()
        return HttpResponseRedirect(authorize_url)
    else:
        return HttpResponseRedirect("/gmail_setup")
 
@login_required
def auth_return(request):
    user = request.user
    if not xsrfutil.validate_token(settings.SECRET_KEY, str(request.REQUEST['state']), user):
        return HttpResponseBadRequest()
    FLOW = FlowModel.objects.get(id=user).flow
    credential = FLOW.step2_exchange(request.REQUEST)
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    storage.put(credential)
    return HttpResponseRedirect("/gmail_setup")

@login_required
def import_start(request):
    user = request.user
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    credential = storage.get()
    http = httplib2.Http()
    http = credential.authorize(http)
    service_people = build('people', 'v1', http=http)
    service_mail = build('gmail', 'v1', http=http)

    contacts_emails = api.parse_contacts(service_people)
    gmail_emails = api.parse_gmail(service_mail)

    all_emails = set()
    if contacts_emails:
        all_emails.update(set(contacts_emails))
    if gmail_emails:
        all_emails.update(set(gmail_emails))
    
    print request

    if request.method == 'POST':
        # process submitted form here
        emails_to_add = [i[0] for i in request.POST.items()[1:]]
        group_name = request.GET.get('group_name')
        print "GROUP NAME:", group_name
        for email in emails_to_add:
            print(email)
            # add these to whitelist / create form here!
            res = update_blacklist_whitelist(user=user, group_name=group_name, email=email, whitelist=True, blacklist=False)
            print(res)
        res = api.create_gmail_filter(service_mail, emails_to_add, FORWARD_ADDRESS)
        return HttpResponseRedirect('/gmail_setup/done')
    else:
        # generate form objects for first load here
        return render(request, 'gmail_setup_import.html', {'contacts_emails': contacts_emails, 'gmail_emails': gmail_emails})