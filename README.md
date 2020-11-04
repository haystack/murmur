
[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/haystack/murmur?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge) [![Django version](https://img.shields.io/badge/Django-1.10-blue)](https://docs.djangoproject.com/en/3.0/releases/1.10/) [![python version](https://img.shields.io/badge/python-2.7-yellowgreen.svg)](https://www.python.org/download/releases/2.7/)

Murmur
=

Murmur uses Django with a MySQL backend (you can replace with any other backend Django supports). For email, we use postfix along with the python lamson library.

#### Install Git and clone this repository
* `git clone https://github.com/haystack/murmur.git`

## Running Docker

**Recommended to use Linux**
 
### Linux 

#### Set Up

To install the Docker Engine select your [Linux distribution](https://docs.docker.com/engine/install/#server) and follow the instructions to install. 

Currently you need a gmail account in order for Murmur to send verification emails, such as registration confirmation.

Next set up the environment variables. The only variables you should need to set are your gmail username and password.

1. `cp .env.example .env`
2. Fill in the correct values in `.env` for your gmail account. Put your gmail address and a google app password.
3. `cp private.py.example private.py`
4. Fill in the correct values in `private.py` such as your AWS IDs for message-attachment storage.  
5. Use `make` to create the database and create a superuser account to login
6. Check it out on `localhost:8000`

#### setup the database 
* change the root mysql account to one written in `.env`
* make sure you can log in to mysql with the password in the command line: `mysql -u root -p`

#### Starting and Stopping Docker 

In order to stop docker you can simply run `make stop` and run `make start` to start it up again.


If you want to deploy Murmur on your own server and domain, check out the [advanced settings](https://github.com/haystack/murmur/wiki/Advanced-set-up:-server-deployment)
