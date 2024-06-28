from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings


@database_sync_to_async
def get_user(user_id):
    User = get_user_model()
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        if 'Authorization' in headers:
            try:
                token_name, token_key = headers['Authorization'].split()
                if token_name == 'Bearer':
                    UntypedToken(token_key)
                    decoded_data = jwt.decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
                    scope['user'] = await get_user(decoded_data['user_id'])
            except (InvalidToken, TokenError, jwt.DecodeError, KeyError):
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
