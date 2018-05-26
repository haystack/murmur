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
            posts = Post.objects.filter(timestamp__range=(lastday_time,now))
            if not posts.exists():
                continue

            digest_subject = "[" + group.name + "] Digest " + lastday_time.strftime('%m-%d %H:%M') + " ~ " + now.strftime('%Y-%m-%d %H:%M') 
            
            # Iterate through members who turn on the digest feature
            memberGroups = MemberGroup.objects.filter(group=group, digest=True)
            for mg in memberGroups:
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
                        digest_body += p.subject + "\n"
                
                if digest_body != "":
                    digest_body = "Today's topics: \n" + digest_body
                send_email(digest_subject, DEFAULT_FROM_EMAIL, mg.member.email, digest_body)