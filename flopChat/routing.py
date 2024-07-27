from django.urls import re_path
from .import consumers, voice_consumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notification/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/call/(?P<room_name>\w+)/$', voice_consumer.VoiceChatConsumer.as_asgi()),
]