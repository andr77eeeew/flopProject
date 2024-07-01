from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import MessageModel
from users.serializers import UserSerializer
from django.db.models import Q


class ChatView(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        messages = MessageModel.objects.filter(Q(sender=user) | Q(receiver=user)).select_related('sender', 'receiver')

        users = set()
        for message in messages:
            users.add(message.sender)
            users.add(message.receiver)
        users.discard(user)
        return list(users)
