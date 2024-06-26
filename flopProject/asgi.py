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
django_settings_module = "flopProject.settings"

# Загрузка приложений Django
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import flopChat.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
            URLRouter(
                flopChat.routing.websocket_urlpatterns
            )
        ),
    })
