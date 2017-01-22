import re
MAX_GROUP_NAME_LENGTH = 20
MAX_GROUP_DESC_LENGTH = 140

msg_code={
	'USER_DOES_NOT_EXIST': 'User %s does not exist in Murmur system.',
	'PRIVILEGE_ERROR': 'Do not have the required privileges',
	'NOT_MEMBER': 'Not a member of this Group',
	'DUPLICATE_ERROR': 'Name already exists',
	'GROUP_NOT_FOUND_ERROR': 'Group not found',
	'POST_NOT_FOUND_ERROR': 'Post not found',
	'THREAD_NOT_FOUND_ERROR': 'Thread not found',
	'TAG_NOT_FOUND_ERROR': 'Tag not found',
	'OWNER_UNSUBSCRIBE_ERROR': 'Can not unsubscribe the owner',
	'REQUEST_ERROR': 'Incorrect request parameters',
	'INCORRECT_GROUP_NAME': 'Group name cannot be of this format',
	'MAX_GROUP_NAME_LENGTH': 'Group name is too long',
	'MAX_GROUP_DESC_LENGTH': 'Group description is too long',
	'UNKNOWN_ERROR': 'Unknown',
	'INVALID_STATUS_ERROR' : '%s is not a valid post status',
}

def extract_hash_tags(s):
	s = re.sub("<.*?>", " ", s)
	s = re.sub("&nbsp;", " ", s)
	
	tags = [re.sub(r'\W+', '', part).lower() for part in s.split() if part.startswith('#') and not part[1:].isdigit()]

	first_three = set()
	for t in tags:
		first_three.add(t)
		if len(first_three) == 3: break
	return first_three 

ALLOWED_MESSAGE_STATUSES = {
	'R' : 'rejected',
	'P' : 'pending',
	'A' : 'approved'
}
