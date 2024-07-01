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
                    await self.send_chat_notification(sender, recipient, message)
            elif message_type == 'mark_as_read':
                await self.mark_messages_as_read(sender, recipient)
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
        except Exception as e:
            logger.error(f"Error fetching and sending messages: {e}")

    async def process_messages(self, sender, recipient):
        logger.info(f"Fetching messages between {sender} and {recipient}")
        try:
            async for message in MessageModel.objects.filter(
                    (Q(sender=sender) & Q(receiver=recipient)) |
                    (Q(sender=recipient) & Q(receiver=sender))).select_related('sender', 'receiver'):
                await self.process_message(message)
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

    @database_sync_to_async
    def mark_messages_as_read(self, sender, recipient):
        logger.info(f"Marking messages as read between {sender} and {recipient}")
        messages = MessageModel.objects.filter(
            (Q(sender=sender) & Q(receiver=recipient) & Q(is_read=False)) |
            (Q(sender=recipient) & Q(receiver=sender) & Q(is_read=False)))
        messages.update(is_read=True)

    async def send_chat_notification(self, sender, recipient, notification_message):
        message = await self.get_last_message(sender, recipient)
        if not message.notification_send:
            logger.info(f"Sending notification from {sender.username} to {recipient.username}: {notification_message}")
            await self.channel_layer.group_send(
                f"user_{recipient.username}",
                {
                    'type': 'send_notification',
                    'sender_id': sender.id,
                    'sender_avatar': sender.avatar.url if sender.avatar else None,
                    'sender_username': sender.username,
                    'notification': notification_message
                }
            )
            await self.mark_notofication_sent(message)

    @database_sync_to_async
    def mark_notification_sent(self, message):
        message.notification_send = True
        message.save()


    @database_sync_to_async
    def get_last_message(self, sender, recipient):
        return MessageModel.objects.filter(sender=sender, receiver=recipient).select_related('notification_send').order_by('-timestamp').first()

    async def send_notification(self, event):
        notification = event['notification']
        sender_id = event['sender_id']
        sender_avatar = event['sender_avatar']
        sender_username = event['sender_username']

        await self.send(text_data=json.dumps({
            'type': 'notification',
            'sender_id': sender_id,
            'sender_avatar': sender_avatar,
            'sender_username': sender_username,
            'notification': notification
        }))


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

    async def process_notification(self, user):
        logger.info(f"Processing notification for {user}")
        try:
            async for message in MessageModel.objects.filter(receiver=user, is_read=False, notification_send=False).select_related('sender', 'receiver' 'notification_send'):
                await self.send_chat_notification(message.sender, message.receiver, message.content)
                await self.mark_notification_sent(message)
                logger.info(f"Sending notification: {message}")
        except Exception as e:
            logger.error(f"Error processing notification: {e}")

    async def send_chat_notification(self, sender, recipient, notification_message):
        logger.info(f"Sending notification from {sender.username} to {recipient.username}: {notification_message}")
        await self.channel_layer.group_send(
            f"user_{recipient.username}",
            {
                'type': 'send_notification',
                'sender_id': sender.id,
                'sender_username': sender.username,
                'sender_avatar': sender.avatar.url if sender.avatar else None,
                'notification': notification_message
            }
        )

    async def send_notification(self, event):
        notification = event['notification']
        sender_id = event['sender_id']
        sender_avatar = event['sender_avatar']
        sender_username = event['sender_username']

        await self.send(text_data=json.dumps({
            'type': 'notification',
            'sender_id': sender_id,
            'sender_avatar': sender_avatar,
            'sender_username': sender_username,
            'notification': notification
        }))

    @database_sync_to_async
    def mark_notification_sent(self, message):
        message.notification_send = True
        message.save()
