from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings
from urllib.parse import parse_qs

@database_sync_to_async
def get_user(user_id):
    User = get_user_model()
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_params = parse_qs(scope['query_string'].decode())
        if 'token' in query_params:
            token_key = query_params['token'][0]
            try:
                decoded_data = jwt.decode(token_key, settings.SECRET_KEY, algorithms=["HS256"])
                scope['user'] = await get_user(decoded_data['user_id'])
            except (InvalidToken, TokenError, jwt.DecodeError, KeyError):
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)