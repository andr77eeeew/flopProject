import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class VoiceChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
        else:
            self.room_group_name = f'chat_{self.room_name}'

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
        logger.info(f"Получен сообщение: {text_data}")
        try:
            text_data_json = json.loads(text_data)
            signal = text_data_json.get('signal')
            sender = text_data_json.get('sender')

            await self.send_signal_message(self.room_group_name, signal, sender)
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")

    async def send_signal_message(self, room_group_name, signal, sender):
        await self.channel_layer.group_send(
            room_group_name,
            {
                'type': 'signal_message',
                'signal': signal if signal else None,
                'sender': sender,
            }
        )

    async def signal_message(self, event):
        logger.info(f"Обработка сигнального сообщения: {event}")
        try:
            signal = event['signal']
            sender = event['sender']

            logger.info(f"Получено сигнальное сообщение: signal={signal}, sender={sender}")

            await self.send_signal_message(self.room_group_name, signal, sender)
        except Exception as e:
            logger.error(f"Ошибка при отправке сигнального сообщения: {e}")

    async def signal_message_handler(self, event):
        await self.signal_message(event)