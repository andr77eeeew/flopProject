import os

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import jwt

SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')



def index(request):
    if request.method == 'POST':
        token = request.headers.get('Authorization', '').split(' ')[1]
        try:
            decoded_token = jwt.decode(token, 'secret', algorithms=['HS256'])
            return JsonResponse({'token': decoded_token})
        except jwt.DecodeError:
            return JsonResponse({'error': 'Invalid token'}, status=401)

    token = jwt.encode({'user_id': 1}, SECRET_KEY, algorithm='HS256')

    response = JsonResponse({'token': token.decode('utf-8')})
    response.set_cookie('token', token, httponly=True)

    return response
