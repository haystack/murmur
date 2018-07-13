from django.core.management.base import BaseCommand, CommandError
from smtp_handler.utils import *
from http_handler.settings import BASE_URL, DEFAULT_FROM_EMAIL, WEBSITE
from schema.models import *
from datetime import datetime, timedelta

class Command(BaseCommand):
    args = ''
    help = 'Export data to remote server'

    def handle(self, *args, **options):
        groups = Group.objects.filter()
        for group in groups:
            # Get lists of subjects of posts for given time span
            now = datetime.now()
            lastday_time = now - timedelta(hours = 24)
            posts = Post.objects.filter(timestamp__range=(lastday_time,now), group=group)
            if not posts.exists():
                continue

            digest_subject = "[" + group.name + "] Digest " + lastday_time.strftime('%m-%d %H:%M') + " ~ " + now.strftime('%m-%d') 
            
            # Iterate through members who turn on the digest feature
            memberGroups = MemberGroup.objects.filter(group=group, digest=True)
            for mg in memberGroups:
                post_cnt = 0
                digest_body = ""
                for p in posts:
                    # TODO do-not-send list
                    thread_posts = Post.objects.filter(thread = p.thread).select_related()
                    post_include = True

                    for tp in thread_posts:
                        if DoNotSendList.objects.filter(group=group, user=p.author, donotsend_user__email=mg.member.email).exists():
                            post_include = False
                            
                        if tp == p:
                            print "THIS POST" 
                            break

                    if post_include:
                        post_cnt = post_cnt + 1
                        permalink = PERMALINK_POST % (HOST, p.thread.id, p.id)
                        subject_link = str(post_cnt) + '. <a href="%s">' % (permalink)
                        subject_link += p.subject + '</a>'
                        sender_name = p.author.get_full_name() if p.author.get_full_name() != "" else p.author.email
                        digest_body += subject_link + " (" + sender_name  + ")<br/>"
                
                if digest_body != "":
                    digest_body = "Today's topics: <br/>" + digest_body

                addr = EDIT_SETTINGS_ADDR % (HOST, group.name)
                footer = "You are set to receive daily digests from this group. <BR><a href=\"%s\">Change your settings</a>" % (addr)

                footer = '%s%s%s' % (HTML_SUBHEAD, footer, HTML_SUBTAIL)
                digest_body = digest_body + footer

                send_email(digest_subject, DEFAULT_FROM_EMAIL, mg.member.email, body_html=digest_body)