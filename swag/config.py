from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = ""
    channel_id: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    poll_interval_min: int = 30
    fresh_hours: int = 48
    max_posts_per_cycle: int = 15
    min_llm_score: int = 6
    db_path: Path = Path("data/swag.db")
    timezone: str = "Europe/Moscow"
    dry_run: bool = True


def load_settings() -> Settings:
    return Settings()
