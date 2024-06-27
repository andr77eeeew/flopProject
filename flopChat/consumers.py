import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import MessageModel
from users.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        if 'get_users' in self.scope:
            try:
                text_data_json = json.loads(self.scope['get_users'])
                sender_username = text_data_json['sender']
                recipient_username = text_data_json['recipient']

                messages = await self.get_messages(sender_username, recipient_username)

                for message in messages:
                    await self.send(text_data=json.dumps({
                        'message': message.content,
                        'sender': message.sender.username,
                        'avatar': message.sender.avatar.url,
                        'recipient': message.recipient.username
                    }))
            except json.JSONDecodeError:
                pass
        else:
            pass

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_username = text_data_json['sender']
        recipient_username = text_data_json['recipient']

        if message and sender_username and recipient_username:
            sender = await self.get_user(sender_username)
            recipient = await self.get_user(recipient_username)

            if sender.avatar:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender': sender.username,
                        'avatar': sender.avatar.url,
                        'recipient': recipient.username
                    }
                )
            else:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender': sender.username,
                        'avatar': None,
                        'recipient': recipient.username
                    }
                )

            await self.save_message(sender, recipient, message)

    @database_sync_to_async
    def get_user(self, username):
        return User.objects.get(username=username)

    @database_sync_to_async
    def save_message(self, sender, recipient, content):
        return MessageModel.objects.create(sender=sender, receiver=recipient, content=content)

    @database_sync_to_async
    def get_messages(self, sender, recipient):
        return (MessageModel.objects.filter(sender=sender, receiver=recipient) |
                MessageModel.objects.filter(sender=recipient, receiver=sender))

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        recipient = event['recipient']
        avatar = event['avatar']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'avatar': avatar,
            'recipient': recipient
        }))


