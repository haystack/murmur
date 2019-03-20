#!/bin/bash

# go to the root file
cd /home/ubuntu/production/mailx || exit;

# remove previous migrations
cd schema/migrations || exit;
# removes all migrations except __init__.py and __init__.pyc
ls | grep -v __init__.py | xargs -r rm;
cd /home/ubuntu/production/mailx || exit;

# create the new database
mysql -h $DATABASE_HOST -u root -p$MYSQL_PASS <<EOF
    drop database if exists $DATABASE_NAME;
    create database $DATABASE_NAME;
    grant all privileges ON $DATABASE_NAME.* TO root@localhost;
EOF

# create the initial tables
python manage.py syncdb;

# create the initial schema migration with south
python manage.py schemamigration schema --initial;

# apply the schema migration
python manage.py migrate schema

# alter tables to utf8
mysql -h $DATABASE_HOST -u root -p$MYSQL_PASS <<EOF
    USE $DATABASE_NAME;

    ALTER TABLE
        youps_folder
        CONVERT TO CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci;

    ALTER TABLE
        youps_message
        CONVERT TO CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci;

    ALTER TABLE
        youps_threads
        CONVERT TO CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci;

    ALTER TABLE
        schema_mailbotmode
        CONVERT TO CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci;

    ALTER TABLE
        schema_imapaccount
        CONVERT TO CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci;

    ALTER TABLE
        schema_action
        CONVERT TO CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci;

    ALTER TABLE
        youps_contact
        CONVERT TO CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci;

EOF

# set the domain name for the site
python manage.py shell <<EOF
from django.contrib.sites.models import Site
mysite = Site.objects.get_current()
mysite.domain = "$DOMAIN_NAME"
mysite.save()
EOF
