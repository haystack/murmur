YoUPS
=

YoUPS is sharing a codebase of Murmur. Check out [Murmur](https://github.com/haystack/murmur/blob/master/README.md) to host YoUPS at your server. 


## Install & Set up

### Running Docker
1. `cp .env.example .env`
2. Fill in the correct values in `.env` for your gmail account. Make sure to enable insecure logins on gmail. 
3. `docker-compose up --force-recreate --build`
4. Check it out on `localhost:8000`

If you run into issues where the web container does not appear to be running 
try `sudo rm -rf run` and go to step 3.

### Not Running Docker

#### Database

1. Check out a how-to-setup instruction of [Murmur](https://github.com/haystack/murmur#setup-the-database) to learn how to set up the database on a new server.
2. If you make any change to the database, you should migrate those change like this:\
`python manage.py schemamigration schema --auto`\
`python manage.py migrate schema`\
3. Run [this sql script](https://github.com/soyapark/murmur/blob/master/youps_db_sql) on the database.

