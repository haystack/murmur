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
            now = datetime.datetime.now()
            lastday_time = now - timedelta(hours = 24)
            posts = Post.objects.filter(timestamp__range=(lastday_time,now))

            if not posts.exists():
                continue
                
            digest_subject = "[" + group.name + "]Digest " + lastday_time.strftime('%Y-%m-%d %H:%M') " ~ " + now.strftime('%Y-%m-%d %H:%M') 
            digest_body = "Today's topics: <br/>"
            for p in posts:
                digest_body = p.subject + "<br/>"

            # Iterate through members who turn on the digest feature
            memberGroups = MemberGroup.objects.filter(group=group, digest=True)
            for mg in memberGroups:
                send_email(digest_subject, DEFAULT_FROM_EMAIL, mg.member.email, digest_body)