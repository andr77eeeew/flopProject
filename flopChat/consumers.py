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
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
        else:
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
                    await self.send_notification(recipient, sender, f"Новое сообщение от {sender.username}: {message}")
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
            await self.send(json.dumps({
                'message': message.content,
                'sender': message.sender.username,
                'avatar': message.sender.avatar.url if message.sender.avatar else None,
                'recipient': message.receiver.username
            }))
            logger.info(f"Sent message: {message}")
        except Exception as e:
            logger.error(f"Error fetching and sending messages: {e}")

    async def process_messages(self, sender, recipient):
        logger.info(f"Fetching messages between {sender} and {recipient}")
        try:
            async for message in MessageModel.objects.filter(
                    (Q(sender=sender) & Q(receiver=recipient)) |
                    (Q(sender=recipient) & Q(receiver=sender))).select_related('sender', 'receiver'):
                await self.process_message(message)
                logger.info(f"Sent message: {message.content}, from {message.sender.username} to {message.receiver.username} at {message.timestamp}")
        except Exception as e:
            logger.error(f"Error processing messages: {e}")

    async def send_chat_message(self, sender, recipient, message):
        logger.info(f"Sending chat message from {sender} to {recipient}: {message}")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender.username,
                'avatar': sender.avatar.url if sender.avatar else None,
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

    async def send_notification(self, sender, recipient, message):
        logger.info(f"Sending notification to {recipient.username}: {message}")
        await self.channel_layer.group_send(
            f"user_{recipient.username}",
            {
                'type': 'notification',
                'sender_id': sender.id,
                'sender_avatar': sender.avatar.url if sender.avatar else None,
                'notification': message
            }
        )


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"user_{self.user.username}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"WebSocket connected for user '{self.user.username}'")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected for user '{self.user.username}' with code {close_code}")

    async def receive(self, text_data):
        logger.info(f"Received message: {text_data}")
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json['type']
            if message_type == 'notification':
                await self.process_notification(self.user)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    @database_sync_to_async
    def fetch_unread_messages(self, user):
        logger.info(f"Fetching unread messages for {user}")
        try:
            unread_messages = MessageModel.objects.filter(receiver=user, is_read=False)
            logger.info(f"Fetched {unread_messages.count()} unread messages")
            return unread_messages
        except Exception as e:
            logger.error(f"Error fetching unread messages: {e}")
            return []

    async def process_notification(self, user):
        logger.info(f"Processing notification for {user}")
        try:
            unread_messages = await self.fetch_unread_messages(user)
            for message in unread_messages:
                notification = {
                    'sender_id': message.sender.id,
                    'sender_avatar': message.sender.avatar.url if message.sender.avatar else None,
                    'notification': f"New message from {message.sender.username}: {message.content}"
                }
                await self.send_notification(notification)
                message.is_read = True
                await database_sync_to_async(message.save)()
        except Exception as e:
            logger.error(f"Error processing notification: {e}")

    async def send_notification(self, notification):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            **notification
        }))