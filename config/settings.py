# This file contains python variables that configure Lamson for email processing.
import sys, os
import logging
sys.path.append('./app')


# You may add additional parameters such as `username' and `password' if your
# relay server requires authentication, `starttls' (boolean) or `ssl' (boolean)
# for secure connections.
relay_config = {'host': 'localhost', 'port': 465}

receiver_config = {'host': '0.0.0.0', 'port': 25}

handlers = ['app.handlers.main']

router_defaults = {'host': '.+'}

template_config = {'dir': 'app', 'module': 'templates'}

# hook django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "browser.settings")

# the config/boot.py will turn these values into variables set in settings
