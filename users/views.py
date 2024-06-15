from django.contrib.auth import authenticate, get_user_model, login
from django.http import JsonResponse
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.serializers import UserSerializer, LoginSerializer
import logging

logger = logging.getLogger(__name__)

class RegisterView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)


class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        logger.debug(f'Attempting login for user: {username}')

        user = authenticate(request, username=username, password=password)
        if not user:
            logger.warning(f'Failed login attempt for user: {username}')
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)
        logger.info(f'User authenticated successfully: {user}')

        # Создание или получение токена
        token, created = Token.objects.get_or_create(user=user)

        # Возвращаем токен и данные пользователя
        response = Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        })

        # Установка токена в куку
        response.set_cookie('token', token.key, max_age=3600, httponly=True)  # Например, срок действия 1 час
        return response