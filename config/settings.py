# This file contains python variables that configure Lamson for email processing.
import sys
import logging

sys.path.append('./webapp')

# You may add additional parameters such as `username' and `password' if your
# relay server requires authentication, `starttls' (boolean) or `ssl' (boolean)
# for secure connections.
relay_config = {'host': 'localhost', 'port': 8825}

receiver_config = {'host': 'slow.csail.mit.edu', 'port': 25}

handlers = ['app.handlers.slow_distribute', 'lamson.handlers.log']

router_defaults = {'host': 'localhost'}

template_config = {'dir': 'app', 'module': 'templates'}

# hook django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "browser.settings")

# the config/boot.py will turn these values into variables set in settings
