import logging
from importlib import import_module
from importlib.util import find_spec
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock
from time import time

from backend.app.core.config import Settings

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.window = timedelta(minutes=1)
        self._history: dict[str, deque[datetime]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = datetime.now(tz=timezone.utc)
        with self._lock:
            entries = self._history[key]
            cutoff = now - self.window
            while entries and entries[0] < cutoff:
                entries.popleft()
            if len(entries) >= self.requests_per_minute:
                return False
            entries.append(now)
            return True


class RedisRateLimiter:
    def __init__(
        self,
        redis_url: str,
        requests_per_minute: int,
        key_prefix: str,
        client=None,
        redis_error_types: tuple[type[BaseException], ...] = (Exception,),
    ):
        self.requests_per_minute = requests_per_minute
        self.key_prefix = key_prefix
        self._redis_error_types = redis_error_types
        if client is not None:
            self.client = client
            return

        if find_spec("redis") is None:
            raise RuntimeError(
                "redis package is not installed; install backend requirements "
                "or set RATE_LIMIT_BACKEND=memory"
            )
        redis_module = import_module("redis")
        redis_exceptions = import_module("redis.exceptions")
        self._redis_error_types = (redis_exceptions.RedisError,)
        self.client = redis_module.Redis.from_url(redis_url, decode_responses=True)

    def allow(self, key: str) -> bool:
        current_window = int(time() // 60)
        redis_key = f"{self.key_prefix}:{key}:{current_window}"
        try:
            pipeline = self.client.pipeline()
            pipeline.incr(redis_key)
            pipeline.expire(redis_key, 120)
            count, _ = pipeline.execute()
            return int(count) <= self.requests_per_minute
        except self._redis_error_types:
            logger.warning("redis_rate_limit_unavailable", exc_info=True)
            return True


def build_rate_limiter(settings: Settings) -> InMemoryRateLimiter | RedisRateLimiter:
    if settings.rate_limit_backend == "redis":
        try:
            return RedisRateLimiter(
                redis_url=settings.redis_url,
                requests_per_minute=settings.rate_limit_per_minute,
                key_prefix=settings.redis_rate_limit_prefix,
            )
        except RuntimeError:
            logger.warning("redis_dependency_missing_falling_back_to_memory", exc_info=True)
    return InMemoryRateLimiter(requests_per_minute=settings.rate_limit_per_minute)
