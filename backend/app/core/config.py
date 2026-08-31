from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):

    database_url : str

    openai_api_key: str | None = None

    langchain_api_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_public_key: str | None = None
    langfuse_base_url: str | None = None

    langchain_tracing_v2: bool = False
    langchain_project: str | None = None

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()