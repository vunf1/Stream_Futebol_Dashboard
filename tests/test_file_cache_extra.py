from src.core.file_cache import invalidate_file_cache, shutdown_file_cache, read_json_cached
import tempfile
import os
import time
import json


def test_invalidate_and_shutdown_idempotent():
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, 'x.json')
        try:
            # Write baseline JSON directly (avoids dependency on async writer thread)
            with open(p, 'w', encoding='utf-8') as f:
                json.dump({"k": 1}, f)
            assert read_json_cached(p, {}).get("k") == 1
            # Invalidate cache and read again
            invalidate_file_cache(p)
            assert read_json_cached(p, {}).get("k") == 1
        finally:
            # Shutdown twice should not raise
            shutdown_file_cache()
            shutdown_file_cache()


