# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""

from sharelink.config import settings


def test_settings():
    assert isinstance(settings.SHARELINK_NAME, str)
    assert isinstance(settings.SHARELINK_DESCRIPTION, str)
    assert isinstance(settings.SHARELINK_AUTHOR, str)
    assert isinstance(settings.SHARELINK_ROBOT, str)
    assert isinstance(settings.SHARELINK_URL, str)
    assert isinstance(settings.SHARELINK_TZ, str)
    assert isinstance(settings.DATABASE_URL, str)
    assert isinstance(settings.LANGUAGE_CODE, str)
    assert isinstance(settings.SECRET_KEY, str)
    assert isinstance(settings.LINKS_PER_PAGE, int)
    assert isinstance(settings.DAILY_PER_PAGE, int)

    assert isinstance(settings.SECRET_KEY, str)
    assert isinstance(settings.COOKIE_SAMESITE, str)
    assert isinstance(settings.COOKIE_SECURE, bool)
    assert isinstance(settings.TOKEN_LOCATION, str)
    assert isinstance(settings.TOKEN_KEY, str)
    assert isinstance(settings.CSRF_TRUSTED_ORIGINS, str)
