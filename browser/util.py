import string
import random

from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger

from schema.models import MemberGroup

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
        active_group = request.GET.get('group_name')
        
    names = [g['name'] for g in groups]
    
    if active_group:
        active_group = {'name': active_group,
                        'active': True}
    elif request.session.get('active_group') in names:
        active_group = {'name': request.session.get('active_group'),
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

def paginator(page, object_list, per_page=10):
    """
    Provides pagination for a given list of objects.
    Call function for any page needing pagination.
    """
    paginator = Paginator(object_list, per_page)

    try:
        objects = paginator.page(page)

    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        objects = paginator.page(1)

    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        objects = []
    return objects

def get_role_from_group_name(user, group_name):
    mg = MemberGroup.objects.get(member=user, group__name=group_name)
    if mg.admin:
        return 'admin'
    if mg.moderator:
        return 'mod'
    return 'member'

def get_groups_links_from_roles(user, groups):

    group_names = [g['name'] for g in groups]
    
    links = []
    for g in group_names:
        role = get_role_from_group_name(user, g)
        if role == 'admin':
            links.append('/groups/%s' % g)
        elif role == 'mod':
            links.append('/mod_queue/%s' % g)
        else:
            links.append(None) # no default link right now for just a member

    return zip(group_names, links)