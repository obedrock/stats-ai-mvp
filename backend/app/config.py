from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://stats_ai:stats_ai_dev@localhost:5432/stats_ai"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-to-at-least-32-random-characters"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days
    debug: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
