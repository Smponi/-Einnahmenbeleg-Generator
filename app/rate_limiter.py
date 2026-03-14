import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse

_RATE_LIMIT_HTML = """<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"><title>Zu viele Anfragen</title>
<style>body{font-family:Arial,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:#f7f7f7;}
.box{background:#fff;padding:2rem;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.1);text-align:center;max-width:400px;}
h2{color:#dc3545;}p{color:#555;}</style></head>
<body><div class="box"><h2>Zu viele Anfragen</h2>
<p>Sie haben das Anfrage-Limit überschritten. Bitte warten Sie eine Minute und versuchen Sie es erneut.</p></div></body></html>"""

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Einfache Middleware, die pro IP maximal max_requests innerhalb von window_seconds zulässt.
    """
    def __init__(self, app, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self.clients = {}  # {ip: [timestamp, ...]}

    async def dispatch(self, request, call_next):
        client_ip = request.client.host
        now = time.time()
        request_times = self.clients.get(client_ip, [])
        # Entferne veraltete Anfragen und leere Einträge (verhindert Memory Leak)
        request_times = [t for t in request_times if now - t < self.window]
        if not request_times and client_ip in self.clients:
            del self.clients[client_ip]
        if len(request_times) >= self.max_requests:
            return HTMLResponse(_RATE_LIMIT_HTML, status_code=429)
        request_times.append(now)
        self.clients[client_ip] = request_times
        response = await call_next(request)
        return response