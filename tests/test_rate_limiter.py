import time
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.rate_limiter import RateLimitMiddleware

app = FastAPI()
app.add_middleware(RateLimitMiddleware, max_requests=3, window_seconds=5)

@app.get("/test")
async def test_endpoint():
    return {"message": "ok"}

client = TestClient(app)

def test_rate_limit():
    # 3 Requests sollten gehen
    for _ in range(3):
        response = client.get("/test")
        assert response.status_code == 200
    # Der 4. Request innerhalb des Fensters muss blockiert werden
    response = client.get("/test")
    assert response.status_code == 429
    # Nach Ablauf des Fensters sollte wieder ein Request funktionieren
    time.sleep(5)
    response = client.get("/test")
    assert response.status_code == 200
