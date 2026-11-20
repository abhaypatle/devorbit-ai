from functools import lru_cache

from pydantic import Field, field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    app_name: str = "DevOrbit AI"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://devorbit:devorbit@localhost:5432/devorbit"
    database_host: str | None = None
    database_port: int = 5432
    database_name: str | None = None
    database_user: str | None = None
    database_password: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]
    storage_mode: str = "filesystem"
    s3_bucket: str = "devorbit-documents"
    s3_region: str = "us-east-1"
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_presigned_url_ttl_seconds: int = 900
    local_storage_path: str = ".local-storage"
    embedding_provider: str = "local"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 384
    openai_api_key: str | None = None
    rag_chunk_size: int = 1200
    rag_chunk_overlap: int = 150
    rag_top_k: int = 5
    max_document_bytes: int = 10 * 1024 * 1024
    max_agent_input_chars: int = 20_000
    guardrail_block_injection: bool = True
    redact_emails: bool = True
    redact_phone_numbers: bool = True
    require_approval_for_invoices: bool = True
    invoice_approval_threshold_cents: int = 100_000
    invoice_due_days: int = 14
    default_tax_rate: float = 0.0
    payment_webhook_secret: str | None = None
    llm_default_provider: str = "local"
    llm_default_model: str = "local-hash-embedder"
    llm_input_price_per_million_usd: float = 0.0
    llm_output_price_per_million_usd: float = 0.0
    llm_provider_pricing: dict[str, dict[str, float]] = Field(default_factory=dict)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def configure_database_url(self) -> "Settings":
        if self.database_host is not None:
            if not all((self.database_name, self.database_user, self.database_password)):
                raise ValueError(
                    "DATABASE_NAME, DATABASE_USER, and DATABASE_PASSWORD are required "
                    "when DATABASE_HOST is configured"
                )
            self.database_url = URL.create(
                "postgresql+asyncpg",
                username=self.database_user,
                password=self.database_password,
                host=self.database_host,
                port=self.database_port,
                database=self.database_name,
            ).render_as_string(hide_password=False)
        return self

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 characters")
        return value

    @field_validator("storage_mode")
    @classmethod
    def validate_storage_mode(cls, value: str) -> str:
        if value not in {"memory", "filesystem", "s3"}:
            raise ValueError("STORAGE_MODE must be memory, filesystem, or s3")
        return value

    @field_validator("embedding_dimensions")
    @classmethod
    def validate_embedding_dimensions(cls, value: int) -> int:
        if value < 8:
            raise ValueError("EMBEDDING_DIMENSIONS must be at least 8")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
