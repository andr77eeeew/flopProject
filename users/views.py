from django.contrib.auth import logout
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from django.middleware.csrf import get_token
from users.models import User
from users.serializers import UserSerializer, RegisterSerializer, LoginSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response({
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
        })
        response.set_cookie('access', str(refresh.access_token), httponly=True, secure=False)
        response.set_cookie('refresh', str(refresh), httponly=True, secure=False)
        return response


class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        response = Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': access,
        })
        response.set_cookie('access', access, httponly=True, secure=False)
        response.set_cookie('refresh', str(refresh), httponly=True, secure=False)
        return response


class LogoutView(APIView):
    authentication_classes = [JWTAuthentication, ]
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logout(request)
            response = Response(status=status.HTTP_205_RESET_CONTENT)
            response.delete_cookie('access')
            response.delete_cookie('refresh')
            return response
        else:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)


def get_csrf_token(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrfToken': csrf_token})


class UserDetailView(generics.RetrieveAPIView):
    authentication_classes = [JWTAuthentication, ]
    permission_classes = [IsAuthenticated, ]

    def get(self, request, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
