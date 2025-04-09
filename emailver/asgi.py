import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

# Set the Django settings module FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emailver.settings')

# Initialize Django application BEFORE importing consumers/routing
django_asgi_app = get_asgi_application()

# Now import WebSocket routes (which may reference models/consumers)
from Games.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(websocket_urlpatterns),
})