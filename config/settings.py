# This file contains python variables that configure Lamson for email processing.
import sys, os
import logging
from http_handler.settings import EMAIL_PORT


# You may add additional parameters such as `username' and `password' if your
# relay server requires authentication, `starttls' (boolean) or `ssl' (boolean)
# for secure connections.
relay_config = {'host': os.getenv('RELAY_HOST', 'localhost'), 'port': 25}

receiver_config = {'host': '0.0.0.0', 'port': EMAIL_PORT}

handlers = ['smtp_handler.main']

router_defaults = {'host': '\*\\.mit\\.edu'}

template_config = {'dir': 'smtp_handler', 'module': 'templates'}

# hook django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "http_handler.settings")

# the config/boot.py will turn these values into variables set in settings
