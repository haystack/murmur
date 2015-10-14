import string
import random



ALLOWED_TAGS = [
    'a',
    'abbr',
    'acronym',
    'b',
    'blockquote',
    'code',
    'em',
    'i',
    'li',
    'ol',
    'strong',
    'ul',
    'div',
    'br',
    'span',
    'img',
    'p',
    'h1',
    'h2',
    'h3',
    'pre',
    's',
    'html',
    'head',
    'meta',
    'body',
    'hr',
    'table',
    'tbody',
    'tr',
    'th',
    'td',
    'u',
    'font'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'abbr': ['title'],
    'acronym': ['title'],
    'img': ['src','alt', 'style', 'width', 'height'],
    'meta': ['content', 'http-equiv'],
    'body': ['bgcolor', 'text'],
    'div': ['class']
}

ALLOWED_STYLES = ['border-style', 'border-width', 'float', 'height', 'margin', 'width']


def load_groups(request, groups, user, group_name=None):
    
    if group_name:
        active_group = group_name
    else:
        if request:
            active_group = request.GET.get('group_name')
        
    if active_group:
        active_group = {'name': active_group,
                        'active': True}
    elif request.session.get('active_group'):
        active_group = request.session.get('active_group')
        active_group = {'name': active_group,
                        'active': True}
    elif len(groups) > 0:
        active_group = groups[0]
        active_group['active'] = True
    else:
        active_group = {'name': 'No Groups Yet',
                        'active': False}
    
    return active_group


def password_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))