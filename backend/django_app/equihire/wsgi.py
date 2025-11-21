"""
WSGI config for equihire project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equihire.settings')

application = get_wsgi_application()

