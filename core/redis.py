import os
import redis.asyncio as redis
from django.conf import settings

# Usually defined in Celery setup, but we provide a default for local dev
REDIS_URL = getattr(
    settings,
    "CELERY_BROKER_URL",
    os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
)


async def get_redis_client() -> redis.Redis:
    """Returns an async redis client."""
    return redis.from_url(REDIS_URL, decode_responses=True)
