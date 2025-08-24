from src.core.filenames import get_env
import os


def test_get_env_raises_on_missing():
    name = "__MISSING_TEST_ENV__"
    if name in os.environ:
        del os.environ[name]
    try:
        raised = False
        try:
            get_env(name)
        except RuntimeError:
            raised = True
        assert raised
    finally:
        if name in os.environ:
            del os.environ[name]


