import redis.asyncio as redis
from app.core.config import settings
from redis.asyncio import Redis

redis_client: Redis | None = None

async def connect() -> None:
    global redis_client
    redis_client = redis.from_url(settings.UPSTASH_REDIS_URL.get_secret_value(), ssl_cert_reqs=None)

async def disconnect() -> None:
    global redis_client  # noqa: PLW0602
    if redis_client is not None:
        await redis_client.close()

def get_redis() -> Redis:
    if redis_client is None:
        raise RuntimeError("Redis has not been initialized.")
    return redis_client