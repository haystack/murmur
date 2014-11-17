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
    'body'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'abbr': ['title'],
    'acronym': ['title'],
    'img': ['src','alt', 'style'],
    'meta': ['content', 'http-equiv'],
    'body': ['bgcolor', 'text']
}

ALLOWED_STYLES = ['border-style', 'border-width', 'float', 'height', 'margin', 'width']


def load_groups(request, groups, user):
        
    active_group = request.GET.get('group_name')
    if active_group:
        request.session['active_group'] = active_group
        active_group = {'name': active_group}
    elif request.session.get('active_group'):
        active_group = request.session.get('active_group')
        active_group = {'name': active_group}
    elif len(groups) > 0:
        active_group = groups[0]
    else:
        active_group = {'name': 'No Groups Yet'}
    
    return active_group


def password_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))