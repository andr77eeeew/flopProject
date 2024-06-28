import asyncio
import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Q
from .models import MessageModel
from users.models import User

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected for room '{self.room_name}'")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected for room '{self.room_name}' with code {close_code}")

    async def receive(self, text_data):
        logger.info(f"Received message: {text_data}")

        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json['type']
            sender_user = text_data_json['sender']
            recipient_user = text_data_json['recipient']

            sender = await self.get_user(sender_user)
            recipient = await self.get_user(recipient_user)

            if message_type == 'get_users':
                await self.process_messages(sender, recipient)
            elif message_type == 'chat_message':
                message = text_data_json['message']
                if message and sender_user and recipient_user:
                    await self.send_chat_message(sender, recipient, message)
                    await self.save_message(sender, recipient, message)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    @database_sync_to_async
    def get_user(self, username):
        logger.info(f"Fetching user: {username}")
        return User.objects.get(username=username)

    @database_sync_to_async
    def save_message(self, sender, recipient, content):
        logger.info(f"Saving message from {sender} to {recipient}: {content}")
        return MessageModel.objects.create(sender=sender, receiver=recipient, content=content)

    async def process_message(self, message):
        try:
            await asyncio.sleep(0.1)
            await self.send(json.dumps({
                'message': message.content,
                'sender': message.sender.username,
                'avatar': message.sender.avatar.url if message.sender.avatar.url else None,
                'recipient': message.receiver.username
            }))
            logger.info(f"Sended message: {message}")
        except Exception as e:
            logger.error(f"Error fetching and sending messages: {e}")

    async def process_messages(self, sender, recipient):
        logger.info(f"Fetching messages between {sender} and {recipient}")
        try:
            async for message in MessageModel.objects.filter(
                    (Q(sender=sender) & Q(receiver=recipient)) |
                    (Q(sender=recipient) & Q(receiver=sender))).select_related('sender', 'receiver'):
                await self.process_message(message)
                logger.info(f"Sent message: {message.content}, from {message.sender.username} and {message.sender.avatar.url} to {message.receiver.username} at {message.timestamp}")
        except Exception as e:
            logger.error(f"Error processing messages: {e}")

    @database_sync_to_async
    def fetch_messages(self, sender, recipient):
        logger.info(f"Fetching messages between {sender} and {recipient}")
        try:
            messages = MessageModel.objects.filter(
                (Q(sender=sender) & Q(receiver=recipient)) |
                (Q(sender=recipient) & Q(receiver=sender))
            ).filter()
            logger.info(f"Fetched {messages.count()} messages")
            return messages
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []

    async def send_chat_message(self, sender, recipient, message):
        logger.info(f"Sending chat message from {sender} to {recipient}: {message}")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender.username,
                'avatar': sender.avatar.url if sender.avatar.url else None,
                'recipient': recipient.username
            }
        )

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
