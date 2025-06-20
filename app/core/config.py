from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str = "secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CHATGPT_API_KEY: str
    ANTHROPIC_API_KEY: str
    REDIS_URL: str
    RESET_PASSWORD_URL: str
    VECTOR_DB_URL: str
    VECTOR_DB_COLLECTION: str
    VECTOR_DB_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
