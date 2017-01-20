import re

def parse_contacts(service_people):
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


def parse_gmail(service_mail):
    mail_response = service_mail.users().messages().list(userId='me', q='from:me').execute()
    messages = mail_response['messages']
    for message in messages:
        message = service_mail.users().messages().get(userId='me', id=message['id']).execute()
        for pair in message['payload']['headers']:
            if pair["name"] == "To":
                emailstring = pair["value"].encode('UTF-8')
                emails = re.findall(r'[\w\.-]+@[\w\.-]+', emailstring)
                for email in emails:
                    print email