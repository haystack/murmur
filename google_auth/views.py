import os
import httplib2
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from oauth2client.django_orm import Storage
 
from apiclient.discovery import build
 
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.contrib.sites.models import get_current_site
 
from .models import CredentialsModel, FlowModel
 
CLIENT_SECRETS = os.path.join(
    os.path.dirname(__file__), 'client_secrets.json')
 
@login_required
def index(request):
    # use the first REDIRECT_URI if you are developing your app
    # locally, and the second in production
    REDIRECT_URI = 'http://localhost:8000/google_auth/callback'
    #REDIRECT_URI = "https://%s%s" % (get_current_site(request).domain, reverse("oauth2:return"))
    FLOW = flow_from_clientsecrets(
        CLIENT_SECRETS,
        scope='https://www.googleapis.com/auth/contacts.readonly https://www.googleapis.com/auth/gmail.readonly',
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
        print "waiting for callback..."
        return HttpResponseRedirect(authorize_url)
    else:
        http = httplib2.Http()
        http = credential.authorize(http)
        service_people = build('people', 'v1', http=http)
        
        response = None

        pageToken = ""
        while pageToken != None:
            response = service_people.people().connections().list(resourceName='people/me',pageSize=500,requestMask_includeField="person.email_addresses", pageToken=pageToken).execute()
            for person in response["connections"]:
                if "emailAddresses" in person:
                    for email in person["emailAddresses"]:
                        print email["value"]
            if "nextPageToken" in response:
                pageToken = response["nextPageToken"]
            else:
                pageToken = None

        service_mail = build('gmail', 'v1', http=http)
        mail_response = service_mail.users().messages().list(userId='me', q='from:me').execute()
        messages = mail_response['messages']
        for message in messages:
            message = service_mail.users().messages().get(userId='me', id=message['id']).execute()
            for pair in message['payload']['headers']:
                if pair["name"] == "To":
                    print pair["value"].encode('UTF-8')
                    nameandemail = pair["value"].encode('UTF-8').split('<')
                    #name = nameandemail[0]
                    #email = nameandemail[1]
                    #print name, email

        return render(request, 'google_auth.html', {'contacts':response})
 
 
@login_required
def auth_return(request):
    user = request.user
    if not xsrfutil.validate_token(settings.SECRET_KEY, str(request.REQUEST['state']), user):
        print "token not validated"
        return HttpResponseBadRequest()
    FLOW = FlowModel.objects.get(id=user).flow
    credential = FLOW.step2_exchange(request.REQUEST)
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    storage.put(credential)
    return HttpResponseRedirect("/google_auth")