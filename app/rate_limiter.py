import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

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
        # Entferne veraltete Anfragen
        request_times = [t for t in request_times if now - t < self.window]
        if len(request_times) >= self.max_requests:
            return Response("Too Many Requests", status_code=429)
        request_times.append(now)
        self.clients[client_ip] = request_times
        response = await call_next(request)
        return response