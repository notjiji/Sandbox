import redis

from app.core.config import get_settings

_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(get_settings().REDIS_URL, decode_responses=True)
    return _redis_client
