# This file contains python variables that configure Lamson for email processing.
import sys, os
import logging


# You may add additional parameters such as `username' and `password' if your
# relay server requires authentication, `starttls' (boolean) or `ssl' (boolean)
# for secure connections.
relay_config = {'host': os.getenv('RELAY_HOST', 'localhost'), 'port': 8825}

receiver_config = {'host': 'localhost', 'port': 8823}

handlers = ['smtp_handler.main']

router_defaults = {'host': '\*\\.mit\\.edu'}

template_config = {'dir': 'smtp_handler', 'module': 'templates'}

# hook django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "http_handler.settings")

# the config/boot.py will turn these values into variables set in settings
