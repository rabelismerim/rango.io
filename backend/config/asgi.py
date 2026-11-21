import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from django.core.asgi import get_asgi_application
django_app = get_asgi_application()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import re_path
from core.consumers import OrderConsumer
application = ProtocolTypeRouter({'http':django_app, 'websocket':AllowedHostsOriginValidator(URLRouter([re_path(r'^ws/orders/(?P<order_id>\d+)/$', OrderConsumer.as_asgi())]))})
