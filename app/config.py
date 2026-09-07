from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "deployment-risk-analyzer"
    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str

    github_token: str = Field(
        default="",
        repr=False,
    )

    gitlab_token: str = Field(
        default="",
        repr=False,
    )

    gemini_api_key: str = Field(
        default="",
        repr=False,
    )

    gemini_model: str = "gemini-3.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_scm_token(self, provider: str) -> str:
        normalized_provider = provider.lower()

        if normalized_provider == "github":
            return self.github_token.strip()

        if normalized_provider == "gitlab":
            return self.gitlab_token.strip()

        raise ValueError(f"Unsupported SCM provider: {provider}")

    def require_scm_token(self, provider: str) -> str:
        token = self.get_scm_token(provider)

        if not token:
            raise ValueError(f"{provider.lower()} SCM token is not configured.")

        return token

    def require_gemini_api_key(self) -> str:
        api_key = self.gemini_api_key.strip()

        if not api_key:
            raise ValueError("Gemini API key is not configured.")

        return api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
