from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Brauzer ws://127.0.0.1:8000/ws/audio/ manziliga ulanmoqchi bo'lsa,
    # uni AudioStreamConsumer ga yo'naltiramiz
    re_path(r'ws/audio/$', consumers.AudioStreamConsumer.as_asgi()),
]