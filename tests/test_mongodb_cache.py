from src.core.mongodb import SmartTeamCache
import time


def test_smart_team_cache_basic_behavior():
    c = SmartTeamCache(base_ttl=1)
    c.set_teams({"A": "AA"})
    assert c.get_team("A") == "AA"
    # Selective invalidation
    c.invalidate_team("A")
    assert c.get_team("A") is None
    # Adaptive TTL behavior (with low usage, TTL should be raised to at least 60s)
    ttl = c.get_ttl()
    assert ttl >= 60


