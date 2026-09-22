from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

	app_env: str = "development"
	jwt_secret: str = Field(default="dev-only-change-this-secret-before-production-1234", min_length=32)
	jwt_algorithm: str = "HS256"
	access_token_minutes: int = Field(default=30, ge=5, le=1440)
	database_url: str = "postgresql+psycopg://devorbit:devorbit@localhost:5432/devorbit"
	allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
	aws_region: str = "us-east-1"
	bedrock_model_id: str = "amazon.nova-lite-v1:0"
	bedrock_enabled: bool = False
	github_webhook_secret: str = ""
	rate_limit_per_minute: int = Field(default=120, ge=10, le=10000)


@lru_cache
def get_settings() -> Settings:
	settings = Settings()
	if settings.app_env == "production" and settings.jwt_secret.startswith("dev-only-"):
		raise RuntimeError("JWT_SECRET must be set in production")
	return settings
