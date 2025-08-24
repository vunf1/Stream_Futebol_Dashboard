import os
import tempfile
import json
import time

from src.core.file_cache import read_json_cached, write_json_sync, shutdown_file_cache


def test_file_cache_mtime_ns_detection():
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, 'test.json')
        try:
            write_json_sync(p, {"a": 1})
            # Spin-wait for async writer to flush
            for _ in range(50):
                d1 = read_json_cached(p, {})
                if d1.get("a") == 1:
                    break
                time.sleep(0.02)
            assert read_json_cached(p, {}).get("a") == 1
            # Write a second time very quickly to ensure ns granularity works
            write_json_sync(p, {"a": 2})
            for _ in range(50):
                d2 = read_json_cached(p, {})
                if d2.get("a") == 2:
                    break
                time.sleep(0.02)
            assert read_json_cached(p, {}).get("a") == 2
        finally:
            # Ensure background writer stops before temp dir removal
            shutdown_file_cache()


