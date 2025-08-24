from src.config.settings import AppConfig


def test_health_settings_defaults():
    assert isinstance(AppConfig.SERVER_HEALTH_URL, str)
    assert AppConfig.SERVER_HEALTH_TIMEOUT_MS >= 0
    assert AppConfig.SERVER_HEALTH_RETRY_MS >= 50


