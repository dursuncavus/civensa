"""Apply the offline deck policy after the application's default headers."""
import re

from starlette.datastructures import MutableHeaders

DECK_POLICY = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
               "img-src data:; font-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'")
DECK_PATH = re.compile(r'/activity-sections/reports/[0-9]+/sunum(?:\.html)?')


class SunumSecurityHeaders:
    """Only successful deck responses can execute their embedded assets.

    The outer ASGI boundary is registered by the report router, after the global
    security middleware. All errors and other pages retain the default policy.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        is_deck = scope['type'] == 'http' and DECK_PATH.fullmatch(scope.get('path', ''))

        async def deck_send(message):
            if is_deck and message['type'] == 'http.response.start' and message['status'] == 200:
                headers = MutableHeaders(scope=message)
                if headers.get('content-type', '').startswith('text/html'):
                    headers['Content-Security-Policy'] = DECK_POLICY + "; frame-ancestors 'none'"
            await send(message)

        await self.app(scope, receive, deck_send)
