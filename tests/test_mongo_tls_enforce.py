from src.core.mongodb import _sanitize_mongo_uri


def test_sanitize_mongo_uri_srv_passthrough():
    uri = "mongodb+srv://user:pass@cluster.example.com/db"
    assert _sanitize_mongo_uri(uri) == uri


def test_sanitize_mongo_uri_add_tls():
    uri = "mongodb://user:pass@host:27017/db"
    out = _sanitize_mongo_uri(uri)
    assert out.startswith("mongodb://")
    assert "tls=true" in out or "tls=True" in out


def test_sanitize_mongo_uri_preserve_query():
    uri = "mongodb://user:pass@host:27017/db?retryWrites=true&w=majority"
    out = _sanitize_mongo_uri(uri)
    assert "retryWrites=true" in out
    assert "tls=true" in out


