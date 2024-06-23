from django.db import models

from users.models import User


class flopLegendsModel(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    cover = models.ImageField(upload_to='covers', null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.title
