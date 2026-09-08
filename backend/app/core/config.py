from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):

    database_url : str

    openai_api_key: str | None = None

    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str

    SLACK_CLIENT_ID: str
    SLACK_CLIENT_SECRET: str
    SLACK_REDIRECT_URI: str

    LINEAR_CLIENT_ID: str
    LINEAR_CLIENT_SECRET: str
    LINEAR_REDIRECT_URI: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()