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


def load_groups(request, group_names, user, group_name=None):
    
    if group_name:
        active_group = group_name
    else:
        if request:
            active_group = request.GET.get('group_name')
        else:
            active_group = None
        
    if active_group:
        active_group = {'name': active_group,
                        'active': True}
    elif request.session.get('active_group') in group_names:
        active_group = {'name': request.session.get('active_group'),
                        'active': True}
        
    elif len(group_names) > 0:
        active_group = {'name': group_names[0],
                        'active': True}
    else:
        active_group = {'name': 'No Groups Yet',
                        'active': False}
    
    return active_group


def password_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))