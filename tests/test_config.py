import pytest

from app.config import Settings


def create_settings(**overrides):
    values = {
        "database_url": (
            "postgresql+psycopg://postgres:postgres" "@localhost:5432/deployment_risk"
        ),
    }

    values.update(overrides)

    return Settings(**values)


def test_scm_token_is_available():
    settings = create_settings(
        github_token="github-secret",
        gitlab_token="gitlab-secret",
    )

    assert settings.get_scm_token("github") == "github-secret"
    assert settings.get_scm_token("gitlab") == "gitlab-secret"


def test_scm_token_is_trimmed():
    settings = create_settings(
        github_token="  github-secret  ",
    )

    assert settings.get_scm_token("github") == "github-secret"


def test_missing_github_token_is_rejected():
    settings = create_settings(
        github_token="",
    )

    with pytest.raises(
        ValueError,
        match="github SCM token is not configured",
    ):
        settings.require_scm_token("github")


def test_missing_gitlab_token_is_rejected():
    settings = create_settings(
        gitlab_token="",
    )

    with pytest.raises(
        ValueError,
        match="gitlab SCM token is not configured",
    ):
        settings.require_scm_token("gitlab")


def test_unsupported_scm_provider_is_rejected():
    settings = create_settings()

    with pytest.raises(
        ValueError,
        match="Unsupported SCM provider",
    ):
        settings.get_scm_token("bitbucket")


def test_missing_gemini_key_is_rejected():
    settings = create_settings(
        gemini_api_key="",
    )

    with pytest.raises(
        ValueError,
        match="Gemini API key is not configured",
    ):
        settings.require_gemini_api_key()


def test_gemini_key_is_trimmed():
    settings = create_settings(
        gemini_api_key="  gemini-secret  ",
    )

    assert settings.require_gemini_api_key() == "gemini-secret"


def test_secrets_are_not_in_settings_repr():
    settings = create_settings(
        github_token="github-secret",
        gitlab_token="gitlab-secret",
        gemini_api_key="gemini-secret",
    )

    representation = repr(settings)

    assert "github-secret" not in representation
    assert "gitlab-secret" not in representation
    assert "gemini-secret" not in representation
