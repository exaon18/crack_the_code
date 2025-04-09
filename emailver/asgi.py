# Games/routing.py
from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack  # Add this
from Games import consumers,routing



application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(  # Wrap with authentication middleware
        URLRouter(routing.websocket_urlpatterns)
    ),
})