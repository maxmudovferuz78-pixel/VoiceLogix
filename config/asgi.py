import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import config.routing  # Biz yaratgan routing.py faylini import qilamiz

# VoiceLogix.settings o'rniga config.settings qilamiz
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    # Oddiy HTTP so'rovlar uchun (Veb-sahifalar)
    "http": get_asgi_application(),

    # Jonli audio oqimlari (WebSocket) kelganda ishlaydigan qism
    "websocket": AuthMiddlewareStack(
        URLRouter(
            config.routing.websocket_urlpatterns
        )
    ),
})
