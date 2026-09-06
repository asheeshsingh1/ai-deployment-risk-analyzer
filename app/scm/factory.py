from app.config import get_settings
from app.scm.base import SCMProvider
from app.scm.github.provider import GitHubProvider
from app.scm.gitlab.provider import GitLabProvider


def get_scm_provider(
    provider: str,
) -> SCMProvider:
    settings = get_settings()

    normalized_provider = provider.lower()

    if normalized_provider == "github":
        return GitHubProvider(
            token=settings.github_token,
        )

    if normalized_provider == "gitlab":
        return GitLabProvider(
            token=settings.gitlab_token,
        )

    raise ValueError(f"Unsupported SCM provider: {provider}")
