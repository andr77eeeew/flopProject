from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    email = models.EmailField(unique=True)
    profile_music = models.FileField(upload_to='profile_music', null=True, blank=True)

