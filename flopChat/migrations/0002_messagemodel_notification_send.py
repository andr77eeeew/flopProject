# Generated by Django 5.0.6 on 2024-07-01 20:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flopChat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagemodel',
            name='notification_send',
            field=models.BooleanField(default=False),
        ),
    ]
