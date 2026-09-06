from __future__ import annotations


class SCMError(Exception):
    """Base exception for all SCM-related failures."""


class SCMProviderError(SCMError):
    """Provider API failure."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.status_code = status_code


class SCMAuthenticationError(SCMProviderError):
    """SCM authentication or authorization failure."""


class SCMNotFoundError(SCMProviderError):
    """Requested repository or change request does not exist."""


class SCMRateLimitError(SCMProviderError):
    """SCM provider rate limit was exceeded."""


class SCMRequestError(SCMProviderError):
    """Generic SCM API request failure."""
