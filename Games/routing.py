from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'wss/ctc/(?P<amount>\d+)/$', consumers.Crack_the_CodeConsumer.as_asgi()),
]