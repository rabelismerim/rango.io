from urllib.parse import parse_qs
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from .models import Order

class OrderConsumer(AsyncJsonWebsocketConsumer):
    @database_sync_to_async
    def allowed(self, token, order_id):
        try:
            user_id = int(AccessToken(token)['user_id'])
            order = Order.objects.select_related('restaurant').get(pk=order_id)
            return user_id in (order.customer_id, order.restaurant.owner_id)
        except Exception: return False
    async def connect(self):
        order_id = self.scope['url_route']['kwargs']['order_id']
        token = parse_qs(self.scope['query_string'].decode()).get('token', [''])[0]
        if not await self.allowed(token, order_id):
            await self.close(code=4403)
            return
        self.group = f'order_{order_id}'
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
    async def disconnect(self, code):
        if hasattr(self, 'group'): await self.channel_layer.group_discard(self.group, self.channel_name)
    async def order_update(self, event): await self.send_json({'id':event['id'], 'status':event['status']})
