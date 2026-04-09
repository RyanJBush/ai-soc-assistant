from backend.app.core.config import Settings
from backend.app.core.rate_limit import InMemoryRateLimiter, RedisRateLimiter, build_rate_limiter


def test_in_memory_rate_limiter_enforces_threshold() -> None:
    limiter = InMemoryRateLimiter(requests_per_minute=2)
    assert limiter.allow("client:/predict")
    assert limiter.allow("client:/predict")
    assert not limiter.allow("client:/predict")


def test_build_rate_limiter_handles_redis_backend_configuration() -> None:
    settings = Settings(
        rate_limit_backend="redis",
        redis_url="redis://localhost:6379/0",
        rate_limit_per_minute=123,
        redis_rate_limit_prefix="test-prefix",
    )
    limiter = build_rate_limiter(settings)
    assert isinstance(limiter, (RedisRateLimiter, InMemoryRateLimiter))


def test_redis_rate_limiter_fails_open_when_backend_errors() -> None:
    class RedisLikeError(Exception):
        pass

    class FailingPipeline:
        def incr(self, _key: str) -> None:
            return None

        def expire(self, _key: str, _ttl: int) -> None:
            return None

        def execute(self) -> list[int]:
            raise RedisLikeError("redis unavailable")

    class FakeRedisClient:
        def pipeline(self) -> FailingPipeline:
            return FailingPipeline()

    limiter = RedisRateLimiter(
        redis_url="redis://localhost:6379/0",
        requests_per_minute=2,
        key_prefix="ai_soc",
        client=FakeRedisClient(),
        redis_error_types=(RedisLikeError,),
    )
    assert limiter.allow("client:/predict")


def test_redis_rate_limiter_blocks_after_threshold() -> None:
    class TrackingPipeline:
        def __init__(self, client):
            self.client = client

        def incr(self, _key: str) -> None:
            self.client.calls += 1
            return None

        def expire(self, _key: str, _ttl: int) -> None:
            return None

        def execute(self) -> list[int]:
            return [self.client.calls, 1]

    class FakeRedisClient:
        def __init__(self):
            self.calls = 0

        def pipeline(self) -> TrackingPipeline:
            return TrackingPipeline(self)

    limiter = RedisRateLimiter(
        redis_url="redis://localhost:6379/0",
        requests_per_minute=2,
        key_prefix="ai_soc",
        client=FakeRedisClient(),
    )
    assert limiter.allow("client:/predict")
    assert limiter.allow("client:/predict")
    assert not limiter.allow("client:/predict")
