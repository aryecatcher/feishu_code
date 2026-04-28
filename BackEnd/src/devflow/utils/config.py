from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App Info
    app_name: str = "DevFlow Engine"
    app_version: str = "0.1.0"
    debug: bool = False

    # LLM Provider Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    deepseek_api_key: str = ""

    # Model Configuration
    openai_model: str = "gpt-4-turbo-preview"
    anthropic_model: str = "claude-3-opus-20240229"
    google_model: str = "gemini-pro"
    deepseek_model: str = "deepseek-chat"
    default_provider: str = "openai"

    # Database
    database_url: str = "sqlite+aiosqlite:///./devflow.db"

    # Redis (optional)
    redis_url: str = "redis://localhost:6379/0"

    # Logging
    log_level: str = "INFO"

    @property
    def llm_config(self) -> dict[str, str]:
        """Get LLM provider configuration."""
        return {
            "openai": {
                "api_key": self.openai_api_key,
                "model": self.openai_model,
            },
            "anthropic": {
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model,
            },
            "google": {
                "api_key": self.google_api_key,
                "model": self.google_model,
            },
            "deepseek": {
                "api_key": self.deepseek_api_key,
                "model": self.deepseek_model,
            },
        }


# Global settings instance
settings = Settings()
