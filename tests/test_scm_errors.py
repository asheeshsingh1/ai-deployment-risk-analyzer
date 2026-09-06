import httpx
import pytest

from app.scm.exceptions import (
    SCMAuthenticationError,
    SCMNotFoundError,
    SCMRateLimitError,
    SCMRequestError,
)
from app.scm.github.provider import GitHubProvider
from app.scm.gitlab.provider import GitLabProvider


def response(
    status_code: int,
    *,
    json_data=None,
    headers=None,
    text="",
) -> httpx.Response:
    request = httpx.Request(
        "GET",
        "https://example.com",
    )

    if json_data is not None:
        return httpx.Response(
            status_code,
            json=json_data,
            headers=headers,
            request=request,
        )

    return httpx.Response(
        status_code,
        text=text,
        headers=headers,
        request=request,
    )


@pytest.mark.parametrize(
    ("provider_class", "status_code", "exception"),
    [
        (GitHubProvider, 401, SCMAuthenticationError),
        (GitHubProvider, 404, SCMNotFoundError),
        (GitHubProvider, 429, SCMRateLimitError),
        (GitLabProvider, 401, SCMAuthenticationError),
        (GitLabProvider, 404, SCMNotFoundError),
        (GitLabProvider, 429, SCMRateLimitError),
    ],
)
def test_provider_maps_http_errors(
    monkeypatch,
    provider_class,
    status_code,
    exception,
):
    provider = provider_class(token="test-token")

    monkeypatch.setattr(
        httpx,
        "request",
        lambda *args, **kwargs: response(
            status_code,
            json_data={"message": "test error"},
        ),
    )

    with pytest.raises(exception):
        provider._request("GET", "/test")


def test_github_rate_limit_detected_from_headers(monkeypatch):
    provider = GitHubProvider(token="test-token")

    monkeypatch.setattr(
        httpx,
        "request",
        lambda *args, **kwargs: response(
            403,
            json_data={"message": "rate limit exceeded"},
            headers={"X-RateLimit-Remaining": "0"},
        ),
    )

    with pytest.raises(SCMRateLimitError):
        provider._request("GET", "/test")


def test_provider_maps_timeout(monkeypatch):
    provider = GitHubProvider(token="test-token")

    def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(
        httpx,
        "request",
        raise_timeout,
    )

    with pytest.raises(SCMRequestError):
        provider._request("GET", "/test")
