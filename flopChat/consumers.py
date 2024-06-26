import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from flopChat.models import MessageModel
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

        sender = self.scope['sender']
        recipient = self.scope['recipient']

        messages = await sync_to_async(MessageModel.objects.filter)(sender=sender,recipient=recipient) | await sync_to_async(MessageModel.objects.filter)(sender=recipient, recipient=sender)
        for message in messages:
            await self.send(text_data=json.dumps({
                'message': message.content,
                'sender': message.sender.username,
                'avatar': message.sender.avatar.url,
                'recipient': message.recipient.username
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_username = text_data_json['sender_username']
        recipient_username = text_data_json['recipient_username']

        if message and sender_username and recipient_username:
            sender = await sync_to_async(User.objects.get)(username=sender_username)
            recipient = await sync_to_async(User.objects.get)(username=recipient_username)

            msg = MessageModel(sender=sender, recipient=recipient, content=message)
            await sync_to_async(msg.save)()

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

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        recipient = event['recipient']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'recipient': recipient
        }))
