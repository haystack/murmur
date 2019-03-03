YoUPS
=

YoUPS is sharing a codebase of Murmur. 

## Database

1. Check out an install instruction of [Murmur](https://github.com/haystack/murmur#setup-the-database) to learn how to set up the database on a new server.
2. If you make any change to the database, you should migrate those change like this:\
`python manage.py schemamigration schema --auto`\
`python manage.py migrate schema`
