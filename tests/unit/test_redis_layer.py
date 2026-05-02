from fnmatch import fnmatch

from src.caching import redis_layer


class FakeRedis:
    def __init__(self):
        self.keys = {
            "query:abc:1": "{}",
            "query:def:2": "{}",
            "session:abc": "{}",
        }

    def scan_iter(self, match: str):
        for key in list(self.keys):
            if fnmatch(key, match):
                yield key

    def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            if key in self.keys:
                deleted += 1
                del self.keys[key]
        return deleted


def test_invalidate_query_cache_only_removes_query_keys(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(redis_layer, "_redis_client", fake)
    monkeypatch.setattr(redis_layer, "_redis_checked", True)

    deleted = redis_layer.invalidate_query_cache()

    assert deleted == 2
    assert fake.keys == {"session:abc": "{}"}
