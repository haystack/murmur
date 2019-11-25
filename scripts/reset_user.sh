#!/bin/bash

# stop on errors
set -e

# stop the cron jobs
pidfile="/home/ubuntu/production/mailx/loop_sync_user_inbox2.lock"
exec 200>$pidfile
flock 200 || exit 1
pidfile="/home/ubuntu/production/mailx/register_inbox2.lock"
exec 201>$pidfile
flock 201 || exit 1

# read the users email
if [ $# -eq 0 ]; then
    read -p "Please enter your email: " email
    echo 
else
    email=$1
fi

# run our code
python manage.py shell <<EOF
from schema.youps import *
me = ImapAccount.objects.get(email="$email")
me.execution_log = ""
MessageSchema.objects.filter(imap_account=me).delete()
FolderSchema.objects.filter(imap_account=me).delete()
BaseMessage.objects.filter(imap_account=me).delete()
ContactSchema.objects.filter(imap_account=me).delete()
ContactAlias.objects.filter(imap_account=me).delete()
me.is_initialized = False
me.save()
EOF

