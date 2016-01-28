
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/haystack/murmur?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

Murmur
=

Murmur uses Django with a MySQL backend (you can replace with any other backend Django supports). For email, we use postfix along with the python lamson library.

### Installation Instructions

#### install required linux packages
`sudo apt-get install libmysqlclient-dev python-dev`

#### install required python packages
* `sudo pip install -r requirements.txt`

#### download murmur
`git clone https://github.com/haystack/murmur.git`

#### configuration
* configure your relay_server (postfix or something else) in config/settings.py
* use port other than 25 (default is currently set at 587)
* edit database details in a new file called private.py. http_handler/settings.py looks for this file to populate database information
* create file /opt/murmur/env with single word containing "dev", "staging", or "prod" for the type of server you are setting up
* create file /opt/murmur/debug with single word containing "true" or "false" to turn on debug mode


#### setup the database 
* `mysql -u root -p`
* `create database murmur`
* Give privileges to the user that will access the database from django: `grant all privileges ON murmur.* TO admin@localhost;`

#### install schema and create superuser
* `python manage.py syncdb`

#### run murmur server
* `lamson start`
* `python manage.py runserver`
