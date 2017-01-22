import re
import time

def parse_contacts(service_people):
    emails = []
    page_token = ""
    while page_token != None:
        response = service_people.people().connections().list(resourceName='people/me', pageSize=500, requestMask_includeField="person.email_addresses", pageToken=page_token).execute()
        for person in response["connections"]:
            if "emailAddresses" in person:
                for email in person["emailAddresses"]:
                    #print email["value"]
                    emails.append(email["value"])
        if "nextPageToken" in response:
            page_token = response["nextPageToken"]
        else:
            page_token = None
    return emails


def parse_gmail(service_mail):
    email_dict = dict()
    page_token = ""
    current_time = time.time()*1000
    time_back = 3.154e+10 # get messages from the last year
    time_not_over = True
    ans = None
    while (page_token != None) and time_not_over:
        response = service_mail.users().messages().list(userId='me', q='from:me !in:draft', pageToken=page_token, maxResults=100).execute()
        if 'messages' in response:
            messages = response['messages']
            for message in messages:
                message = service_mail.users().messages().get(userId='me', id=message['id']).execute()
                if int(message["internalDate"]) < int(current_time - time_back):
                    time_not_over = False
                    break
                for pair in message['payload']['headers']:
                    if pair["name"] == "To":
                        emailstring = pair["value"].encode('UTF-8')
                        emails = re.findall(r'[\w\.-]+@[\w\.-]+', emailstring)
                        for email in emails:
                            if email in email_dict:
                                email_dict[email] += 1
                            else:
                                email_dict[email] = 1
            if "nextPageToken" in response:
                page_token = response["nextPageToken"]
            else:
                page_token = None
        else:
            page_token = None
    sorted(email_dict, key=email_dict.get, reverse=True)
    return ans

def get_google_emails(service_people, service_mail):
    contacts = parse_contacts(service_people)
    emails = parse_gmail(service_mail)
    return list(set(contacts).union(set(emails)))

def create_gmail_filter(service_mail, whitelist_emails, forward_address):
    response = service_mail.users().settings().filters().list(userId='me').execute()
    if 'filter' in response:
        existing_filters = response['filter']
        for filter in existing_filters:
            if 'forward' in filter['action']:
                if filter['action']['forward'] == forward_address:
                    service_mail.users().settings().filters().delete(userId='me', id=filter['id']).execute()
    email_list_piped = "|".join(whitelist_emails)
    filter = {
        'criteria': {
            'from': email_list_piped
        },
        'action': {
            'removeLabelIds': ['INBOX'],
            'forward': forward_address
        }
    }
    result = service_mail.users().settings().filters().create(userId='me', body=filter).execute()
    return result

def add_to_whitelist(emails):
    return

def check_forwarding_address(service_mail, forward_address):
    result = service_mail.users().settings().forwardingAddresses().list(userId='me').execute()
    for item in result['forwardingAddresses']:
        if item['forwardingEmail'] == forward_address:
            return item['verificationStatus']
    return False