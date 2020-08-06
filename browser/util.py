import string, random, logging

from django.core.paginator import EmptyPage, Paginator, PageNotAnInteger
from bleach import clean
from bs4 import BeautifulSoup
from schema.models import MemberGroup, Attachment

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

ALLOWED_STYLES = ['border-style', 'border-width', 'float', 'height', 'margin', 'width', 'max-width']

logger = logging.getLogger('murmur')


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
    mg_res = MemberGroup.objects.filter(member=user, group__name=group_name)
    if not mg_res.exists():
        return None
    mg = mg_res[0]
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

'''
so inline attachments weren't displaying if the post was made via SMTP, because they would 
show up in the post body as something like <img src="cid:xxxx" alt="filename_here"> where 
the cid is the content-id of the attachment in the original post. but it's not a real link,
so the browser had no way to render the image.

this function cleans the HTML up and then goes through and finds all the inline images, and 
if their "alt" tag (the filename) matches a stored attachment, replaces the src with a link 
to the image on S3.
'''
def fix_html_and_img_srcs(msg_id, post_text, include_line_break = True):
    if not include_line_break:
        post_text = post_text.replace("<br>", " ")
        post_text = post_text.replace("<br/>", " ")
    
    post_soup = BeautifulSoup(post_text, 'html5lib')
    imgs = post_soup.find_all('img')
    attachments = Attachment.objects.filter(msg_id=msg_id)
    for i in imgs:
        filename = i.get('alt')
        cid = i.get('src')
        match = None

        if filename:
            match_by_filename = attachments.filter(true_filename=filename)
            if match_by_filename.exists():
                match = match_by_filename[0]

        if cid and not match:
            id_no = '<%s>' % cid.split(':')[1]
            match_by_cid = attachments.filter(content_id=id_no)
            if match_by_cid.exists():
                match = match_by_cid[0]

        if match:
            i['src'] = "attachment/" + match.hash_filename

    style = post_soup.find_all('style')
    for s in style:
        s.replace_with('')

    return clean(str(post_soup), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, styles=ALLOWED_STYLES)
