from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

routers = DefaultRouter()
routers.register(r'users_chat', views.ChatView, basename='users_chat')

urlpatterns = [
    path('', include(routers.urls)),
]