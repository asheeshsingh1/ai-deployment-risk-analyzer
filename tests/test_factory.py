import pytest

from app.config import Settings
from app.scm.factory import get_scm_provider


def test_github_provider_requires_token(monkeypatch):
    settings = Settings(
        database_url="sqlite://",
        github_token="",
        gemini_api_key="test-key",
    )

    monkeypatch.setattr(
        "app.scm.factory.get_settings",
        lambda: settings,
    )

    with pytest.raises(
        ValueError,
        match="github SCM token is not configured",
    ):
        get_scm_provider("github")


def test_gitlab_provider_requires_token(monkeypatch):
    settings = Settings(
        database_url="sqlite://",
        gitlab_token="",
        gemini_api_key="test-key",
    )

    monkeypatch.setattr(
        "app.scm.factory.get_settings",
        lambda: settings,
    )

    with pytest.raises(
        ValueError,
        match="gitlab SCM token is not configured",
    ):
        get_scm_provider("gitlab")


def test_unsupported_provider_is_rejected():
    with pytest.raises(
        ValueError,
        match="Unsupported SCM provider",
    ):
        get_scm_provider("bitbucket")
