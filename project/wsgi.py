"""
WSGI config for project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import sys

# Add your project root to the Python path
# This helps Python find your 'project' and other app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')) # Add parent directory

# Explicitly set DJANGO_SETTINGS_MODULE before getting the WSGI application
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings' 

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
