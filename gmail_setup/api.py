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
                    emails.append(email["value"])
        if "nextPageToken" in response:
            page_token = response["nextPageToken"]
        else:
            page_token = None
    return emails

def parse_gmail(service_mail):
    email_dict = dict()
    received_dict = dict()
    received_list = []
    frequency_dict = dict()
    page_token = ""
    current_time = time.time()*1000
    time_back = 3.154e+10 # get messages from the last year
    time_back = 2e+9 # shorter time for testing, TODO delete this line
    time_not_over = True
    ans = None

    def batch_cb(request_id, response, exception):
        message = response
        list_message_object = {}
        batch_cb.stop = False
        if int(message["internalDate"]) < int(current_time - time_back):
            batch_cb.stop = True
            return
        for pair in message['payload']['headers']:
            if pair["name"] == "From":
                emailstring = pair["value"].encode('UTF-8')
                list_message_object['email'] = re.findall(r'[\w\.-]+@[\w\.-]+', emailstring)[0]
                name = emailstring.split('<')[0].strip()
                if name.startswith('"') and name.endswith('"'):
                    name = name[1:-1]
                list_message_object['name'] = name
        list_message_object['label'] = None
        for label in message['labelIds']:
            if label == "CATEGORY_PERSONAL": list_message_object['label'] = 'personal'
            if label == "CATEGORY_SOCIAL": list_message_object['label'] = 'social'
            if label == "CATEGORY_PROMOTIONS": list_message_object['label'] = 'promotions'
            if label == "CATEGORY_UPDATES": list_message_object['label'] = 'updates'
            if label == "CATEGORY_FORUMS": list_message_object['label'] = 'forums'
        # TODO: labels at the moment are only decided based on most recent email; change to be mode
        if list_message_object['label'] != None:
            received_list.append(list_message_object)

    # receieved:
    while (page_token != None) and time_not_over:
        response = service_mail.users().messages().list(userId='me', q='!in:draft', pageToken=page_token, maxResults=100).execute()
        if 'messages' not in response:
            page_token = None
            break
        response_messages = None
        batch = service_mail.new_batch_http_request(callback=batch_cb)
        for message in response['messages']:
            batch.add(service_mail.users().messages().get(userId='me', id=message['id']))
        batch.execute()
        if batch_cb.stop:
            time_not_over = False       
        if "nextPageToken" in response:
            page_token = response["nextPageToken"]
        else:
            page_token = None

    for message in received_list:
        if message['email'] in frequency_dict:
            frequency_dict[message['email']] += 1
        else:
            frequency_dict[message['email']] = 1
            received_dict[message['email']] = {'name': message['name'], 'label': message['label']}
    for email in frequency_dict:
        received_dict[email]['frequency'] = frequency_dict[email]
    sorted_list_temp = sorted(frequency_dict, key=frequency_dict.get, reverse=True)
    sorted_list = []
    for email in sorted_list_temp:
        sorted_list.append((email, received_dict[email]['frequency'], received_dict[email]['name'], received_dict[email]['label']))
    return sorted_list

    # sent:
    '''
    page_token = ""
    time_not_over = True
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
    ans = sorted(received_dict, key=received_dict.get, reverse=True)
    return ans
    '''

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
    if 'forwardingAddresses' in result:
        for item in result['forwardingAddresses']:
            if item['forwardingEmail'] == forward_address:
                return item['verificationStatus']
    return False

def extract_emails_from_csv(email_string):
    emails = re.findall(r'[\w\.-]+@[\w\.-]+', email_string)
    return emails
