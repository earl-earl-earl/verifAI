import redis.asyncio as redis
from app.core.config import settings

redis_client = None

async def connect():
    global redis_client
    redis_client = redis.from_url(settings.UPSTASH_REDIS_URL.get_secret_value(), ssl_cert_reqs=None)

async def disconnect():
    global redis_client
    await redis_client.close()

def get_redis():
    return redis_client