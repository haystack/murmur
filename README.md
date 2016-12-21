
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/haystack/murmur?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

Murmur
=

Murmur uses Django with a MySQL backend (you can replace with any other backend Django supports). For email, we use postfix along with the python lamson library.

### Installation Instructions

#### make sure to use system python
* if a non-system Python is used as standard Python (check with `which python`), the following error may be encountered:  
  `ERROR: The executable /Users/username/Documents/workspace/murmur/bin/python is not functioning`  
  `ERROR: It thinks sys.prefix is '/Users/username/Documents/workspace' (should be '/Users/username/Documents/workspace/murmur')`  
  `ERROR: virtualenv is not compatible with this system or executable`  
* must point virtualenv to the correct Python installation
* fix: comment out wrong base prefix in .bash_profile  
  `sudo vi .bash_profile`  
  comment out `#export PATH="//anaconda/bin:$PATH"`  
  `source ~/.bash_profile`  

#### install virtualenv
* `/usr/bin/python2.7`
* pip: `sudo easy_install pip`
* `sudo pip install virtualenv `

#### install required linux packages
* `sudo apt-get install libmysqlclient-dev python-dev`

#### install required python packages
* `pip install mysql-python`
* `sudo pip install -r requirements.txt`

#### download murmur
* `git clone https://github.com/haystack/murmur.git`

#### configuration
* configure your relay_server (postfix or something else) in config/settings.py
* use port other than 25 (default is currently set at 587)
* edit database details in a new file called private.py. http_handler/settings.py looks for this file to populate database information:  
  `MYSQL_LOCAL = {  
	  'NAME': 'murmur',  
	  'USER': 'root',  
	  'PASSWORD': 'password',  
	  'HOST': 'localhost'  
  }`
* create file /opt/murmur/env with single word containing "dev", "staging", or "prod" for the type of server you are setting up
* create file /opt/murmur/debug with single word containing "true" or "false" to turn on debug mode
* edit file /opt/murmur/website with single word containing "murmur" or "squadbox" to direct to the respective landing page


#### setup the database 
* (optional: only during new database setup) change root password by: `set PASSWORD = PASSWORD('newPassword');`
* `mysql -u root -p`
* `create database murmur`
* Give privileges to the user that will access the database from django: `grant all privileges ON murmur.* TO admin@localhost;`

#### install schema and create superuser
* `python manage.py syncdb`and create superuser
* fake migration: `python manage.py migrate schema 0001 --fake`

#### run murmur server
* `lamson start`
* `python manage.py runserver`
