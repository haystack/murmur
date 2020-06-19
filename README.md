
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/haystack/murmur?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge) [![Django version](https://img.shields.io/badge/django-1.6-blue.svg)](https://docs.djangoproject.com/en/2.2/releases/1.6/) [![python version](https://img.shields.io/badge/python-2.7-yellowgreen.svg)](https://www.python.org/download/releases/2.7/)

Murmur
=

Murmur uses Django with a MySQL backend (you can replace with any other backend Django supports). For email, we use postfix along with the python lamson library.

#### Private File

Please contact us for an example of the private file. You cannot run the program without it.

#### setup the database 
* change the root mysql account to one written in private file.
* make sure you can log in to mysql with the password in the command line: `mysql -u root -p`

## Running Docker

**Recommended to use Linux**
 
### Linux 

#### Set Up

To install the Docker Engine select your [Linux distribution](https://docs.docker.com/engine/install/#server) and follow the instructions to install. 

Currently you need a gmail account in order for Murmur to send verification emails, such as registration confirmation. In order for Murmur to log in to your gmail account you need to [enable less secure logins](https://support.google.com/accounts/answer/6010255?hl=en).

Next set up the environment variables. The only variables you should need to set are your gmail username and password.

1. `cp .env.example .env`
2. Fill in the correct values in `.env` for your gmail account. Make sure to enable insecure logins on gmail. 
3. Use `make` to create the database and create a superuser account to login
4. Check it out on `localhost:8000

#### Starting and Stopping Docker 

In order to stop docker you can simply run `make stop` and run `make start` to start it up again.

## Not Running Docker i.e. on the server

### Web Installation Instructions
  
#### Install MySQL Server

#### Install Git and clone this repository
* `git clone https://github.com/haystack/murmur.git`

#### install required linux packages if on linux
* `sudo apt-get install libmysqlclient-dev python-dev`

#### install virtualenv and python packages
* `/usr/bin/python2.7`
* pip: `sudo easy_install pip`
* `sudo pip install virtualenv `
* create a virtualenv for this project: `virtualenv murmur-env`
* make sure your virtualenv is activated: `source murmur-env/bin/activate`

#### install required python packages
* `pip install mysql-python`
* `pip install -r requirements.txt`

#### configuration
* edit database details in a new file called private.py. http_handler/settings.py looks for this file to populate database information:  
  `MYSQL_LOCAL = {  
	  'NAME': 'murmur',  
	  'USER': 'admin',  
	  'PASSWORD': 'password',  
	  'HOST': 'localhost'  
  }`
* also in this private.py file, add your Amazon S3 settings:
* `AWS_STORAGE_BUCKET_NAME = 'bucket-name-goes-here'`
* `AWS_ACCESS_KEY_ID = 'key-goes-here'`
* `AWS_SECRET_ACCESS_KEY = 'secret-key-goes-here'`
* create file /opt/murmur/env with single word containing "dev", "staging", or "prod" for the type of server you are setting up
* create file /opt/murmur/debug with single word containing "true" or "false" to turn on debug mode
* edit file /opt/murmur/website with single word containing "murmur" or "squadbox" to direct to the respective landing page
* If using Google integration, create a Google API project and enable the Gmail, People and Contacts APIs; generate an Oauth2 client_secrets.json file for this project and put this in the /gmail_setup/ directory
* Run [this command](https://github.com/haystack/murmur/blob/master/mysql_encoding) at mysql

#### setup the database 
* `mysql -u root -p`
* `create database murmur;`
* Give privileges to the user that will access the database from django: `grant all privileges ON murmur.* TO admin@localhost;`

#### install schema and create superuser
* `python manage.py syncdb`and create superuser
* Convert schema app to be managed by South: `python manage.py schemamigration schema --initial`
* Then do fake migration:  `python manage.py migrate schema 0001 --fake`

#### run murmur server
* Webserver: `python manage.py runserver 0.0.0.0:8000` (check [here](https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-apache-and-mod_wsgi-on-ubuntu-16-04) for details)

### Email Instructions
 
Setting for relay & outgoing server is in `config/settings.py` (Double check you open firewall for the ports)

#### Postfix setting (if you are using postfix as a relay system)

If you are using Postfix, you should update two postfix files:

1. `master.cf`: add a line `RELAY_PORT_YOU_SPECIFIED_at_config/settings.py      inet  n       -       n      -       -       smtpd`
2. `main.cf`: 
```
mydestination =
local_recipient_maps =
local_transport = error: local mail delivery disabled
relay_domains = YOUR DOMAIN NAME
relay_transport = smtp:127.0.0.1:[RECEIVER PORT YOU SPECIFIED at config/settings.py]
```

Then reboot Postfix. 

#### run murmur server
* If running email server: `lamson start`
	+ ⚠️ If it is not running without any error msg or throws `connection refused` error, then check your email port being used by other services (e.g., `netstat -peanut | grep ":8825"`) and check logs at logs/lamson.err. If the port is being used, use another port or kill the process using the port.  

#### enable daily digest feature
* `crontab -e` and add a line `0 */24 * * * python ABSOLUTE_DIRECTORY/manage.py digest`
