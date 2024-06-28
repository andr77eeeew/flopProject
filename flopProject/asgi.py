"""
ASGI config for flopProject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
import django
from pathlib import Path

# Укажите путь к вашему файлу settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flopProject.settings')

# Загрузка приложений Django
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from flopChat.routing import websocket_urlpatterns
from flopChat.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
