YoUPS
=

YouPS is forked from the codebase of Murmur. If you run into issues in your installation check out [Murmur](https://github.com/haystack/murmur/blob/master/README.md) and you may find an answer. Otherwise open an issue and let us know! 

## Install & Set up

### Private File 

Please contact us for an example of the private file. You cannot run the program without it.

### Running Docker

Currently you need a gmail account in order for Murmur to send verification emails, such as registration confirmation. In order for Murmur to log in to your gmail account you need to [enable less secure logins](https://support.google.com/accounts/answer/6010255?hl=en).

Next set up the environment variables. The only variables you should need to set are your gmail username and password.

1. `cp .env.example .env`
2. Fill in the correct values in `.env` for your gmail account. Make sure to enable insecure logins on gmail. 
3. Now you can start the application using `make start` 
4. Check it out on `localhost:8000`

If you run into issues where the web container does not appear to be running 
try `sudo rm -rf run` and go to step 3. Make sure you do not commit the changes to the `run/.gitignore` these are needed on the server.

### Stopping Docker 

In order to stop docker you can simply run `make stop`

### Not Running Docker i.e. on the server

The server requires some setup to be run from scratch. 

1. You need mysql 5.7 and python 2.7
2. You must have the requirements in requirements.docker.txt installed 
3. You must have a mail server running. See instructions at [Murmur](https://github.com/haystack/murmur#if-setting-up-a-local-email-server-not-necessary-to-run-webserver)
4. You must have apache2 running django
5. you must have the files in murmur-env stored in /opt/murmur

**Set up the cron jobs** by enabling the cronjobs in `tasks-cron-server`. The easiest way to do this is to use `crontab -e` and paste the cron jobs.

#### Database

1. You can set up the initial database by running `./scripts/new_database.sh`
2. If you make any change to the database, you should migrate those change like this:

```sh
python manage.py schemamigration schema --auto \
python manage.py migrate schema
```
