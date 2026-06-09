from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    github_app_id: str = ""
    github_private_key_path: str = "private-key.pem"
    github_webhook_secret: str = ""
    redis_url: str = "redis://localhost:6379"
    environment: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()