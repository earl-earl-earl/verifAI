from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App General Configuration
    DEBUG: bool = False
    ENVIRONMENT:str = "development"

    # MongoDB Atlas Configuration
    MONGODB_URL: SecretStr
    MONGODB_DB_NAME: str = "verifAI"

    # Upstash Redis Configuration
    UPSTASH_REDIS_URL: SecretStr
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: SecretStr
    UPSTASH_REDIS_CACHE_TTL: int = 3600

    # Gemini
    GEMINI_API_KEY: SecretStr

    # Model Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Model Singleton
settings = Settings()