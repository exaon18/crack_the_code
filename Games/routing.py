from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'wss/ctc/(?P<amount>\d+)/$', consumers.Crack_the_CodeConsumer.as_asgi()),
    re_path(r'ws/bingo/(?P<amount>\d+)/$', consumers.BingoConsumer.as_asgi()),

]