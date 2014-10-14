MailX
=
### Installation Instructions

#### install required linux packages
`sudo apt-get install postgresql`

#### install required python packages
* `sudo pip install -r requirements.txt`

#### download mailx
`git clone git@github.com:abhardwaj/mailx.git`

#### configuration
* configure your relay_server (exim4 or sendmail) in config/settings.py
* use port other than 25 (default 587)
* edit database details in http_handler/settings.py 


#### setup the database 
* `psql -U postgres -W -h localhost`
* `create database mailx`

#### install schema
* `python manage.py syncdb`

#### run mailx server
* `lamson start`
* `python manage.py runserver`
