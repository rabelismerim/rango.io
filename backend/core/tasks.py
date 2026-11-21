from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Order

@shared_task(autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=3)
def notify_order(order_id):
    order = Order.objects.get(pk=order_id)
    async_to_sync(get_channel_layer().group_send)(f'order_{order.pk}', {'type':'order.update', 'id':order.pk, 'status':order.status})
