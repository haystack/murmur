
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/haystack/murmur?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

Murmur
=

Murmur uses Django with a MySQL backend (you can replace with any other backend Django supports). For email, we use postfix along with the python lamson library.

### Installation Instructions
  
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

#### if setting up a local email server (not necessary to run webserver)
* configure your relay_server (postfix or something else) in config/settings.py
* use port other than 25 (default is currently set at 587)

#### setup the database 
* (optional: only during new database setup) change root password by: `set PASSWORD = PASSWORD('newPassword');`
* `mysql -u root -p`
* `create database murmur;`
* Give privileges to the user that will access the database from django: `grant all privileges ON murmur.* TO admin@localhost;`

#### install schema and create superuser
* `python manage.py syncdb`and create superuser
* Convert schema app to be managed by South: `python manage.py schemamigration schema --initial`
* Then do fake migration:  `python manage.py migrate schema 0001 --fake`

#### run murmur server
* If running email server: `lamson start`
	+ ⚠️ If it is not running without any error msg or throws `connection refused` error, then check your email port being used by other services (e.g., `netstat -peanut | grep ":587"`) and check logs at logs/lamson.err. If the port is being used, use another port or kill the process using the port.   
* Webserver: `python manage.py runserver 0.0.0.0:8000`

#### enable daily digest feature
* `crontab -e` and add a line `0 */24 * * * python ABSOLUTE_DIRECTORY/manage.py digest`
