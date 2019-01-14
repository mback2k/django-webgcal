from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter, URLRouter
import django_live_templates.routing

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                django_live_templates.routing.websocket_urlpatterns
            ),
        ),
    ),
})
