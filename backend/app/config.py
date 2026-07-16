import os
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "MIDAS 2.0 Dataset Quality Evaluation Toolkit"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # Postgres Database
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_DB: str = Field(default="aikosh_quality")
    POSTGRES_HOST: str = Field(default="postgres")
    POSTGRES_PORT: str = Field(default="5432")
    
    @property
    def DATABASE_URL(self) -> str:
        # Standard synchronous URL for migrations/direct DB calls
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        # Async URL for FastAPI async database operations
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis (Broker + Results)
    REDIS_URL: str = Field(default="redis://redis:6379/0")

    # MinIO / S3 Object Storage
    S3_ENDPOINT_URL: str = Field(default="http://minio:9000")
    S3_PUBLIC_ENDPOINT_URL: str = Field(default="http://localhost:9000")
    S3_ACCESS_KEY: str = Field(default="minioadmin")
    S3_SECRET_KEY: str = Field(default="minioadmin")
    S3_BUCKET_NAME: str = Field(default="aikosh-datasets")
    S3_REGION: str = Field(default="us-east-1")

    # Security
    API_KEY_SECRET: str = Field(default="tkt_secret_super_secure_key_12345678")
    JWT_SECRET: str = Field(default="supersecretjwtsessionkeychangeinproduction123456!")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRY_MINUTES: int = Field(default=43200)
    CORS_ORIGINS: list[str] = Field(default=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3001", "http://127.0.0.1:3001"
    ])

    # Integrations & Thresholds
    AIKOSH_WEBHOOK_URL: str = Field(default="")
    AIKOSH_WEBHOOK_SECRET: str = Field(default="")
    MAX_FILE_SIZE_BYTES: int = Field(default=5368709120)
    PROFILING_SAMPLE_ROWS: int = Field(default=100000)

    @field_validator("JWT_SECRET")
    @classmethod
    def jwt_secret_min_length(cls, v):
        assert len(v) >= 32, "JWT_SECRET must be at least 32 characters long"
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
