import time

from src.ui import DebouncedEventBus


def test_debounced_event_bus_coalesces_events():
    bus = DebouncedEventBus(delay_ms=50)
    calls = {"n": 0}
    def cb():
        calls["n"] += 1
    bus.subscribe("tick", cb)
    for _ in range(10):
        bus.publish("tick")
    time.sleep(0.2)
    assert calls["n"] == 1


